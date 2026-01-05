# Azure App Service Deployment Guide

This guide walks through deploying SmartFridge to Azure App Service with PostgreSQL.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed (`az`)
- Docker (optional, for container deployment)

## Option 1: Deploy as Web App with Code

### 1. Create Azure Resources

```bash
# Login to Azure
az login

# Set variables
RESOURCE_GROUP="smartfridge-rg"
LOCATION="uksouth"
APP_NAME="smartfridge-app"
PLAN_NAME="smartfridge-plan"
DB_SERVER="smartfridge-db-server"
DB_NAME="smartfridge"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service plan (Linux, Python)
az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --is-linux \
    --sku B1

# Create Web App
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --runtime "PYTHON:3.11"
```

### 2. Create PostgreSQL Database

```bash
# Create PostgreSQL Flexible Server
az postgres flexible-server create \
    --name $DB_SERVER \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user smartfridgeadmin \
    --admin-password "YourSecurePassword123!" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32

# Create database
az postgres flexible-server db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $DB_SERVER \
    --database-name $DB_NAME

# Allow Azure services to connect
az postgres flexible-server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --name $DB_SERVER \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0
```

### 3. Configure App Settings

```bash
# Get database connection string
DB_HOST="${DB_SERVER}.postgres.database.azure.com"
DATABASE_URL="postgresql://smartfridgeadmin:YourSecurePassword123!@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

# Generate secret key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Set environment variables
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        FLASK_CONFIG=production \
        SECRET_KEY="$SECRET_KEY" \
        DATABASE_URL="$DATABASE_URL" \
        AI_ADAPTER=local \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

### 4. Configure Startup Command

```bash
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "gunicorn --bind=0.0.0.0:8000 --workers=4 wsgi:application"
```

### 5. Deploy Code

```bash
# From project root
az webapp up \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --runtime "PYTHON:3.11"

# Or using Git deployment
az webapp deployment source config-local-git \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP

# Get Git URL and push
GIT_URL=$(az webapp deployment source config-local-git \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query url -o tsv)

git remote add azure $GIT_URL
git push azure main
```

### 6. Initialise Database

```bash
# SSH into the container
az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP

# Run commands
flask db upgrade
flask create-admin --username admin --email admin@example.com --password "SecureAdminP@ss123!"
flask seed-recipes
exit
```

## Option 2: Deploy as Container

### 1. Build and Push Container

```bash
# Create Azure Container Registry
ACR_NAME="smartfridgeacr"

az acr create \
    --name $ACR_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku Basic \
    --admin-enabled true

# Login to ACR
az acr login --name $ACR_NAME

# Build and push
az acr build \
    --registry $ACR_NAME \
    --image smartfridge:latest \
    .
```

### 2. Create Web App for Containers

```bash
# Get ACR credentials
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Create Web App for Containers
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --deployment-container-image-name "${ACR_NAME}.azurecr.io/smartfridge:latest"

# Configure container registry
az webapp config container set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name "${ACR_NAME}.azurecr.io/smartfridge:latest" \
    --docker-registry-server-url "https://${ACR_NAME}.azurecr.io" \
    --docker-registry-server-user $ACR_NAME \
    --docker-registry-server-password $ACR_PASSWORD
```

### 3. Enable Continuous Deployment

```bash
# Enable CI/CD webhook
az webapp deployment container config \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --enable-cd true
```

## Option 3: Deploy with Azure Developer CLI (azd)

### 1. Create azure.yaml

```yaml
# azure.yaml
name: smartfridge
services:
  web:
    project: .
    language: python
    host: appservice
```

### 2. Deploy

```bash
# Initialize (first time)
azd init

# Provision and deploy
azd up
```

## Post-Deployment Configuration

### Enable HTTPS Only

```bash
az webapp update \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --https-only true
```

### Configure Custom Domain

```bash
# Add custom domain
az webapp config hostname add \
    --webapp-name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --hostname "smartfridge.yourdomain.com"

# Create managed certificate
az webapp config ssl create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --hostname "smartfridge.yourdomain.com"
```

### Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
    --app smartfridge-insights \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --application-type web

# Get instrumentation key
APPINSIGHTS_KEY=$(az monitor app-insights component show \
    --app smartfridge-insights \
    --resource-group $RESOURCE_GROUP \
    --query instrumentationKey -o tsv)

# Configure app
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=$APPINSIGHTS_KEY
```

### Configure Scaling

```bash
# Enable autoscale
az monitor autoscale create \
    --resource-group $RESOURCE_GROUP \
    --resource $PLAN_NAME \
    --resource-type "Microsoft.Web/serverfarms" \
    --name smartfridge-autoscale \
    --min-count 1 \
    --max-count 5 \
    --count 1

# Add CPU-based rule
az monitor autoscale rule create \
    --resource-group $RESOURCE_GROUP \
    --autoscale-name smartfridge-autoscale \
    --condition "Percentage CPU > 70 avg 5m" \
    --scale out 1

az monitor autoscale rule create \
    --resource-group $RESOURCE_GROUP \
    --autoscale-name smartfridge-autoscale \
    --condition "Percentage CPU < 30 avg 5m" \
    --scale in 1
```

## Monitoring and Maintenance

### View Logs

```bash
# Stream live logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### Database Backups

```bash
# Enable point-in-time restore
az postgres flexible-server update \
    --name $DB_SERVER \
    --resource-group $RESOURCE_GROUP \
    --backup-retention 14
```

### Health Checks

```bash
# Configure health check endpoint
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --generic-configurations '{"healthCheckPath": "/health"}'
```

## Cost Optimisation

- Use **B1** tier for development/testing
- Consider **P1v2** for production workloads
- Use **Burstable** PostgreSQL tier for cost efficiency
- Enable auto-shutdown for non-production environments

## Troubleshooting

### View Application Errors

```bash
# Check deployment logs
az webapp log deployment show --name $APP_NAME --resource-group $RESOURCE_GROUP

# Check application logs
az webapp log show --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### Common Issues

1. **502 Bad Gateway** - Check startup command and app logs
2. **Database connection failed** - Verify firewall rules and connection string
3. **Static files not loading** - Ensure WhiteNoise is configured or use CDN

### Reset Deployment

```bash
# Restart app
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

# Redeploy
az webapp deployment source sync --name $APP_NAME --resource-group $RESOURCE_GROUP
```

## Cleanup

```bash
# Delete all resources
az group delete --name $RESOURCE_GROUP --yes --no-wait
```
