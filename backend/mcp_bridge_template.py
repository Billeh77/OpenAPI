"""
MCP-to-HTTP Bridge Template
===========================

This template provides a complete bridge implementation that:
1. Understands the MCP protocol (JSON-RPC over stdin/stdout)
2. Manages MCP server subprocess lifecycle
3. Implements proper MCP handshake and communication
4. Exposes MCP tools as HTTP REST endpoints
5. Handles errors, timeouts, and recovery

Usage: This template should be customized for specific MCP servers
"""

import asyncio
import json
import logging
import subprocess
import time
import uuid
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPMessageType(str, Enum):
    """MCP message types according to the protocol"""
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    PING = "ping"
    PONG = "pong"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"


@dataclass
class MCPCapabilities:
    """MCP server capabilities"""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None


class MCPRequest(BaseModel):
    """JSON-RPC request format"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """JSON-RPC response format"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class ToolCallRequest(BaseModel):
    """HTTP request for calling MCP tools"""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    """HTTP response for tool calls"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float


class MCPServerManager:
    """Manages MCP server subprocess and communication"""
    
    def __init__(self, server_command: List[str], working_dir: str = "/app"):
        self.server_command = server_command
        self.working_dir = working_dir
        self.process: Optional[subprocess.Popen] = None
        self.capabilities: Optional[MCPCapabilities] = None
        self.tools: List[Dict[str, Any]] = []
        self.resources: List[Dict[str, Any]] = []
        self.prompts: List[Dict[str, Any]] = []
        self.is_initialized = False
        self.request_id_counter = 0
        
    async def start(self) -> bool:
        """Start the MCP server process"""
        try:
            logger.info(f"Starting MCP server: {' '.join(self.server_command)}")
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir,
                bufsize=0  # Unbuffered for real-time communication
            )
            
            # Wait a moment for process to start
            await asyncio.sleep(0.5)
            
            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else "No error output"
                logger.error(f"MCP server failed to start: {stderr}")
                return False
                
            # Initialize MCP connection
            success = await self._initialize()
            if success:
                await self._discover_capabilities()
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.sleep(1)
                if self.process.poll() is None:
                    self.process.kill()
                logger.info("MCP server stopped")
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
    
    def _get_next_id(self) -> str:
        """Generate next request ID"""
        self.request_id_counter += 1
        return str(self.request_id_counter)
    
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request to MCP server"""
        if not self.process or self.process.poll() is not None:
            logger.error("MCP server process not running")
            return None
            
        request_id = self._get_next_id()
        request = MCPRequest(
            id=request_id,
            method=method,
            params=params or {}
        )
        
        try:
            # Send request
            request_json = request.model_dump_json() + "\n"
            logger.debug(f"Sending MCP request: {request_json.strip()}")
            
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Read response with timeout
            response_line = await self._read_response_with_timeout(timeout=30.0)
            if not response_line:
                return None
                
            logger.debug(f"Received MCP response: {response_line.strip()}")
            response_data = json.loads(response_line)
            
            # Validate response ID matches request ID
            if response_data.get("id") != request_id:
                logger.warning(f"Response ID mismatch: expected {request_id}, got {response_data.get('id')}")
            
            if "error" in response_data:
                logger.error(f"MCP server error: {response_data['error']}")
                return None
                
            return response_data.get("result")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from MCP server: {e}")
            return None
        except Exception as e:
            logger.error(f"Error communicating with MCP server: {e}")
            return None
    
    async def _read_response_with_timeout(self, timeout: float) -> Optional[str]:
        """Read response from MCP server with timeout"""
        try:
            # Use asyncio to add timeout to blocking read
            loop = asyncio.get_event_loop()
            
            def read_line():
                return self.process.stdout.readline()
            
            response_line = await asyncio.wait_for(
                loop.run_in_executor(None, read_line),
                timeout=timeout
            )
            
            return response_line.strip() if response_line else None
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for MCP server response ({timeout}s)")
            return None
        except Exception as e:
            logger.error(f"Error reading MCP server response: {e}")
            return None
    
    async def _initialize(self) -> bool:
        """Initialize MCP connection with handshake"""
        logger.info("Initializing MCP connection...")
        
        # Send initialize request
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "mcp-http-bridge",
                "version": "1.0.0"
            }
        }
        
        result = await self._send_request(MCPMessageType.INITIALIZE, init_params)
        if not result:
            logger.error("Failed to initialize MCP connection")
            return False
        
        # Store server capabilities
        self.capabilities = MCPCapabilities(
            tools=result.get("capabilities", {}).get("tools"),
            resources=result.get("capabilities", {}).get("resources"),
            prompts=result.get("capabilities", {}).get("prompts"),
            logging=result.get("capabilities", {}).get("logging")
        )
        
        # Send initialized notification (no response expected)
        initialized_request = {
            "jsonrpc": "2.0",
            "method": MCPMessageType.INITIALIZED,
            "params": {}
        }
        
        try:
            request_json = json.dumps(initialized_request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            logger.info("MCP connection initialized successfully")
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to send initialized notification: {e}")
            return False
    
    async def _discover_capabilities(self):
        """Discover available tools, resources, and prompts"""
        logger.info("Discovering MCP server capabilities...")
        
        # Discover tools
        if self.capabilities and self.capabilities.tools:
            tools_result = await self._send_request(MCPMessageType.TOOLS_LIST)
            if tools_result and "tools" in tools_result:
                self.tools = tools_result["tools"]
                logger.info(f"Discovered {len(self.tools)} tools: {[t.get('name') for t in self.tools]}")
        
        # Discover resources
        if self.capabilities and self.capabilities.resources:
            resources_result = await self._send_request(MCPMessageType.RESOURCES_LIST)
            if resources_result and "resources" in resources_result:
                self.resources = resources_result["resources"]
                logger.info(f"Discovered {len(self.resources)} resources")
        
        # Discover prompts
        if self.capabilities and self.capabilities.prompts:
            prompts_result = await self._send_request(MCPMessageType.PROMPTS_LIST)
            if prompts_result and "prompts" in prompts_result:
                self.prompts = prompts_result["prompts"]
                logger.info(f"Discovered {len(self.prompts)} prompts")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="MCP server not initialized")
        
        # Validate tool exists
        tool_names = [tool.get("name") for tool in self.tools]
        if tool_name not in tool_names:
            raise HTTPException(
                status_code=404, 
                detail=f"Tool '{tool_name}' not found. Available tools: {tool_names}"
            )
        
        start_time = time.time()
        
        try:
            params = {
                "name": tool_name,
                "arguments": arguments
            }
            
            result = await self._send_request(MCPMessageType.TOOLS_CALL, params)
            execution_time = time.time() - start_time
            
            if result is None:
                return {
                    "success": False,
                    "error": "Tool execution failed or timed out",
                    "execution_time": execution_time
                }
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health"""
        if not self.process:
            return {"status": "down", "reason": "Process not started"}
        
        if self.process.poll() is not None:
            return {"status": "down", "reason": "Process terminated"}
        
        if not self.is_initialized:
            return {"status": "starting", "reason": "Not initialized"}
        
        # Try a ping if server supports it
        try:
            result = await self._send_request(MCPMessageType.PING)
            if result is not None:
                return {"status": "healthy", "tools_count": len(self.tools)}
        except:
            pass
        
        # Fallback: check if we can list tools
        try:
            tools_result = await self._send_request(MCPMessageType.TOOLS_LIST)
            if tools_result:
                return {"status": "healthy", "tools_count": len(self.tools)}
        except:
            pass
        
        return {"status": "unhealthy", "reason": "Server not responding"}


# Global MCP server manager instance
mcp_server: Optional[MCPServerManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager"""
    global mcp_server
    
    # Startup
    logger.info("Starting MCP-HTTP Bridge...")
    
    # This will be customized per MCP server
    server_command = ["REPLACE_WITH_ACTUAL_COMMAND"]  # e.g., ["mcp-server-git"]
    
    mcp_server = MCPServerManager(server_command)
    
    success = await mcp_server.start()
    if not success:
        logger.error("Failed to start MCP server")
        raise RuntimeError("MCP server startup failed")
    
    logger.info("MCP-HTTP Bridge started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down MCP-HTTP Bridge...")
    if mcp_server:
        await mcp_server.stop()
    logger.info("MCP-HTTP Bridge stopped")


