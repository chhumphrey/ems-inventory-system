from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, date, timedelta
from models import db, User, Location, Item, InventoryItem, Inventory, InventoryDetail, AuditLog
from sqlalchemy import and_, or_, func
from forms import LoginForm, UserForm, LocationForm, ItemForm, InventoryItemForm, InventoryForm, SearchForm
import csv
from io import StringIO
from flask import Response
import json
import os

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
            vehicle_id=form.vehicle_id.data,
            has_sections=form.has_sections.data
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
        location.has_sections = form.has_sections.data
        
        db.session.commit()
        log_audit('UPDATE', 'location', location.id, old_values={'name': location.name, 'description': location.description, 'location_type': location.location_type, 'vehicle_id': location.vehicle_id, 'has_sections': location.has_sections})
        flash('Location updated successfully.')
        return redirect(url_for('admin.manage_locations'))
    
    return render_template('admin/location_form.html', form=form, title='Edit Location')

@admin_bp.route('/items')
@login_required
def manage_items():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('main.index'))
    
    # Get search parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    required_filter = request.args.get('required', '').strip()
    
    # Build the base query
    query = Item.query.filter_by(deleted_at=None)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Item.name.ilike(f'%{search}%'),
                Item.item_number.ilike(f'%{search}%'),
                Item.manufacturer.ilike(f'%{search}%')
            )
        )
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)
    
    # Apply required filter
    if required_filter:
        if required_filter == 'required':
            query = query.filter_by(is_required=True)
        elif required_filter == 'optional':
            query = query.filter_by(is_required=False)
    
    # Order by name
    items = query.order_by(Item.name).all()
    
    return render_template('admin/items.html', 
                         items=items, 
                         search=search, 
                         status_filter=status_filter, 
                         required_filter=required_filter)

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
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    # Build the base query - show only items from the most recent completed inventory for each location
    # First, get the most recent inventory date for each location
    subquery = db.session.query(
        Inventory.location_id,
        func.max(Inventory.inventory_date).label('max_inventory_date')
    ).filter(
        Inventory.is_active == True,
        Inventory.deleted_at == None
    ).group_by(Inventory.location_id).subquery()
    
    query = db.session.query(
        Location.name.label('location_name'),
        Item.name.label('item_name'),
        Item.id.label('item_id'),
        Location.id.label('location_id'),
        InventoryItem.quantity.label('quantity'),
        InventoryItem.expiration_date.label('expiration_date'),
        InventoryItem.lot_number.label('lot_number'),
        InventoryItem.section.label('section'),
        InventoryItem.id.label('inventory_item_id'),
        Inventory.inventory_date.label('inventory_date')
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).join(
        Inventory, and_(
            Inventory.location_id == InventoryItem.location_id,
            Inventory.is_active == True,
            Inventory.deleted_at == None
        )
    ).join(
        subquery, and_(
            subquery.c.location_id == Inventory.location_id,
            subquery.c.max_inventory_date == Inventory.inventory_date
        )
    ).filter(
        InventoryItem.is_active == True, 
        InventoryItem.deleted_at == None
    )
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Item.name.ilike(f'%{search}%'),
                Location.name.ilike(f'%{search}%'),
                InventoryItem.lot_number.ilike(f'%{search}%'),
                InventoryItem.section.ilike(f'%{search}%')
            )
        )
    
    # Apply location filter
    if location_filter:
        query = query.filter(Location.id == int(location_filter))
    
    # Apply status filter
    today = date.today()
    today_plus_30 = today + timedelta(days=30)
    
    if status_filter == 'low_stock':
        query = query.filter(InventoryItem.quantity <= 2)
    elif status_filter == 'expired':
        query = query.filter(
            and_(
                InventoryItem.expiration_date.isnot(None),
                InventoryItem.expiration_date < today
            )
        )
    elif status_filter == 'expiring_soon':
        query = query.filter(
            and_(
                InventoryItem.expiration_date.isnot(None),
                InventoryItem.expiration_date >= today,
                InventoryItem.expiration_date <= today_plus_30
            )
        )
    
    # Apply default sorting: Location, then Section, then Item name
    inventory_summary = query.order_by(Location.name, InventoryItem.section, Item.name).all()
    
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
    
    # Generate alerts for inventory dashboard
    alerts = []
    
    # Count expired items
    expired_count = db.session.query(func.count(InventoryItem.id)).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date < today,
        InventoryItem.expiration_date.isnot(None)
    ).scalar() or 0
    
    # Count items expiring soon (within 30 days)
    expiring_soon_count = db.session.query(func.count(InventoryItem.id)).filter(
        InventoryItem.is_active == True,
        InventoryItem.deleted_at == None,
        InventoryItem.expiration_date >= today,
        InventoryItem.expiration_date <= today_plus_30,
        InventoryItem.expiration_date.isnot(None)
    ).scalar() or 0
    
    # Count low stock items (items below minimum threshold) - ONLY for Supply Room locations
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
    
    return render_template('inventory/dashboard.html', 
                         locations=locations, 
                         items=items, 
                         inventory_summary=inventory_summary,
                         location_last_inventory=location_last_inventory,
                         today=today,
                         today_plus_30=today_plus_30,
                         current_user=current_user,
                         alerts=alerts,
                         search=search,
                         location_filter=location_filter,
                         status_filter=status_filter)

