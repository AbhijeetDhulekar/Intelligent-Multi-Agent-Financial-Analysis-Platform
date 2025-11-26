# api/progressive_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

app = FastAPI(
    title="FAB Financial Analyzer - Progressive API",
    description="API that gradually adds functionality",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str
    include_calculations: bool = True
    include_sources: bool = True

class QueryResponse(BaseModel):
    answer: str
    data_points: List[Dict[str, Any]] = []
    calculations: List[Dict[str, Any]] = []
    sources: List[Dict[str, str]] = []
    confidence: float = 0.0
    processing_time: float = 0.0
    status: str = "success"

# Initialize components progressively
print(" Initializing FAB Financial Analyzer...")

# Step 1: Basic components (these work)
from config.settings import settings
from data_processing.vector_store import FinancialVectorStore
from agents.financial_extractor import FinancialDataExtractor

vector_store = FinancialVectorStore()
data_extractor = FinancialDataExtractor()

print(" Basic components initialized")

# Step 2: Try to initialize orchestrator (this might fail)
orchestrator = None
try:
    from agents.orchestrator import OrchestratorAgent
    orchestrator = OrchestratorAgent()
    print(" Full orchestrator initialized")
except Exception as e:
    print(f"  Full orchestrator failed: {e}")
    print(" Using fallback analysis mode")

@app.post("/analyze", response_model=QueryResponse)
async def analyze_financial_query(request: QueryRequest):
    """Progressive analysis endpoint"""
    import time
    start_time = time.time()
    
    try:
        if orchestrator:
            # Use full orchestrator if available
            result = orchestrator.process_query(request.query)
            processing_time = time.time() - start_time
            
            return QueryResponse(
                answer=result.get("answer", "No answer generated"),
                data_points=[dp.dict() for dp in result.get("data_points", [])],
                calculations=result.get("calculations", []),
                sources=result.get("sources", []),
                confidence=result.get("confidence", 0.0),
                processing_time=processing_time
            )
        else:
            # Fallback: Use data extractor only
            print(f" Fallback mode: Extracting data for: {request.query}")
            
            from models.schemas import QueryType
            data_points = data_extractor.extract_data(request.query, QueryType.SINGLE_FACT)
            
            # Simple answer generation
            if data_points:
                answer = f"Found {len(data_points)} data points for your query: '{request.query}'\n\n"
                for dp in data_points[:5]:  # Show first 5 data points
                    answer += f"- {dp.metric.value}: {dp.value:,.0f} million AED ({dp.period})\n"
                
                if len(data_points) > 5:
                    answer += f"\n... and {len(data_points) - 5} more data points"
            else:
                answer = f"No specific financial data found for: '{request.query}'. Try asking about net profit, total assets, loans, deposits, or shareholder equity."
            
            processing_time = time.time() - start_time
            
            return QueryResponse(
                answer=answer,
                data_points=[dp.dict() for dp in data_points],
                calculations=[],
                sources=[],
                confidence=0.7 if data_points else 0.3,
                processing_time=processing_time
            )
    
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = "healthy_full" if orchestrator else "healthy_fallback"
    return {
        "status": status, 
        "service": "FAB Financial Analyzer",
        "documents_in_db": vector_store.collection.count(),
        "mode": "full" if orchestrator else "fallback"
    }

@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities"""
    base_capabilities = [
        "Financial data extraction",
        "Vector-based document retrieval", 
        "Multi-document search",
        "Basic financial analysis"
    ]
    
    if orchestrator:
        base_capabilities.extend([
            "Multi-agent reasoning",
            "Advanced calculations", 
            "Temporal analysis",
            "Risk analysis",
            "Comprehensive synthesis"
        ])
    
    return {
        "capabilities": base_capabilities,
        "supported_documents": [
            "Quarterly Financial Statements",
            "Earnings Presentations", 
            "Results Call Transcripts",
            "Annual Reports"
        ],
        "mode": "full" if orchestrator else "fallback",
        "documents_loaded": vector_store.collection.count()
    }

@app.get("/test-query")
async def test_query():
    """Test endpoint with a sample query"""
    test_queries = [
        "What was FAB's net profit in Q1 2022?",
        "How much were total assets in 2022?",
        "What were total deposits in Q3 2022?",
        "Show me shareholder equity for 2023"
    ]
    
    results = []
    for query in test_queries:
        try:
            response = await analyze_financial_query(QueryRequest(query=query))
            results.append({
                "query": query,
                "status": "success", 
                "data_points": len(response.data_points),
                "answer_preview": response.answer[:100] + "..."
            })
        except Exception as e:
            results.append({
                "query": query, 
                "status": "failed",
                "error": str(e)
            })
    
    return {"test_results": results}

def start_server():
    """Start the progressive server"""
    print(" Starting Progressive FAB Financial Analyzer API...")
    print(" Server: http://localhost:8000")
    print(" Docs: http://localhost:8000/docs")
    print(" Mode:", "FULL" if orchestrator else "FALLBACK")
    print(" Documents in DB:", vector_store.collection.count())
    print(" Press Ctrl+C to stop")
    
    uvicorn.run(
        "api.progressive_api:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()