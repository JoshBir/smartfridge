# SmartFridge - Getting Started Guide

This guide provides step-by-step instructions for running SmartFridge locally in development mode and deploying to Azure.

---

## Part 1: Local Development Setup

### Prerequisites

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **VS Code** (recommended) - [Download VS Code](https://code.visualstudio.com/)

### Step 1: Clone the Repository

```powershell
# Navigate to your projects folder
cd C:\Projects

# Clone the repository
git clone https://github.com/JoshBir/smartfridge.git

# Enter the project directory
cd smartfridge
```

### Step 2: Create a Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate

# Activate it (Windows Command Prompt)
venv\Scripts\activate.bat

# Activate it (Linux/macOS)
source venv/bin/activate
```

You should see `(venv)` at the start of your command prompt.

### Step 3: Install Dependencies

```powershell
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Step 4: Configure Environment Variables

```powershell
# Copy the example environment file
copy .env.example .env
```

Open `.env` in your editor and update these values:

```ini
# Required: Generate a secure secret key
SECRET_KEY=your-secret-key-here-make-it-long-and-random

# Optional: Set to 'development' for debug mode
FLASK_CONFIG=development

# Optional: AI adapter (use 'local' for development)
AI_ADAPTER=local
```

**Tip:** Generate a secure secret key with Python:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Initialise the Database

```powershell
# Create database tables
flask init-db

# Create an admin user (follow the prompts)
flask create-admin

# Load sample recipes (optional)
flask seed-recipes
```

### Step 6: Run the Development Server

```powershell
# Start the application
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 7: Access the Application

Open your browser and go to: **http://127.0.0.1:5000**

- Login with the admin credentials you created
- Start adding fridge items!

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Useful Development Commands

```powershell
# List all CLI commands
flask --help

# List all users
flask list-users

# Reset a user's password
flask set-password

# Activate/deactivate a user
flask activate-user
flask deactivate-user

# Clean up old expired items
flask clean-expired --days 30
```

---

## Part 2: Deploying to Azure

### Prerequisites

- **Azure Account** - [Create free account](https://azure.microsoft.com/free/)
- **Azure CLI** - [Install Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)

### Step 1: Login to Azure

```powershell
# Login to Azure (opens browser)
az login

# Verify your subscription
az account show
```

### Step 2: Set Configuration Variables

```powershell
# Set these variables (adjust as needed)
$RESOURCE_GROUP = "smartfridge-rg"
$LOCATION = "uksouth"
$APP_NAME = "smartfridge-$(Get-Random -Maximum 9999)"
$PLAN_NAME = "smartfridge-plan"
$DB_SERVER = "smartfridge-db-$(Get-Random -Maximum 9999)"
$DB_NAME = "smartfridge"
$DB_ADMIN = "smartfridgeadmin"
$DB_PASSWORD = "$(python -c 'import secrets; print(secrets.token_urlsafe(16))')!Aa1"

# Display the app name (you'll need this later)
Write-Host "Your app will be at: https://$APP_NAME.azurewebsites.net"
Write-Host "Database password: $DB_PASSWORD (save this!)"
```

### Step 3: Create Resource Group

```powershell
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 4: Create PostgreSQL Database

```powershell
# Create PostgreSQL Flexible Server
az postgres flexible-server create `
    --name $DB_SERVER `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --admin-user $DB_ADMIN `
    --admin-password $DB_PASSWORD `
    --sku-name Standard_B1ms `
    --tier Burstable `
    --storage-size 32 `
    --yes

# Create the database
az postgres flexible-server db create `
    --resource-group $RESOURCE_GROUP `
    --server-name $DB_SERVER `
    --database-name $DB_NAME

# Allow Azure services to connect
az postgres flexible-server firewall-rule create `
    --resource-group $RESOURCE_GROUP `
    --name $DB_SERVER `
    --rule-name AllowAzure `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0
```

### Step 5: Create App Service

```powershell
# Create App Service Plan
az appservice plan create `
    --name $PLAN_NAME `
    --resource-group $RESOURCE_GROUP `
    --is-linux `
    --sku B1

# Create Web App
az webapp create `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --plan $PLAN_NAME `
    --runtime "PYTHON:3.11"
```

### Step 6: Configure App Settings

```powershell
# Generate a secret key
$SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"

# Build database connection string
$DB_HOST = "$DB_SERVER.postgres.database.azure.com"
$DATABASE_URL = "postgresql://${DB_ADMIN}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

# Set environment variables
az webapp config appsettings set `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --settings `
        FLASK_CONFIG=production `
        SECRET_KEY=$SECRET_KEY `
        DATABASE_URL=$DATABASE_URL `
        AI_ADAPTER=local `
        SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

### Step 7: Configure Startup Command

```powershell
az webapp config set `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --startup-file "gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=600 wsgi:application"
```

### Step 8: Deploy the Code

```powershell
# Deploy from local directory
az webapp up `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --runtime "PYTHON:3.11"
```

This may take 5-10 minutes. You'll see progress in the terminal.

### Step 9: Initialise the Database

```powershell
# SSH into the web app
az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP
```

Once connected, run:
```bash
# Inside the SSH session
cd /home/site/wwwroot
flask db upgrade
flask create-admin --username admin --email admin@example.com
flask seed-recipes
exit
```

### Step 10: Access Your Application

Open your browser and go to:
```
https://<APP_NAME>.azurewebsites.net
```

Login with the admin credentials you created.

---

## Post-Deployment Configuration

### Enable HTTPS Only

```powershell
az webapp update `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --https-only true
```

### View Application Logs

```powershell
# Stream live logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# Enable logging
az webapp log config `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --application-logging filesystem `
    --level information
```

### Set Up Custom Domain (Optional)

```powershell
# Add custom domain
az webapp config hostname add `
    --webapp-name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --hostname "smartfridge.yourdomain.com"
```

### Scale Up (If Needed)

```powershell
# Upgrade to a more powerful tier
az appservice plan update `
    --name $PLAN_NAME `
    --resource-group $RESOURCE_GROUP `
    --sku P1V2
```

---

## Updating Your Deployment

After making changes locally:

```powershell
# Test locally first
pytest

# Commit your changes
git add .
git commit -m "Description of changes"
git push origin main

# Redeploy to Azure
az webapp up `
    --name $APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --runtime "PYTHON:3.11"
```

---

## Cleanup (Delete All Resources)

**Warning:** This permanently deletes everything!

```powershell
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## Troubleshooting

### Local Issues

| Problem | Solution |
|---------|----------|
| `venv\Scripts\Activate` fails | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `flask` command not found | Ensure venv is activated: `.\venv\Scripts\Activate` |
| Database errors | Delete `instance/smartfridge.db` and run `flask init-db` again |

### Azure Issues

| Problem | Solution |
|---------|----------|
| 502 Bad Gateway | Check logs: `az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP` |
| Database connection failed | Verify firewall rules allow Azure services |
| Deployment stuck | Restart the app: `az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP` |

### Getting Help

- Check the logs: `az webapp log tail ...`
- SSH into the container: `az webapp ssh ...`
- Review app settings: `az webapp config appsettings list ...`

---

## Cost Estimate

| Resource | Tier | Estimated Monthly Cost |
|----------|------|----------------------|
| App Service | B1 (Basic) | ~£10/month |
| PostgreSQL | Burstable B1ms | ~£12/month |
| **Total** | | **~£22/month** |

Free tier options:
- App Service: F1 (free, limited)
- PostgreSQL: Use SQLite locally, upgrade for production
