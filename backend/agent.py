import rag
import llm
import execution_manager

# MCP Adapter Configuration

MAX_RETRIES = 3



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

    # 2. Initial Deployment Package Generation
    try:
        deployment_files = llm.generate_deployment_package(user_query, retrieved_docs)
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate initial deployment package: {e}"}

    # 3. Execution Loop with Retry - accumulate error history
    error_history = []
    
    for attempt in range(MAX_RETRIES + 1):
        print(f"--- Build Attempt {attempt + 1} for {server_name} ---")

        with execution_manager.build_and_run_mcp_server(deployment_files, server_name) as (url, logs, status):

            if status == "success":
                return {
                    "status": "success",
                    "server_name": server_name,
                    "message": f"MCP server successfully deployed and is running.",
                    "connection_url": url,
                    "deployment_files": deployment_files,
                    "logs": logs,
                    "attempts": attempt + 1
                }

            # Record this failure in our history
            error_entry = {
                "attempt": attempt + 1,
                "deployment_files": deployment_files,
                "error": logs,
                "status": status
            }
            error_history.append(error_entry)

            # If we have retries left, try to fix the Dockerfile
            if attempt < MAX_RETRIES:
                print(f"--- Attempt {attempt + 1} failed. Attempting to self-correct... ---")
                
                # Create comprehensive error context for the LLM
                error_context = f"Attempt {attempt + 1} failed with status '{status}':\n{logs}"
                if len(error_history) > 1:
                    error_context += f"\n\nPrevious failure history:"
                    for i, prev_error in enumerate(error_history[:-1], 1):
                        error_context += f"\n--- Previous Attempt {prev_error['attempt']} ---"
                        error_context += f"\nStatus: {prev_error['status']}"
                        error_context += f"\nError: {prev_error['error'][:500]}..."  # Truncate for brevity
                
                try:
                    deployment_files = llm.generate_deployment_package_with_retry(
                        old_deployment_files=deployment_files,
                        error=error_context,
                        user_query=user_query,
                        retrieved_docs=retrieved_docs,
                        error_history=[e["error"] for e in error_history[:-1]]  # Pass previous errors
                    )
                except Exception as e:
                    return {
                        "status": "failed",
                        "server_name": server_name,
                        "message": f"Failed to generate retry deployment package: {e}",
                        "error_details": logs,
                        "deployment_files": deployment_files,
                        "error_history": error_history
                    }
                continue # Go to the next attempt in the loop

            # If it's the last retry, return comprehensive failure info
            return {
                "status": "failed",
                "server_name": server_name,
                "message": f"Failed to deploy MCP server after {MAX_RETRIES + 1} attempts.",
                "error_details": logs,
                "deployment_files": deployment_files,
                "error_history": error_history,
                "total_attempts": attempt + 1
            } 