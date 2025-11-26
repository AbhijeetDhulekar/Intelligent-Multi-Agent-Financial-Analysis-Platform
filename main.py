#!/usr/bin/env python3
"""
FAB Financial Analysis Multi-Agent System
Main entry point for the application
"""

import argparse
import sys
from pathlib import Path


class FABFinancialAnalyzer:
    def __init__(self):
        from agents.orchestrator import OrchestratorAgent
        from data_processing.vector_store import FinancialVectorStore
        self.orchestrator = OrchestratorAgent()
        self.vector_store = FinancialVectorStore()
    
    def process_query(self, query: str):
        """Main method to process financial queries"""
        print(f" Processing query: {query}")
        return self.orchestrator.process_query(query)
    
    def initialize_system(self):
        """Initialize the system - check if vector store is populated"""
        try:
            # Check if vector store has documents
            sample_results = self.vector_store.search("financial performance", n_results=1)
            if not sample_results:
                print("  Vector store is empty. Please run data pipeline first.")
                return False
            print(" System initialized successfully")
            return True
        except Exception as e:
            print(f" System initialization failed: {e}")
            return False


def interactive_mode():
    """Run the system in interactive command-line mode"""
    analyzer = FABFinancialAnalyzer()
    
    if not analyzer.initialize_system():
        print("Please run: python main.py --mode process-data first")
        return
    
    print("\n FAB Financial Analyzer - Interactive Mode")
    print("Example queries:")
    print("1. 'What was FAB's net profit in Q1 2022?'")
    print("2. 'Calculate ROE trend over last 4 quarters'") 
    print("3. 'Compare loan-to-deposit ratio Q4 2022 vs Q4 2023'")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            query = input("\n Enter your financial query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
                
            # Process the query
            result = analyzer.process_query(query)
            
            print(f"\n RESULT:")
            print(f"Answer: {result.get('answer', 'No answer generated')}")
            print(f"Confidence: {result.get('confidence', 0)}")
            print(f"Data Points: {len(result.get('data_points', []))}")
            print(f"Calculations: {len(result.get('calculations', []))}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f" Error processing query: {e}")

def main():
    parser = argparse.ArgumentParser(description="FAB Financial Analysis Multi-Agent System")
    parser.add_argument(
        "--mode", 
        choices=["api", "ui", "process-data", "test", "interactive"],  # ADDED interactive mode
        default="api",
        help="Run mode: api (FastAPI server), ui (Streamlit UI), process-data (data pipeline), test (run tests), interactive (command-line)"
    )
    parser.add_argument(
        "--data-dir", 
        default="./data_raw",
        help="Directory containing raw PDF documents"
    )
    
    args = parser.parse_args()
    
    if args.mode == "api":
        from api.main import app
        import uvicorn
        from config.settings import settings
        
        print(" Starting FAB Financial Analysis API...")
        uvicorn.run(
            "api.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=True
        )
    
    elif args.mode == "ui":
        import subprocess
        print(" Starting Streamlit UI...")
        subprocess.run(["streamlit", "run", "streamlit_app.py"])
  
  
  
    elif args.mode == "interactive":
        interactive_mode()
    
    elif args.mode == "process-data":
        from data_processing.document_parser import FABDocumentParser
        from data_processing.chunking_strategy import FinancialChunkingStrategy
        from data_processing.vector_store import FinancialVectorStore
        import json
        
        print(" Processing financial documents...")
        
        # Initialize components
        parser = FABDocumentParser()
        chunker = FinancialChunkingStrategy()
        vector_store = FinancialVectorStore()
        
        # Process all documents
        all_chunks = []
        data_dir = Path(args.data_dir)
        total_files = 0
        successful_files = 0
        
        for doc_category in ["Financial_Statements", "Earnings_Presentation", "Results_Call"]:
            category_path = data_dir / doc_category
            if category_path.exists():
                pdf_files = list(category_path.glob("FAB_*.pdf"))
                print(f" Found {len(pdf_files)} PDFs in {doc_category}")
                
                for pdf_file in pdf_files:
                    total_files += 1
                    print(f" Processing {pdf_file.name}...")
                    try:
                        chunks = parser.parse_financial_statement(str(pdf_file))
                        if chunks:
                            all_chunks.extend(chunks)
                            successful_files += 1
                            print(f"    Success: {len(chunks)} chunks")
                        else:
                            print(f"     Warning: No chunks generated")
                    except Exception as e:
                        print(f"    Error: {str(e)}")
        
        print(f"\n Processing Summary:")
        print(f"   Total files: {total_files}")
        print(f"   Successful: {successful_files}")
        print(f"   Failed: {total_files - successful_files}")
        
        if not all_chunks:
            print("  CRITICAL: No chunks were generated from any PDF files!")
            print("  Possible solutions:")
            print("   1. Run debug_pdf_processing.py to diagnose the issue")
            print("   2. Check if PDFs are scanned/image-based (not text-based)")
            print("   3. Try different PDF files")
            return
        
        # Create intelligent chunks
        print("Creating intelligent chunks...")
        final_chunks = chunker.create_section_chunks(all_chunks)
        print(f" Created {len(final_chunks)} final chunks")
        
        # Add to vector store
        print("Adding to vector database...")
        try:
            vector_store.add_documents(final_chunks)
            print(" Successfully added to vector database")
        except Exception as e:
            print(f" Error adding to vector database: {e}")
            print(" Trying to add chunks individually...")
            
            # Try adding chunks one by one
            successful_adds = 0
            for chunk in final_chunks:
                try:
                    vector_store.add_documents([chunk])
                    successful_adds += 1
                except:
                    continue
            
            print(f"   Partially added {successful_adds}/{len(final_chunks)} chunks")
        
        # Save processing summary
        summary = {
            "total_files_processed": total_files,
            "successful_files": successful_files,
            "total_chunks_created": len(final_chunks),
            "document_categories": ["Financial_Statements", "Earnings_Presentation", "Results_Call"]
        }
        
        with open("processing_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(" Processing summary saved to processing_summary.json")
    
    elif args.mode == "test":
        from evaluation.test_suite import run_test_suite
        print(" Running test suite...")
        run_test_suite()

if __name__ == "__main__":
    main()