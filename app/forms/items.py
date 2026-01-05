"""
Item forms for SmartFridge application.
"""

from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from app.models.item import ItemCategory


class ItemForm(FlaskForm):
    """Form for creating and editing fridge items."""
    
    name = StringField(
        'Item Name',
        validators=[
            DataRequired(message='Please enter an item name.'),
            Length(min=1, max=100, message='Item name must be between 1 and 100 characters.')
        ],
        render_kw={'placeholder': 'e.g., Milk, Chicken Breast, Tomatoes', 'autofocus': True}
    )
    
    brand = StringField(
        'Brand',
        validators=[
            Optional(),
            Length(max=100, message='Brand must be less than 100 characters.')
        ],
        render_kw={'placeholder': 'e.g., Tesco, Heinz'}
    )
    
    quantity = StringField(
        'Quantity',
        validators=[
            DataRequired(message='Please enter a quantity.'),
            Length(max=50, message='Quantity must be less than 50 characters.')
        ],
        default='1',
        render_kw={'placeholder': 'e.g., 2 litres, 500g, 6 pieces'}
    )
    
    category = SelectField(
        'Category',
        choices=[
            (ItemCategory.DAIRY.value, 'Dairy'),
            (ItemCategory.MEAT.value, 'Meat'),
            (ItemCategory.FISH.value, 'Fish'),
            (ItemCategory.VEGETABLES.value, 'Vegetables'),
            (ItemCategory.FRUITS.value, 'Fruits'),
            (ItemCategory.BEVERAGES.value, 'Beverages'),
            (ItemCategory.CONDIMENTS.value, 'Condiments'),
            (ItemCategory.LEFTOVERS.value, 'Leftovers'),
            (ItemCategory.FROZEN.value, 'Frozen'),
            (ItemCategory.OTHER.value, 'Other'),
        ],
        default=ItemCategory.OTHER.value
    )
    
    expiry_date = DateField(
        'Expiry Date',
        validators=[Optional()],
        format='%Y-%m-%d',
        render_kw={'type': 'date'}
    )
    
    barcode = StringField(
        'Barcode',
        validators=[
            Optional(),
            Length(max=50, message='Barcode must be less than 50 characters.')
        ],
        render_kw={'placeholder': 'Scanned or manual barcode'}
    )
    
    notes = TextAreaField(
        'Notes',
        validators=[
            Optional(),
            Length(max=500, message='Notes must be less than 500 characters.')
        ],
        render_kw={'placeholder': 'Any additional notes...', 'rows': 3}
    )
    
    submit = SubmitField('Save Item')
    
    def validate_expiry_date(self, field):
        """Optional: warn about past expiry dates but don't block."""
        # We allow past dates as items might already be expired when added
        pass


class ItemSearchForm(FlaskForm):
    """Form for searching and filtering items."""
    
    search = StringField(
        'Search',
        validators=[Optional()],
        render_kw={'placeholder': 'Search items...'}
    )
    
    category = SelectField(
        'Category',
        choices=[
            ('', 'All Categories'),
            (ItemCategory.DAIRY.value, 'Dairy'),
            (ItemCategory.MEAT.value, 'Meat'),
            (ItemCategory.FISH.value, 'Fish'),
            (ItemCategory.VEGETABLES.value, 'Vegetables'),
            (ItemCategory.FRUITS.value, 'Fruits'),
            (ItemCategory.BEVERAGES.value, 'Beverages'),
            (ItemCategory.CONDIMENTS.value, 'Condiments'),
            (ItemCategory.LEFTOVERS.value, 'Leftovers'),
            (ItemCategory.FROZEN.value, 'Frozen'),
            (ItemCategory.OTHER.value, 'Other'),
        ],
        default=''
    )
    
    status = SelectField(
        'Status',
        choices=[
            ('', 'All Items'),
            ('fresh', 'Fresh'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
        ],
        default=''
    )
    
    submit = SubmitField('Filter')


class BulkDeleteForm(FlaskForm):
    """Form for bulk deleting items."""
    submit = SubmitField('Delete Selected')
