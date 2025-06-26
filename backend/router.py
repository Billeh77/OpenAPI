from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import agent
import docker

router = APIRouter()

class ChatIn(BaseModel):
    message: str

# Initialize Docker client for container management
try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    docker_client = None

@router.post("/chat")
def chat(payload: ChatIn):
    """
    Receives a user's message, passes it to the agent,
    and returns the agent's response.
    """
    if not payload.message:
        return {"error": "Message cannot be empty."}
        
    response = agent.handle_query(payload.message)
    
    return response


@router.get("/containers")
def list_mcp_containers():
    """List all running MCP containers"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        containers = docker_client.containers.list(
            filters={"ancestor": "mcp-adapter"}
        )
        
        container_info = []
        for container in containers:
            ports = container.ports.get('8080/tcp', [])
            port = ports[0]['HostPort'] if ports else None
            
            container_info.append({
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "port": port,
                "url": f"http://localhost:{port}" if port else None,
                "created": container.attrs['Created']
            })
        
        return {"containers": container_info}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing containers: {str(e)}")


@router.delete("/containers/{container_id}")
def stop_mcp_container(container_id: str):
    """Stop and remove a specific MCP container"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        
        return {"message": f"Container {container_id} stopped and removed"}
    
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping container: {str(e)}")


@router.delete("/containers")
def cleanup_all_mcp_containers():
    """Stop and remove all MCP containers"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        containers = docker_client.containers.list(
            filters={"ancestor": "mcp-adapter"},
            all=True
        )
        
        stopped_count = 0
        for container in containers:
            try:
                container.stop()
                container.remove()
                stopped_count += 1
            except:
                pass
        
        return {"message": f"Stopped and removed {stopped_count} MCP containers"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up containers: {str(e)}") 