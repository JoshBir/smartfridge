"""
Recipe forms for SmartFridge application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, URL, NumberRange


class RecipeForm(FlaskForm):
    """Form for creating and editing recipes."""
    
    title = StringField(
        'Recipe Title',
        validators=[
            DataRequired(message='Please enter a recipe title.'),
            Length(min=1, max=200, message='Title must be between 1 and 200 characters.')
        ],
        render_kw={'placeholder': 'e.g., Creamy Mushroom Pasta', 'autofocus': True}
    )
    
    ingredients_text = TextAreaField(
        'Ingredients',
        validators=[
            DataRequired(message='Please list the ingredients.'),
            Length(min=10, message='Please provide a complete ingredients list.')
        ],
        render_kw={
            'placeholder': '• 400g pasta\n• 200g mushrooms\n• 150ml cream\n• Salt and pepper to taste',
            'rows': 8
        }
    )
    
    instructions = TextAreaField(
        'Instructions',
        validators=[
            DataRequired(message='Please provide cooking instructions.'),
            Length(min=20, message='Please provide complete cooking instructions.')
        ],
        render_kw={
            'placeholder': '1. Cook pasta according to packet instructions.\n2. Sauté mushrooms in butter.\n3. Add cream and simmer.\n4. Toss with pasta and serve.',
            'rows': 10
        }
    )
    
    source_url = StringField(
        'Source URL',
        validators=[
            Optional(),
            URL(message='Please enter a valid URL.'),
            Length(max=500, message='URL must be less than 500 characters.')
        ],
        render_kw={'placeholder': 'https://example.com/recipe (optional)'}
    )
    
    servings = IntegerField(
        'Servings',
        validators=[
            Optional(),
            NumberRange(min=1, max=50, message='Servings must be between 1 and 50.')
        ],
        render_kw={'placeholder': 'e.g., 4'}
    )
    
    prep_time_minutes = IntegerField(
        'Prep Time (minutes)',
        validators=[
            Optional(),
            NumberRange(min=0, max=1440, message='Prep time must be between 0 and 1440 minutes.')
        ],
        render_kw={'placeholder': 'e.g., 15'}
    )
    
    cook_time_minutes = IntegerField(
        'Cook Time (minutes)',
        validators=[
            Optional(),
            NumberRange(min=0, max=1440, message='Cook time must be between 0 and 1440 minutes.')
        ],
        render_kw={'placeholder': 'e.g., 30'}
    )
    
    submit = SubmitField('Save Recipe')


class RecipeSuggestionForm(FlaskForm):
    """Form for requesting recipe suggestions."""
    
    submit = SubmitField('Suggest Recipes')


class SaveSuggestionForm(FlaskForm):
    """Form for saving a recipe suggestion."""
    
    title = HiddenField()
    ingredients_text = HiddenField()
    instructions = HiddenField()
    servings = HiddenField()
    prep_time_minutes = HiddenField()
    cook_time_minutes = HiddenField()
    
    submit = SubmitField('Save This Recipe')


class RecipeSearchForm(FlaskForm):
    """Form for searching recipes."""
    
    search = StringField(
        'Search',
        validators=[Optional()],
        render_kw={'placeholder': 'Search recipes...'}
    )
    
    submit = SubmitField('Search')
