# HAEN AI Hub Gateway

The HAEN AI Hub Gateway is a solution accelerator that provides a centralized AI API gateway specifically designed for the HAEN application. It enables various components of the HAEN ecosystem to leverage Azure AI services in a secure, governed, and efficient manner.

## User Story

The HAEN AI Hub Gateway is designed to be a central hub for AI services within the HAEN ecosystem, providing a single point of entry for AI services, and enabling the organization to manage and govern AI services in a consistent manner.

![HAEN AI Hub Gateway](assets/ai-hub-gateway-architecture.png)

### Key features

- **Centralized AI API Gateway**: A central hub for HAEN AI services, providing a single point of entry for AI services that can be shared among multiple agents and components in a secure and governed approach.
- **Seamless integration with Azure AI services**: Ability to just update endpoints and keys in existing HAEN agents to switch to use AI Hub Gateway.
- **AI routing and orchestration**: The HAEN AI Hub Gateway provides a mechanism to route and orchestrate AI services, based on priority and target model enabling the organization to manage and govern AI services in a consistent manner.
- **Granular access control**: The HAEN AI Hub Gateway does not use master keys to access AI services, instead, it uses managed identities to access AI services while consumers can use gateway keys.
- **Private connectivity**: The HAEN AI Hub Gateway is designed to be deployed in a private network, and it uses private endpoints to access AI services.
- **Capacity management**: The HAEN AI Hub Gateway provides a mechanism to manage capacity based on requests and tokens.
- **Usage & charge-back**: The HAEN AI Hub Gateway provides a mechanism to track usage and charge-back to the respective components with flexible integration with existing charge-back & data platforms.
- **Resilient and scalable**: The HAEN AI Hub Gateway is designed to be resilient and scalable, and it uses Azure API Management with its zonal redundancy and regional gateways which provides a scalable and resilient solution.
- **Full observability**: The HAEN AI Hub Gateway provides full observability with Azure Monitor, Application Insights, and Log Analytics with detailed insights into performance, usage, and errors.
- **Hybrid support**: The HAEN AI Hub Gateway approach the deployment of backends and gateway on Azure, on-premises or other clouds.

## One-click deploy

This solution accelerator provides a one-click deploy option to deploy the HAEN AI Hub Gateway in your Azure subscription through Azure Developer CLI (azd) or Bicep (IaC).

### What is being deployed?

#### Azure components

The one-click deploy option will deploy the following components in your Azure subscription:

1. **Azure API Management**: Azure API Management is a fully managed service that powers most of the GenAI gateway capabilities.
2. **Application Insights**: Application Insights is an extensible Application Performance Management (APM) service that will provides critical insights on the gateway operational performance. It will also include a dashboard for the key metrics.
3. **Event Hub**: Event Hub is a fully managed, real-time data ingestion service that's simple, trusted, and scalable and it is used to stream usage and charge-back data to target data and charge back platforms.
4. **Azure OpenAI**: 3 instances of Azure OpenAI across 3 regions. Azure OpenAI is a cloud deployment of cutting edge generative models from OpenAI (like ChatGPT, DALL.E and more).
5. **Cosmos DB**: Azure Cosmos DB is a fully managed NoSQL database for storing usage and charge-back data.
6. **Azure Function App**: to support real-time event processing service that will be used to process the usage and charge-back data from Event Hub and push it to Cosmos DB.
7. **User Managed Identity**: A user managed identity to be used by the Azure API Management to access the Azure OpenAI services/Event Hub and another for Azure Stream Analytics to access Event Hub and Cosmos DB.
8. **Virtual Network**: A virtual network to host the Azure API Management and the other Azure resources.
9. **Private Endpoints & Private DNS Zones**: Private endpoints for Azure OpenAI, Cosmos DB, Azure Function, Azure Monitor and Event Hub to enable private connectivity.

### Prerequisites

In order to deploy and run this solution accelerator, you'll need:

* **Azure Account** - If you're new to Azure, get an Azure account for free and you'll get some free Azure credits to get started.
* **Azure subscription with access enabled for the Azure OpenAI service** - You can request access. You can also visit the Cognitive Search docs to get some free Azure credits to get you started.
* **Azure account permissions** - Your Azure Account must have `Microsoft.Authorization/roleAssignments/write` permissions, such as User Access Administrator or Owner.

For local development, you'll need:

* **Azure CLI** - The Azure CLI is a command-line tool that provides a great experience for managing Azure resources. You can install the Azure CLI on your local machine by following the instructions [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
* **Azure Developer CLI (azd)** - The Azure Developer CLI is a command-line tool that provides a great experience for deploying Azure resources. You can install the Azure Developer CLI on your local machine by following the instructions [here](https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd).
* **VS Code** - Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS, and Linux. You can install Visual Studio Code on your local machine by following the instructions [here](https://code.visualstudio.com/Download).

### How to deploy?

It is recommended to check first the main.bicep file that includes the deployment configuration and parameters.

Make sure you have enough OpenAI capacity for gpt-35-turbo and embedding in the selected regions.

When you are happy with the configuration, you can deploy the solution using the following command:

```bash
# Use --tenant-id if you have multiple tenants with login
azd auth login

# Setup new environment
azd env new haen-ai-hub-gateway-dev

# Deploy the solution accelerator
azd up

# You can also use to provision only the infrastructure
# azd provision

# You can also use this to deploy the associated Logic App workflows code (given that infrastructure is already deployed)
# azd deploy
```

> **NOTE**: If you faced any deployment errors, try to rerun the `azd up` command as you might be facing a transient error.

After that, you can start using the HAEN AI Hub Gateway through the Azure API Management on Azure Portal.

## Supporting documents

To dive deeper into the HAEN AI Hub Gateway technical mechanics, you can check out the following guides:

### Architecture guides

* Architecture deep dive
* Deployment components
* API Management configuration
* OpenAI Usage Ingestion
* Bring your own Network

### Onboarding guides

* OpenAI Onboarding
* AI Search Onboarding
* Power BI Dashboard
* Throttling Events Alerts
* AI Studio Integration

### HAEN Integration guides

* Integrating HAEN Data Analytics Agent
* Integrating HAEN Auditing Logs Agent
* Integrating HAEN Grounded Bing Agent
* Integrating HAEN Create Alerts Agent
* Integrating HAEN Authority Action Agent
* Integrating HAEN ACS Realtime AI API Communications

## License

This project is licensed under the MIT License - see the LICENSE file for details. 