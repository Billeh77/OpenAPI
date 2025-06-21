import os
import glob
import yaml
import json
from dotenv import load_dotenv

# Load environment variables at the top of the script
# This ensures they are available before other modules are imported.
load_dotenv()

from pinecone import Pinecone
from rag import get_embedding
from db_models import ApiDoc

def main():
    """
    One-time script to parse, validate, and embed API documentation,
    then upsert it into Pinecone.
    """
    print("Environment variables loaded.")

    # --- Pinecone Initialization ---
    try:
        api_key = os.environ["PINECONE_API_KEY"]
        index_name = "api-rag"
        
        pc = Pinecone(api_key=api_key)
        
        if index_name not in pc.list_indexes().names():
            print(f"Creating Pinecone index '{index_name}'...")
            pc.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
            )
            print("Index created successfully.")
        else:
            print(f"Index '{index_name}' already exists.")
            
        index = pc.Index(index_name)
        
    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
        return

    # --- Document Processing and Upserting ---
    docs_path = os.path.join(os.path.dirname(__file__), 'api_docs', '*.md')
    markdown_files = glob.glob(docs_path)
    
    if not markdown_files:
        print(f"No markdown files found in {os.path.dirname(docs_path)}. Nothing to index.")
        return

    print(f"Found {len(markdown_files)} documents to process.")
    
    vectors_to_upsert = []
    for file_path in markdown_files:
        vector_id = os.path.basename(file_path).replace('.md', '')
        print(f"  - Processing {vector_id}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # The first part of the file is YAML front matter
                yaml_content = f.read().strip('--- \n')
                doc_data = yaml.safe_load(yaml_content)

            # Validate data with Pydantic model
            api_doc = ApiDoc(**doc_data)
            
            # Generate embedding from the description only
            embedding = get_embedding(api_doc.description)
            
            # Prepare the structured metadata
            metadata = api_doc.model_dump()

            # --- FIX: Serialize the 'examples' list to a JSON string ---
            if 'examples' in metadata and isinstance(metadata['examples'], list):
                metadata['examples'] = json.dumps(metadata['examples'])

            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            })
            print(f"    - Validation and embedding successful.")
            
        except Exception as e:
            print(f"    - Error processing file {file_path}: {e}")

    # --- Batch Upsert to Pinecone ---
    if vectors_to_upsert:
        print("\nUpserting vectors to Pinecone...")
        try:
            index.upsert(vectors=vectors_to_upsert)
            print(f"  - Successfully upserted {len(vectors_to_upsert)} vectors.")
        except Exception as e:
            print(f"    - Error upserting vectors: {e}")
        print("\nIndexing complete!")
    else:
        print("No valid vectors were generated. Nothing to upsert.")

if __name__ == "__main__":
    main() 