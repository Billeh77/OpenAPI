import rag
import llm
import execution_manager

# MCP Adapter Configuration

MAX_RETRIES = 1



def handle_query(user_query: str) -> dict:
    """
    Orchestrates the new MCP adapter flow:
    1. Find an MCP server using RAG.
    2. Generate a Dockerfile for it using an LLM.
    3. Attempt to build and run it using the Execution Manager.
    4. On build failure, use the LLM to self-correct the Dockerfile.
    """
    print(f"\n--- Handling MCP request: '{user_query}' ---")

    # 1. RAG Retrieval
    try:
        retrieved_docs = rag.retrieve(user_query, k=1) # Get the single best match
        if not retrieved_docs:
            return {"status": "error", "message": "Could not find a relevant MCP server."}
        server_doc = retrieved_docs[0]
        server_name = server_doc.get('name', 'unknown-server')
    except Exception as e:
        return {"status": "error", "message": f"RAG retrieval failed: {e}"}

    # 2. Initial Dockerfile Generation
    dockerfile = llm.generate_dockerfile(user_query, retrieved_docs)

    # 3. Execution Loop with Retry
    for attempt in range(MAX_RETRIES + 1):
        print(f"--- Build Attempt {attempt + 1} for {server_name} ---")

        with execution_manager.build_and_run_mcp_server(dockerfile, server_name) as (url, logs, status):

            if status == "success":
                return {
                    "status": "success",
                    "server_name": server_name,
                    "message": f"MCP server successfully deployed and is running.",
                    "connection_url": url,
                    "dockerfile": dockerfile,
                    "logs": logs
                }

            # If build failed and we have retries left
            if status == "build_error" and attempt < MAX_RETRIES:
                print("--- Dockerfile build failed. Attempting to self-correct... ---")
                error_message = f"Build failed with logs:\n{logs}"
                dockerfile = llm.generate_dockerfile_with_retry(
                    old_dockerfile=dockerfile,
                    error=error_message,
                    user_query=user_query,
                    retrieved_docs=retrieved_docs
                )
                continue # Go to the next attempt in the loop

            # If it's a runtime error or the last retry
            return {
                "status": "failed",
                "server_name": server_name,
                "message": "Failed to deploy MCP server after all attempts.",
                "error_details": logs,
                "dockerfile": dockerfile
            } 