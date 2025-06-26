# backend/execution_manager.py
import docker
import tempfile
import os
from contextlib import contextmanager

# Initialize Docker client from the environment
try:
    client = docker.from_env()
except docker.errors.DockerException:
    print("ERROR: Docker is not running or not installed. The Execution Manager cannot function.")
    client = None

@contextmanager
def build_and_run_mcp_server(deployment_files: dict, server_name: str):
    """
    Builds and runs an MCP server in a Docker container from a complete deployment package.
    This is a context manager to ensure proper cleanup.
    
    Args:
        deployment_files: Dictionary mapping filenames to file contents
        server_name: Name of the MCP server
    """
    if not client:
        yield None, "Docker client not available.", "error"
        return

    container = None
    image_tag = f"mcp-adapter/{server_name}:latest"

    with tempfile.TemporaryDirectory() as temp_dir:
        # Write all deployment files to temporary directory
        for filename, content in deployment_files.items():
            filepath = os.path.join(temp_dir, filename)
            
            # Create subdirectories if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            # Make shell scripts executable
            if filename.endswith('.sh'):
                os.chmod(filepath, 0o755)

        try:
            print(f"--- Building Docker image: {image_tag} ---")
            # Build the image from the temporary Dockerfile
            _, build_log_stream = client.images.build(path=temp_dir, tag=image_tag, rm=True, forcerm=True)
            build_logs = "".join([log.get('stream', '') for log in build_log_stream if 'stream' in log])

            print("--- Running container... ---")
            # Run the container, mapping port 8080 to a random available host port
            container = client.containers.run(image_tag, detach=True, ports={'8080/tcp': None})

            # Wait a moment for container to start
            import time
            time.sleep(2)
            
            container.reload() # Refresh state to get port
            
            # Check if container is still running
            if container.status != 'running':
                container_logs = container.logs().decode('utf-8')
                yield None, f"Container failed to start. Logs:\n{container_logs}", "runtime_error"
                return
            
            # Get the mapped port safely
            port_info = container.ports.get('8080/tcp')
            if not port_info or len(port_info) == 0:
                container_logs = container.logs().decode('utf-8')
                yield None, f"Port 8080 not exposed or mapped. Container logs:\n{container_logs}", "runtime_error"
                return
                
            host_port = port_info[0]['HostPort']
            url = f"http://localhost:{host_port}"

            print(f"--- Container '{container.short_id}' for '{server_name}' running at: {url} ---")
            # Yield the URL and logs on success
            yield url, build_logs, "success"

        except docker.errors.BuildError as e:
            print(f"--- Docker build failed for {server_name} ---")
            error_logs = "".join([log.get('stream', '') for log in e.build_log if 'stream' in log])
            yield None, error_logs, "build_error"
        except Exception as e:
            yield None, str(e), "runtime_error"
        finally:
            # Note: Container left running for persistent service
            # Users can manually stop with: docker stop <container_id>
            if container and container.status != 'running':
                # Only cleanup if container failed to start
                print(f"--- Cleaning up failed container {container.short_id}... ---")
                try:
                    container.remove()
                except:
                    pass 