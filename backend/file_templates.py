"""
File Templates for MCP Server Deployment
========================================

This module contains templates for all files needed to deploy an MCP server:
1. Dockerfile - Container definition
2. mcp_bridge.py - MCP-to-HTTP bridge implementation
3. requirements.txt - Python dependencies
4. entrypoint.sh - Container startup script
5. health_check.py - Health monitoring
6. docker-compose.yml - Optional orchestration
7. README.md - Deployment documentation
"""

# Template for Dockerfile
DOCKERFILE_TEMPLATE = """# MCP Server Deployment Container
# Generated automatically for: {server_name}

FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone MCP server repository
RUN git clone {repo_url} .

# Navigate to server directory if needed
{navigate_command}

# Install Python dependencies
{install_commands}

# Copy bridge files
COPY mcp_bridge.py /app/mcp_bridge.py
COPY requirements.txt /app/bridge_requirements.txt
COPY entrypoint.sh /app/entrypoint.sh
COPY health_check.py /app/health_check.py

# Install bridge dependencies
RUN pip install -r /app/bridge_requirements.txt

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose HTTP port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python /app/health_check.py

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
"""

# Template for bridge requirements.txt
BRIDGE_REQUIREMENTS_TEMPLATE = """# MCP Bridge Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.25.2
asyncio-subprocess==0.1.0
"""

# Template for entrypoint script
ENTRYPOINT_TEMPLATE = """#!/bin/bash
set -e

echo "Starting MCP-HTTP Bridge for {server_name}..."

# Set environment variables
export PYTHONPATH=/app:$PYTHONPATH
export MCP_SERVER_COMMAND="{server_command}"
export MCP_WORKING_DIR="{working_dir}"

# Wait for any dependencies to be ready
sleep 2

# Check if MCP server is available
echo "Checking MCP server availability..."
if ! command -v {server_binary} &> /dev/null; then
    echo "ERROR: MCP server binary '{server_binary}' not found"
    exit 1
fi

# Test MCP server can start
echo "Testing MCP server startup..."
timeout 10s {server_command} --help > /dev/null 2>&1 || {{
    echo "WARNING: MCP server test failed, but continuing..."
}}

# Start the bridge
echo "Starting MCP-HTTP Bridge..."
exec python /app/mcp_bridge.py
"""

# Template for health check script
HEALTH_CHECK_TEMPLATE = """#!/usr/bin/env python3
\"\"\"
Health check script for MCP-HTTP Bridge
\"\"\"

import sys
import requests
import json
from typing import Dict, Any

def check_health() -> bool:
    \"\"\"Check if the MCP bridge is healthy\"\"\"
    try:
        # Check if HTTP server is responding
        response = requests.get("http://localhost:8080/health", timeout=5)
        
        if response.status_code != 200:
            print(f"HTTP health check failed: {response.status_code}")
            return False
        
        health_data = response.json()
        
        # Check if MCP server is healthy
        if health_data.get("status") != "healthy":
            print(f"MCP server not healthy: {health_data}")
            return False
        
        print("Health check passed")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Health check failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Invalid health check response: {e}")
        return False
    except Exception as e:
        print(f"Unexpected health check error: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
"""

# Template for docker-compose.yml
DOCKER_COMPOSE_TEMPLATE = """version: '3.8'

services:
  {service_name}:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PYTHONPATH=/app
      - MCP_LOG_LEVEL=INFO
    volumes:
      # Add volumes if needed for persistent data
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "/app/health_check.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - mcp_network

networks:
  mcp_network:
    driver: bridge
"""

