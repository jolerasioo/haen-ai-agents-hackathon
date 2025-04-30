import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as cosmos_exceptions
from azure.cosmos.partition_key import PartitionKey
from dotenv import load_dotenv

from models import AuditLog, LogQueryParams, LogCategory, LogSeverity

# Load environment variables
load_dotenv()


class CosmosDBService:
    def __init__(self):
        # Initialize Cosmos client
        self.client = cosmos_client.CosmosClient(
            url=os.environ["COSMOS_ENDPOINT"],
            credential=os.environ["COSMOS_KEY"]
        )
        self.database_name = os.environ["COSMOS_DATABASE"]
        self.container_name = os.environ["COSMOS_CONTAINER"]
        
        # Create database if it doesn't exist
        self.database = self.client.create_database_if_not_exists(id=self.database_name)
        
        # Create container if it doesn't exist
        self.container = self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/category"),
            indexing_policy={
                'indexingMode': 'consistent',
                'automatic': True,
                'includedPaths': [
                    {'path': '/*'},
                ],
                'excludedPaths': [
                    {'path': '/"_etag"/?'}
                ]
            }
        )

    async def create_log(self, log: AuditLog) -> AuditLog:
        """Create a new audit log entry in Cosmos DB"""
        log_dict = log.dict()
        
        # Convert datetime to string for Cosmos DB
        log_dict["timestamp"] = log_dict["timestamp"].isoformat()
        
        # Create the item in Cosmos DB
        created_item = self.container.create_item(body=log_dict)
        
        # Convert timestamp back to datetime
        created_item["timestamp"] = datetime.fromisoformat(created_item["timestamp"])
        
        return AuditLog(**created_item)

    async def get_logs(self, query_params: LogQueryParams) -> Dict[str, Any]:
        """Query audit logs based on specified parameters"""
        query_parts = ["SELECT * FROM c WHERE 1=1"]
        query_params_dict = {}
        
        # Add timestamp range conditions if provided
        if query_params.start_time:
            query_parts.append("AND c.timestamp >= @start_time")
            query_params_dict["@start_time"] = query_params.start_time.isoformat()
        
        if query_params.end_time:
            query_parts.append("AND c.timestamp <= @end_time")
            query_params_dict["@end_time"] = query_params.end_time.isoformat()
        
        # Add category filter if provided
        if query_params.category:
            query_parts.append("AND c.category = @category")
            query_params_dict["@category"] = query_params.category.value
        
        # Add severity filter if provided
        if query_params.severity:
            query_parts.append("AND c.severity = @severity")
            query_params_dict["@severity"] = query_params.severity.value
        
        # Add source filter if provided
        if query_params.source:
            query_parts.append("AND c.source = @source")
            query_params_dict["@source"] = query_params.source
        
        # Add user_id filter if provided
        if query_params.user_id:
            query_parts.append("AND c.user_id = @user_id")
            query_params_dict["@user_id"] = query_params.user_id
        
        # Add action filter if provided
        if query_params.action:
            query_parts.append("AND c.action = @action")
            query_params_dict["@action"] = query_params.action
        
        # Add correlation_id filter if provided
        if query_params.correlation_id:
            query_parts.append("AND c.correlation_id = @correlation_id")
            query_params_dict["@correlation_id"] = query_params.correlation_id
        
        # Add search text filter if provided (search in description)
        if query_params.search_text:
            query_parts.append("AND CONTAINS(c.description, @search_text)")
            query_params_dict["@search_text"] = query_params.search_text
        
        # Add tags filter if provided
        if query_params.tags and len(query_params.tags) > 0:
            tag_conditions = []
            for i, tag in enumerate(query_params.tags):
                tag_param = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {tag_param})")
                query_params_dict[tag_param] = tag
            
            query_parts.append(f"AND ({' OR '.join(tag_conditions)})")
        
        # Add ORDER BY clause
        query_parts.append("ORDER BY c.timestamp DESC")
        
        # Build the complete query
        query = " ".join(query_parts)
        
        # Execute the query to get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(1) as count")
        count_results = list(self.container.query_items(
            query=count_query,
            parameters=query_params_dict,
            enable_cross_partition_query=True
        ))
        total_count = count_results[0]["count"] if count_results else 0
        
        # Add OFFSET and LIMIT for pagination
        query += f" OFFSET {query_params.offset} LIMIT {query_params.limit}"
        
        # Execute the query
        items = list(self.container.query_items(
            query=query,
            parameters=query_params_dict,
            enable_cross_partition_query=True
        ))
        
        # Convert timestamps to datetime objects
        for item in items:
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])
        
        # Convert items to AuditLog objects
        logs = [AuditLog(**item) for item in items]
        
        # Calculate next offset
        next_offset = None
        if len(logs) == query_params.limit and (query_params.offset + query_params.limit) < total_count:
            next_offset = query_params.offset + query_params.limit
        
        return {
            "logs": logs,
            "total_count": total_count,
            "next_offset": next_offset
        }

    async def get_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Get a specific audit log by ID"""
        try:
            # We need to query by ID across partitions since we don't know the category
            query = "SELECT * FROM c WHERE c.id = @id"
            params = [{"name": "@id", "value": log_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return None
            
            item = items[0]
            
            # Convert timestamp to datetime
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])
            
            return AuditLog(**item)
        
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None
    
    async def delete_log(self, log_id: str, category: LogCategory) -> bool:
        """Delete an audit log by ID"""
        try:
            self.container.delete_item(item=log_id, partition_key=category.value)
            return True
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return False