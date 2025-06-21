import os
import openai
import json
from pinecone import Pinecone

# Initialize clients from environment variables
try:
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pinecone_index = pc.Index("api-rag")
except Exception as e:
    pc = None
    openai_client = None
    pinecone_index = None
    print(f"Warning: RAG system not initialized. Error: {e}")

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generates an embedding for the given text using OpenAI's API."""
    if not openai_client:
        raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
    text = text.replace("\n", " ")
    return openai_client.embeddings.create(input=[text], model=model).data[0].embedding

def retrieve(query: str, k: int = 2) -> list[dict]:
    """
    Retrieves the top-k most relevant API documents from Pinecone for a given query.
    Returns the structured metadata for each retrieved document.
    """
    if not pinecone_index:
        raise ValueError("Pinecone index not initialized. Please check your API keys and environment.")
        
    print(f"Retrieving top {k} docs for query: '{query}'")
    
    query_embedding = get_embedding(query)
    
    results = pinecone_index.query(
        vector=query_embedding,
        top_k=k,
        include_metadata=True
    )
    
    if not results['matches']:
        print("Warning: No relevant API documentation found in Pinecone.")
        return []
        
    # The full, structured document is now in the metadata
    retrieved_docs = []
    for match in results['matches']:
        metadata = match['metadata']
        if 'examples' in metadata and isinstance(metadata['examples'], str):
            try:
                metadata['examples'] = json.loads(metadata['examples'])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode 'examples' JSON for doc {metadata.get('name')}")
                metadata['examples'] = []
        retrieved_docs.append(metadata)

    print(f"Retrieved docs: {[doc.get('name', 'N/A') for doc in retrieved_docs]}")
    
    return retrieved_docs 