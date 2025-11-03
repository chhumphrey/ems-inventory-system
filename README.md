# EMS Inventory Management System

A comprehensive inventory management system designed specifically for volunteer Fire Company EMS groups. This system provides a mobile-friendly web interface with proper authentication, inventory tracking, and reporting capabilities.

## Features

### Core Functionality
- **User Authentication**: Secure login system with role-based access control
- **Inventory Management**: Track items across multiple locations (ambulances, supply rooms, go bags)
- **Attendance Tracking**: Record attendance for training, drills, meetings, and incidents
- **Member Management**: Manage EMS personnel with badges, contact info, and membership types
- **Event Management**: Create and manage events with locations, dates, and attendance rosters
- **Expiration Tracking**: Monitor expiration dates for time-sensitive medical supplies
- **Location Management**: Organize inventory by physical locations and vehicles
- **Soft Delete**: Maintain data integrity with soft-delete functionality
- **Audit Logging**: Complete audit trail of all system activities

### User Roles
- **Regular Users**: Can perform inventory counts and view reports
- **Administrators**: Can manage users, locations, items, and restore deleted data

### Inventory Features
- **Multi-location Support**: Track inventory across ambulances, supply rooms, and go bags
- **Expiration Management**: Handle multiple expiration dates for the same item
- **State Standards Compliance**: Track required quantities for state-mandated supplies
- **Threshold Alerts**: Monitor minimum stock levels
- **Lot Number Tracking**: Track specific batches of supplies

### Attendance Features
- **Event Management**: Create training, drills, meetings, and incident events
- **Member Roster**: Manage personnel with badge numbers and contact information
- **Attendance Tracking**: Record presence, late arrival, excused absences, and absent status
- **Multiple Check-in Methods**: Support for roster, QR code, PIN, kiosk, and admin entry
- **Attendance Reports**: Generate reports by member, event type, and date range
- **Real-time Updates**: Live attendance tracking with instant status updates

### Reporting
- **Current Inventory**: Real-time view of all supplies across locations
- **Expired Items**: Identify supplies that have expired
- **Expiring Soon**: Alert for items expiring within 30 days
- **Low Stock**: Identify items below minimum thresholds
- **Export Capabilities**: Generate reports for ordering and compliance

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project files**
   ```bash
   cd ~/ems-inventory-system
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables (optional)**
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export DATABASE_URL="sqlite:///ems_inventory.db"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the system**
   - Open your web browser and navigate to `http://localhost:5000`
   - Default admin credentials:
     - Username: `admin`
     - Password: `admin123`

## Configuration

### Database
The system uses SQLite by default for simplicity. For production use, consider:
- PostgreSQL for better performance and concurrent access
- MySQL for enterprise environments
- Update the `DATABASE_URL` environment variable accordingly

### Security
- Change the default admin password immediately after first login
- Update the `SECRET_KEY` environment variable in production
- Consider implementing HTTPS for production deployments

### Colors and Branding
The system uses a fire/EMS color scheme:
- **Fire Engine Red**: #D32F2F (Primary actions, headers)
- **EMS Blue**: #1976D2 (Secondary actions, links)
- **Warning Yellow**: #FFC107 (Alerts, warnings)
- **Safety Green**: #4CAF50 (Success, good status)
- **Alert Red**: #F44336 (Danger, expired items)
- **Caution Orange**: #FF9800 (Warnings, expiring soon)

## Usage

### First Time Setup
1. Log in with the default admin account
2. Create additional user accounts for your team
3. Set up locations (ambulances, supply rooms, go bags)
4. Add inventory items with proper specifications
5. Perform your first inventory count

### Daily Operations
1. **Perform Inventory Counts**: Use the "New Count" feature to record current stock levels
2. **Monitor Reports**: Check the reports section for expired items, low stock, and expiring supplies
3. **Update Inventory**: Modify counts as supplies are used or restocked