# Create FastAPI app with lifespan
app = FastAPI(
    title="MCP-HTTP Bridge",
    description="HTTP bridge for Model Context Protocol (MCP) servers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MCP-HTTP Bridge",
        "status": "running",
        "mcp_initialized": mcp_server.is_initialized if mcp_server else False
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    health_status = await mcp_server.health_check()
    
    if health_status["status"] == "down":
        raise HTTPException(status_code=503, detail=health_status["reason"])
    
    return health_status


@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    if not mcp_server or not mcp_server.is_initialized:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return {
        "tools": mcp_server.tools,
        "count": len(mcp_server.tools)
    }


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call an MCP tool"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    result = await mcp_server.call_tool(request.tool_name, request.arguments)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ToolCallResponse(**result)


@app.get("/resources")
async def list_resources():
    """List available MCP resources"""
    if not mcp_server or not mcp_server.is_initialized:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return {
        "resources": mcp_server.resources,
        "count": len(mcp_server.resources)
    }


@app.get("/prompts")
async def list_prompts():
    """List available MCP prompts"""
    if not mcp_server or not mcp_server.is_initialized:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return {
        "prompts": mcp_server.prompts,
        "count": len(mcp_server.prompts)
    }


@app.get("/debug/capabilities")
async def debug_capabilities():
    """Debug endpoint to show MCP server capabilities"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return {
        "capabilities": mcp_server.capabilities.__dict__ if mcp_server.capabilities else None,
        "tools": mcp_server.tools,
        "resources": mcp_server.resources,
        "prompts": mcp_server.prompts,
        "is_initialized": mcp_server.is_initialized
    }


if __name__ == "__main__":
    uvicorn.run(
        "mcp_bridge:app",
        host="0.0.0.0",
        port=8080,
        log_level="info"
    ) 