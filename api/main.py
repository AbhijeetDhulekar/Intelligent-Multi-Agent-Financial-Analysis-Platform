# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from models.schemas import AgentResponse
from config.settings import settings

app = FastAPI(
    title="FAB Financial Analysis Multi-Agent System",
    description="Intelligent multi-agent system for analyzing FAB's financial statements",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str
    include_calculations: bool = True
    include_sources: bool = True

class QueryResponse(BaseModel):
    answer: str
    data_points: List[Dict[str, Any]]
    calculations: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    confidence: float
    processing_time: float

# Don't initialize orchestrator here - do it lazily in endpoints
_orchestrator = None

def get_orchestrator():
    """Lazy initialization of orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        try:
            from agents.orchestrator import OrchestratorAgent
            _orchestrator = OrchestratorAgent()
            print(" Orchestrator initialized successfully")
        except Exception as e:
            print(f" Orchestrator initialization failed: {e}")
            raise
    return _orchestrator

@app.post("/analyze", response_model=QueryResponse)
async def analyze_financial_query(request: QueryRequest):
    """Main endpoint for financial analysis queries"""
    try:
        import time
        start_time = time.time()
        
        # Initialize orchestrator only when needed
        orchestrator = get_orchestrator()
        result = orchestrator.process_query(request.query)
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            answer=result["answer"],
            data_points=[dp.dict() for dp in result["data_points"]],
            calculations=result["calculations"],
            sources=result["sources"],
            confidence=result["confidence"],
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test if orchestrator can be initialized
        orchestrator = get_orchestrator()
        return {
            "status": "healthy", 
            "service": "FAB Financial Analyzer",
            "orchestrator": "initialized"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "FAB Financial Analyzer", 
            "orchestrator": "failed",
            "error": str(e)
        }

@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities"""
    try:
        # Test orchestrator initialization
        orchestrator = get_orchestrator()
        capabilities = {
            "capabilities": [
                "Multi-hop financial reasoning",
                "Temporal analysis and comparisons",
                "Financial ratio calculations", 
                "Trend analysis",
                "Risk factor identification",
                "Management commentary synthesis"
            ],
            "supported_documents": [
                "Quarterly Financial Statements",
                "Earnings Presentations",
                "Results Call Transcripts", 
                "Annual Reports"
            ],
            "status": "full_capabilities",
            "documents_loaded": orchestrator.vector_store.collection.count() if hasattr(orchestrator, 'vector_store') else 0
        }
    except Exception as e:
        capabilities = {
            "capabilities": [
                "Basic document retrieval",
                "Financial data extraction"
            ],
            "supported_documents": [
                "Quarterly Financial Statements", 
                "Earnings Presentations",
                "Results Call Transcripts",
                "Annual Reports"
            ],
            "status": "limited_capabilities",
            "error": str(e)
        }
    
    # Add example queries regardless of orchestrator status
    capabilities["example_queries"] = [
        "What was the year-over-year percentage change in Net Profit between Q3 2022 and Q3 2023?",
        "How has FAB's Return on Equity trended over the last 6 quarters?",
        "Compare FAB's loan-to-deposit ratio between Q4 2022 and Q4 2023.",
        "What were the top 3 risk factors mentioned in the 2023 reports?"
    ]
    
    return capabilities

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "FAB Financial Analyzer API is running", "status": "ok"}

if __name__ == "__main__":
    print(" Starting FAB Financial Analyzer API...")
    print(" Server will be available at: http://localhost:8000")
    print(" API docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )