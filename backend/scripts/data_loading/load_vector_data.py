import os
import json
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..','..', 'data')
KNOWLEDGE_FILE = os.path.join(DATA_DIR, 'chipchip_knowledge.json')
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
COLLECTION_NAME = "chipchip_knowledge"

try:
    doc_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        task_type="RETRIEVAL_DOCUMENT"
    )
except ImportError:
    print("Please install langchain-google-genai: pip install langchain-google-genai")
    exit()

def load_vector_database():
    print("[INFO] Starting Vector Database Loading Process (using Google Embeddings)")
    
    try:
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] The file '{KNOWLEDGE_FILE}' was not found.")
        return

    print(f"[INFO] Loaded {len(knowledge_data)} documents from the knowledge base.")

    try:
        chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        chroma_client.heartbeat()
        
        if COLLECTION_NAME in [c.name for c in chroma_client.list_collections()]:
            print(f"[INFO] Collection '{COLLECTION_NAME}' already exists. Deleting it for a fresh load.")
            chroma_client.delete_collection(name=COLLECTION_NAME)

        collection = chroma_client.create_collection(name=COLLECTION_NAME)
        print(f"[SUCCESS] Successfully connected to ChromaDB and created collection '{COLLECTION_NAME}'.")

    except Exception as e:
        print(f"[ERROR] Error connecting to ChromaDB: {e}")
        print(f"[INFO] Please ensure the ChromaDB Docker container is running and accessible at {CHROMA_HOST}:{CHROMA_PORT}.")
        return

    documents = [item['content'] for item in knowledge_data]
    metadatas = [{"document_type": item['document_type'], "topic": item['topic']} for item in knowledge_data]
    ids = [f"doc_{i+1}" for i in range(len(knowledge_data))]

    print("[INFO] Generating embeddings via Google AI and loading into ChromaDB... (This may take a moment)")
    
    try:
        from langchain.vectorstores import Chroma

        Chroma.from_texts(
            texts=documents,
            embedding=doc_embeddings,
            metadatas=metadatas,
            ids=ids,
            collection_name=COLLECTION_NAME,
            client=chroma_client
        )

        print("-" * 30)
        print(f"[SUCCESS] Successfully generated embeddings and loaded {len(documents)} documents into ChromaDB.")
        print("-" * 30)

    except Exception as e:
        print(f"[ERROR] An error occurred during embedding and loading: {e}")
        print("[INFO] Please check your GOOGLE_API_KEY and network connection.")

if __name__ == "__main__":
    load_vector_database()