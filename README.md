# SmartFridge

A secure, production-ready Flask application for managing fridge ingredients, generating AI-powered recipe suggestions, and organising favourite cooking websites.

## Features

- **Barcode Scanning** - Scan products with your phone camera to auto-fill item details
- **Ingredient Management** - Track fridge items with expiry dates
- **AI Recipe Suggestions** - Get recipe ideas based on available ingredients
- **Cook & Deduct** - Mark recipes as cooked to automatically remove used ingredients
- **Favourite Sites** - Save and organise cooking websites by tags
- **Multi-User Support** - Individual accounts with admin approval for new registrations
- **Security First** - OWASP-aligned security practices
- **Responsive Design** - Works on desktop and mobile

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
   ```

4. **Configure environment**
   ```bash
   # Windows
   copy .env.example .env

   # Linux/macOS
   cp .env.example .env
   ```
   Edit `.env` with your settings (especially add your AI API key).

5. **Initialise the database**
   ```bash
   flask init-db
   flask create-admin
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

   Visit http://127.0.0.1:5000 in your browser.

## Key Features Explained

### Barcode Scanning

Scan product barcodes using your phone's camera to automatically fill in:
- Product name
- Brand
- Category
- Quantity

**Powered by [Open Food Facts](https://world.openfoodfacts.org)** - a free, open-source food database with millions of products. No API key required!

### Cook & Deduct Ingredients

When you cook a recipe:
1. Click "Cook This" on any saved recipe
2. SmartFridge matches recipe ingredients to your fridge items
3. Select which items you're using
4. Items are automatically removed from your fridge

### User Registration & Admin Approval

New users must be approved by an admin before they can log in:
1. User registers an account
2. Admin sees pending approval in the admin dashboard
3. Admin approves or rejects the registration
4. User can log in once approved

## AI Recipe Suggestions

SmartFridge supports multiple AI backends for recipe suggestions:

| Provider | Free Tier | Setup |
|----------|-----------|-------|
| **Local** (default) | Unlimited | No setup needed - rule-based matching |
| **OpenRouter** (recommended) | Free models available | Get key at [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Google Gemini** | 15 RPM, 1M tokens/day | Get key at [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Groq** | 30 RPM, 14,400 req/day | Get key at [console.groq.com](https://console.groq.com/keys) |
| **OpenAI** | Paid | Get key at [platform.openai.com](https://platform.openai.com) |

### Recommended: OpenRouter (Free)

OpenRouter provides access to many free AI models. Configure with:
```ini
AI_PROVIDER=openrouter
AI_API_KEY=sk-or-v1-your-key-here
AI_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

Free models available:
- `meta-llama/llama-3.2-3b-instruct:free`
- `google/gemma-2-9b-it:free`
- `mistralai/mistral-7b-instruct:free`

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_CONFIG` | Configuration mode | `development` |
| `SECRET_KEY` | Session encryption key | *Required* |
| `DATABASE_URL` | Database connection string | `sqlite:///smartfridge.db` |
| `AI_PROVIDER` | AI backend (`local`, `openrouter`, `gemini`, `groq`, `openai`, `azure`) | `openrouter` |
| `AI_API_KEY` | API key for AI provider | *Required for AI* |
| `AI_MODEL` | AI model to use | Provider-specific default |

See `.env.example` for all options.

## CLI Commands

```bash
# Database management
flask init-db              # Create database tables

# User management
flask create-admin         # Create admin user
flask set-password         # Reset user password
flask list-users           # List all users

# Data management
flask seed-recipes         # Load sample recipes
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
docker-compose up -d
```

### Azure App Service

See [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) for complete setup and deployment guide.

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
- [OpenRouter](https://openrouter.ai) - AI model gateway
