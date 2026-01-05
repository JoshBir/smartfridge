"""
Team model for SmartFridge application (optional feature).

Allows users to share fridge items within a team/family group.
"""

from datetime import datetime
from typing import List, Optional

from app.extensions import db


# Association table for User-Team many-to-many relationship
user_teams = db.Table(
    'user_teams',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True),
    db.Column('role', db.String(20), default='member'),  # owner, admin, member
    db.Column('joined_at', db.DateTime, default=datetime.utcnow),
)


class Team(db.Model):
    """
    Team/Family group model.
    
    Attributes:
        id: Primary key.
        name: Team name.
        created_by: User ID of creator.
        created_at: Creation timestamp.
    """
    
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invite_code = db.Column(db.String(32), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    members = db.relationship(
        'User',
        secondary=user_teams,
        lazy='dynamic',
        backref=db.backref('teams', lazy='dynamic')
    )
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f'<Team {self.name}>'
    
    @property
    def member_count(self) -> int:
        """Get number of team members."""
        return self.members.count()
    
    def add_member(self, user, role: str = 'member') -> None:
        """
        Add a user to the team.
        
        Args:
            user: User instance to add.
            role: Member role (owner, admin, member).
        """
        if not self.is_member(user):
            # Insert with role
            stmt = user_teams.insert().values(
                user_id=user.id,
                team_id=self.id,
                role=role
            )
            db.session.execute(stmt)
            db.session.commit()
    
    def remove_member(self, user) -> None:
        """
        Remove a user from the team.
        
        Args:
            user: User instance to remove.
        """
        if self.is_member(user):
            stmt = user_teams.delete().where(
                (user_teams.c.user_id == user.id) &
                (user_teams.c.team_id == self.id)
            )
            db.session.execute(stmt)
            db.session.commit()
    
    def is_member(self, user) -> bool:
        """
        Check if user is a team member.
        
        Args:
            user: User instance to check.
        
        Returns:
            True if member, False otherwise.
        """
        return self.members.filter_by(id=user.id).first() is not None
    
    def get_member_role(self, user) -> Optional[str]:
        """
        Get a user's role in the team.
        
        Args:
            user: User instance.
        
        Returns:
            Role string or None if not a member.
        """
        result = db.session.execute(
            user_teams.select().where(
                (user_teams.c.user_id == user.id) &
                (user_teams.c.team_id == self.id)
            )
        ).first()
        return result.role if result else None
    
    @classmethod
    def get_user_teams(cls, user_id: int) -> List['Team']:
        """
        Get all teams a user belongs to.
        
        Args:
            user_id: User ID.
        
        Returns:
            List of Team instances.
        """
        return cls.query.join(user_teams).filter(
            user_teams.c.user_id == user_id
        ).all()
    
    @classmethod
    def create(cls, name: str, created_by: int,
               description: Optional[str] = None) -> 'Team':
        """
        Create a new team.
        
        Args:
            name: Team name.
            created_by: Creator's user ID.
            description: Team description.
        
        Returns:
            Created Team instance.
        """
        import secrets
        
        team = cls(
            name=name,
            created_by=created_by,
            description=description,
            invite_code=secrets.token_urlsafe(16),
        )
        db.session.add(team)
        db.session.commit()
        
        # Add creator as owner
        from app.models.user import User
        creator = User.query.get(created_by)
        if creator:
            team.add_member(creator, role='owner')
        
        return team
