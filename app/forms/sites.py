"""
Site forms for SmartFridge application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL, ValidationError

from app.models.site import Site


class SiteForm(FlaskForm):
    """Form for creating and editing favourite sites."""
    
    title = StringField(
        'Site Name',
        validators=[
            DataRequired(message='Please enter a site name.'),
            Length(min=1, max=200, message='Name must be between 1 and 200 characters.')
        ],
        render_kw={'placeholder': 'e.g., BBC Good Food', 'autofocus': True}
    )
    
    url = StringField(
        'URL',
        validators=[
            DataRequired(message='Please enter the website URL.'),
            URL(message='Please enter a valid URL.'),
            Length(max=500, message='URL must be less than 500 characters.')
        ],
        render_kw={'placeholder': 'https://www.bbcgoodfood.com'}
    )
    
    tags = StringField(
        'Tags',
        validators=[
            Optional(),
            Length(max=200, message='Tags must be less than 200 characters.')
        ],
        render_kw={'placeholder': 'e.g., recipes, british, baking (comma-separated)'}
    )
    
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=500, message='Description must be less than 500 characters.')
        ],
        render_kw={'placeholder': 'A brief description of the site...', 'rows': 3}
    )
    
    submit = SubmitField('Save Site')
    
    def __init__(self, owner_id=None, site_id=None, *args, **kwargs):
        """
        Initialise form with owner context for URL uniqueness validation.
        
        Args:
            owner_id: Current user's ID.
            site_id: Site ID being edited (for excluding from unique check).
        """
        super().__init__(*args, **kwargs)
        self.owner_id = owner_id
        self.site_id = site_id
    
    def validate_url(self, field):
        """Check URL is unique for this user."""
        if self.owner_id:
            if Site.url_exists(self.owner_id, field.data, exclude_id=self.site_id):
                raise ValidationError('You have already saved this URL.')


class SiteSearchForm(FlaskForm):
    """Form for searching sites."""
    
    search = StringField(
        'Search',
        validators=[Optional()],
        render_kw={'placeholder': 'Search sites...'}
    )
    
    tag = StringField(
        'Tag',
        validators=[Optional()],
        render_kw={'placeholder': 'Filter by tag...'}
    )
    
    submit = SubmitField('Search')