### Administrative Tasks
1. **User Management**: Add/remove users and manage permissions
2. **Location Management**: Add new locations or modify existing ones
3. **Item Management**: Add new supplies or update specifications
4. **Data Restoration**: Restore accidentally deleted data (admin only)

## File Structure

```
ems-inventory-system/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── models.py             # Database models
├── forms.py              # Form definitions
├── routes.py             # Route handlers
├── requirements.txt      # Python dependencies
├── static/               # Static assets
│   ├── css/
│   │   └── style.css    # Custom styling
│   └── js/
│       └── app.js       # JavaScript functionality
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── index.html       # Main dashboard
│   ├── inventory/       # Inventory templates
│   └── admin/           # Admin templates
└── README.md            # This file
```

## Database Schema

### Core Tables
- **Users**: User accounts and authentication
- **Locations**: Physical locations and vehicles
- **Items**: Supply specifications and requirements
- **InventoryItems**: Current stock levels and expiration dates
- **Inventories**: Inventory count sessions
- **InventoryDetails**: Detailed count records
- **AuditLog**: Complete activity logging

### Attendance Module Tables
- **Organizations**: Multi-tenant organization support
- **Members**: EMS personnel with badges and contact information
- **Events**: Training, drills, meetings, and incidents
- **AttendanceRecords**: Attendance tracking with status and methods

### Key Features
- **Soft Delete**: Records are marked as deleted rather than removed
- **Audit Trail**: All changes are logged with user and timestamp
- **Relationships**: Proper foreign key relationships maintain data integrity

## Mobile Responsiveness

The system is designed to work on all devices:
- **Desktop**: Full-featured interface with advanced controls
- **Tablet**: Optimized layout for touch interfaces
- **Mobile**: Streamlined interface for field use during inventory counts

## Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Secure session handling with Flask-Login
- **CSRF Protection**: Built-in CSRF protection for all forms
- **Input Validation**: Comprehensive form validation and sanitization
- **Access Control**: Role-based access control for all features

## Troubleshooting

### Common Issues

1. **Database Errors**
   - Ensure the application has write permissions to the current directory
   - Check that all dependencies are properly installed

2. **Login Issues**
   - Verify the database was created successfully
   - Check that the default admin user was created

3. **Import Errors**
   - Ensure all requirements are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

### Support

For technical support or feature requests, please contact your system administrator or refer to the application logs.

## Using the Attendance Module

### Getting Started
1. Navigate to the **Attendance** menu in the main navigation
2. Add members using the **Members** page
3. Create events for training, drills, meetings, or incidents
4. Record attendance using the event detail page
5. View attendance reports to track participation

### Member Management
- Add members with badge numbers, contact information, and membership types
- Track active, reserve, probationary, and inactive members
- Search members by name or badge number

### Event Management
- Create events with type, title, date/time, and location
- Link events to physical locations from your inventory system
- Track training hours and participation

### Recording Attendance
- Use the event detail page to record attendance for all members
- Mark members as Present, Late, Excused, or Absent
- Track check-in times automatically
- View attendance statistics and counts in real-time

## Future Enhancements

Planned features for future versions:
- **QR Code Check-in**: Generate QR codes for quick member check-in
- **Barcode Scanning**: Mobile barcode scanning for faster inventory counts
- **API Integration**: REST API for third-party integrations
- **Advanced Reporting**: Custom report builder and scheduling
- **Email Alerts**: Automated notifications for low stock and expiring items
- **Backup/Restore**: Automated database backup and restoration
- **Mobile App**: Native mobile application for field use

## License

This system is developed for volunteer Fire Company EMS groups. Please ensure compliance with your organization's policies and local regulations.

## Contributing

To contribute to this project:
1. Follow the existing code style and structure
2. Test all changes thoroughly
3. Update documentation as needed
4. Ensure all new features include proper error handling

---

**Note**: This system is designed for internal use by emergency services organizations. Ensure all data handling complies with relevant privacy and security regulations.