# Template for deployment README
README_TEMPLATE = """# {server_name} MCP Server Deployment

This container provides HTTP access to the {server_name} MCP server.

## What is MCP?

Model Context Protocol (MCP) is a protocol that allows AI assistants to connect to external tools and data sources. MCP servers provide "tools" that AI can call to perform specific tasks.

## What This Container Does

This container:
1. Runs the {server_name} MCP server as a subprocess
2. Provides an HTTP bridge that translates HTTP requests to MCP protocol calls
3. Exposes the MCP server's tools as REST API endpoints
4. Handles MCP protocol handshake and communication

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `GET /tools` - List available MCP tools
- `POST /tools/call` - Call an MCP tool
- `GET /resources` - List available resources (if supported)
- `GET /prompts` - List available prompts (if supported)
- `GET /debug/capabilities` - Debug information

## Usage

### Start the container:
```bash
docker run -p 8080:8080 {container_name}
```

### List available tools:
```bash
curl http://localhost:8080/tools
```

### Call a tool:
```bash
curl -X POST http://localhost:8080/tools/call \\
  -H "Content-Type: application/json" \\
  -d '{
    "tool_name": "example_tool",
    "arguments": {
      "param1": "value1"
    }
  }'
```

## Environment Variables

- `MCP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_TIMEOUT` - Request timeout in seconds (default: 30)

## Volumes

{volume_info}

## Health Monitoring

The container includes health checks that verify:
- HTTP server is responding
- MCP server process is running
- MCP protocol communication is working

## Troubleshooting

### Container won't start
- Check logs: `docker logs <container_id>`
- Verify MCP server dependencies are installed
- Check if required system packages are available

### MCP server not responding
- Check if the MCP server binary is available
- Verify working directory and file permissions
- Check MCP server specific requirements

### HTTP bridge errors
- Verify port 8080 is not in use
- Check bridge logs for MCP protocol errors
- Ensure proper JSON-RPC message formatting

## Development

To modify this deployment:
1. Edit the bridge configuration in `mcp_bridge.py`
2. Update dependencies in `requirements.txt`
3. Modify startup sequence in `entrypoint.sh`
4. Rebuild the container

## Support

This is an automatically generated deployment. For MCP server specific issues, refer to the original {server_name} documentation.
"""

def generate_deployment_package(server_config: dict) -> dict:
    """
    Generate a complete deployment package for an MCP server
    
    Args:
        server_config: Configuration dictionary containing:
            - server_name: Name of the MCP server
            - repo_url: Git repository URL
            - server_command: CLI command to run the server
            - server_binary: Binary name for testing
            - working_dir: Working directory for the server
            - navigate_command: Command to navigate to server directory
            - install_commands: Commands to install dependencies
            - volume_info: Information about required volumes
            - container_name: Docker container name
            - service_name: Docker service name
    
    Returns:
        Dictionary mapping filenames to file contents
    """
    
    files = {}
    
    # Generate Dockerfile
    files["Dockerfile"] = DOCKERFILE_TEMPLATE.format(**server_config)
    
    # Generate bridge requirements
    files["requirements.txt"] = BRIDGE_REQUIREMENTS_TEMPLATE
    
    # Generate entrypoint script
    files["entrypoint.sh"] = ENTRYPOINT_TEMPLATE.format(**server_config)
    
    # Generate health check
    files["health_check.py"] = HEALTH_CHECK_TEMPLATE
    
    # Generate docker-compose
    files["docker-compose.yml"] = DOCKER_COMPOSE_TEMPLATE.format(**server_config)
    
    # Generate README
    files["README.md"] = README_TEMPLATE.format(**server_config)
    
    # Generate customized bridge (will be done by LLM)
    files["mcp_bridge.py"] = "# This will be generated by LLM with server-specific customizations"
    
    return files


# Example server configurations for common MCP servers
EXAMPLE_CONFIGS = {
    "mcp-server-git": {
        "server_name": "Git MCP Server",
        "repo_url": "https://github.com/modelcontextprotocol/servers.git",
        "server_command": "mcp-server-git",
        "server_binary": "mcp-server-git",
        "working_dir": "/app/src/git",
        "navigate_command": "WORKDIR /app/src/git",
        "install_commands": "RUN pip install -e .",
        "volume_info": "- `./git_repos:/app/repos` - Git repositories to work with",
        "container_name": "mcp-git-server",
        "service_name": "mcp_git"
    },
    
    "mcp-server-filesystem": {
        "server_name": "Filesystem MCP Server", 
        "repo_url": "https://github.com/modelcontextprotocol/servers.git",
        "server_command": "mcp-server-filesystem",
        "server_binary": "mcp-server-filesystem",
        "working_dir": "/app/src/filesystem",
        "navigate_command": "WORKDIR /app/src/filesystem",
        "install_commands": "RUN pip install -e .",
        "volume_info": "- `./data:/app/data` - Filesystem access directory",
        "container_name": "mcp-filesystem-server",
        "service_name": "mcp_filesystem"
    }
} 