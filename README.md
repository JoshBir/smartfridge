# SmartFridge

A secure, production-ready Flask application for managing fridge ingredients, generating AI-powered recipe suggestions, and organising favourite cooking websites.

## Features

-  **Barcode Scanning** - Scan products with your phone camera to auto-fill item details
-  **Ingredient Management** - Track fridge items with expiry dates
-  **AI Recipe Suggestions** - Get recipe ideas based on available ingredients
-  **Cook & Deduct** - Mark recipes as cooked to automatically remove used ingredients
-  **Favourite Sites** - Save and organise cooking websites by tags
-  **Multi-User Support** - Individual accounts with admin approval for new registrations
-  **Security First** - OWASP-aligned security practices
-  **Responsive Design** - Works on desktop and mobile

## Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JoshBir/smartfridge.git
   cd smartfridge
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt

   # For development
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialise the database**
   ```bash
   flask init-db
   flask create-admin --username admin --email admin@example.com
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

   Visit http://127.0.0.1:5000 in your browser.

## Key Features Explained

###  Barcode Scanning

Scan product barcodes using your phone's camera to automatically fill in:
- Product name
- Brand
- Category
- Quantity

**Powered by [Open Food Facts](https://world.openfoodfacts.org)** - a free, open-source food database with millions of products. No API key required!

The scanner works best on mobile devices with camera access. You can also manually enter barcodes.

###  Cook & Deduct Ingredients

When you cook a recipe:
1. Click "Cook This" on any saved recipe
2. SmartFridge matches recipe ingredients to your fridge items
3. Select which items you're using
4. Items are automatically removed from your fridge

###  User Registration & Admin Approval

New users must be approved by an admin before they can log in:
1. User registers an account
2. Admin sees pending approval in the admin dashboard
3. Admin approves or rejects the registration
4. User can log in once approved

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_CONFIG` | Configuration mode | `development` |
| `SECRET_KEY` | Session encryption key | *Required* |
| `DATABASE_URL` | Database connection string | `sqlite:///smartfridge.db` |
| `AI_PROVIDER` | AI backend (`local`, `openai`, `azure`, `gemini`, `groq`) | `local` |
| `AI_API_KEY` | API key for AI provider | *Optional* |

See `.env.example` for all options.

## AI Recipe Suggestions

SmartFridge supports multiple AI backends for recipe suggestions:

| Provider | Free Tier | Setup |
|----------|-----------|-------|
| **Local** (default) | Unlimited | No setup needed - rule-based matching |
| **Google Gemini** | 15 RPM, 1M tokens/day | Get key at [makersuite.google.com](https://makersuite.google.com/app/apikey) |
| **Groq** | 30 RPM, 14,400 req/day | Get key at [console.groq.com](https://console.groq.com/keys) |
| **OpenAI** | Paid | Get key at [platform.openai.com](https://platform.openai.com) |
| **Azure OpenAI** | Paid | Azure subscription required |

Configure with:
```ini
AI_PROVIDER=gemini
AI_API_KEY=your-api-key
```

## CLI Commands

```bash
# Database management
flask init-db              # Create database tables
flask db upgrade           # Run migrations

# User management
flask create-admin         # Create admin user
flask set-password         # Reset user password
flask list-users           # List all users

# Data management
flask seed-recipes         # Load canonical recipes
flask clean-expired        # Remove old expired items
```

## Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Deployment

### Docker

```bash
# Build and run
docker-compose up -d
```

### Azure App Service

See [docs/azure-deploy.md](docs/azure-deploy.md) for detailed instructions.

See [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) for complete setup guide.

## Security Features

- **CSRF Protection** - All forms protected with tokens
- **Password Hashing** - bcrypt with work factor 12
- **Session Security** - HttpOnly, Secure, SameSite cookies
- **Rate Limiting** - Protection against brute force attacks
- **Admin Approval** - New registrations require admin approval
- **Input Validation** - Server-side validation on all inputs

See [SECURITY.md](SECURITY.md) for security policy.

## Licence

MIT Licence - see [LICENCE](LICENCE) file.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - UI framework
- [Open Food Facts](https://world.openfoodfacts.org) - Barcode database
