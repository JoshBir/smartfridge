"""
Add barcode and brand columns to items table.

This migration adds barcode scanning support.

Run this migration with:
    flask db upgrade

Or manually with SQLite:
    ALTER TABLE items ADD COLUMN barcode VARCHAR(50);
    ALTER TABLE items ADD COLUMN brand VARCHAR(100);
    CREATE INDEX idx_items_barcode ON items(barcode);
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_add_barcode_support'
down_revision = '002_add_user_approval'
branch_labels = None
depends_on = None


def upgrade():
    """Add barcode and brand columns to items table."""
    op.add_column('items', sa.Column('barcode', sa.String(50), nullable=True))
    op.add_column('items', sa.Column('brand', sa.String(100), nullable=True))
    op.create_index('idx_items_barcode', 'items', ['barcode'])


def downgrade():
    """Remove barcode and brand columns from items table."""
    op.drop_index('idx_items_barcode', table_name='items')
    op.drop_column('items', 'brand')
    op.drop_column('items', 'barcode')