@inventory_bp.route('/export')
@login_required
def export_inventory():
    # Get search and filter parameters (same as dashboard)
    search = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    # Build the base query (same as dashboard) - show only items from the most recent completed inventory for each location
    # First, get the most recent inventory date for each location
    subquery = db.session.query(
        Inventory.location_id,
        func.max(Inventory.inventory_date).label('max_inventory_date')
    ).filter(
        Inventory.is_active == True,
        Inventory.deleted_at == None
    ).group_by(Inventory.location_id).subquery()
    
    query = db.session.query(
        Location.name.label('location_name'),
        Item.name.label('item_name'),
        Item.id.label('item_id'),
        Location.id.label('location_id'),
        InventoryItem.quantity.label('quantity'),
        InventoryItem.expiration_date.label('expiration_date'),
        InventoryItem.lot_number.label('lot_number'),
        InventoryItem.section.label('section'),
        InventoryItem.id.label('inventory_item_id'),
        Inventory.inventory_date.label('inventory_date')
    ).select_from(InventoryItem).join(
        Location, InventoryItem.location_id == Location.id
    ).join(
        Item, InventoryItem.item_id == Item.id
    ).join(
        Inventory, and_(
            Inventory.location_id == InventoryItem.location_id,
            Inventory.is_active == True,
            Inventory.deleted_at == None
        )
    ).join(
        subquery, and_(
            subquery.c.location_id == Inventory.location_id,
            subquery.c.max_inventory_date == Inventory.inventory_date
        )
    ).filter(
        InventoryItem.is_active == True, 
        InventoryItem.deleted_at == None
    )
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                Item.name.ilike(f'%{search}%'),
                Location.name.ilike(f'%{search}%'),
                InventoryItem.lot_number.ilike(f'%{search}%'),
                InventoryItem.section.ilike(f'%{search}%')
            )
        )
    
    # Apply location filter
    if location_filter:
        query = query.filter(Location.id == int(location_filter))
    
    # Apply status filter
    today = date.today()
    today_plus_30 = today + timedelta(days=30)
    
    if status_filter == 'low_stock':
        query = query.filter(InventoryItem.quantity <= 2)
    elif status_filter == 'expired':
        query = query.filter(
            and_(
                InventoryItem.expiration_date.isnot(None),
                InventoryItem.expiration_date < today
            )
        )
    elif status_filter == 'expiring_soon':
        query = query.filter(
            and_(
                InventoryItem.expiration_date.isnot(None),
                InventoryItem.expiration_date >= today,
                InventoryItem.expiration_date <= today_plus_30
            )
        )
    
    # Apply default sorting: Location, then Section, then Item name
    inventory_data = query.order_by(Location.name, InventoryItem.section, Item.name).all()
    
    # Create CSV output
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Location', 'Section', 'Item Name', 'Quantity', 'Expiration Date', 
        'Lot Number', 'Last Inventory Date', 'Status'
    ])
    
    # Write data rows
    for item in inventory_data:
        # Determine status
        if item.quantity <= 2:
            status = 'Low Stock'
        elif item.expiration_date and item.expiration_date < today:
            status = 'Expired'
        elif item.expiration_date and item.expiration_date < today_plus_30:
            status = 'Expiring Soon'
        else:
            status = 'Good'
        
        # Format expiration date
        exp_date = item.expiration_date.strftime('%Y-%m-%d') if item.expiration_date else 'No Expiry'
        
        writer.writerow([
            item.location_name,
            item.section or 'N/A',
            item.item_name,
            item.quantity,
            exp_date,
            item.lot_number or 'N/A',
            item.inventory_date.strftime('%Y-%m-%d') if item.inventory_date else 'N/A',
            status
        ])
    
    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=inventory_export.csv'}
    )

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
        
        # Copy items from the most recent inventory for this location
        most_recent_inventory = Inventory.query.filter(
            Inventory.location_id == inventory.location_id,
            Inventory.id != inventory.id,  # Exclude the new inventory we just created
            Inventory.is_active == True,
            Inventory.deleted_at == None
        ).order_by(Inventory.inventory_date.desc()).first()
        
        if most_recent_inventory:
            # Get all items from the most recent inventory
            recent_items = InventoryItem.query.filter(
                InventoryItem.location_id == inventory.location_id,
                InventoryItem.is_active == True,
                InventoryItem.deleted_at == None
            ).all()
            
            # Create new inventory items with the same data but new IDs
            for recent_item in recent_items:
                new_inventory_item = InventoryItem(
                    item_id=recent_item.item_id,
                    location_id=inventory.location_id,
                    quantity=recent_item.quantity,
                    expiration_date=recent_item.expiration_date,
                    lot_number=recent_item.lot_number,
                    section=recent_item.section,
                    is_active=True
                )
                db.session.add(new_inventory_item)
            
            db.session.commit()
            
            # Log the copying action
            log_audit('COPY', 'inventory', inventory.id, 
                     old_values={'source_inventory_id': most_recent_inventory.id, 'items_copied': len(recent_items)},
                     new_values={'location_id': inventory.location_id, 'user_id': current_user.id})
        
        log_audit('CREATE', 'inventory', inventory.id, new_values=form.data)
        return redirect(url_for('inventory.edit_inventory', inventory_id=inventory.id))
    
    return render_template('inventory/new_inventory.html', form=form)

