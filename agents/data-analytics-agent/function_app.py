import azure.functions as func
import logging
import json
from datetime import datetime
from typing import Dict, Any

from agent_service import DataAnalyticsAgent

# Initialize the agent
data_analytics_agent = DataAnalyticsAgent()

# Create function app
app = func.FunctionApp()

@app.route(route="GetDbSchema", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def get_db_schema(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get the schema of the Cosmos DB database.
    """
    logging.info("Processing request to get database schema")
    
    try:
        schema = data_analytics_agent.get_database_schema()
        
        if "error" in schema:
            return func.HttpResponse(
                json.dumps({"error": schema["error"]}),
                status_code=400,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps({"schema": schema}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error getting database schema: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="GetSchemaDescription", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def get_schema_description(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get a human-readable description of the database schema.
    """
    logging.info("Processing request to get schema description")
    
    try:
        schema = data_analytics_agent.get_database_schema()
        summary = data_analytics_agent.summarize_schema(schema)
        
        return func.HttpResponse(
            json.dumps({"description": summary}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error getting schema description: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="RunSqlQuery", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def run_sql_query(req: func.HttpRequest) -> func.HttpResponse:
    """
    Run a SQL query against the Cosmos DB database.
    """
    logging.info("Processing request to run SQL query")
    
    try:
        # Get request body
        req_body = req.get_json()
        
        # Get SQL query from request
        sql_query = req_body.get("query")
        analysis_type = req_body.get("analysis_type", "summary")
        
        if not sql_query:
            return func.HttpResponse(
                json.dumps({"error": "SQL query is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Check if it's a simple query or an analytical query
        if analysis_type and analysis_type != "summary":
            results = data_analytics_agent.execute_analytical_query(sql_query, analysis_type)
        else:
            results = data_analytics_agent.execute_sql_query(sql_query)
        
        # Generate a human-readable summary
        summary = data_analytics_agent.analyze_results(results)
        
        return func.HttpResponse(
            json.dumps({
                "query": sql_query,
                "results": results,
                "summary": summary
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error running SQL query: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="HealthCheck", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint.
    """
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }),
        status_code=200,
        mimetype="application/json"
    )