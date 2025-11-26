# tools/document_retriever.py
from typing import List, Dict, Any, Optional
from data_processing.vector_store import FinancialVectorStore
from models.schemas import DocumentType

class DocumentRetriever:
    def __init__(self):
        self.vector_store = FinancialVectorStore()
    
    def retrieve_relevant_documents(self, query: str, filters: Optional[Dict] = None, 
                                  n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents based on query and filters"""
        return self.vector_store.search(query, filters, n_results)
    
    def retrieve_by_metadata(self, year: Optional[int] = None, 
                           quarter: Optional[str] = None,
                           document_type: Optional[DocumentType] = None,
                           section_type: Optional[str] = None,
                           n_results: int = 10) -> List[Dict[str, Any]]:
        """Retrieve documents by specific metadata filters"""
        filters = {}
        
        if year:
            filters["year"] = year
        if quarter:
            filters["quarter"] = quarter
        if document_type:
            filters["document_type"] = document_type.value
        if section_type:
            filters["section_type"] = section_type
        
        # Use a generic query that matches the filters
        query_text = self._build_query_from_filters(filters)
        
        return self.vector_store.search(query_text, filters, n_results)
    
    def _build_query_from_filters(self, filters: Dict) -> str:
        """Build a query string from metadata filters"""
        query_parts = []
        
        if "year" in filters:
            query_parts.append(f"{filters['year']}")
        if "quarter" in filters:
            query_parts.append(f"{filters['quarter']} quarter")
        if "document_type" in filters:
            query_parts.append(f"{filters['document_type']} report")
        if "section_type" in filters:
            query_parts.append(f"{filters['section_type']} section")
        
        return " ".join(query_parts) if query_parts else "financial performance"
    
    def retrieve_for_temporal_analysis(self, periods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retrieve documents for temporal analysis across multiple periods"""
        all_documents = []
        
        for period in periods:
            docs = self.retrieve_by_metadata(
                year=period.get("year"),
                quarter=period.get("quarter"),
                n_results=3
            )
            all_documents.extend(docs)
        
        return all_documents
    
    def retrieve_risk_documents(self, n_results: int = 8) -> List[Dict[str, Any]]:
        """Retrieve documents likely containing risk information"""
        risk_queries = [
            "risk management credit risk market risk operational risk",
            "risk factors challenges concerns",
            "risk assessment mitigation control"
        ]
        
        all_risk_docs = []
        for query in risk_queries:
            docs = self.retrieve_relevant_documents(
                query, 
                filters={"section_type": "risk_management"},
                n_results=3
            )
            all_risk_docs.extend(docs)
        
        # Remove duplicates by chunk_id
        seen_ids = set()
        unique_docs = []
        for doc in all_risk_docs:
            chunk_id = doc["metadata"].get("chunk_id")
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_docs.append(doc)
        
        return unique_docs[:n_results]