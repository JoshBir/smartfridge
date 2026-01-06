# SmartFridge - AI Project Summary

> **Purpose:** This document provides a comprehensive technical summary of the SmartFridge project for AI assistants to understand the codebase, architecture, and implementation details.

---

## Project Overview

**SmartFridge** is a production-ready Flask web application for managing fridge inventory, tracking food expiry dates, generating AI-powered recipe suggestions, and organising cooking websites. It features user authentication with admin approval workflow, barcode scanning for quick item entry, and automatic ingredient deduction when cooking recipes.

**Repository:** https://github.com/JoshBir/smartfridge

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, Flask 2.3+ |
| **Database** | SQLAlchemy ORM, SQLite (dev), PostgreSQL (prod) |
| **Auth** | Flask-Login, bcrypt password hashing |
| **Forms** | Flask-WTF, WTForms with CSRF protection |
| **Security** | Flask-Talisman (CSP), Flask-Limiter (rate limiting) |
| **Frontend** | Bootstrap 5, Jinja2 templates |
| **AI** | OpenAI, Google Gemini, Groq (all optional) |
| **Barcode** | Open Food Facts API (free, no key required) |
| **Server** | Gunicorn (production) |

---

## Project Structure

```
smartfridge/
├── app/                          # Main application package
│   ├── __init__.py               # Application factory (create_app)
│   ├── config.py                 # Configuration classes (dev/test/prod)
│   ├── extensions.py             # Flask extension instances
│   ├── cli.py                    # CLI commands (flask init-db, create-admin, etc.)
│   │
│   ├── blueprints/               # Route handlers (MVC Controllers)
│   │   ├── admin/                # Admin panel, user management, pending approvals
│   │   ├── auth/                 # Login, register, profile, password change
│   │   ├── items/                # Fridge items CRUD, barcode scanning
│   │   ├── main/                 # Dashboard, home, about pages
│   │   ├── recipes/              # Recipes CRUD, AI suggestions, cook feature
│   │   └── sites/                # Cooking websites bookmarks
│   │
│   ├── forms/                    # WTForms form classes
│   │   ├── admin.py              # User management forms
│   │   ├── auth.py               # Login, register, password forms
│   │   ├── items.py              # Item create/edit forms
│   │   ├── recipes.py            # Recipe forms
│   │   └── sites.py              # Website bookmark forms
│   │
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py               # User with roles, approval status
│   │   ├── item.py               # Fridge items with expiry tracking
│   │   ├── recipe.py             # Recipes and RecipeDraft DTO
│   │   ├── site.py               # Cooking website bookmarks
│   │   └── team.py               # Team/household management (future)
│   │
│   ├── services/                 # Business logic layer
│   │   ├── barcode.py            # Open Food Facts barcode lookup
│   │   ├── recipes/
│   │   │   ├── ai_adapter.py     # AI provider adapters (Local, OpenAI, Gemini, Groq)
│   │   │   └── rules_engine.py   # Local recipe matching engine
│   │   └── security/
│   │       └── password.py       # Password hashing and validation
│   │
│   ├── static/                   # CSS, JavaScript
│   └── templates/                # Jinja2 HTML templates
│
├── data/
│   └── canonical_recipes.json    # Seed recipes for rules engine
│
├── docs/
│   ├── GETTING-STARTED.md        # Setup and deployment guide
│   └── azure-deploy.md           # Azure-specific deployment
│
├── migrations/                   # Database migration scripts
│   ├── 002_add_user_approval.py  # is_approved column
│   └── 003_add_barcode_support.py # barcode, brand columns
│
├── tests/                        # Pytest test suite
│   ├── conftest.py               # Fixtures
│   ├── test_auth.py
│   ├── test_items.py
│   ├── test_recipes.py
│   └── test_security.py
│
├── .env.example                  # Environment variables template
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Dev dependencies (pytest, etc.)
├── run.py                        # Development server entry point
├── wsgi.py                       # Production WSGI entry point
├── Dockerfile                    # Container configuration
└── docker-compose.yml            # Multi-container setup
```

---

## Data Models

### User (`app/models/user.py`)

```python
class User(UserMixin, db.Model):
    id: int                    # Primary key
    username: str              # Unique, indexed
    email: str                 # Unique, indexed, lowercased
    password_hash: str         # bcrypt hash
    role: str                  # 'admin' or 'user' (UserRole enum)
    is_active: bool            # Account active status (default: True)
    is_approved: bool          # Admin approval status (default: False)
    created_at: datetime
    last_login: datetime
    
    # Relationships
    items: List[Item]          # User's fridge items
    recipes: List[Recipe]      # User's saved recipes
    sites: List[Site]          # User's bookmarked sites
```