@inventory_bp.route('/<int:inventory_id>/edit')
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
                'current_section': inv_item.section,
                'inventory_item_id': inv_item.id
            })
    
    all_items = Item.query.filter_by(deleted_at=None, is_active=True).all()
    
    return render_template('inventory/edit_inventory.html', 
                         inventory=inventory, 
                         items=items, 
                         all_items=all_items,
                         current_user=current_user)

@inventory_bp.route('/<int:inventory_id>/update-item', methods=['POST'])
@login_required
def update_inventory_item(inventory_id):
    """Update a single inventory item in real-time"""
    try:
        data = request.get_json()
        inventory_item_id = data.get('inventory_item_id')  # Use specific inventory item ID
        quantity = int(data.get('quantity', 0))
        expiration_date = data.get('expiration_date')
        lot_number = data.get('lot_number', '')
        section = data.get('section', '')
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Find the specific inventory item by its ID
        inventory_item = InventoryItem.query.filter_by(
            id=inventory_item_id,
            is_active=True,
            deleted_at=None
        ).first()
        
        if not inventory_item:
            return jsonify({'success': False, 'error': 'Inventory item not found'}), 404
        
        # Verify the inventory item belongs to the current inventory location
        if inventory_item.location_id != inventory.location_id:
            return jsonify({'success': False, 'error': 'Inventory item does not belong to this inventory'}), 403
        
        # Update existing item
        old_values = {
            'quantity': inventory_item.quantity,
            'expiration_date': inventory_item.expiration_date,
            'lot_number': inventory_item.lot_number,
            'section': inventory_item.section
        }
        
        inventory_item.quantity = quantity
        inventory_item.expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None
        inventory_item.lot_number = lot_number
        inventory_item.section = section
        
        if quantity == 0:
            # Soft delete if quantity is 0
            inventory_item.is_active = False
            inventory_item.deleted_at = datetime.now()
            action = 'DELETE'
        else:
            action = 'UPDATE'
        
        db.session.commit()
        
        # Log the action
        if action != 'DELETE':
            log_audit(action, 'inventory_item', inventory_item.id, old_values, {
                'quantity': quantity,
                'expiration_date': expiration_date,
                'lot_number': lot_number,
                'section': section
            })
        
        return jsonify({
            'success': True, 
            'message': f'Item updated successfully',
            'inventory_item_id': inventory_item.id
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
        section = data.get('section', '')
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than 0'}), 400
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Check if item already exists in inventory with same expiration date and lot number
        # Allow multiple instances of the same item with different expiration dates or lot numbers
        existing_item = InventoryItem.query.filter_by(
            item_id=item_id,
            location_id=inventory.location_id,
            expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None,
            lot_number=lot_number,
            section=section,
            is_active=True,
            deleted_at=None
        ).first()
        
        if existing_item:
            # If exact same item exists, update quantity instead of creating duplicate
            existing_item.quantity += quantity
            db.session.commit()
            
            # Log the action
            log_audit('UPDATE', 'inventory_item', existing_item.id, 
                     {'quantity': existing_item.quantity - quantity}, 
                     {'quantity': existing_item.quantity})
            
            return jsonify({
                'success': True, 
                'message': 'Item quantity updated successfully',
                'inventory_item_id': existing_item.id
            })
        
        # Create new inventory item
        inventory_item = InventoryItem(
            item_id=item_id,
            location_id=inventory.location_id,
            section=section,
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
            'section': section,
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

@inventory_bp.route('/<int:inventory_id>/update-item-definition', methods=['POST'])
@login_required
def update_item_definition(inventory_id):
    """Update an item definition from the inventory page (admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied. Administrator privileges required.'}), 403
    
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        name = data.get('name', '').strip()
        item_number = data.get('item_number', '').strip()
        manufacturer = data.get('manufacturer', '').strip()
        is_required = data.get('is_required', False)
        required_quantity = int(data.get('required_quantity', 0)) if data.get('required_quantity') else 0
        minimum_threshold = int(data.get('minimum_threshold', 0)) if data.get('minimum_threshold') else 0
        
        if not name:
            return jsonify({'success': False, 'error': 'Item name is required'}), 400
        
        # Get the item
        item = Item.query.get_or_404(item_id)
        
        # Store old values for audit log
        old_values = {
            'name': item.name,
            'item_number': item.item_number,
            'manufacturer': item.manufacturer,
            'is_required': item.is_required,
            'required_quantity': item.required_quantity,
            'minimum_threshold': item.minimum_threshold
        }
        
        # Update the item
        item.name = name
        item.item_number = item_number
        item.manufacturer = manufacturer
        item.is_required = is_required
        item.required_quantity = required_quantity
        item.minimum_threshold = minimum_threshold
        
        db.session.commit()
        
        # Log the action
        log_audit('UPDATE', 'item', item.id, old_values, {
            'name': name,
            'item_number': item_number,
            'manufacturer': manufacturer,
            'is_required': is_required,
            'required_quantity': required_quantity,
            'minimum_threshold': minimum_threshold
        })
        
        return jsonify({
            'success': True,
            'message': 'Item updated successfully',
            'item': {
                'id': item.id,
                'name': item.name,
                'item_number': item.item_number,
                'manufacturer': item.manufacturer,
                'is_required': item.is_required,
                'required_quantity': item.required_quantity,
                'minimum_threshold': item.minimum_threshold
            }
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
            section=original_item.section,  # Include section information
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
            'section': original_item.section,
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

@inventory_bp.route('/manage-counts')
@login_required
def manage_inventory_counts():
    """Admin page to manage all inventory counts"""
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.')
        return redirect(url_for('main.index'))
    
    # Get search and filter parameters
    location_filter = request.args.get('location', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    # Build the base query
    query = db.session.query(
        Inventory.id.label('inventory_id'),
        Inventory.inventory_date.label('inventory_date'),
        Location.name.label('location_name'),
        User.username.label('user_name'),
        func.count(InventoryItem.id).label('item_count')
    ).select_from(Inventory).join(
        Location, Inventory.location_id == Location.id
    ).join(
        User, Inventory.user_id == User.id
    ).outerjoin(
        InventoryItem, and_(
            InventoryItem.location_id == Inventory.location_id,
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None
        )
    ).filter(
        Inventory.is_active == True,
        Inventory.deleted_at == None
    ).group_by(
        Inventory.id, Inventory.inventory_date, Location.name, User.username
    )
    
    # Apply location filter
    if location_filter:
        query = query.filter(Location.id == int(location_filter))
    
    # Apply date range filter
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Inventory.inventory_date >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            # Add one day to include the end date
            end_date_obj = end_date_obj + timedelta(days=1)
            query = query.filter(Inventory.inventory_date < end_date_obj)
        except ValueError:
            pass
    
    # Get all locations for the filter dropdown
    locations = Location.query.filter_by(deleted_at=None, is_active=True).all()
    
    # Apply default sorting by date (newest first)
    inventory_counts = query.order_by(Inventory.inventory_date.desc()).all()
    
    return render_template('inventory/manage_counts.html',
                         inventory_counts=inventory_counts,
                         locations=locations,
                         location_filter=location_filter,
                         start_date=start_date,
                         end_date=end_date)

@inventory_bp.route('/<int:inventory_id>/delete-count', methods=['POST'])
@login_required
def delete_inventory_count(inventory_id):
    """Delete an inventory count (requires admin privileges)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied. Administrator privileges required.'}), 403
    
    try:
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Soft delete the inventory
        old_values = {
            'location_id': inventory.location_id,
            'location_name': inventory.location.name,
            'user_id': inventory.user_id,
            'user_name': inventory.user.username,
            'inventory_date': inventory.inventory_date.strftime('%Y-%m-%d %H:%M:%S'),
            'notes': inventory.notes
        }
        
        inventory.is_active = False
        inventory.deleted_at = datetime.now()
        
        # Also soft delete all associated inventory items
        inventory_items = InventoryItem.query.filter_by(
            location_id=inventory.location_id,
            is_active=True,
            deleted_at=None
        ).all()
        
        for item in inventory_items:
            item.is_active = False
            item.deleted_at = datetime.now()
        
        db.session.commit()
        
        # Log the action
        log_audit('DELETE', 'inventory', inventory.id, old_values, None)
        
        return jsonify({
            'success': True,
            'message': 'Inventory count deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/clear-all-inventories', methods=['POST'])
@login_required
def clear_all_inventories():
    """Clear all existing inventories (admin only) - for testing purposes"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied. Administrator privileges required.'}), 403
    
    try:
        # Get all active inventories
        all_inventories = Inventory.query.filter_by(is_active=True, deleted_at=None).all()
        
        cleared_count = 0
        for inventory in all_inventories:
            # Soft delete the inventory
            inventory.is_active = False
            inventory.deleted_at = datetime.now()
            
            # Soft delete all associated inventory items
            inventory_items = InventoryItem.query.filter_by(
                location_id=inventory.location_id,
                is_active=True,
                deleted_at=None
            ).all()
            
            for item in inventory_items:
                item.is_active = False
                item.deleted_at = datetime.now()
            
            cleared_count += 1
        
        db.session.commit()
        
        # Log the action
        log_audit('CLEAR_ALL', 'inventory', 0, 
                 old_values={'inventories_cleared': cleared_count},
                 new_values={'user_id': current_user.id, 'timestamp': datetime.now().isoformat()})
        
        return jsonify({
            'success': True,
            'message': f'Successfully cleared {cleared_count} inventories and all associated items',
            'cleared_count': cleared_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

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

# Import functionality
@inventory_bp.route('/import')
@login_required
def import_tool():
    """Import tool landing page - step 1"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('inventory.inventory_dashboard'))
    
    return render_template('inventory/import.html')

@inventory_bp.route('/import/template/<file_type>')
@login_required
def download_template(file_type):
    """Download import template files"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('inventory.inventory_dashboard'))
    
    if file_type == 'items':
        # Create CSV template for items
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Item Name', 'Item Number', 'Manufacturer', 'Required by State Standards', 'Required Quantity', 'Minimum Threshold'])
        writer.writerow(['Sample Item', 'SAMPLE-001', 'Sample Manufacturer', 'Yes', '5', '2'])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=items_import_template.csv'}
        )
    
    elif file_type == 'inventory':
        # Create CSV template for inventory counts
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Location ID', 'Item Number', 'Quantity', 'Expiration Date (YYYY-MM-DD)', 'Lot Number'])
        writer.writerow(['1', 'SAMPLE-001', '10', '2025-12-31', 'LOT123'])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=inventory_import_template.csv'}
        )
    
    flash('Invalid template type.', 'error')
    return redirect(url_for('inventory.import_tool'))

@inventory_bp.route('/import/upload', methods=['POST'])
@login_required
def upload_import_file():
    """Handle file upload and parse data - step 2"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if not file.filename.lower().endswith(('.csv', '.tsv')):
        return jsonify({'success': False, 'error': 'Invalid file format. Please use CSV or TSV.'})
    
    try:
        # Determine delimiter
        delimiter = ',' if file.filename.lower().endswith('.csv') else '\t'
        
        # Read file content
        content = file.read().decode('utf-8')
        lines = content.split('\n')
        
        # Parse headers and data
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File must have at least a header row and one data row'})
        
        headers = [h.strip() for h in lines[0].split(delimiter)]
        data_rows = []
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                row_data = [cell.strip() for cell in line.split(delimiter)]
                if len(row_data) == len(headers):
                    data_rows.append(dict(zip(headers, row_data)))
                else:
                    return jsonify({'success': False, 'error': f'Row {i} has incorrect number of columns'})
        
        # Determine import type based on headers
        import_type = None
        if 'Item Name' in headers and 'Item Number' in headers:
            import_type = 'items'
        elif 'Location ID' in headers and 'Item Number' in headers and 'Quantity' in headers:
            import_type = 'inventory'
        else:
            return jsonify({'success': False, 'error': 'File format not recognized. Please use the provided templates.'})
        
        # Check for duplicates and prepare data
        processed_data = []
        duplicates = []
        
        for row in data_rows:
            if import_type == 'items':
                item_number = row.get('Item Number', '').strip()
                if item_number:
                    existing_item = Item.query.filter_by(item_number=item_number, deleted_at=None).first()
                    if existing_item:
                        duplicates.append({
                            'row': row,
                            'existing': existing_item,
                            'type': 'items'
                        })
                    else:
                        processed_data.append(row)
            
            elif import_type == 'inventory':
                item_number = row.get('Item Number', '').strip()
                location_id = row.get('Location ID', '').strip()
                if item_number and location_id:
                    # Check if item exists
                    item = Item.query.filter_by(item_number=item_number, deleted_at=None).first()
                    if not item:
                        return jsonify({'success': False, 'error': f'Item with number "{item_number}" not found in database'})
                    
                    # Check if location exists
                    location = Location.query.filter_by(id=location_id, deleted_at=None).first()
                    if not location:
                        return jsonify({'success': False, 'error': f'Location with ID "{location_id}" not found in database'})
                    
                    processed_data.append(row)
        
        # Store data in session for step 3
        session['import_data'] = {
            'type': import_type,
            'data': processed_data,
            'duplicates': duplicates,
            'headers': headers
        }
        
        return jsonify({
            'success': True,
            'import_type': import_type,
            'total_rows': len(processed_data),
            'duplicate_count': len(duplicates),
            'has_duplicates': len(duplicates) > 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error processing file: {str(e)}'})

@inventory_bp.route('/import/review')
@login_required
def review_import():
    """Review import data and handle duplicates - step 2 continued"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('inventory.import_tool'))
    
    import_data = session.get('import_data')
    if not import_data:
        flash('No import data found. Please upload a file first.', 'error')
        return redirect(url_for('inventory.import_tool'))
    
    return render_template('inventory/import_review.html', import_data=import_data)

@inventory_bp.route('/import/process-duplicates', methods=['POST'])
@login_required
def process_duplicates():
    """Process duplicate handling decisions"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    import_data = session.get('import_data')
    if not import_data:
        return jsonify({'success': False, 'error': 'No import data found'})
    
    data = request.get_json()
    decisions = data.get('decisions', {})
    
    # Process duplicate decisions
    for duplicate_id, decision in decisions.items():
        duplicate = import_data['duplicates'][int(duplicate_id)]
        
        if decision == 'replace':
            # Mark existing item for replacement
            duplicate['action'] = 'replace'
        elif decision == 'add':
            # Generate new item number
            base_number = duplicate['row']['Item Number']
            counter = 1
            new_number = f"{base_number}-{counter}"
            
            # Check if new number already exists
            while Item.query.filter_by(item_number=new_number, deleted_at=None).first():
                counter += 1
                new_number = f"{base_number}-{counter}"
            
            duplicate['row']['Item Number'] = new_number
            duplicate['action'] = 'add'
            import_data['data'].append(duplicate['row'])
    
    # Update session
    session['import_data'] = import_data
    
    return jsonify({'success': True, 'message': 'Duplicate decisions processed'})

@inventory_bp.route('/import/commit', methods=['POST'])
@login_required
def commit_import():
    """Commit imported data to database - step 3"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    import_data = session.get('import_data')
    if not import_data:
        return jsonify({'success': False, 'error': 'No import data found'})
    
    try:
        if import_data['type'] == 'items':
            # Import item definitions
            items_created = 0
            items_updated = 0
            
            for row in import_data['data']:
                item_number = row.get('Item Number', '').strip()
                existing_item = Item.query.filter_by(item_number=item_number, deleted_at=None).first()
                
                if existing_item:
                    # Update existing item
                    existing_item.name = row.get('Item Name', '').strip()
                    existing_item.manufacturer = row.get('Manufacturer', '').strip()
                    existing_item.is_required = row.get('Required by State Standards', '').strip().lower() in ['yes', 'true', '1']
                    existing_item.required_quantity = int(row.get('Required Quantity', 0) or 0)
                    existing_item.minimum_threshold = int(row.get('Minimum Threshold', 0) or 0)
                    items_updated += 1
                else:
                    # Create new item
                    new_item = Item(
                        name=row.get('Item Name', '').strip(),
                        item_number=item_number,
                        manufacturer=row.get('Manufacturer', '').strip(),
                        is_required=row.get('Required by State Standards', '').strip().lower() in ['yes', 'true', '1'],
                        required_quantity=int(row.get('Required Quantity', 0) or 0),
                        minimum_threshold=int(row.get('Minimum Threshold', 0) or 0)
                    )
                    db.session.add(new_item)
                    items_created += 1
            
            db.session.commit()
            
            # Clear session data
            session.pop('import_data', None)
            
            return jsonify({
                'success': True,
                'message': f'Import completed successfully. {items_created} items created, {items_updated} items updated.',
                'items_created': items_created,
                'items_updated': items_updated
            })
        
        elif import_data['type'] == 'inventory':
            # Import inventory counts
            inventory_items_created = 0
            inventory_items_updated = 0
            
            for row in import_data['data']:
                item_number = row.get('Item Number', '').strip()
                location_id = int(row.get('Location ID', 0))
                quantity = int(row.get('Quantity', 0) or 0)
                expiration_date_str = row.get('Expiration Date (YYYY-MM-DD)', '').strip()
                lot_number = row.get('Lot Number', '').strip()
                
                # Get item and location
                item = Item.query.filter_by(item_number=item_number, deleted_at=None).first()
                location = Location.query.filter_by(id=location_id, deleted_at=None).first()
                
                if not item or not location:
                    continue
                
                # Check if inventory item already exists
                existing_inv_item = InventoryItem.query.filter_by(
                    item_id=item.id,
                    location_id=location.id,
                    is_active=True,
                    deleted_at=None
                ).first()
                
                if existing_inv_item:
                    # Update existing inventory item
                    existing_inv_item.quantity = quantity
                    if expiration_date_str:
                        existing_inv_item.expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
                    existing_inv_item.lot_number = lot_number
                    inventory_items_updated += 1
                else:
                    # Create new inventory item
                    new_inv_item = InventoryItem(
                        item_id=item.id,
                        location_id=location.id,
                        quantity=quantity,
                        expiration_date=datetime.strptime(expiration_date_str, '%Y-%m-%d').date() if expiration_date_str else None,
                        lot_number=lot_number
                    )
                    db.session.add(new_inv_item)
                    inventory_items_created += 1
            
            db.session.commit()
            
            # Clear session data
            session.pop('import_data', None)
            
            return jsonify({
                'success': True,
                'message': f'Import completed successfully. {inventory_items_created} inventory items created, {inventory_items_updated} inventory items updated.',
                'inventory_items_created': inventory_items_created,
                'inventory_items_updated': inventory_items_updated
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error committing import: {str(e)}'})

@admin_bp.route('/test-import', methods=['GET'])
@login_required
def test_import_access():
    """Test route to check admin access and basic functionality"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
    
    try:
        # Test basic functionality
        result = {
            'status': 'success',
            'user': current_user.username,
            'is_admin': current_user.is_admin,
            'data_export_exists': os.path.exists('data_export'),
            'current_directory': os.getcwd(),
            'files_in_root': os.listdir('.') if os.path.exists('.') else []
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/import-data', methods=['GET', 'POST'])
@login_required
def import_data_web():
    """Web-based data import interface for admins"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Get the import type from form
            import_type = request.form.get('import_type')
            
            if import_type == 'users':
                success, message = import_users_from_json()
            elif import_type == 'locations':
                success, message = import_locations_from_json()
            elif import_type == 'items':
                success, message = import_items_from_json()
            elif import_type == 'all':
                success, message = import_all_data_from_json()
            else:
                flash('Invalid import type selected.', 'danger')
                return redirect(url_for('admin.import_data_web'))
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
                
        except Exception as e:
            flash(f'Import failed: {str(e)}', 'danger')
    
    # Check if data files exist and get summary
    data_files_exist = False
    summary = {}
    
    try:
        # Check if data_export directory exists
        if os.path.exists('data_export'):
            # Check if summary file exists
            summary_file = 'data_export/export_summary.json'
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                data_files_exist = True
            else:
                # Check individual files
                required_files = ['users.json', 'locations.json', 'items.json']
                data_files_exist = all(os.path.exists(f'data_export/{file}') for file in required_files)
    except Exception as e:
        print(f"Error checking data files: {e}")
        data_files_exist = False
    
    return render_template('admin/import_data.html', 
                         data_files_exist=data_files_exist, 
                         summary=summary)

def import_users_from_json():
    """Import users from exported JSON data"""
    try:
        json_file = 'data_export/users.json'
        if not os.path.exists(json_file):
            return False, 'Users JSON file not found. Please ensure data_export/users.json exists.'
        
        with open(json_file, 'r') as f:
            users_data = json.load(f)
        
        imported_count = 0
        for user_data in users_data:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    is_admin=user_data['is_admin']
                )
                user.set_password('changeme123')
                db.session.add(user)
                imported_count += 1
        
        db.session.commit()
        return True, f'Successfully imported {imported_count} users. Default password: changeme123'
        
    except Exception as e:
        db.session.rollback()
        return False, f'Failed to import users: {str(e)}'

def import_locations_from_json():
    """Import locations from exported JSON data"""
    try:
        json_file = 'data_export/locations.json'
        if not os.path.exists(json_file):
            return False, 'Locations JSON file not found. Please ensure data_export/locations.json exists.'
        
        with open(json_file, 'r') as f:
            locations_data = json.load(f)
        
        imported_count = 0
        for location_data in locations_data:
            existing_location = Location.query.filter_by(name=location_data['name']).first()
            if not existing_location:
                location = Location(
                    name=location_data['name'],
                    description=location_data['description'],
                    location_type=location_data['location_type'],
                    vehicle_id=location_data['vehicle_id']
                )
                db.session.add(location)
                imported_count += 1
        
        db.session.commit()
        return True, f'Successfully imported {imported_count} locations'
        
    except Exception as e:
        db.session.rollback()
        return False, f'Failed to import locations: {str(e)}'

def import_items_from_json():
    """Import items from exported JSON data"""
    try:
        json_file = 'data_export/items.json'
        if not os.path.exists(json_file):
            return False, 'Items JSON file not found. Please ensure data_export/items.json exists.'
        
        with open(json_file, 'r') as f:
            items_data = json.load(f)
        
        imported_count = 0
        for item_data in items_data:
            existing_item = Item.query.filter_by(item_number=item_data['item_number']).first()
            if not existing_item:
                item = Item(
                    name=item_data['name'],
                    item_number=item_data['item_number'],
                    manufacturer=item_data['manufacturer'],
                    is_required=item_data['is_required'],
                    required_quantity=item_data['required_quantity'],
                    minimum_threshold=item_data['minimum_threshold']
                )
                db.session.add(item)
                imported_count += 1
        
        db.session.commit()
        return True, f'Successfully imported {imported_count} items'
        
    except Exception as e:
        db.session.rollback()
        return False, f'Failed to import items: {str(e)}'

def import_all_data_from_json():
    """Import all data from exported JSON files"""
    try:
        # Import in order: users, locations, items
        user_success, user_message = import_users_from_json()
        if not user_success:
            return False, f'User import failed: {user_message}'
        
        location_success, location_message = import_locations_from_json()
        if not location_success:
            return False, f'Location import failed: {location_message}'
        
        item_success, item_message = import_items_from_json()
        if not item_success:
            return False, f'Item import failed: {item_message}'
        
        return True, f'All data imported successfully! {user_message} {location_message} {item_message}'
        
    except Exception as e:
        return False, f'Failed to import all data: {str(e)}'
