from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, date, timedelta
from models import db, User, Location, Item, InventoryItem, Inventory, InventoryDetail, AuditLog
from sqlalchemy import and_, or_, func
from forms import LoginForm, UserForm, LocationForm, ItemForm, InventoryItemForm, InventoryForm, SearchForm

# Blueprints
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)
inventory_bp = Blueprint('inventory', __name__)

def log_audit(action, table_name, record_id, old_values=None, new_values=None):
    """Log audit trail for all changes"""
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=str(old_values) if old_values else None,
        new_values=str(new_values) if new_values else None,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

# Main routes
@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    # Calculate dashboard statistics
    from sqlalchemy import func, and_
    
    # Total active inventory items (sum of all quantities across all locations)
    total_items = db.session.query(func.sum(InventoryItem.quantity)).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None
    ).scalar() or 0
    
    # Count of locations
    location_count = Location.query.filter_by(deleted_at=None, is_active=True).count()
    
    # Count of low stock items (items below minimum threshold) - ONLY for Supply Room locations
    low_stock_count = db.session.query(func.count(Item.id)).join(
        Location, Location.location_type == 'supply_room'
    ).outerjoin(
        InventoryItem, db.and_(
            InventoryItem.item_id == Item.id,
            InventoryItem.location_id == Location.id,
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None
        )
    ).filter(
        Item.is_active == True,
        Item.deleted_at == None,
        Item.minimum_threshold > 0,
        Location.is_active == True,
        Location.deleted_at == None
    ).group_by(
        Location.id, Item.id, Item.minimum_threshold
    ).having(
        func.coalesce(func.sum(InventoryItem.quantity), 0) <= Item.minimum_threshold
    ).count()
    
    # Count of expired items
    today = date.today()
    expired_count = db.session.query(func.count(InventoryItem.id)).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date < today,
        InventoryItem.expiration_date.isnot(None)
    ).scalar() or 0
    
    # Count of items expiring soon (within 30 days)
    expiring_soon_count = db.session.query(func.count(InventoryItem.id)).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date >= today,
        InventoryItem.expiration_date <= today + timedelta(days=30),
        InventoryItem.expiration_date.isnot(None)
    ).scalar() or 0
    
    # Generate alerts
    alerts = []
    
    if expired_count > 0:
        alerts.append({
            'type': 'danger',
            'message': f'{expired_count} item(s) have expired and need immediate attention.'
        })
    
    if expiring_soon_count > 0:
        alerts.append({
            'type': 'warning',
            'message': f'{expiring_soon_count} item(s) are expiring within 30 days.'
        })
    
    if low_stock_count > 0:
        alerts.append({
            'type': 'warning',
            'message': f'{low_stock_count} item(s) are below minimum stock levels.'
        })
    
    # Get current date
    now = datetime.now()
    
    return render_template('index.html', 
                         total_items=total_items,
                         low_stock_count=low_stock_count,
                         expired_count=expired_count,
                         location_count=location_count,
                         alerts=alerts,
                         now=now)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, deleted_at=None).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.now()
            db.session.commit()
            log_audit('LOGIN', 'user', user.id)
            return redirect(url_for('main.index'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT', 'user', current_user.id)
    logout_user()
    return redirect(url_for('main.login'))

# Admin routes
@admin_bp.route('/')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.')
        return redirect(url_for('main.index'))
    
    users = User.query.filter_by(deleted_at=None).all()
    locations = Location.query.filter_by(deleted_at=None).all()
    items = Item.query.filter_by(deleted_at=None).all()
    
    return render_template('admin/dashboard.html', users=users, locations=locations, items=items)

@admin_bp.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    users = User.query.filter_by(deleted_at=None).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_audit('CREATE', 'user', user.id, new_values=form.data)
        flash('User created successfully.')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/user_form.html', form=form, title='New User')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        log_audit('UPDATE', 'user', user.id, old_values={'username': user.username, 'email': user.email, 'is_admin': user.is_admin})
        flash('User updated successfully.')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/user_form.html', form=form, title='Edit User')

@admin_bp.route('/locations')
@login_required
def manage_locations():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    locations = Location.query.filter_by(deleted_at=None).all()
    return render_template('admin/locations.html', locations=locations)

@admin_bp.route('/locations/new', methods=['GET', 'POST'])
@login_required
def new_location():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    form = LocationForm()
    if form.validate_on_submit():
        location = Location(
            name=form.name.data,
            description=form.description.data,
            location_type=form.location_type.data,
            vehicle_id=form.vehicle_id.data
        )
        db.session.add(location)
        db.session.commit()
        log_audit('CREATE', 'location', location.id, new_values=form.data)
        flash('Location created successfully.')
        return redirect(url_for('admin.manage_locations'))
    
    return render_template('admin/location_form.html', form=form, title='New Location')

@admin_bp.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_location(location_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    location = Location.query.get_or_404(location_id)
    form = LocationForm(obj=location)
    
    if form.validate_on_submit():
        location.name = form.name.data
        location.description = form.description.data
        location.location_type = form.location_type.data
        location.vehicle_id = form.vehicle_id.data
        
        db.session.commit()
        log_audit('UPDATE', 'location', location.id, old_values={'name': location.name, 'description': location.description, 'location_type': location.location_type, 'vehicle_id': location.vehicle_id})
        flash('Location updated successfully.')
        return redirect(url_for('admin.manage_locations'))
    
    return render_template('admin/location_form.html', form=form, title='Edit Location')

@admin_bp.route('/items')
@login_required
def manage_items():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    items = Item.query.filter_by(deleted_at=None).all()
    return render_template('admin/items.html', items=items)

@admin_bp.route('/items/new', methods=['GET', 'POST'])
@login_required
def new_item():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            item_number=form.item_number.data,
            manufacturer=form.manufacturer.data,
            is_required=form.is_required.data,
            required_quantity=form.required_quantity.data or 0,
            minimum_threshold=form.minimum_threshold.data or 0
        )
        db.session.add(item)
        db.session.commit()
        log_audit('CREATE', 'item', item.id, new_values=form.data)
        flash('Item created successfully.')
        return redirect(url_for('admin.manage_items'))
    
    return render_template('admin/item_form.html', form=form, title='New Item')

@admin_bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.item_number = form.item_number.data
        item.manufacturer = form.manufacturer.data
        item.is_required = form.is_required.data
        item.required_quantity = form.required_quantity.data or 0
        item.minimum_threshold = form.minimum_threshold.data or 0
        
        db.session.commit()
        log_audit('UPDATE', 'item', item.id, old_values={'name': item.name, 'item_number': item.item_number, 'manufacturer': item.manufacturer, 'is_required': item.is_required, 'required_quantity': item.required_quantity, 'minimum_threshold': item.minimum_threshold})
        flash('Item updated successfully.')
        return redirect(url_for('admin.manage_items'))
    
    return render_template('admin/item_form.html', form=form, title='Edit Item')

# Inventory routes
@inventory_bp.route('/')
@login_required
def inventory_dashboard():
    locations = Location.query.filter_by(deleted_at=None, is_active=True).all()
    items = Item.query.filter_by(deleted_at=None, is_active=True).all()
    
    # Get current inventory summary with all instances
    inventory_summary = db.session.query(
        Location.name.label('location_name'),
        Item.name.label('item_name'),
        Item.id.label('item_id'),
        Location.id.label('location_id'),
        InventoryItem.quantity.label('quantity'),
        InventoryItem.expiration_date.label('expiration_date'),
        InventoryItem.lot_number.label('lot_number'),
        InventoryItem.id.label('inventory_item_id')
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).filter(
        InventoryItem.is_active == True, 
        InventoryItem.deleted_at == None
    ).order_by(Location.name, Item.name, InventoryItem.expiration_date).all()
    
    # Get last inventory date for each location
    location_last_inventory = {}
    for location in locations:
        last_inv = Inventory.query.filter(
            Inventory.location_id == location.id,
            Inventory.is_active == True,
            Inventory.deleted_at == None
        ).order_by(Inventory.inventory_date.desc()).first()
        
        if last_inv:
            location_last_inventory[location.id] = last_inv.inventory_date.date()
        else:
            location_last_inventory[location.id] = None
    
    # Add today's date for expiry calculations
    today = date.today()
    today_plus_30 = today + timedelta(days=30)
    
    return render_template('inventory/dashboard.html', 
                         locations=locations, 
                         items=items, 
                         inventory_summary=inventory_summary,
                         location_last_inventory=location_last_inventory,
                         today=today,
                         today_plus_30=today_plus_30)

@inventory_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_inventory():
    form = InventoryForm()
    form.location_id.choices = [(l.id, l.name) for l in Location.query.filter_by(deleted_at=None, is_active=True).all()]
    
    if form.validate_on_submit():
        inventory = Inventory(
            location_id=form.location_id.data,
            user_id=current_user.id,
            notes=form.notes.data
        )
        db.session.add(inventory)
        db.session.commit()
        log_audit('CREATE', 'inventory', inventory.id, new_values=form.data)
        return redirect(url_for('inventory.edit_inventory', inventory_id=inventory.id))
    
    return render_template('inventory/new_inventory.html', form=form)

@inventory_bp.route('/<int:inventory_id>/edit', methods=['GET'])
@login_required
def edit_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    
    # Get current inventory items for this location
    current_inventory_items = db.session.query(InventoryItem).filter(
        InventoryItem.location_id == inventory.location_id,
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None
    ).all()
    
    # Create a list of items with their current quantities
    items = []
    for inv_item in current_inventory_items:
        item = inv_item.item
        if item and item.is_active and not item.deleted_at:
            items.append({
                'item': item,
                'current_quantity': inv_item.quantity,
                'current_expiration': inv_item.expiration_date,
                'current_lot_number': inv_item.lot_number,
                'inventory_item_id': inv_item.id
            })
    
    all_items = Item.query.filter_by(deleted_at=None, is_active=True).all()
    
    return render_template('inventory/edit_inventory.html', inventory=inventory, items=items, all_items=all_items)

@inventory_bp.route('/<int:inventory_id>/update-item', methods=['POST'])
@login_required
def update_inventory_item(inventory_id):
    """Update a single inventory item in real-time"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 0))
        expiration_date = data.get('expiration_date')
        lot_number = data.get('lot_number', '')
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Check if inventory item already exists
        inventory_item = InventoryItem.query.filter_by(
            item_id=item_id,
            location_id=inventory.location_id,
            is_active=True,
            deleted_at=None
        ).first()
        
        if inventory_item:
            # Update existing item
            old_values = {
                'quantity': inventory_item.quantity,
                'expiration_date': inventory_item.expiration_date,
                'lot_number': inventory_item.lot_number
            }
            
            inventory_item.quantity = quantity
            inventory_item.expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None
            inventory_item.lot_number = lot_number
            
            if quantity == 0:
                # Soft delete if quantity is 0
                inventory_item.is_active = False
                inventory_item.deleted_at = datetime.now()
                action = 'DELETE'
            else:
                action = 'UPDATE'
        else:
            # Create new inventory item
            if quantity > 0:
                inventory_item = InventoryItem(
                    item_id=item_id,
                    location_id=inventory.location_id,
                    quantity=quantity,
                    expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None,
                    lot_number=lot_number
                )
                db.session.add(inventory_item)
                action = 'CREATE'
                old_values = None
            else:
                # Don't create item with 0 quantity
                return jsonify({'success': True, 'message': 'Item not created (quantity is 0)'})
        
        db.session.commit()
        
        # Log the action
        if action != 'DELETE':
            log_audit(action, 'inventory_item', inventory_item.id, old_values, {
                'quantity': quantity,
                'expiration_date': expiration_date,
                'lot_number': lot_number
            })
        
        return jsonify({
            'success': True, 
            'message': f'Item updated successfully',
            'inventory_item_id': inventory_item.id if inventory_item else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/<int:inventory_id>/add-item', methods=['POST'])
@login_required
def add_item_to_inventory(inventory_id):
    """Add a new item to the inventory in real-time"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 0))
        expiration_date = data.get('expiration_date')
        lot_number = data.get('lot_number', '')
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than 0'}), 400
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Check if item already exists in inventory
        existing_item = InventoryItem.query.filter_by(
            item_id=item_id,
            location_id=inventory.location_id,
            is_active=True,
            deleted_at=None
        ).first()
        
        if existing_item:
            return jsonify({'success': False, 'error': 'Item already exists in inventory'}), 400
        
        # Create new inventory item
        inventory_item = InventoryItem(
            item_id=item_id,
            location_id=inventory.location_id,
            quantity=quantity,
            expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None,
            lot_number=lot_number
        )
        db.session.add(inventory_item)
        db.session.commit()
        
        # Log the action
        log_audit('CREATE', 'inventory_item', inventory_item.id, None, {
            'item_id': item_id,
            'location_id': inventory.location_id,
            'quantity': quantity,
            'expiration_date': expiration_date,
            'lot_number': lot_number
        })
        
        return jsonify({
            'success': True, 
            'message': 'Item added to inventory successfully',
            'inventory_item_id': inventory_item.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/<int:inventory_id>/remove-item', methods=['POST'])
@login_required
def remove_item_from_inventory(inventory_id):
    """Remove an item from the inventory in real-time"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Find and soft delete the inventory item
        inventory_item = InventoryItem.query.filter_by(
            item_id=item_id,
            location_id=inventory.location_id,
            is_active=True,
            deleted_at=None
        ).first()
        
        if not inventory_item:
            return jsonify({'success': False, 'error': 'Item not found in inventory'}), 404
        
        # Soft delete
        old_values = {
            'quantity': inventory_item.quantity,
            'expiration_date': inventory_item.expiration_date,
            'lot_number': inventory_item.lot_number
        }
        
        inventory_item.is_active = False
        inventory_item.deleted_at = datetime.now()
        
        db.session.commit()
        
        # Log the action
        log_audit('DELETE', 'inventory_item', inventory_item.id, old_values, None)
        
        return jsonify({
            'success': True, 
            'message': 'Item removed from inventory successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/<int:inventory_id>/create-and-add-item', methods=['POST'])
@login_required
def create_and_add_item(inventory_id):
    """Create a new item and add it to inventory in real-time"""
    try:
        data = request.get_json()
        name = data.get('name')
        item_number = data.get('item_number', '')
        manufacturer = data.get('manufacturer', '')
        is_required = data.get('is_required', False)
        required_quantity = int(data.get('required_quantity', 0))
        minimum_threshold = int(data.get('minimum_threshold', 0))
        quantity = int(data.get('quantity', 0))
        expiration_date = data.get('expiration_date')
        lot_number = data.get('lot_number', '')
        
        if not name or quantity <= 0:
            return jsonify({'success': False, 'error': 'Name and quantity are required'}), 400
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Create new item
        new_item = Item(
            name=name,
            item_number=item_number if item_number else None,
            manufacturer=manufacturer if manufacturer else None,
            is_required=is_required,
            required_quantity=required_quantity,
            minimum_threshold=minimum_threshold
        )
        db.session.add(new_item)
        db.session.flush()  # Get the new item ID
        
        # Create inventory item for the new item
        inventory_item = InventoryItem(
            item_id=new_item.id,
            location_id=inventory.location_id,
            quantity=quantity,
            expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None,
            lot_number=lot_number
        )
        db.session.add(inventory_item)
        db.session.commit()
        
        # Log the actions
        log_audit('CREATE', 'item', new_item.id, None, {
            'name': name,
            'item_number': item_number,
            'manufacturer': manufacturer,
            'is_required': is_required,
            'required_quantity': required_quantity,
            'minimum_threshold': minimum_threshold
        })
        
        log_audit('CREATE', 'inventory_item', inventory_item.id, None, {
            'item_id': new_item.id,
            'location_id': inventory.location_id,
            'quantity': quantity,
            'expiration_date': expiration_date,
            'lot_number': lot_number
        })
        
        return jsonify({
            'success': True, 
            'message': 'Item created and added to inventory successfully',
            'item': {
                'id': new_item.id,
                'name': new_item.name,
                'item_number': new_item.item_number,
                'manufacturer': new_item.manufacturer,
                'is_required': new_item.is_required,
                'required_quantity': new_item.required_quantity,
                'minimum_threshold': new_item.minimum_threshold
            },
            'inventory_item_id': inventory_item.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/<int:inventory_id>/duplicate-item', methods=['POST'])
@login_required
def duplicate_inventory_item(inventory_id):
    """Duplicate an existing inventory item"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        inventory_item_id = data.get('inventory_item_id')
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Get the original inventory item to copy its properties
        original_item = InventoryItem.query.get_or_404(inventory_item_id)
        
        # Create a duplicate inventory item
        duplicate_item = InventoryItem(
            item_id=item_id,
            location_id=inventory.location_id,
            quantity=original_item.quantity,
            expiration_date=original_item.expiration_date,
            lot_number=original_item.lot_number
        )
        db.session.add(duplicate_item)
        db.session.commit()
        
        # Log the action
        log_audit('CREATE', 'inventory_item', duplicate_item.id, None, {
            'item_id': item_id,
            'location_id': inventory.location_id,
            'quantity': original_item.quantity,
            'expiration_date': original_item.expiration_date,
            'lot_number': original_item.lot_number,
            'action': 'duplicated_from_inventory_item_id'
        })
        
        return jsonify({
            'success': True, 
            'message': 'Item duplicated successfully',
            'inventory_item_id': duplicate_item.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/debug/<int:inventory_id>')
@login_required
def debug_inventory(inventory_id):
    """Debug route to see what's in the inventory"""
    inventory = Inventory.query.get_or_404(inventory_id)
    inventory_items = InventoryItem.query.filter_by(
        location_id=inventory.location_id,
        is_active=True,
        deleted_at=None
    ).all()
    
    debug_info = {
        'inventory_id': inventory.id,
        'location': inventory.location.name,
        'user': inventory.user.username,
        'date': inventory.inventory_date.strftime('%Y-%m-%d %H:%M:%S'),
        'total_items': len(inventory_items),
        'items': []
    }
    
    for item in inventory_items:
        debug_info['items'].append({
            'item_name': item.item.name,
            'quantity': item.quantity,
            'expiration': item.expiration_date.strftime('%Y-%m-%d') if item.expiration_date else 'None',
            'lot_number': item.lot_number or 'None'
        })
    
    return jsonify(debug_info)

@inventory_bp.route('/test')
@login_required
def test_inventory():
    """Simple test route to verify database queries"""
    try:
        # Test basic queries
        location_count = Location.query.filter_by(deleted_at=None).count()
        item_count = Item.query.filter_by(deleted_at=None).count()
        inventory_count = Inventory.query.filter_by(deleted_at=None).count()
        inventory_item_count = InventoryItem.query.filter_by(deleted_at=None).count()
        
        # Test a simple join
        test_query = db.session.query(
            InventoryItem.id,
            InventoryItem.quantity,
            Item.name.label('item_name')
        ).select_from(InventoryItem).join(
            Item, InventoryItem.item_id == Item.id
        ).limit(5).all()
        
        return jsonify({
            'status': 'success',
            'counts': {
                'locations': location_count,
                'items': item_count,
                'inventories': inventory_count,
                'inventory_items': inventory_item_count
            },
            'test_query': [
                {
                    'id': item.id,
                    'quantity': item.quantity,
                    'item_name': item.item_name
                } for item in test_query
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500

@inventory_bp.route('/reports')
@login_required
def reports():
    today = date.today()
    
    # Get expired items
    expired_items = db.session.query(
        Location.name.label('location_name'),
        Location.id.label('location_id'),
        Item.name.label('item_name'),
        InventoryItem.quantity,
        InventoryItem.expiration_date,
        InventoryItem.lot_number
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date < today,
        InventoryItem.expiration_date.isnot(None)
    ).all()
    
    # Get items expiring in different time periods
    expiring_30_days = db.session.query(
        Location.name.label('location_name'),
        Location.id.label('location_id'),
        Item.name.label('item_name'),
        InventoryItem.quantity,
        InventoryItem.expiration_date,
        InventoryItem.lot_number
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date >= today,
        InventoryItem.expiration_date <= today + timedelta(days=30),
        InventoryItem.expiration_date.isnot(None)
    ).all()
    
    expiring_60_days = db.session.query(
        Location.name.label('location_name'),
        Location.id.label('location_id'),
        Item.name.label('item_name'),
        InventoryItem.quantity,
        InventoryItem.expiration_date,
        InventoryItem.lot_number
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date > today + timedelta(days=30),
        InventoryItem.expiration_date <= today + timedelta(days=60),
        InventoryItem.expiration_date.isnot(None)
    ).all()
    
    expiring_90_days = db.session.query(
        Location.name.label('location_name'),
        Location.id.label('location_id'),
        Item.name.label('item_name'),
        InventoryItem.quantity,
        InventoryItem.expiration_date,
        InventoryItem.lot_number
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date > today + timedelta(days=60),
        InventoryItem.expiration_date <= today + timedelta(days=90),
        InventoryItem.expiration_date.isnot(None)
    ).all()
    
    expiring_180_days = db.session.query(
        Location.name.label('location_name'),
        Location.id.label('location_id'),
        Item.name.label('item_name'),
        InventoryItem.quantity,
        InventoryItem.expiration_date,
        InventoryItem.lot_number
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date > today + timedelta(days=90),
        InventoryItem.expiration_date <= today + timedelta(days=180),
        InventoryItem.expiration_date.isnot(None)
    ).all()
    
    # Get low stock items (combined regardless of expiration date) - ONLY for Supply Room locations
    low_stock = db.session.query(
        Location.name.label('location_name'),
        Location.id.label('location_id'),
        Item.name.label('item_name'),
        func.coalesce(func.sum(InventoryItem.quantity), 0).label('total_quantity'),
        Item.minimum_threshold,
        Item.required_quantity
    ).select_from(Item).join(
        Location, Location.location_type == 'supply_room'
    ).outerjoin(
        InventoryItem, db.and_(
            InventoryItem.item_id == Item.id,
            InventoryItem.location_id == Location.id,
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None
        )
    ).filter(
        Item.is_active == True,
        Item.deleted_at == None,
        Item.minimum_threshold > 0,
        Location.is_active == True,
        Location.deleted_at == None
    ).group_by(
        Location.name, Location.id, Item.name, Item.minimum_threshold, Item.required_quantity
    ).having(
        func.coalesce(func.sum(InventoryItem.quantity), 0) <= Item.minimum_threshold
    ).all()
    
    return render_template('inventory/reports.html', 
                         expired_items=expired_items,
                         expiring_30_days=expiring_30_days,
                         expiring_60_days=expiring_60_days,
                         expiring_90_days=expiring_90_days,
                         expiring_180_days=expiring_180_days,
                         low_stock=low_stock,
                         today=today)
