import azure.functions as func
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

from models import AuditLog, LogCategory, LogSeverity
from cosmos_service import CosmosDBService
from search_service import SearchService
from monitor_service import MonitorService
from semantic_kernel_service import SemanticKernelService

# Create service instances
cosmos_service = CosmosDBService()
search_service = SearchService()
monitor_service = MonitorService()
semantic_kernel_service = SemanticKernelService()

# Create function app
app = func.FunctionApp()


@app.route(route="create_log", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def create_log(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new audit log entry"""
    logging.info("Processing request to create a new audit log")
    
    try:
        # Parse the request body
        req_body = req.get_json()
        
        # Extract required fields
        category = req_body.get("category")
        source = req_body.get("source")
        action = req_body.get("action")
        
        # Check for required fields
        if not all([category, source, action]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields: category, source, or action"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Extract optional fields
        description = req_body.get("description")
        severity = req_body.get("severity")
        user_id = req_body.get("user_id")
        details = req_body.get("details")
        correlation_id = req_body.get("correlation_id")
        tags = req_body.get("tags")
        
        # If description is not provided, generate it
        if not description:
            description = await semantic_kernel_service.generate_log_description(
                action=action,
                source=source,
                category=category,
                user_id=user_id,
                details=details
            )
        
        # If severity is not provided, classify it
        if not severity:
            severity = await semantic_kernel_service.classify_log_severity(
                action=action,
                source=source,
                description=description,
                details=details
            )
            severity_value = severity.value
        else:
            severity_value = severity
        
        # Create the audit log
        log = AuditLog(
            category=LogCategory(category),
            source=source,
            action=action,
            description=description,
            severity=LogSeverity(severity_value) if isinstance(severity_value, str) else severity,
            user_id=user_id,
            details=details,
            correlation_id=correlation_id,
            tags=tags
        )
        
        # Save to Cosmos DB
        created_log = await cosmos_service.create_log(log)
        
        # Index in Azure AI Search
        await search_service.index_logs([created_log])
        
        # Send to Azure Monitor
        await monitor_service.send_log_to_monitor(created_log)
        
        # Return the created log
        return func.HttpResponse(
            created_log.json(),
            status_code=201,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error creating log: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="get_logs", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
async def get_logs(req: func.HttpRequest) -> func.HttpResponse:
    """Get audit logs based on query parameters"""
    logging.info("Processing request to get audit logs")
    
    try:
        # Extract query parameters
        start_time = req.params.get("start_time")
        end_time = req.params.get("end_time")
        category = req.params.get("category")
        severity = req.params.get("severity")
        source = req.params.get("source")
        user_id = req.params.get("user_id")
        action = req.params.get("action")
        search_text = req.params.get("search_text")
        correlation_id = req.params.get("correlation_id")
        tags = req.params.get("tags")
        limit = int(req.params.get("limit", 100))
        offset = int(req.params.get("offset", 0))
        
        # Parse datetime strings if provided
        start_time_dt = datetime.fromisoformat(start_time) if start_time else None
        end_time_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # Parse tags if provided
        tags_list = tags.split(",") if tags else None
        
        # Create query parameters
        query_params = LogQueryParams(
            start_time=start_time_dt,
            end_time=end_time_dt,
            category=LogCategory(category) if category else None,
            severity=LogSeverity(severity) if severity else None,
            source=source,
            user_id=user_id,
            action=action,
            search_text=search_text,
            correlation_id=correlation_id,
            tags=tags_list,
            limit=limit,
            offset=offset
        )
        
        # If search_text is provided, use Azure AI Search
        if search_text:
            result = await search_service.search_logs(query_params)
        else:
            # Use Cosmos DB for regular queries
            result = await cosmos_service.get_logs(query_params)
        
        # Return the logs
        return func.HttpResponse(
            json.dumps({
                "logs": [log.dict() for log in result["logs"]],
                "total_count": result["total_count"],
                "next_offset": result["next_offset"]
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error getting logs: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="get_log/{log_id}", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
async def get_log(req: func.HttpRequest) -> func.HttpResponse:
    """Get a specific audit log by ID"""
    logging.info("Processing request to get a specific audit log")
    
    try:
        # Extract log ID from the route parameter
        log_id = req.route_params.get("log_id")
        
        if not log_id:
            return func.HttpResponse(
                json.dumps({"error": "Log ID is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get the log from Cosmos DB
        log = await cosmos_service.get_log_by_id(log_id)
        
        if not log:
            return func.HttpResponse(
                json.dumps({"error": "Log not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Return the log
        return func.HttpResponse(
            log.json(),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error getting log: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="delete_log/{log_id}", auth_level=func.AuthLevel.FUNCTION, methods=["DELETE"])
async def delete_log(req: func.HttpRequest) -> func.HttpResponse:
    """Delete an audit log by ID"""
    logging.info("Processing request to delete an audit log")
    
    try:
        # Extract log ID from the route parameter
        log_id = req.route_params.get("log_id")
        
        # Extract category from query parameter
        category = req.params.get("category")
        
        if not log_id or not category:
            return func.HttpResponse(
                json.dumps({"error": "Log ID and category are required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Delete the log from Cosmos DB
        success = await cosmos_service.delete_log(log_id, LogCategory(category))
        
        if not success:
            return func.HttpResponse(
                json.dumps({"error": "Log not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Return success response
        return func.HttpResponse(status_code=204)
    
    except Exception as e:
        logging.error(f"Error deleting log: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="analyze_logs", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def analyze_logs(req: func.HttpRequest) -> func.HttpResponse:
    """Analyze audit logs using Semantic Kernel"""
    logging.info("Processing request to analyze audit logs")
    
    try:
        # Parse the request body
        req_body = req.get_json()
        
        # Extract query parameters from request body
        start_time = req_body.get("start_time")
        end_time = req_body.get("end_time")
        category = req_body.get("category")
        severity = req_body.get("severity")
        source = req_body.get("source")
        user_id = req_body.get("user_id")
        action = req_body.get("action")
        correlation_id = req_body.get("correlation_id")
        tags = req_body.get("tags")
        limit = req_body.get("limit", 100)
        
        # Parse datetime strings if provided
        start_time_dt = datetime.fromisoformat(start_time) if start_time else None
        end_time_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # Create query parameters
        query_params = LogQueryParams(
            start_time=start_time_dt,
            end_time=end_time_dt,
            category=LogCategory(category) if category else None,
            severity=LogSeverity(severity) if severity else None,
            source=source,
            user_id=user_id,
            action=action,
            correlation_id=correlation_id,
            tags=tags,
            limit=limit,
            offset=0
        )
        
        # Get logs based on query parameters
        result = await cosmos_service.get_logs(query_params)
        logs = result["logs"]
        
        if not logs:
            return func.HttpResponse(
                json.dumps({"analysis": "No logs found for the specified criteria."}),
                status_code=200,
                mimetype="application/json"
            )
        
        # Analyze logs
        analysis = await semantic_kernel_service.analyze_logs(logs)
        
        # Return the analysis
        return func.HttpResponse(
            json.dumps({"analysis": analysis}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error analyzing logs: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )