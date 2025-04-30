# Integrating HAEN Components with AI Hub Gateway

This guide provides instructions for integrating various HAEN (Humanitarian AI Emergency Network) components with the AI Hub Gateway to leverage centralized AI services.

## Overview

The HAEN AI Hub Gateway provides a centralized, secure, and governed approach to accessing Azure AI services. By routing all AI requests through the gateway, HAEN components can benefit from:

- Improved reliability through multi-region deployment
- Centralized monitoring and observability
- Consistent governance and access control
- Usage tracking and chargebacks
- Optimized AI model routing

## Prerequisites

Before integrating any HAEN component with the AI Hub Gateway, ensure you have:

1. Successfully deployed the HAEN AI Hub Gateway
2. Access to the API Management service in the Azure Portal
3. A valid subscription key for the API Management service
4. Access to the HAEN component code that needs integration

## Integration Steps

### Step 1: Obtain API Management Subscription Key

1. Navigate to the API Management service in the Azure Portal
2. Go to the "Subscriptions" section
3. Create a new subscription or use an existing one
4. Copy the primary or secondary key for use in your HAEN component

### Step 2: Update API Endpoints in HAEN Components

For each HAEN component, update the OpenAI endpoint to point to the AI Hub Gateway instead of directly to Azure OpenAI. The endpoint format will be:

```
https://{apim-name}.azure-api.net/openai/deployments/{deployment-name}/completions
```

Where:
- `{apim-name}` is the name of your API Management instance
- `{deployment-name}` is the name of the OpenAI deployment (e.g., `chat`, `embedding`, `gpt-4o`, or `haen-response`)

### Step 3: Update Authentication Method

Replace the Azure OpenAI key authentication with the API Management subscription key:

1. Remove any existing `api-key` headers pointing to Azure OpenAI
2. Add a new `Ocp-Apim-Subscription-Key` header with your API Management subscription key
3. If using an SDK, update the authentication configuration accordingly

## HAEN Component-Specific Integration

### Data Analytics Agent

The Data Analytics Agent requires both chat completion and embedding capabilities:

```python
# Before
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# After
openai_client = AzureOpenAI(
    api_key=os.getenv("APIM_SUBSCRIPTION_KEY"),
    api_version="2023-05-15",
    azure_endpoint="https://{apim-name}.azure-api.net/openai"
)
```

### Auditing Logs Agent

Update the Auditing Logs Agent configuration:

```javascript
// Before
const openaiConfig = {
  apiKey: process.env.AZURE_OPENAI_API_KEY,
  endpoint: process.env.AZURE_OPENAI_ENDPOINT,
  deployment: "chat"
};

// After
const openaiConfig = {
  apiKey: process.env.APIM_SUBSCRIPTION_KEY,
  endpoint: `https://${apim-name}.azure-api.net/openai`,
  deployment: "chat",
  headers: {
    "Ocp-Apim-Subscription-Key": process.env.APIM_SUBSCRIPTION_KEY
  }
};
```

### Grounded Bing Agent

The Grounded Bing Agent will need updates to its OpenAI configuration:

```python
# Before
openai.api_type = "azure"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")

# After
openai.api_type = "azure"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("APIM_SUBSCRIPTION_KEY")
openai.api_base = f"https://{apim-name}.azure-api.net/openai"
```

### Create Alerts Agent

For the Create Alerts Agent, modify its configuration:

```python
# Before
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# After
client = AzureOpenAI(
    api_key=os.getenv("APIM_SUBSCRIPTION_KEY"),
    api_version="2023-07-01-preview",
    azure_endpoint=f"https://{apim-name}.azure-api.net/openai"
)
```

### Authority Action Agent

For emergency response scenarios, the Authority Action Agent should use the `haen-response` deployment:

```python
# Before
completion = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    temperature=0.7
)

# After
completion = client.chat.completions.create(
    model="haen-response",  # Using the high-capacity emergency response model
    messages=messages,
    temperature=0.7
)
```

### ACS Realtime AI API Communications

For real-time communications, update the endpoint configuration:

```csharp
// Before
var openAIClient = new OpenAIClient(
    new Uri(Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")),
    new AzureKeyCredential(Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY"))
);

// After
var openAIClient = new OpenAIClient(
    new Uri($"https://{apim-name}.azure-api.net/openai"),
    new AzureKeyCredential(Environment.GetEnvironmentVariable("APIM_SUBSCRIPTION_KEY"))
);
```

## Usage Monitoring

After integration, you can monitor the AI service usage by each HAEN component:

1. Navigate to the API Management service in the Azure Portal
2. Go to the "Analytics" section
3. View the metrics by API, operation, and subscription
4. Use the Power BI dashboard for more detailed usage reports and chargeback information

## Troubleshooting

If you encounter issues when integrating with the AI Hub Gateway:

1. Verify that your subscription key is valid and active
2. Check that the deployment name in the URL matches one of the available deployments
3. Inspect the request/response logs in API Management
4. Check Application Insights for detailed error information

For further assistance, contact the HAEN infrastructure team. 