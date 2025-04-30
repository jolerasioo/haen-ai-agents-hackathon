# Azure App Service Deployment Instructions

## Prerequisites
- Azure account with subscription
- Azure CLI installed

## Deployment Options

### Option 1: Deploy using Azure CLI

1. Log in to Azure:
   ```bash
   az login
   ```

2. Create a resource group (if you don't have one):
   ```bash
   az group create --name myResourceGroup --location westus2
   ```

3. Create an App Service Plan:
   ```bash
   az appservice plan create --name myAppServicePlan --resource-group myResourceGroup --sku B1 --is-linux
   ```

4. Create the Web App:
   ```bash
   az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name your-app-name --runtime "PYTHON:3.10" --deployment-local-git
   ```

5. Configure App Settings (environment variables):
   ```bash
   az webapp config appsettings set --resource-group myResourceGroup --name your-app-name --settings PROJECT_CONNECTION_STRING="your_connection_string" BING_CONNECTION_NAME="your_bing_connection"
   ```

6. Deploy the code:
   ```bash
   git remote add azure https://your-deployment-url
   git push azure main
   ```

### Option 2: Deploy from Azure Portal

1. In the Azure portal, navigate to App Services
2. Create a new Web App with Linux and Python 3.10 runtime
3. Once created, go to the Deployment Center
4. Choose "Local Git" as the source
5. Follow the instructions to push your code to the provided Git URL

### Option 3: Deploy using Docker

1. Build the Docker image:
   ```bash
   docker build -t grounded-bing-agent .
   ```

2. Create an Azure Container Registry (ACR) or use Docker Hub
3. Push your image to the registry
4. Create a Web App for Containers pointing to your image

## Configuration

Ensure these environment variables are set in your App Service Configuration:

- `PROJECT_CONNECTION_STRING`: Your Azure AI project connection string
- `BING_CONNECTION_NAME`: Your Bing connection name

You can set these in the Azure portal under Configuration > Application settings.