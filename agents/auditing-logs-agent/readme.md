# Auditing Logs Agent

A comprehensive auditing logs management system built with Azure services.

## Features

- Create, retrieve, and delete audit logs
- Semantic search capability with Azure AI Search
- Real-time log analysis with Azure OpenAI and Semantic Kernel
- Integration with Azure Monitor and Azure Sentinel
- Support for various log categories and severity levels
- Ability to filter logs by multiple criteria

## Architecture

This solution uses the following Azure services:

- **Azure Functions**: For serverless API endpoints
- **Azure Cosmos DB**: Primary storage for audit logs
- **Azure AI Search**: For semantic search capability
- **Azure Monitor**: For real-time log monitoring
- **Azure Sentinel**: For security incident monitoring
- **Azure OpenAI/Semantic Kernel**: For log analysis and AI-powered insights

## API Endpoints

### Function App Endpoints

- `POST /create_log`: Create a new audit log entry
- `GET /get_logs`: Retrieve logs based on query parameters
- `GET /get_log/{log_id}`: Get a specific log by ID
- `DELETE /delete_log/{log_id}`: Delete a log by ID
- `POST /analyze_logs`: Analyze logs using AI

### Web App Endpoints (FastAPI)

- `POST /logs`: Create a new audit log entry
- `GET /logs`: Query logs with filtering
- `GET /logs/{log_id}`: Get a specific log
- `DELETE /logs/{log_id}`: Delete a log
- `POST /logs/analyze`: AI analysis of logs
- `GET /security/incidents`: Get Azure Sentinel security incidents
- `GET /health`: Health check

## Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Deploy to Azure:
   - Function App: Use Azure Functions Core Tools or VS Code
   - Web App: Deploy as an Azure App Service

## Log Structure

Audit logs include:

- `id`: Unique identifier (UUID)
- `timestamp`: When the log was created
- `category`: Log category (USER_ACTION, SYSTEM_EVENT, SECURITY, AGENT_ACTION, INTEGRATION)
- `severity`: Log severity (INFO, WARNING, ERROR, CRITICAL)
- `source`: The source system or component
- `action`: The action or event being logged
- `description`: A description of the log entry
- `user_id`: Optional ID of the user who performed the action
- `details`: Optional additional details (object)
- `correlation_id`: Optional ID to correlate related logs
- `tags`: Optional tags for categorization

## Sample Usage

### Creating a Log

```json
POST /logs
{
  "category": "USER_ACTION",
  "source": "auth-service",
  "action": "user-login",
  "user_id": "user123",
  "details": {
    "ip": "192.168.1.1",
    "browser": "Chrome"
  },
  "tags": ["authentication", "security"]
}
```

### Querying Logs

```
GET /logs?category=USER_ACTION&start_time=2025-01-01T00:00:00Z&limit=10
```

### Analyzing Logs

```json
POST /logs/analyze
{
  "category": "SECURITY",
  "start_time": "2025-01-01T00:00:00Z",
  "end_time": "2025-01-31T23:59:59Z"
}
```

## License

This project is licensed under the MIT License.