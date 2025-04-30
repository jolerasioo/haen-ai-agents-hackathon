import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    ComplexField,
    SearchIndex,
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset,
)
from dotenv import load_dotenv

from models import AuditLog, LogQueryParams

# Load environment variables
load_dotenv()


class SearchService:
    def __init__(self):
        # Initialize Azure Search clients
        self.endpoint = os.environ["SEARCH_ENDPOINT"]
        self.key = os.environ["SEARCH_API_KEY"]
        self.index_name = os.environ["SEARCH_INDEX_NAME"]
        
        self.credential = AzureKeyCredential(self.key)
        self.index_client = SearchIndexClient(endpoint=self.endpoint, credential=self.credential)
        self.search_client = SearchClient(endpoint=self.endpoint, index_name=self.index_name, credential=self.credential)
        
        # Create search index if it doesn't exist
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Create the search index if it doesn't exist"""
        try:
            # Check if index exists
            self.index_client.get_index(name=self.index_name)
        except Exception:
            # Index doesn't exist, create it
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
                SimpleField(name="timestamp", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
                SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="severity", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="action", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="correlation_id", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
                ComplexField(name="details", fields=[
                    SearchableField(name="content", type=SearchFieldDataType.String)
                ])
            ]
            
            # Create the index
            index = SearchIndex(name=self.index_name, fields=fields)
            self.index_client.create_or_update_index(index)
    
    async def index_logs(self, logs: List[AuditLog]):
        """Index audit logs in Azure AI Search"""
        if not logs:
            return
        
        # Prepare documents for indexing
        documents = []
        for log in logs:
            # Convert the log to a dictionary
            log_dict = log.dict()
            
            # Convert datetime to string
            log_dict["timestamp"] = log_dict["timestamp"].isoformat()
            
            # Convert details dictionary to a format suitable for indexing
            if log_dict.get("details"):
                log_dict["details"] = {"content": str(log_dict["details"])}
            
            documents.append(log_dict)
        
        # Upload documents to the search index
        self.search_client.upload_documents(documents=documents)
    
    async def search_logs(self, query_params: LogQueryParams) -> Dict[str, Any]:
        """Search for audit logs using Azure AI Search"""
        # Build the search query
        search_text = query_params.search_text or "*"
        
        # Build filter conditions
        filter_conditions = []
        
        # Add timestamp range conditions if provided
        if query_params.start_time:
            filter_conditions.append(f"timestamp ge {query_params.start_time.isoformat()}")
        
        if query_params.end_time:
            filter_conditions.append(f"timestamp le {query_params.end_time.isoformat()}")
        
        # Add category filter if provided
        if query_params.category:
            filter_conditions.append(f"category eq '{query_params.category.value}'")
        
        # Add severity filter if provided
        if query_params.severity:
            filter_conditions.append(f"severity eq '{query_params.severity.value}'")
        
        # Add source filter if provided
        if query_params.source:
            filter_conditions.append(f"source eq '{query_params.source}'")
        
        # Add user_id filter if provided
        if query_params.user_id:
            filter_conditions.append(f"user_id eq '{query_params.user_id}'")
        
        # Add action filter if provided
        if query_params.action:
            filter_conditions.append(f"action eq '{query_params.action}'")
        
        # Add correlation_id filter if provided
        if query_params.correlation_id:
            filter_conditions.append(f"correlation_id eq '{query_params.correlation_id}'")
        
        # Add tags filter if provided
        if query_params.tags and len(query_params.tags) > 0:
            tag_conditions = [f"tags/any(t: t eq '{tag}')" for tag in query_params.tags]
            filter_conditions.append(f"({' or '.join(tag_conditions)})")
        
        # Join filter conditions
        filter_string = " and ".join(filter_conditions) if filter_conditions else None
        
        # Execute the search
        results = self.search_client.search(
            search_text=search_text,
            filter=filter_string,
            order_by=["timestamp desc"],
            skip=query_params.offset,
            top=query_params.limit,
            include_total_count=True
        )
        
        # Process search results
        logs = []
        for result in results:
            # Convert the search result to a dictionary
            log_dict = dict(result)
            
            # Convert timestamp from string to datetime
            log_dict["timestamp"] = datetime.fromisoformat(log_dict["timestamp"])
            
            # Convert details from search format back to dictionary
            if log_dict.get("details") and log_dict["details"].get("content"):
                try:
                    import ast
                    log_dict["details"] = ast.literal_eval(log_dict["details"]["content"])
                except:
                    log_dict["details"] = {"content": log_dict["details"]["content"]}
            
            # Create AuditLog object
            log = AuditLog(**log_dict)
            logs.append(log)
        
        # Get total count
        total_count = results.get_count()
        
        # Calculate next offset
        next_offset = None
        if len(logs) == query_params.limit and (query_params.offset + query_params.limit) < total_count:
            next_offset = query_params.offset + query_params.limit
        
        return {
            "logs": logs,
            "total_count": total_count,
            "next_offset": next_offset
        }