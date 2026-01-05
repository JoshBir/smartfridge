"""
Add is_approved column to users table.

This migration adds the is_approved column to support
admin approval workflow for new user registrations.

Run this migration with:
    flask db upgrade

Or manually with SQLite:
    ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0 NOT NULL;

For existing users (to auto-approve them):
    UPDATE users SET is_approved = 1 WHERE is_approved = 0;
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_add_user_approval'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_approved column to users table."""
    # Add the column with default False
    op.add_column('users', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='0'))
    
    # Auto-approve all existing users (they were created before this feature)
    op.execute("UPDATE users SET is_approved = 1")


def downgrade():
    """Remove is_approved column from users table."""
    op.drop_column('users', 'is_approved')
