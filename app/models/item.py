"""
Item model for SmartFridge application.

Represents fridge items with expiry tracking.
"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, List

from sqlalchemy import Index

from app.extensions import db


class ItemCategory(str, Enum):
    """Item category enumeration."""
    DAIRY = 'dairy'
    MEAT = 'meat'
    FISH = 'fish'
    VEGETABLES = 'vegetables'
    FRUITS = 'fruits'
    BEVERAGES = 'beverages'
    CONDIMENTS = 'condiments'
    LEFTOVERS = 'leftovers'
    FROZEN = 'frozen'
    OTHER = 'other'


class ExpiryStatus(str, Enum):
    """Expiry status for visual indicators."""
    FRESH = 'fresh'      # Green - more than 3 days until expiry
    WARNING = 'warning'  # Amber - 3 days or less until expiry
    EXPIRED = 'expired'  # Red - past expiry date


class Item(db.Model):
    """
    Fridge item model.
    
    Attributes:
        id: Primary key.
        owner_id: Foreign key to User.
        name: Item name.
        quantity: Quantity with unit (e.g., "500ml", "2 pieces").
        category: Item category.
        expiry_date: Expected expiry date.
        notes: Additional notes.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """
    
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False, default='1')
    category = db.Column(db.String(30), default=ItemCategory.OTHER.value, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                          nullable=False)
    
    def __repr__(self) -> str:
        return f'<Item {self.name} ({self.quantity})>'
    
    @property
    def expiry_status(self) -> ExpiryStatus:
        """
        Calculate the expiry status for visual display.
        
        Returns:
            ExpiryStatus enum value.
        """
        if self.expiry_date is None:
            return ExpiryStatus.FRESH
        
        today = date.today()
        days_until_expiry = (self.expiry_date - today).days
        
        if days_until_expiry < 0:
            return ExpiryStatus.EXPIRED
        elif days_until_expiry <= 3:
            return ExpiryStatus.WARNING
        else:
            return ExpiryStatus.FRESH
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """
        Calculate days until expiry.
        
        Returns:
            Number of days until expiry, or None if no expiry date.
            Negative values indicate expired items.
        """
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days
    
    @property
    def is_expired(self) -> bool:
        """Check if item is expired."""
        return self.expiry_status == ExpiryStatus.EXPIRED
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if item is expiring within 3 days."""
        return self.expiry_status == ExpiryStatus.WARNING
    
    @property
    def status_class(self) -> str:
        """
        Get Bootstrap CSS class for status display.
        
        Returns:
            CSS class name (success, warning, danger).
        """
        status_classes = {
            ExpiryStatus.FRESH: 'success',
            ExpiryStatus.WARNING: 'warning',
            ExpiryStatus.EXPIRED: 'danger',
        }
        return status_classes.get(self.expiry_status, 'secondary')
    
    @classmethod
    def get_by_owner(cls, owner_id: int, include_expired: bool = True) -> List['Item']:
        """
        Get all items for a user.
        
        Args:
            owner_id: User ID.
            include_expired: Whether to include expired items.
        
        Returns:
            List of Item instances.
        """
        query = cls.query.filter_by(owner_id=owner_id)
        if not include_expired:
            query = query.filter(
                (cls.expiry_date >= date.today()) | (cls.expiry_date.is_(None))
            )
        return query.order_by(cls.expiry_date.asc().nullslast()).all()
    
    @classmethod
    def get_expiring_soon(cls, owner_id: int, days: int = 3) -> List['Item']:
        """
        Get items expiring within specified days.
        
        Args:
            owner_id: User ID.
            days: Number of days to look ahead.
        
        Returns:
            List of Item instances expiring soon.
        """
        threshold = date.today() + timedelta(days=days)
        return cls.query.filter(
            cls.owner_id == owner_id,
            cls.expiry_date <= threshold,
            cls.expiry_date >= date.today()
        ).order_by(cls.expiry_date.asc()).all()
    
    @classmethod
    def get_expired(cls, owner_id: int) -> List['Item']:
        """
        Get expired items for a user.
        
        Args:
            owner_id: User ID.
        
        Returns:
            List of expired Item instances.
        """
        return cls.query.filter(
            cls.owner_id == owner_id,
            cls.expiry_date < date.today()
        ).order_by(cls.expiry_date.desc()).all()
    
    @classmethod
    def get_by_category(cls, owner_id: int, category: str) -> List['Item']:
        """
        Get items by category.
        
        Args:
            owner_id: User ID.
            category: Category to filter by.
        
        Returns:
            List of Item instances in the category.
        """
        return cls.query.filter_by(
            owner_id=owner_id,
            category=category
        ).order_by(cls.expiry_date.asc().nullslast()).all()
    
    @classmethod
    def search(cls, owner_id: int, query: str) -> List['Item']:
        """
        Search items by name.
        
        Args:
            owner_id: User ID.
            query: Search term.
        
        Returns:
            List of matching Item instances.
        """
        search_term = f'%{query}%'
        return cls.query.filter(
            cls.owner_id == owner_id,
            cls.name.ilike(search_term)
        ).order_by(cls.name.asc()).all()
    
    @classmethod
    def create(cls, owner_id: int, name: str, quantity: str = '1',
               category: str = ItemCategory.OTHER.value,
               expiry_date: Optional[date] = None,
               notes: Optional[str] = None) -> 'Item':
        """
        Create a new item.
        
        Args:
            owner_id: User ID.
            name: Item name.
            quantity: Quantity string.
            category: Item category.
            expiry_date: Expiry date.
            notes: Additional notes.
        
        Returns:
            Created Item instance.
        """
        item = cls(
            owner_id=owner_id,
            name=name,
            quantity=quantity,
            category=category,
            expiry_date=expiry_date,
            notes=notes,
        )
        db.session.add(item)
        db.session.commit()
        return item


# Composite indexes for common queries
Index('idx_items_owner_expiry', Item.owner_id, Item.expiry_date)
Index('idx_items_owner_category', Item.owner_id, Item.category)
