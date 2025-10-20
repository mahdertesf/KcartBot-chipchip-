import os
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

def chipchip_rag_tool(query: str) -> str:
    """
    Performs RAG (Retrieval Augmented Generation) on the chipchip_knowledge collection.
    Returns relevant context as a formatted string.
    """
    try:
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='localhost', port=8001)
        
        # Initialize embedding function for query retrieval
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            task_type="RETRIEVAL_QUERY",
            google_api_key=os.environ.get('GOOGLE_API_KEY')
        )
        
        # Create LangChain vector store
        vectorstore = Chroma(
            client=client,
            collection_name="chipchip_knowledge",
            embedding_function=embeddings
        )
        
        # Perform similarity search - get top 3 documents
        docs = vectorstore.similarity_search(query, k=3)
        
        # Format and return results
        if not docs:
            return "No relevant information found in the knowledge base."
        
        context_parts = ["Here are the top 3 retrieved documents. Use only those which are relevant for answering the query:\n"]
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"Document {i}:\n{doc.page_content}")
        
        return "\n\n".join(context_parts)
        
    except Exception as e:
        print(f"Error in chipchip_rag_tool: {e}")
        return f"Error retrieving information: {str(e)}"

