
# How to run the piplene 
# Terminal 1:
# change the directory to the env variable
fab_env/scripts/activate

# set up library
cp .env.example .env

#  Run system
python main.py --mode api


# Terminal 2:
# change the directory to the env variable
fab_env/scripts/activate

# set up library
cp .env.example .env

#  Run system
python main.py --mode ui


# Project Summary 
Project Spotlight: FAB Financial Analyzer Designed and built an intelligent financial analysis platform that transforms static PDF statements into interactive insights. I tackled the challenge of parsing complex financial tables by creating a custom multi-library processing pipeline and a semantic chunking strategy that respects accounting boundaries. The system features a LangGraph-orchestrated multi-agent workflow—separating concerns between calculation, temporal analysis, and risk extraction—powered by GPT-4o and ChromaDB. The result is a high-accuracy tool that answers multi-hop financial questions in seconds.

Engineered a Multi-Agent GenAI System: Built "FAB Financial Analyzer" using LangGraph and GPT-4o, orchestrating specialized agents to handle complex financial queries (e.g., ratio calculations, YoY comparisons, risk assessment) with banking-grade accuracy.

Advanced RAG Pipeline: Developed a hybrid parsing strategy (combining PyMuPDF, pdfplumber, and PyPDF2) and a custom semantic chunking algorithm to preserve the integrity of complex financial tables and accounting sections.

Vector Search & Storage: Implemented ChromaDB with Sentence Transformers to index 7,000+ document chunks, utilizing rich metadata filtering for precise retrieval across multi-year financial statements.

Full-Stack Implementation: Delivered a production-ready interactive platform using FastAPI (backend) and Streamlit (frontend), featuring automated confidence scoring and domain-specific validation loops.

