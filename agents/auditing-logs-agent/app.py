import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import AuditLog, LogQueryParams, LogCategory, LogSeverity, LogResponse
from cosmos_service import CosmosDBService
from search_service import SearchService
from monitor_service import MonitorService, SentinelService
from semantic_kernel_service import SemanticKernelService

app = FastAPI(title="Auditing Logs Agent", description="API for managing and querying audit logs")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances
cosmos_service = CosmosDBService()
search_service = SearchService()
monitor_service = MonitorService()
sentinel_service = SentinelService()
semantic_kernel_service = SemanticKernelService()


# Models for API requests and responses
class CreateLogRequest(BaseModel):
    category: LogCategory
    source: str
    action: str
    description: Optional[str] = None
    severity: Optional[LogSeverity] = None
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    tags: Optional[List[str]] = None


class LogAnalysisResponse(BaseModel):
    analysis: str


class SentinelIncidentsResponse(BaseModel):
    incidents: List[Dict[str, Any]]


# Dependency to get query parameters
async def get_query_params(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    category: Optional[LogCategory] = None,
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    search_text: Optional[str] = None,
    correlation_id: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
) -> LogQueryParams:
    return LogQueryParams(
        start_time=start_time,
        end_time=end_time,
        category=category,
        severity=severity,
        source=source,
        user_id=user_id,
        action=action,
        search_text=search_text,
        correlation_id=correlation_id,
        tags=tags,
        limit=limit,
        offset=offset,
    )


# Routes
@app.post("/logs", response_model=AuditLog, status_code=201)
async def create_log(request: CreateLogRequest):
    """Create a new audit log entry"""
    # If description is not provided, generate it
    if not request.description:
        description = await semantic_kernel_service.generate_log_description(
            action=request.action,
            source=request.source,
            category=request.category.value,
            user_id=request.user_id,
            details=request.details
        )
    else:
        description = request.description
    
    # If severity is not provided, classify it
    if not request.severity:
        severity = await semantic_kernel_service.classify_log_severity(
            action=request.action,
            source=request.source,
            description=description,
            details=request.details
        )
    else:
        severity = request.severity
    
    # Create the audit log
    log = AuditLog(
        category=request.category,
        source=request.source,
        action=request.action,
        description=description,
        severity=severity,
        user_id=request.user_id,
        details=request.details,
        correlation_id=request.correlation_id,
        tags=request.tags
    )
    
    # Save to Cosmos DB
    created_log = await cosmos_service.create_log(log)
    
    # Index in Azure AI Search
    await search_service.index_logs([created_log])
    
    # Send to Azure Monitor
    await monitor_service.send_log_to_monitor(created_log)
    
    return created_log


@app.get("/logs", response_model=LogResponse)
async def get_logs(query_params: LogQueryParams = Depends(get_query_params)):
    """Get audit logs based on query parameters"""
    # If search_text is provided, use Azure AI Search
    if query_params.search_text:
        result = await search_service.search_logs(query_params)
    else:
        # Use Cosmos DB for regular queries
        result = await cosmos_service.get_logs(query_params)
    
    return LogResponse(
        logs=result["logs"],
        total_count=result["total_count"],
        next_offset=result["next_offset"]
    )


@app.get("/logs/{log_id}", response_model=AuditLog)
async def get_log(log_id: str = Path(..., description="The ID of the audit log")):
    """Get a specific audit log by ID"""
    log = await cosmos_service.get_log_by_id(log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return log


@app.delete("/logs/{log_id}", status_code=204)
async def delete_log(
    log_id: str = Path(..., description="The ID of the audit log"),
    category: LogCategory = Query(..., description="The category of the audit log")
):
    """Delete an audit log by ID"""
    success = await cosmos_service.delete_log(log_id, category)
    
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {}


@app.post("/logs/analyze", response_model=LogAnalysisResponse)
async def analyze_logs(query_params: LogQueryParams = Depends(get_query_params)):
    """Analyze audit logs using Semantic Kernel"""
    # Get logs based on query parameters
    result = await cosmos_service.get_logs(query_params)
    logs = result["logs"]
    
    if not logs:
        return LogAnalysisResponse(analysis="No logs found for the specified criteria.")
    
    # Analyze logs
    analysis = await semantic_kernel_service.analyze_logs(logs)
    
    return LogAnalysisResponse(analysis=analysis)


@app.get("/security/incidents", response_model=SentinelIncidentsResponse)
async def get_security_incidents(timespan: str = Query("P7D", description="Time span for incidents (e.g., P1D, P7D)")):
    """Get security incidents from Azure Sentinel"""
    incidents = await sentinel_service.get_security_incidents(timespan)
    
    return SentinelIncidentsResponse(incidents=incidents)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)