**Key Methods:**
- `set_password(password)` / `check_password(password)` - bcrypt hashing
- `approve()` / `reject()` - Admin approval workflow
- `activate()` / `deactivate()` - Account status management
- `get_pending_users()` - Class method for pending registrations
- `is_admin` / `is_pending_approval` - Property helpers

### Item (`app/models/item.py`)

```python
class Item(db.Model):
    id: int
    owner_id: int              # FK to users
    name: str                  # Item name
    quantity: str              # e.g., "500ml", "2 pieces"
    category: str              # ItemCategory enum value
    expiry_date: date          # Optional
    barcode: str               # EAN/UPC (optional)
    brand: str                 # Brand name (optional)
    notes: str                 # Additional notes
    created_at: datetime
    updated_at: datetime
```

**Categories:** `dairy`, `meat`, `fish`, `vegetables`, `fruits`, `beverages`, `condiments`, `leftovers`, `frozen`, `other`

**Key Properties:**
- `expiry_status` - Returns `ExpiryStatus` enum: `FRESH`, `WARNING` (≤3 days), `EXPIRED`
- `days_until_expiry` - Integer (negative if expired)
- `status_class` - Bootstrap CSS class: `success`, `warning`, `danger`

**Key Methods:**
- `get_by_owner(owner_id, include_expired=True)` - User's items
- `get_expiring_soon(owner_id, days=3)` - Items expiring within N days
- `get_expired(owner_id)` - Expired items
- `get_by_barcode(owner_id, barcode)` - Find by barcode

### Recipe (`app/models/recipe.py`)

```python
class Recipe(db.Model):
    id: int
    owner_id: int              # FK to users
    title: str
    ingredients_text: str      # Plain text, newline-separated
    instructions: str          # Plain text, numbered steps
    source_url: str            # Optional URL
    is_ai_generated: bool      # Flag for AI-generated recipes
    servings: int
    prep_time_minutes: int
    cook_time_minutes: int
    created_at: datetime
    updated_at: datetime

class RecipeDraft:             # DTO for suggestions (not persisted)
    title: str
    ingredients_text: str
    instructions: str
    match_score: float         # 0-100 relevance score
    missing_ingredients: List[str]
```

### Site (`app/models/site.py`)

```python
class Site(db.Model):
    id: int
    owner_id: int
    name: str                  # Display name
    url: str                   # Website URL
    description: str           # Notes
    category: str              # 'general', 'healthy', 'quick', etc.
    created_at: datetime
```

---

## Key Features & Implementation

### 1. User Registration with Admin Approval

**Flow:**
1. User registers at `/auth/register`
2. User record created with `is_approved=False`
3. User shown "pending approval" message, cannot login
4. Admin sees pending count in admin panel
5. Admin visits `/admin/pending-users`
6. Admin clicks Approve or Reject for each user
7. Approved users can now login

**Key Code Locations:**
- `app/blueprints/auth/__init__.py` - `register()`, `login()` routes
- `app/blueprints/admin/__init__.py` - `pending_users()`, `approve_user()`, `reject_user()`
- `app/models/user.py` - `is_approved`, `approve()`, `reject()`, `get_pending_users()`

### 2. Barcode Scanning

**Flow:**
1. User navigates to `/items/scan`
2. Browser requests camera permission
3. BarcodeDetector Web API scans EAN/UPC codes
4. JavaScript sends barcode to `/items/api/barcode/<code>`
5. Server queries Open Food Facts API
6. Product info returned, user confirms to add item

**Open Food Facts API:**
```
GET https://world.openfoodfacts.org/api/v2/product/{barcode}.json
```
- Free, no API key required
- Returns: product_name, brands, quantity, categories_tags, image_url

**Key Code Locations:**
- `app/services/barcode.py` - `lookup_barcode()`, `ProductInfo` dataclass
- `app/blueprints/items/__init__.py` - `scan()`, `api_barcode_lookup()`, `api_add_by_barcode()`
- `app/templates/items/scan.html` - Camera UI with BarcodeDetector API

### 3. Cook Recipe & Ingredient Deduction

**Flow:**
1. User views recipe, clicks "Cook This"
2. Server matches recipe ingredients against user's fridge items
3. Page shows matched items with checkboxes (pre-selected)
4. User unchecks items they didn't use
5. User clicks "Cook & Remove Items"
6. Selected items deleted from database

**Matching Algorithm:**
```python
# For each fridge item, check if name appears in ingredient line
for item in user_items:
    for ingredient in recipe_ingredients:
        if item.name.lower() in ingredient.lower():
            matched = True
        # Also check word tokens (e.g., "chicken" in "chicken breast")
```

**Key Code Locations:**
- `app/blueprints/recipes/__init__.py` - `cook()` route
- `app/templates/recipes/cook.html` - Confirmation UI

### 4. AI Recipe Suggestions

**Adapter Pattern:** Multiple AI providers supported via common interface.

```python
class AIAdapter(Protocol):
    def generate_recipes(self, items: List[Item], max_results: int = 3) -> List[RecipeDraft]: ...
```

**Adapters:**
| Adapter | Provider | Config Key | Default Model |
|---------|----------|------------|---------------|
| `LocalAdapter` | Rules Engine | `local` | N/A |
| `OpenAIAdapter` | OpenAI | `openai` | `gpt-3.5-turbo` |
| `AzureOpenAIAdapter` | Azure OpenAI | `azure` | `gpt-35-turbo` |
| `GeminiAdapter` | Google | `gemini` | `gemini-1.5-flash` |
| `GroqAdapter` | Groq | `groq` | `llama-3.1-8b-instant` |
| `MockAdapter` | Testing | `mock` | N/A |

**Configuration:**
```ini
AI_PROVIDER=gemini          # or local, openai, azure, groq
AI_API_KEY=your-api-key
AI_MODEL=gemini-1.5-flash   # Optional override
```

**Factory Function:**
```python
def get_ai_adapter() -> AIAdapter:
    provider = current_app.config.get('AI_PROVIDER', 'local')
    # Returns appropriate adapter instance
```

**Key Code Locations:**
- `app/services/recipes/ai_adapter.py` - All adapters
- `app/services/recipes/rules_engine.py` - Local matching
- `app/blueprints/recipes/__init__.py` - `suggest()` route

---

## Configuration

### Environment Variables (`.env`)

```ini
# Required
SECRET_KEY=<64-char-hex>

# Database
SQLALCHEMY_DATABASE_URI=postgresql://...   # Prod only
# SQLite used automatically in development

# Flask
FLASK_CONFIG=development   # or production, testing

# AI (all optional)
AI_PROVIDER=local          # local, openai, azure, gemini, groq
AI_API_KEY=
AI_MODEL=                  # Provider-specific
AI_AZURE_ENDPOINT=         # Azure OpenAI only
```

### Configuration Classes (`app/config.py`)

```python
config = {
    'development': DevelopmentConfig,   # Debug on, SQLite, no rate limiting
    'testing': TestingConfig,           # In-memory SQLite, CSRF disabled
    'production': ProductionConfig,     # PostgreSQL, Talisman, HTTPS
}
```

---

## CLI Commands

```bash
flask init-db              # Create database tables
flask create-admin         # Create admin user (interactive)
flask seed-recipes         # Load canonical recipes from JSON
flask list-users           # List all users
flask set-password         # Reset user password
flask activate-user        # Activate user account
flask deactivate-user      # Deactivate user account
flask clean-expired --days 30  # Remove old expired items
```

---

## URL Routes

### Main (`/`)
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home/landing page |
| `/dashboard` | GET | User dashboard |
| `/about` | GET | About page |

### Auth (`/auth`)
| Route | Method | Description |
|-------|--------|-------------|
| `/auth/login` | GET, POST | Login |
| `/auth/logout` | GET | Logout |
| `/auth/register` | GET, POST | Registration (pending approval) |
| `/auth/profile` | GET, POST | User profile |
| `/auth/change-password` | GET, POST | Password change |

### Items (`/items`)
| Route | Method | Description |
|-------|--------|-------------|
| `/items/` | GET | List items |
| `/items/new` | GET, POST | Add item |
| `/items/<id>` | GET | View item |
| `/items/<id>/edit` | GET, POST | Edit item |
| `/items/<id>/delete` | POST | Delete item |
| `/items/scan` | GET | Barcode scanner UI |
| `/items/expiring` | GET | Expiring soon |
| `/items/expired` | GET | Expired items |
| `/items/api/barcode/<code>` | GET | API: Barcode lookup |
| `/items/api/add-by-barcode` | POST | API: Add item from barcode |

### Recipes (`/recipes`)
| Route | Method | Description |
|-------|--------|-------------|
| `/recipes/` | GET | List recipes |
| `/recipes/new` | GET, POST | Add recipe |
| `/recipes/<id>` | GET | View recipe |
| `/recipes/<id>/edit` | GET, POST | Edit recipe |
| `/recipes/<id>/delete` | POST | Delete recipe |
| `/recipes/<id>/cook` | GET, POST | Cook & deduct ingredients |
| `/recipes/suggest` | GET, POST | AI suggestions |
| `/recipes/save-suggestion` | POST | Save AI suggestion |
| `/recipes/api/suggest` | POST | API: Get suggestions JSON |

