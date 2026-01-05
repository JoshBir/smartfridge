# SmartFridge

A secure, production-ready Flask application for managing fridge ingredients, generating AI-powered recipe suggestions, and organising favourite cooking websites.

## Features

- 🥗 **Ingredient Management** - Track fridge items with expiry dates
- 🤖 **AI Recipe Suggestions** - Get recipe ideas based on available ingredients
- 🌐 **Favourite Sites** - Save and organise cooking websites by tags
- 👥 **Multi-User Support** - Individual accounts with role-based access
- 🔒 **Security First** - OWASP-aligned security practices
- 📱 **Responsive Design** - Works on desktop and mobile

## Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartfridge.git
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

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_CONFIG` | Configuration mode | `development` |
| `SECRET_KEY` | Session encryption key | *Required* |
| `DATABASE_URL` | Database connection string | `sqlite:///smartfridge.db` |
| `AI_ADAPTER` | AI backend (`local`, `openai`, `azure`) | `local` |

See `.env.example` for all options.

## CLI Commands

```bash
# Database management
flask init-db              # Create database tables
flask db upgrade           # Run migrations

# User management
flask create-admin         # Create admin user
flask set-password         # Reset user password
flask list-users           # List all users
flask activate-user        # Activate a user
flask deactivate-user      # Deactivate a user

# Data management
flask seed-recipes         # Load canonical recipes
flask clean-expired        # Remove old expired items
```

## Project Structure

```
smartfridge/
├── app/
│   ├── __init__.py        # Application factory
│   ├── config.py          # Configuration classes
│   ├── extensions.py      # Flask extensions
│   ├── cli.py             # CLI commands
│   ├── blueprints/        # Route handlers
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── items.py
│   │   ├── recipes.py
│   │   ├── sites.py
│   │   └── admin.py
│   ├── models/            # Database models
│   │   ├── user.py
│   │   ├── item.py
│   │   ├── recipe.py
│   │   ├── site.py
│   │   └── team.py
│   ├── forms/             # WTForms
│   ├── services/          # Business logic
│   │   ├── security/
│   │   └── recipes/
│   ├── templates/         # Jinja2 templates
│   └── static/            # CSS, JS, images
├── data/
│   └── canonical_recipes.json
├── tests/                 # pytest tests
├── migrations/            # Alembic migrations
├── run.py                 # Development entry point
├── wsgi.py                # Production entry point
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
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

# With production profile (includes nginx, redis)
docker-compose --profile production up -d
```

### Azure App Service

See [azure-deploy.md](docs/azure-deploy.md) for detailed instructions.

### Manual Deployment

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

## Security Features

- **CSRF Protection** - All forms protected with tokens
- **Password Hashing** - bcrypt with work factor 12
- **Session Security** - HttpOnly, Secure, SameSite cookies
- **Rate Limiting** - Protection against brute force attacks
- **Content Security Policy** - XSS prevention headers
- **Input Validation** - Server-side validation on all inputs

See [SECURITY.md](SECURITY.md) for security policy and reporting.

## AI Recipe Suggestions

SmartFridge supports multiple AI backends:

- **Local** (default) - Rule-based matching with canonical recipes
- **OpenAI** - GPT-powered suggestions
- **Azure OpenAI** - Enterprise Azure deployment

Configure with `AI_ADAPTER` environment variable.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Licence

This project is licensed under the MIT Licence - see the [LICENCE](LICENCE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/) - The web framework
- [Bootstrap](https://getbootstrap.com/) - UI framework
- [Bootstrap Icons](https://icons.getbootstrap.com/) - Icon library
