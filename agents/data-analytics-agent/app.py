import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from passlib.context import CryptContext

from agent_service import DataAnalyticsAgent

# Initialize FastAPI app
app = FastAPI(title="Data Analytics Agent", description="API for SQL querying and data analysis")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
data_analytics_agent = DataAnalyticsAgent()

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_change_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# For demo purposes, we'll use an in-memory user database
# In a real app, this would come from a database
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("adminpassword"),
        "disabled": False,
    }
}

# API Models
class SqlQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute against Cosmos DB")
    analysis_type: Optional[str] = Field("summary", 
                                        description="Type of analysis to perform (summary, trend, distribution, correlation)")

class SchemaResponse(BaseModel):
    schema: Dict[str, Any] = Field(..., description="Database schema")

class QueryResponse(BaseModel):
    query: str = Field(..., description="Original SQL query")
    results: Dict[str, Any] = Field(..., description="Query results")
    summary: str = Field(..., description="Human-readable summary of the results")

# Security functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# API Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/schema", response_model=SchemaResponse)
async def get_database_schema(current_user: User = Depends(get_current_active_user)):
    """
    Get the schema of the Cosmos DB database.
    """
    schema = data_analytics_agent.get_database_schema()
    return {"schema": schema}

@app.post("/query", response_model=QueryResponse)
async def execute_sql_query(
    query_request: SqlQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a SQL query against the Cosmos DB database.
    """
    if not query_request.query:
        raise HTTPException(status_code=400, detail="SQL query is required")
    
    # Check if it's a simple query or an analytical query
    if query_request.analysis_type and query_request.analysis_type != "summary":
        results = data_analytics_agent.execute_analytical_query(
            query_request.query, query_request.analysis_type
        )
    else:
        results = data_analytics_agent.execute_sql_query(query_request.query)
    
    # Generate a human-readable summary
    summary = data_analytics_agent.analyze_results(results)
    
    return {
        "query": query_request.query,
        "results": results,
        "summary": summary
    }

@app.get("/schema/summary")
async def get_schema_summary(current_user: User = Depends(get_current_active_user)):
    """
    Get a human-readable summary of the database schema.
    """
    schema = data_analytics_agent.get_database_schema()
    summary = data_analytics_agent.summarize_schema(schema)
    
    return {"summary": summary}

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)