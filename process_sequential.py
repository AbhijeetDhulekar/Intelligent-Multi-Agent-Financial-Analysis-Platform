# process_sequential.py
import sys
from pathlib import Path
import json

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from data_processing.document_parser import FABDocumentParser
from data_processing.vector_store import FinancialVectorStore

# NEW: Import semantic chunking with fallback
try:
    from data_processing.semantic_chunking import SemanticFinancialChunking
    SEMANTIC_CHUNKING_AVAILABLE = True
    print(" Semantic chunking available")
except ImportError:
    from data_processing.chunking_strategy import FinancialChunkingStrategy
    SEMANTIC_CHUNKING_AVAILABLE = False
    print("  Semantic chunking not available, using basic chunking")

def clear_vector_database():
    """Clear the vector database before processing to avoid duplicates"""
    try:
        vector_store = FinancialVectorStore()
        # ChromaDB doesn't have a direct clear() method, so we recreate collection
        vector_store.client.delete_collection(name=vector_store.collection.name)
        print("  Cleared existing vector database")
        
        # Recreate collection
        vector_store.collection = vector_store.client.create_collection(
            name=vector_store.collection.name,
            metadata={"description": "FAB Financial Documents"}
        )
        print(" Created fresh vector database")
        return vector_store
    except Exception as e:
        print(f"  Could not clear database: {e}")
        return FinancialVectorStore()

def process_folder(folder_name, data_dir="./data_raw", vector_store=None):
    """Process one folder at a time - ENHANCED WITH SEMANTIC CHUNKING"""
    if vector_store is None:
        vector_store = FinancialVectorStore()
    
    print("=" * 50)
    print(f" PROCESSING: {folder_name}") 
    print("=" * 50)
    
    parser = FABDocumentParser()
    
    # ENHANCED: Use semantic chunking if available
    if SEMANTIC_CHUNKING_AVAILABLE:
        chunker = SemanticFinancialChunking()
        print("    Using semantic chunking strategy")
    else:
        from data_processing.chunking_strategy import FinancialChunkingStrategy
        chunker = FinancialChunkingStrategy()
        print("    Using basic chunking strategy")
    
    category_path = Path(data_dir) / folder_name
    if not category_path.exists():
        print(f" Folder not found: {folder_name}")
        return []
    
    # ENHANCED: Handle both quarterly and annual PDFs
    if folder_name == "Annual_Reports":
        pdf_files = list(category_path.glob("FAB_*_Annual_Report.pdf"))
        print(f" Found {len(pdf_files)} annual reports")
    else:
        pdf_files = list(category_path.glob("FAB_*.pdf"))
        print(f" Found {len(pdf_files)} PDF files")
    
    all_chunks = []
    successful_files = 0
    
    for pdf_file in pdf_files:
        print(f" Processing {pdf_file.name}...")
        try:
            chunks = parser.parse_financial_statement(str(pdf_file))
            if chunks:
                # ENHANCED: Apply semantic chunking
                final_chunks = chunker.create_semantic_chunks(chunks)
                all_chunks.extend(final_chunks)
                successful_files += 1
                print(f"    {len(final_chunks)} semantic chunks created")
            else:
                print(f"     No chunks generated")
        except Exception as e:
            print(f"    Error: {e}")
    
    # Create intelligent chunks for this folder
    if all_chunks:
        print(f" Created {len(all_chunks)} total chunks for {folder_name}")
        
        # Add to vector store
        print(f"Adding {folder_name} chunks to vector database...")
        try:
            vector_store.add_documents(all_chunks)
            print(f" Successfully added {folder_name} to vector database")
            return all_chunks
        except Exception as e:
            print(f" Error adding {folder_name}: {e}")
            # Try adding chunks individually
            successful_adds = 0
            for chunk in all_chunks:
                try:
                    vector_store.add_documents([chunk])
                    successful_adds += 1
                except:
                    continue
            print(f"     Partially added {successful_adds}/{len(all_chunks)} chunks")
            return all_chunks[:successful_adds]  # Return only successful chunks
    
    return []

def main():
    # ENHANCED: Add Annual_Reports to the processing list
    folders = ["Financial_Statements", "Earnings_Presentations", "Results_Calls", "Annual_Reports"]
    all_final_chunks = []
    total_files_processed = 0
    
    print(" Starting Sequential Folder Processing with Semantic Chunking")
    print(" Folders to process:", ", ".join(folders))
    print(" Semantic chunking:", "Enabled" if SEMANTIC_CHUNKING_AVAILABLE else "Disabled")
    print("This will process one folder at a time to prevent memory issues.")
    print("You can stop after any folder by pressing 'n' when prompted.")
    
    # Ask if user wants to clear the database first
    print("\n  Database Options:")
    print("1. Clear existing database and start fresh")
    print("2. Keep existing database and add new documents")
    db_choice = input("Choose option (1 or 2): ").strip()
    
    if db_choice == "1":
        vector_store = clear_vector_database()
        print(" Starting with fresh database...")
    else:
        vector_store = FinancialVectorStore()
        print(" Adding to existing database...")
    
    for i, folder in enumerate(folders):
        chunks = process_folder(folder, vector_store=vector_store)
        all_final_chunks.extend(chunks)
        total_files_processed += len(chunks)
        
        # Ask to continue or stop (except after last folder)
        if i < len(folders) - 1:
            print(f"\n⏸  Finished {folder}. {len(folders) - i - 1} folder(s) remaining.")
            response = input("Continue to next folder? (y/n): ").strip().lower()
            if response != 'y':
                print(" Stopping as requested.")
                break
        else:
            print(f"\n Processed all {len(folders)} folders!")
    
    # Save processing summary
    summary = {
        "folders_processed": folders[:len(all_final_chunks)],
        "total_chunks_created": len(all_final_chunks),
        "processing_mode": "sequential_with_semantic_chunking",
        "semantic_chunking_used": SEMANTIC_CHUNKING_AVAILABLE,
        "database_cleared": db_choice == "1",
        "chunk_types_created": {
            "financial_tables": len([c for c in all_final_chunks if c.get("metadata", {}).get("chunk_type") == "financial_table"]),
            "text_sections": len([c for c in all_final_chunks if c.get("metadata", {}).get("chunk_type") == "text_section"]),
            "financial_metrics": len([c for c in all_final_chunks if c.get("metadata", {}).get("chunk_type") == "financial_metric"])
        }
    }
    
    with open("sequential_processing_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n Processing complete!")
    print(f" Total chunks created: {len(all_final_chunks)}")
    print(f" Semantic chunking: {'Enabled' if SEMANTIC_CHUNKING_AVAILABLE else 'Disabled'}")
    print(f"  Chunk types:")
    print(f"   - Financial tables: {summary['chunk_types_created']['financial_tables']}")
    print(f"   - Text sections: {summary['chunk_types_created']['text_sections']}")
    print(f"   - Financial metrics: {summary['chunk_types_created']['financial_metrics']}")
    print(f" Summary saved to: sequential_processing_summary.json")
    print(f" Vector database updated with all processed chunks")
    
    # Test the database
    print(f"\n Testing database...")
    try:
        test_results = vector_store.search("net profit", n_results=3)
        print(f" Database test successful: Found {len(test_results)} results for 'net profit'")
        
        # Test annual reports if processed
        if "Annual_Reports" in folders[:len(all_final_chunks)]:
            annual_results = vector_store.search("annual report", n_results=2)
            print(f" Annual reports indexed: Found {len(annual_results)} annual report chunks")
            
    except Exception as e:
        print(f"  Database test failed: {e}")

if __name__ == "__main__":
    main()