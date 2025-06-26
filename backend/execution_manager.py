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
def build_and_run_mcp_server(dockerfile_content: str, server_name: str):
    """
    Builds and runs an MCP server in a Docker container.
    This is a context manager to ensure proper cleanup.
    """
    if not client:
        yield None, "Docker client not available.", "error"
        return

    container = None
    image_tag = f"mcp-adapter/{server_name}:latest"

    with tempfile.TemporaryDirectory() as temp_dir:
        dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        try:
            print(f"--- Building Docker image: {image_tag} ---")
            # Build the image from the temporary Dockerfile
            _, build_log_stream = client.images.build(path=temp_dir, tag=image_tag, rm=True, forcerm=True)
            build_logs = "".join([log.get('stream', '') for log in build_log_stream if 'stream' in log])

            print("--- Running container... ---")
            # Run the container, mapping port 8080 to a random available host port
            container = client.containers.run(image_tag, detach=True, ports={'8080/tcp': None})

            container.reload() # Refresh state to get port
            host_port = container.ports['8080/tcp'][0]['HostPort']
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
            # Cleanup: Stop and remove the container if it was created
            if container:
                print(f"--- Cleaning up container {container.short_id}... ---")
                container.stop()
                container.remove() 