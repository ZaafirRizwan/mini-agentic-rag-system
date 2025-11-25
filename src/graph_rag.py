import os
import pickle
import networkx as nx
from typing import List
from google import genai
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Custom Embeddings Wrapper for google-genai
class GoogleGenAIEmbeddingsWrapper(Embeddings):
    def __init__(self, model: str = "gemini-embedding-001"):
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Batch embedding not directly shown in snippet, doing loop for safety or batch if supported
        # The snippet shows single content. We'll assume list support or loop.
        # client.models.embed_content supports 'contents' as list? Let's check docs or assume loop for now.
        embeddings = []
        for text in texts:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text
            )
            embeddings.append(result.embeddings[0].values) # Assuming result.embeddings is list of Embedding objects
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=text
        )
        return result.embeddings[0].values

class KnowledgeGraphRetriever:
    def __init__(self, storage_dir: str = "graph"):
        self.storage_dir = storage_dir
        self.graph_path = os.path.join(storage_dir, "knowledge_graph.gpickle")
        self.vector_store_path = os.path.join(storage_dir, "vector_store")
        
        self.graph = nx.Graph()
        self.vector_store = None
        self.embeddings = GoogleGenAIEmbeddingsWrapper(model="gemini-embedding-001")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        # Load if exists
        self.load()

    def ingest(self, directory_path: str):
        print("⚙️  Ingesting and building Knowledge Graph...")
        docs = []
        
        # 1. Read and Chunk
        if not os.path.exists(directory_path):
            print(f"⚠️ Directory {directory_path} not found.")
            return

        for filename in os.listdir(directory_path):
            if filename.endswith(".md") or filename.endswith(".txt"):
                path = os.path.join(directory_path, filename)
                with open(path, "r") as f:
                    content = f.read()
                    file_chunks = self.text_splitter.create_documents(
                        [content], 
                        metadatas=[{"source": filename}]
                    )
                    for i, chunk in enumerate(file_chunks):
                        chunk_id = f"{filename}_{i}"
                        chunk.metadata["id"] = chunk_id
                        docs.append(chunk)

        if not docs:
            print("No documents found.")
            return

        # 2. Build Vector Store
        print(f"📊 Embedding {len(docs)} chunks...")
        self.vector_store = FAISS.from_documents(docs, self.embeddings)
        self.vector_store.save_local(self.vector_store_path)

        # 3. Build Graph Structure (NetworkX)
        self.graph = nx.Graph() # Reset graph
        for doc in docs:
            node_id = doc.metadata["id"]
            self.graph.add_node(node_id, content=doc.page_content, source=doc.metadata["source"])

        # Create Edges
        for i in range(len(docs) - 1):
            curr = docs[i]
            next_doc = docs[i+1]
            if curr.metadata["source"] == next_doc.metadata["source"]:
                self.graph.add_edge(curr.metadata["id"], next_doc.metadata["id"], relation="next_chunk")
            
            # Simple keyword linking
            keywords = ["LangChain", "Gemini", "Dependency", "Payment", "Auth"]
            for kw in keywords:
                if kw in curr.page_content and kw in next_doc.page_content:
                    self.graph.add_edge(curr.metadata["id"], next_doc.metadata["id"], relation="shared_concept")

        # Save Graph
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        
        with open(self.graph_path, "wb") as f:
            pickle.dump(self.graph, f)

        print(f"✅ Graph Built: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges.")
        print(f"💾 Saved to {self.storage_dir}")

    def load(self):
        if os.path.exists(self.graph_path):
            with open(self.graph_path, "rb") as f:
                self.graph = pickle.load(f)
        
        if os.path.exists(self.vector_store_path):
            try:
                self.vector_store = FAISS.load_local(self.vector_store_path, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"⚠️ Could not load vector store: {e}")

    def retrieve(self, query: str, hops: int = 1) -> str:
        if not self.vector_store:
            return "Knowledge base is empty."

        # Step 1: Vector Search
        results = self.vector_store.similarity_search(query, k=2)
        if not results:
            return "No relevant context found."

        # Step 2: Graph Traversal
        final_context = []
        visited_nodes = set()

        for res in results:
            entry_id = res.metadata["id"]
            if entry_id in visited_nodes: continue
            
            if entry_id in self.graph.nodes:
                node_data = self.graph.nodes[entry_id]
                final_context.append(f"Source: {node_data['source']}\nContent: {node_data['content']}")
                visited_nodes.add(entry_id)
            
            try:
                neighbors = list(nx.bfs_tree(self.graph, source=entry_id, depth_limit=hops))
                for n_id in neighbors:
                    if n_id != entry_id and n_id not in visited_nodes:
                        node_data = self.graph.nodes[n_id]
                        final_context.append(f"--- Linked Context (Source: {node_data['source']}) ---\n{node_data['content']}")
                        visited_nodes.add(n_id)
            except Exception:
                pass

        return "\n\n".join(final_context)