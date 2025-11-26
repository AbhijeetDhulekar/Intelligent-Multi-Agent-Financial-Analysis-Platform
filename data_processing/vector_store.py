import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
from sentence_transformers import SentenceTransformer
from config.settings import settings

class FinancialVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
       
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"description": "FAB Financial Documents"}
        )

    

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata to ensure ChromaDB compatibility"""
        cleaned = {}
        
        for key, value in metadata.items():
            if value is None:
                cleaned[key] = ""
            elif isinstance(value, list):
                
                if value:
                    cleaned[key] = ", ".join(str(v) for v in value)
                else:
                    cleaned[key] = ""  # Empty list becomes empty string
            elif isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            else:
                # Convert any other type to string
                cleaned[key] = str(value)
        
        return cleaned
        
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add document chunks to vector store"""
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            doc_id = str(uuid.uuid4())
            documents.append(chunk["content"])
            
            # CLEAN THE METADATA BEFORE ADDING
            cleaned_metadata = self._clean_metadata(chunk["metadata"])
            metadatas.append(cleaned_metadata)
            
            ids.append(doc_id)
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, filters: Optional[Dict] = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents with filtering - FIXED VERSION"""
        
        
        where_clause = None
        if filters and any(filters.values()):
            # Clean filters - remove None/empty values
            clean_filters = {k: v for k, v in filters.items() if v is not None and v != ""}
            if clean_filters:
                where_clause = clean_filters
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,  # Use None for no filters
                include=["metadatas", "documents", "distances"]
            )
            
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "score": 1 - results["distances"][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f" Vector search error with filters: {e}")
            # Fallback: search without any filters
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=None,  # Explicitly None
                    include=["metadatas", "documents", "distances"]
                )
                
                formatted_results = []
                if results["documents"] and results["documents"][0]:
                    for i in range(len(results["documents"][0])):
                        formatted_results.append({
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i],
                            "score": 1 - results["distances"][0][i]
                        })
                
                return formatted_results
            except Exception as e2:
                print(f" Fallback search also failed: {e2}")
                return []
    
    def _build_filter_condition(self, filters: Dict) -> Dict:
        """Build ChromaDB filter condition - SIMPLIFIED VERSION"""
        if not filters:
            return None  # Return None instead of empty dict
        
        # For simple key-value filters, ChromaDB expects direct mapping
        # Try simple format first
        simple_filters = {}
        for key, value in filters.items():
            if value is not None:
                simple_filters[key] = value
        
        if simple_filters:
            return simple_filters
        
        return None
    
    def get_similar_periods(self, year: int, quarter: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Get documents from similar time periods for trend analysis"""
        # This is a simplified approach - in production, you might want more sophisticated temporal reasoning
        return self.search(
            query=f"financial performance {year} {quarter}",
            n_results=n_results
        )