from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from datetime import date, timedelta

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm Password')
    is_admin = BooleanField('Administrator Access')
    submit = SubmitField('Save User')

class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    location_type = SelectField('Location Type', choices=[
        ('ambulance', 'Ambulance'),
        ('supply_room', 'Supply Room'),
        ('go_bag', 'Go Bag')
    ], validators=[DataRequired()])
    vehicle_id = StringField('Vehicle ID (for Go Bags)')
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
