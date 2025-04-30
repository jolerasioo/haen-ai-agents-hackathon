# HAEN AI Hub Gateway Quick Start Guide

This guide will help you quickly set up and deploy the HAEN AI Hub Gateway in your Azure environment.

## Prerequisites

Before you begin, ensure you have:

1. **Azure Account** with the following:
   - Access to Azure OpenAI service
   - Permissions to create resources (Owner or Contributor role)
   - Microsoft.Authorization/roleAssignments/write permissions

2. **Development Environment** with:
   - Azure CLI installed
   - Azure Developer CLI (azd) installed
   - Git installed

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/haen-ai-hub-gateway.git
cd haen-ai-hub-gateway
```

## Step 2: Login to Azure

```bash
# Login to Azure (use --tenant-id if you have multiple tenants)
az login

# Set the correct subscription
az account set --subscription "Your Subscription Name"

# Login with Azure Developer CLI
azd auth login
```

## Step 3: Configure Deployment Parameters

The HAEN AI Hub Gateway deployment can be customized by modifying parameters in `infra/main.bicep`. 

The most important parameters to consider:

- `location`: Primary Azure region where resources will be deployed
- `openAiInstances`: Configuration of OpenAI instances including models and regions
- `apimSku`: API Management SKU (Developer or Premium)
- `apimNetworkType`: Network type for APIM (External or Internal)

For most deployments, the default values should be sufficient.

## Step 4: Setup Environment and Deploy

```bash
# Create a new environment
azd env new haen-ai-hub-gateway-dev

# Deploy the solution
azd up
```

This will:
1. Create all required Azure resources
2. Configure API Management policies
3. Set up monitoring and observability
4. Configure OpenAI instances and deployments

The deployment process typically takes 20-30 minutes to complete.

## Step 5: Access the AI Hub Gateway

After deployment completes, you'll see outputs including:

- APIM_NAME: The name of your API Management instance
- APIM_GATEWAY_URL: The URL for accessing your API Management gateway
- APIM_AOI_PATH: The path for OpenAI APIs

You can access the API Management portal in the Azure Portal to:
- Create and manage API subscriptions
- Monitor API usage
- Test API calls

## Step 6: Integrate HAEN Components

See the [HAEN Integration Guide](./haen-integration.md) for detailed instructions on integrating each HAEN component with the AI Hub Gateway.

The basic integration pattern involves:

1. Obtaining an API Management subscription key
2. Updating API endpoints in HAEN components to point to the gateway
3. Replacing direct Azure OpenAI authentication with API Management subscription key

## Monitoring and Observability

The deployment includes:

- Application Insights for monitoring API performance
- Log Analytics for log collection
- Dashboards for visualizing key metrics
- Usage tracking for chargeback

Access these in the Azure Portal under the respective resource types.

## Troubleshooting

If you encounter issues during deployment:

1. Check Azure deployment logs in the resource group
2. Review the Azure Developer CLI logs
3. Ensure your account has sufficient permissions
4. Verify that Azure OpenAI is available in the selected regions

For persistent issues, refer to the [Deployment Troubleshooting Guide](./deployment-troubleshooting.md).

## Next Steps

- [HAEN Integration Guide](./haen-integration.md)
- [Architecture Deep Dive](./architecture-deep-dive.md)
- [OpenAI Usage Ingestion](./openai-usage-ingestion.md)
- [API Management Configuration](./apim-configuration.md) 