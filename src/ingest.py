import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph_rag import KnowledgeGraphRetriever

def main():
    load_dotenv()
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    graph_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "graph")
    
    print(f"📂 Data Directory: {data_dir}")
    print(f"📂 Graph Output Directory: {graph_dir}")
    
    kg = KnowledgeGraphRetriever(storage_dir=graph_dir)
    kg.ingest(data_dir)

if __name__ == "__main__":
    main()
