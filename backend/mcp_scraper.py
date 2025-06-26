from typing import List, Dict

def get_mcp_servers() -> List[Dict]:
    """
    Simulates scraping MCP server information for the MVP.
    This provides the seed data for our knowledge base.
    """
    mock_servers = [
        {
            "name": "mcp-filesystem",
            "description": "An MCP server for interacting with the local filesystem. It provides tools for reading, writing, and listing files and directories.",
            "repository_url": "https://github.com/modelcontextprotocol/servers.git",
            "installation_type": "python",
            "documentation_summary": "Exposes tools like 'fs/readFile', 'fs/writeFile', and 'fs/listDirectory'. Requires a Python environment. Located in src/filesystem subdirectory.",
            "required_env_vars": []
        },
        {
            "name": "mcp-git",
            "description": "An MCP server that acts as a wrapper around the Git command-line tool. It can be used to clone repositories, check status, and inspect commits.",
            "repository_url": "https://github.com/modelcontextprotocol/servers.git",
            "installation_type": "python",
            "documentation_summary": "Exposes tools for Git operations like 'git/clone', 'git/status', and 'git/log'. Needs Git installed in the container. Located in src/git subdirectory.",
            "required_env_vars": []
        },
        {
            "name": "simple-test-server",
            "description": "A simple HTTP server for testing MCP adapter functionality. Just returns a hello world message.",
            "repository_url": "https://github.com/python/cpython.git",
            "installation_type": "python",
            "documentation_summary": "A minimal test server that demonstrates the MCP adapter deployment process.",
            "required_env_vars": []
        }
    ]
    return mock_servers 