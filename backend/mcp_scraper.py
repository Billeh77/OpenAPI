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
            "documentation_summary": "Exposes tools like 'fs/readFile', 'fs/writeFile', and 'fs/listDirectory'. Requires a Python environment. Located in src/filesystem subdirectory. Uses pyproject.toml for dependencies. Entry point is in src/filesystem/server.py.",
            "required_env_vars": []
        },
        {
            "name": "mcp-git",
            "description": "An MCP server that acts as a wrapper around the Git command-line tool. It can be used to clone repositories, check status, and inspect commits.",
            "repository_url": "https://github.com/modelcontextprotocol/servers.git",
            "installation_type": "python",
            "documentation_summary": "Exposes tools for Git operations like 'git/clone', 'git/status', and 'git/log'. Needs Git installed in the container. Located in src/git subdirectory. Uses pyproject.toml for dependencies. Entry point is in src/git/server.py.",
            "required_env_vars": []
        },
        {
            "name": "mcp-memory",
            "description": "An MCP server that provides persistent memory and knowledge management capabilities. Can store and retrieve information across sessions.",
            "repository_url": "https://github.com/modelcontextprotocol/servers.git",
            "installation_type": "python",
            "documentation_summary": "Provides memory and knowledge storage tools. Located in src/memory subdirectory. Uses pyproject.toml for dependencies. Entry point is in src/memory/server.py.",
            "required_env_vars": []
        },
        {
            "name": "mcp-sqlite",
            "description": "An MCP server for interacting with SQLite databases. Provides tools for querying, creating, and managing SQLite databases.",
            "repository_url": "https://github.com/modelcontextprotocol/servers.git", 
            "installation_type": "python",
            "documentation_summary": "Provides SQLite database interaction tools. Located in src/sqlite subdirectory. Uses pyproject.toml for dependencies. Entry point is in src/sqlite/server.py.",
            "required_env_vars": []
        }
    ]
    return mock_servers 