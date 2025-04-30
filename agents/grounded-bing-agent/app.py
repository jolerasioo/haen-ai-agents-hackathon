from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import BingGroundedAgent

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
try:
    agent = BingGroundedAgent()
except Exception as e:
    print(f"Error initializing agent: {e}")
    agent = None

# Create a model for the query request
class QueryRequest(BaseModel):
    query: str

# Create a model for the query response
class QueryResponse(BaseModel):
    response: str

# Endpoint to check if the agent is properly initialized
@app.get("/health")
async def health_check():
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    return {"status": "healthy"}

# Endpoint to process a query
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Create a new thread for this conversation
        thread = agent.create_thread()
        
        # Process the query
        response = agent.process_query(thread.id, request.query)
        
        return QueryResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)