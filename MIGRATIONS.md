# Database Migrations Guide

SmartFridge uses Flask-Migrate (Alembic) for database schema migrations.

## Initial Setup

If starting fresh with no migrations:

```bash
# Initialise migrations folder
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

## Making Changes

When you modify models:

1. **Make your model changes** in `app/models/`

2. **Generate migration**
   ```bash
   flask db migrate -m "Description of changes"
   ```

3. **Review the generated migration** in `migrations/versions/`

4. **Apply the migration**
   ```bash
   flask db upgrade
   ```

## Common Commands

```bash
# Show current migration version
flask db current

# Show migration history
flask db history

# Upgrade to latest
flask db upgrade

# Upgrade to specific revision
flask db upgrade <revision>

# Downgrade one step
flask db downgrade

# Downgrade to specific revision
flask db downgrade <revision>

# Show SQL without executing
flask db upgrade --sql

# Generate migration with autogenerate
flask db migrate -m "Add new column"
```

## Migration Best Practices

### 1. Always Review Generated Migrations

Alembic's autogenerate is helpful but not perfect. Always review:

```python
# migrations/versions/xxxx_description.py
def upgrade():
    # Review these operations
    op.add_column('users', sa.Column('new_field', sa.String(100)))

def downgrade():
    # Ensure this reverses upgrade correctly
    op.drop_column('users', 'new_field')
```

### 2. Handle Data Migrations Separately

For data changes (not just schema):

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Define a lightweight table reference
    users = table('users',
        column('id', sa.Integer),
        column('role', sa.String)
    )
    
    # Update data
    op.execute(
        users.update().where(users.c.role == None).values(role='user')
    )

def downgrade():
    pass  # Data migrations often aren't reversible
```

### 3. Test Migrations

Before applying to production:

```bash
# Create a test database
export DATABASE_URL=sqlite:///test_migration.db

# Run upgrade
flask db upgrade

# Run downgrade
flask db downgrade

# Verify data integrity
flask shell
>>> from app.models import User
>>> User.query.count()
```

### 4. Backup Before Production Migrations

```bash
# PostgreSQL backup
pg_dump smartfridge > backup_$(date +%Y%m%d_%H%M%S).sql

# Then run migration
flask db upgrade
```

## Common Scenarios

### Adding a New Column

```python
# In your model
class User(db.Model):
    # ... existing fields ...
    phone = db.Column(db.String(20), nullable=True)  # New field
```

```bash
flask db migrate -m "Add phone to users"
flask db upgrade
```

### Renaming a Column

Alembic doesn't auto-detect renames. Create manual migration:

```python
def upgrade():
    op.alter_column('items', 'name', new_column_name='title')

def downgrade():
    op.alter_column('items', 'title', new_column_name='name')
```

### Adding a Non-Nullable Column

For existing data, add as nullable first, then alter:

```python
def upgrade():
    # Step 1: Add as nullable
    op.add_column('users', sa.Column('display_name', sa.String(100), nullable=True))
    
    # Step 2: Populate with default
    users = table('users', column('id'), column('display_name'), column('username'))
    op.execute(users.update().values(display_name=users.c.username))
    
    # Step 3: Make non-nullable
    op.alter_column('users', 'display_name', nullable=False)

def downgrade():
    op.drop_column('users', 'display_name')
```

### Creating an Index

```python
def upgrade():
    op.create_index('ix_items_expiry_date', 'items', ['expiry_date'])

def downgrade():
    op.drop_index('ix_items_expiry_date', table_name='items')
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Stamp current state
flask db stamp head

# Then try again
flask db migrate
```

### "Can't locate revision"

```bash
# Reset to known state
flask db stamp <known_revision>

# Or recreate from scratch (CAUTION: data loss)
rm -rf migrations/
flask db init
flask db migrate -m "Initial"
flask db upgrade
```

### Multiple Heads

```bash
# View heads
flask db heads

# Merge heads
flask db merge -m "Merge heads"
flask db upgrade
```

## Environment-Specific Notes

### Development (SQLite)

SQLite has limited ALTER TABLE support. Some operations may fail.

Workaround: Use `batch_op`:

```python
def upgrade():
    with op.batch_alter_table('items') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(100)))
```

### Production (PostgreSQL)

- Always backup before migrations
- Consider running during low-traffic periods
- Use `--sql` to review changes first
- Monitor for locks on large tables

```bash
# Generate SQL for review
flask db upgrade --sql > migration.sql

# Review migration.sql
# Then apply
flask db upgrade
```

## Migration Files Structure

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py               # Environment setup
├── script.py.mako       # Template for new migrations
├── README               # Alembic readme
└── versions/            # Migration scripts
    ├── 001_initial.py
    ├── 002_add_teams.py
    └── 003_add_notes.py
```
