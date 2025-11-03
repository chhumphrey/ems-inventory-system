from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, DateField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo, ValidationError
from datetime import date, timedelta

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    password = PasswordField('Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm Password')
    is_admin = BooleanField('Administrator Access')
    submit = SubmitField('Save User')
    
    def validate_confirm_password(self, field):
        if self.password.data and field.data != self.password.data:
            raise ValidationError('Passwords must match')

class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    location_type = SelectField('Location Type', choices=[
        ('ambulance', 'Ambulance'),
        ('supply_room', 'Supply Room'),
        ('go_bag', 'Go Bag')
    ], validators=[DataRequired()])
    vehicle_id = StringField('Vehicle ID (for Go Bags)')
    has_sections = BooleanField('Has Sections')
    submit = SubmitField('Save Location')

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=200)])
    item_number = StringField('Item Number', validators=[Length(max=100)])
    manufacturer = StringField('Manufacturer', validators=[Length(max=200)])
    is_required = BooleanField('Required by State Standards')
    required_quantity = IntegerField('Required Quantity', validators=[Optional(), NumberRange(min=0)])
    minimum_threshold = IntegerField('Minimum Threshold', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Item')

class InventoryItemForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    expiration_date = DateField('Expiration Date', validators=[Optional()])
    lot_number = StringField('Lot Number', validators=[Length(max=100)])
    submit = SubmitField('Save')

class InventoryForm(FlaskForm):
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Start Inventory')

class SearchForm(FlaskForm):
    search = StringField('Search Items')
    location_filter = SelectField('Location', coerce=int)
    expired_filter = BooleanField('Show Expired Only')
    low_stock_filter = BooleanField('Show Low Stock Only')
    submit = SubmitField('Search')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')

# Attendance Module Forms

class EventForm(FlaskForm):
    type = SelectField('Event Type', choices=[
        ('training', 'Training'),
        ('drill', 'Drill'),
        ('incident', 'Incident'),
        ('meeting', 'Meeting'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    starts_at = StringField('Start Date/Time', validators=[DataRequired()])
    ends_at = StringField('End Date/Time')
    location_id = SelectField('Location', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Event')

class MemberForm(FlaskForm):
    badge_number = StringField('Badge Number', validators=[Optional(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    membership_type = SelectField('Membership Type', choices=[
        ('active', 'Active'),
        ('reserve', 'Reserve'),
        ('probationary', 'Probationary'),
        ('life', 'Life'),
        ('inactive', 'Inactive')
    ], validators=[Optional()])
    submit = SubmitField('Save Member')

class AttendanceRecordForm(FlaskForm):
    member_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('absent', 'Absent')
    ], validators=[DataRequired()])
    method = SelectField('Method', choices=[
        ('roster', 'Roster'),
        ('qr', 'QR Code'),
        ('pin', 'PIN'),
        ('kiosk', 'Kiosk'),
        ('admin', 'Admin Entry')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Attendance')