### Admin (`/admin`)
| Route | Method | Description |
|-------|--------|-------------|
| `/admin/` | GET | Admin dashboard |
| `/admin/users` | GET | User list |
| `/admin/users/<id>` | GET | View user |
| `/admin/users/<id>/edit` | GET, POST | Edit user |
| `/admin/users/<id>/delete` | POST | Delete user |
| `/admin/pending-users` | GET | Pending approvals |
| `/admin/users/<id>/approve` | POST | Approve user |
| `/admin/users/<id>/reject` | POST | Reject user |
| `/admin/approve-all` | POST | Approve all pending |

### Sites (`/sites`)
| Route | Method | Description |
|-------|--------|-------------|
| `/sites/` | GET | List bookmarks |
| `/sites/new` | GET, POST | Add bookmark |
| `/sites/<id>` | GET | View bookmark |
| `/sites/<id>/edit` | GET, POST | Edit bookmark |
| `/sites/<id>/delete` | POST | Delete bookmark |

---

## Security Features

1. **Password Security**
   - bcrypt hashing (work factor 12)
   - Policy: 8+ chars, uppercase, lowercase, digit, special char
   - Configurable via `PasswordService`

2. **CSRF Protection**
   - Flask-WTF enabled globally
   - 1-hour token lifetime

3. **Rate Limiting**
   - Flask-Limiter: 200/day, 50/hour default
   - Disabled in development/testing

4. **Content Security Policy**
   - Flask-Talisman in production
   - Strict CSP headers

5. **Session Security**
   - HTTPOnly cookies
   - Secure flag in production
   - SameSite=Lax

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_auth.py -v
```

**Test Configuration:** Uses `TestingConfig` with in-memory SQLite and disabled CSRF.

---

## Database Migrations

Manual SQL migrations in `migrations/` folder:

```python
# migrations/002_add_user_approval.py
def upgrade():
    # Add is_approved column with default False
    
# migrations/003_add_barcode_support.py
def upgrade():
    # Add barcode and brand columns to items
```

Run via Flask-Migrate or direct SQL execution.

---

## Deployment

### Local Development
```bash
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env with SECRET_KEY
flask init-db
flask create-admin
python run.py
```

### Production (Azure App Service)
- Python 3.11 runtime
- PostgreSQL Flexible Server
- Gunicorn WSGI server
- Environment variables for secrets

See `docs/GETTING-STARTED.md` for full deployment guide.

---

## External APIs

### Open Food Facts
- **URL:** `https://world.openfoodfacts.org/api/v2/product/{barcode}.json`
- **Auth:** None required
- **Rate Limit:** None (be respectful)
- **Used For:** Barcode product lookup

### AI Providers (Optional)
| Provider | Free Tier | URL |
|----------|-----------|-----|
| Google Gemini | 15 RPM, 1M tokens/day | https://makersuite.google.com/app/apikey |
| Groq | 30 RPM, 14,400 req/day | https://console.groq.com/keys |

---

## Key Design Patterns

1. **Application Factory** - `create_app()` function for flexible configuration
2. **Blueprint Organization** - Routes grouped by feature
3. **Service Layer** - Business logic separated from routes
4. **Adapter Pattern** - Pluggable AI providers
5. **Repository Pattern** - Model class methods for queries
6. **DTO Pattern** - `RecipeDraft` for non-persisted data transfer

---

## Common Code Patterns

### Getting Current User's Items
```python
from flask_login import current_user
from app.models.item import Item

items = Item.get_by_owner(current_user.id, include_expired=False)
```

### Protecting Routes
```python
from flask_login import login_required

@blueprint.route('/protected')
@login_required
def protected():
    pass
```

### Admin-Only Routes
```python
from functools import wraps
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated
```

### Creating Records
```python
# Using class method (preferred)
item = Item.create(
    owner_id=current_user.id,
    name='Milk',
    quantity='1L',
    category='dairy'
)

# Manual
item = Item(owner_id=current_user.id, name='Milk')
db.session.add(item)
db.session.commit()
```

---

## Version History

| Date | Changes |
|------|---------|
| 2026-01 | Added barcode scanning, cook & deduct feature |
| 2026-01 | Added admin approval workflow for registrations |
| 2026-01 | Added Gemini and Groq AI adapters |
| Initial | Core app with items, recipes, sites, auth |

---

*Last Updated: January 2026*
