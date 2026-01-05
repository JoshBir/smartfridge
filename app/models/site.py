"""
Site model for SmartFridge application.

Stores favourite cooking websites.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import UniqueConstraint

from app.extensions import db


class Site(db.Model):
    """
    Favourite cooking website model.
    
    Attributes:
        id: Primary key.
        owner_id: Foreign key to User.
        title: Website title/name.
        url: Website URL.
        tags: Comma-separated tags.
        description: Optional description.
        created_at: Creation timestamp.
    """
    
    __tablename__ = 'sites'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    tags = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint: same URL per user
    __table_args__ = (
        UniqueConstraint('owner_id', 'url', name='uq_site_owner_url'),
    )
    
    def __repr__(self) -> str:
        return f'<Site {self.title}>'
    
    @property
    def tags_list(self) -> List[str]:
        """
        Parse tags string into a list.
        
        Returns:
            List of tag strings.
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tags(self, tags: List[str]) -> None:
        """
        Set tags from a list.
        
        Args:
            tags: List of tag strings.
        """
        self.tags = ', '.join(tag.strip() for tag in tags if tag.strip())
    
    @classmethod
    def get_by_owner(cls, owner_id: int) -> List['Site']:
        """
        Get all sites for a user.
        
        Args:
            owner_id: User ID.
        
        Returns:
            List of Site instances.
        """
        return cls.query.filter_by(owner_id=owner_id)\
            .order_by(cls.title.asc()).all()
    
    @classmethod
    def get_by_tag(cls, owner_id: int, tag: str) -> List['Site']:
        """
        Get sites with a specific tag.
        
        Args:
            owner_id: User ID.
            tag: Tag to filter by.
        
        Returns:
            List of Site instances with the tag.
        """
        search_pattern = f'%{tag}%'
        return cls.query.filter(
            cls.owner_id == owner_id,
            cls.tags.ilike(search_pattern)
        ).order_by(cls.title.asc()).all()
    
    @classmethod
    def search(cls, owner_id: int, query: str) -> List['Site']:
        """
        Search sites by title, URL, or tags.
        
        Args:
            owner_id: User ID.
            query: Search term.
        
        Returns:
            List of matching Site instances.
        """
        search_term = f'%{query}%'
        return cls.query.filter(
            cls.owner_id == owner_id,
            (cls.title.ilike(search_term) |
             cls.url.ilike(search_term) |
             cls.tags.ilike(search_term))
        ).order_by(cls.title.asc()).all()
    
    @classmethod
    def get_all_tags(cls, owner_id: int) -> List[str]:
        """
        Get all unique tags for a user.
        
        Args:
            owner_id: User ID.
        
        Returns:
            List of unique tag strings.
        """
        sites = cls.query.filter_by(owner_id=owner_id).all()
        tags = set()
        for site in sites:
            tags.update(site.tags_list)
        return sorted(tags)
    
    @classmethod
    def url_exists(cls, owner_id: int, url: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if URL already exists for user.
        
        Args:
            owner_id: User ID.
            url: URL to check.
            exclude_id: Site ID to exclude (for updates).
        
        Returns:
            True if URL exists, False otherwise.
        """
        query = cls.query.filter_by(owner_id=owner_id, url=url)
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        return query.first() is not None
    
    @classmethod
    def create(cls, owner_id: int, title: str, url: str,
               tags: Optional[str] = None,
               description: Optional[str] = None) -> 'Site':
        """
        Create a new site.
        
        Args:
            owner_id: User ID.
            title: Website title.
            url: Website URL.
            tags: Comma-separated tags.
            description: Optional description.
        
        Returns:
            Created Site instance.
        """
        site = cls(
            owner_id=owner_id,
            title=title,
            url=url,
            tags=tags,
            description=description,
        )
        db.session.add(site)
        db.session.commit()
        return site
