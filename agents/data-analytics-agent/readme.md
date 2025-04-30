# Data Analytics Agent

A comprehensive data analytics agent that provides SQL querying and data analysis capabilities against Cosmos DB databases.

## Features

- Database schema exploration
- SQL query execution
- Data analysis and summarization
- Trend analysis for time-series data
- Distribution analysis for numerical data
- Correlation analysis between variables
- Integration with Azure AI Agent Service

## Architecture

This solution is built with the following components:

- **Cosmos DB Service**: Handles database interactions
- **Data Analytics Agent**: Processes queries and generates insights
- **FastAPI Web Application**: Provides REST API endpoints
- **Azure Functions**: Serverless API endpoints
- **AI Agent Integration**: Connects with Azure AI Agent Service

## API Endpoints

### Web Application (FastAPI)

- `GET /schema`: Get the database schema
- `GET /schema/summary`: Get a human-readable summary of the schema
- `POST /query`: Execute a SQL query and get results with analysis
- `GET /health`: Health check endpoint

### Function App

- `GET /api/GetDbSchema`: Get the database schema
- `GET /api/GetSchemaDescription`: Get a human-readable description of the schema
- `POST /api/RunSqlQuery`: Execute a SQL query and get results with analysis
- `GET /api/HealthCheck`: Health check endpoint

### AI Agent Service Integration

- `POST /api/AiAgentProcessor`: Process requests from Azure AI Agent Service
- `GET /api/GetToolDefinitions`: Get tool definitions for Azure AI Agent Service

## AI Agent Tools

The agent exposes the following tools to Azure AI Agent Service:

1. **GetDbSchema**: Retrieves the database schema
2. **RunSqlQuery**: Executes SQL queries with optional analysis types

## Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the web application:
   ```bash
   uvicorn app:app --reload
   ```
5. Deploy the Function App to Azure:
   ```bash
   func azure functionapp publish your-function-app-name
   ```

## Authentication

The web application uses OAuth2 with JWT for authentication:

1. Get an access token:
   ```
   POST /token
   Content-Type: application/x-www-form-urlencoded
   
   username=admin&password=adminpassword
   ```

2. Use the token in subsequent requests:
   ```
   GET /schema
   Authorization: Bearer your_token_here
   ```

## Sample Queries

### Basic Query

```sql
SELECT * FROM Users
```

### Analytical Query

```sql
SELECT OrderDate, Amount, ProductID 
FROM Orders
WHERE OrderDate >= '2023-01-01'
```

## Using the AI Agent Integration

To integrate with Azure AI Agent Service:

1. Deploy the Function App to Azure
2. Configure your AI Agent to use the tool endpoints
3. Set up any necessary authentication between services

## License

This project is licensed under the MIT License.