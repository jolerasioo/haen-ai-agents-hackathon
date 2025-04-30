# Grounded Bing Agent

A FastAPI application that uses Azure AI Agent Service with Bing Grounding to provide up-to-date responses to user queries.

## Prerequisites

- Azure AI Projects SDK
- Azure Identity credentials
- Project connection string from Azure AI Foundry
- Bing connection name from Azure AI Foundry

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```
   PROJECT_CONNECTION_STRING=your_project_connection_string
   BING_CONNECTION_NAME=your_bing_connection_name
   ```

## Running the Application

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

The API will be available at http://localhost:8000

## API Endpoints

### Health Check
```
GET /health
```

### Process Query
```
POST /query
Content-Type: application/json

{
    "query": "What's the latest news about climate change?"
}
```

## Architecture

- `agent.py`: Core agent implementation using Azure AI Projects SDK
- `app.py`: FastAPI web application exposing the agent's functionality

## Deployment

This application can be deployed to Azure App Service or any container-based service that supports Python.

```bash
# Example Azure App Service deployment
az webapp up --sku B1 --name your-app-name
```