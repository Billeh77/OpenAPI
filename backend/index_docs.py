import os
import openai
from pinecone import Pinecone
from dotenv import load_dotenv
from db_models import McpServerDoc
from mcp_scraper import get_mcp_servers

# Load environment variables at the top of the script
# This ensures they are available before other modules are imported.
load_dotenv()

# --- Configuration ---
PINECONE_INDEX_NAME = "mcp-rag-mvp"
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# --- Client Initialization ---
pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(input=[text.replace("\n", " ")], model=EMBEDDING_MODEL)
    return response.data[0].embedding

def main():
    print("--- Starting MCP Server Indexing MVP ---")

    # 1. Ensure Pinecone index exists
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating new Pinecone index: '{PINECONE_INDEX_NAME}'")
        pc.create_index(
            name=PINECONE_INDEX_NAME, 
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
        )
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)

    # 2. Get server data from our MVP scraper
    servers_data = get_mcp_servers()
    if not servers_data:
        print("No server data found. Exiting.")
        return

    # 3. Process and upsert data
    vectors_to_upsert = []
    for server_data in servers_data:
        try:
            mcp_doc = McpServerDoc(**server_data)
            vector_id = mcp_doc.name
            print(f"  - Processing: {vector_id}")

            embedding = get_embedding(mcp_doc.description)
            metadata = mcp_doc.dict()

            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            })
        except Exception as e:
            print(f"    - ERROR processing {server_data.get('name', 'N/A')}: {e}")

    if vectors_to_upsert:
        print(f"\nUpserting {len(vectors_to_upsert)} vectors to '{PINECONE_INDEX_NAME}'...")
        pinecone_index.upsert(vectors=vectors_to_upsert)
        print("--- Indexing complete! ---")
    else:
        print("No valid vectors were generated.")

if __name__ == "__main__":
    main() 