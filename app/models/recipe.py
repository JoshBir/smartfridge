"""
Recipe model for SmartFridge application.

Stores user-saved recipes, including AI-generated suggestions.
"""

from datetime import datetime
from typing import Optional, List

from app.extensions import db


class Recipe(db.Model):
    """
    Recipe model.
    
    Attributes:
        id: Primary key.
        owner_id: Foreign key to User.
        title: Recipe title.
        ingredients_text: Ingredients list (plain text).
        instructions: Cooking instructions.
        source_url: Optional source URL.
        is_ai_generated: Whether recipe was AI-generated.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """
    
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    ingredients_text = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    is_ai_generated = db.Column(db.Boolean, default=False, nullable=False)
    servings = db.Column(db.Integer, nullable=True)
    prep_time_minutes = db.Column(db.Integer, nullable=True)
    cook_time_minutes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                          nullable=False)
    
    def __repr__(self) -> str:
        return f'<Recipe {self.title}>'
    
    @property
    def total_time_minutes(self) -> Optional[int]:
        """Calculate total cooking time."""
        if self.prep_time_minutes and self.cook_time_minutes:
            return self.prep_time_minutes + self.cook_time_minutes
        return self.prep_time_minutes or self.cook_time_minutes
    
    @property
    def ingredients_list(self) -> List[str]:
        """
        Parse ingredients text into a list.
        
        Returns:
            List of ingredient strings.
        """
        if not self.ingredients_text:
            return []
        return [
            line.strip()
            for line in self.ingredients_text.strip().split('\n')
            if line.strip()
        ]
    
    @property
    def instructions_list(self) -> List[str]:
        """
        Parse instructions into numbered steps.
        
        Returns:
            List of instruction strings.
        """
        if not self.instructions:
            return []
        return [
            line.strip()
            for line in self.instructions.strip().split('\n')
            if line.strip()
        ]
    
    @classmethod
    def get_by_owner(cls, owner_id: int) -> List['Recipe']:
        """
        Get all recipes for a user.
        
        Args:
            owner_id: User ID.
        
        Returns:
            List of Recipe instances.
        """
        return cls.query.filter_by(owner_id=owner_id)\
            .order_by(cls.created_at.desc()).all()
    
    @classmethod
    def search(cls, owner_id: int, query: str) -> List['Recipe']:
        """
        Search recipes by title or ingredients.
        
        Args:
            owner_id: User ID.
            query: Search term.
        
        Returns:
            List of matching Recipe instances.
        """
        search_term = f'%{query}%'
        return cls.query.filter(
            cls.owner_id == owner_id,
            (cls.title.ilike(search_term) | cls.ingredients_text.ilike(search_term))
        ).order_by(cls.title.asc()).all()
    
    @classmethod
    def create(cls, owner_id: int, title: str, ingredients_text: str,
               instructions: str, source_url: Optional[str] = None,
               is_ai_generated: bool = False, servings: Optional[int] = None,
               prep_time_minutes: Optional[int] = None,
               cook_time_minutes: Optional[int] = None) -> 'Recipe':
        """
        Create a new recipe.
        
        Args:
            owner_id: User ID.
            title: Recipe title.
            ingredients_text: Ingredients list.
            instructions: Cooking instructions.
            source_url: Source URL (optional).
            is_ai_generated: Whether AI-generated.
            servings: Number of servings.
            prep_time_minutes: Preparation time.
            cook_time_minutes: Cooking time.
        
        Returns:
            Created Recipe instance.
        """
        recipe = cls(
            owner_id=owner_id,
            title=title,
            ingredients_text=ingredients_text,
            instructions=instructions,
            source_url=source_url,
            is_ai_generated=is_ai_generated,
            servings=servings,
            prep_time_minutes=prep_time_minutes,
            cook_time_minutes=cook_time_minutes,
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe


class RecipeDraft:
    """
    Data transfer object for recipe suggestions.
    
    Used by AI adapter to return recipe suggestions before saving.
    """
    
    def __init__(
        self,
        title: str,
        ingredients_text: str,
        instructions: str,
        source_url: Optional[str] = None,
        servings: Optional[int] = None,
        prep_time_minutes: Optional[int] = None,
        cook_time_minutes: Optional[int] = None,
        match_score: float = 0.0,
        missing_ingredients: Optional[List[str]] = None,
    ):
        self.title = title
        self.ingredients_text = ingredients_text
        self.instructions = instructions
        self.source_url = source_url
        self.servings = servings
        self.prep_time_minutes = prep_time_minutes
        self.cook_time_minutes = cook_time_minutes
        self.match_score = match_score
        self.missing_ingredients = missing_ingredients or []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialisation."""
        return {
            'title': self.title,
            'ingredients_text': self.ingredients_text,
            'instructions': self.instructions,
            'source_url': self.source_url,
            'servings': self.servings,
            'prep_time_minutes': self.prep_time_minutes,
            'cook_time_minutes': self.cook_time_minutes,
            'match_score': self.match_score,
            'missing_ingredients': self.missing_ingredients,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RecipeDraft':
        """Create from dictionary."""
        return cls(
            title=data.get('title', ''),
            ingredients_text=data.get('ingredients_text', ''),
            instructions=data.get('instructions', ''),
            source_url=data.get('source_url'),
            servings=data.get('servings'),
            prep_time_minutes=data.get('prep_time_minutes'),
            cook_time_minutes=data.get('cook_time_minutes'),
            match_score=data.get('match_score', 0.0),
            missing_ingredients=data.get('missing_ingredients', []),
        )
