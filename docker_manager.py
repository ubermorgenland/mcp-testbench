# Docker manager for MCP testbench

import subprocess
import shlex
from pathlib import Path

class DockerManager:
    """Utility to build and run the isolated test harness container."""

    def __init__(self, image_name: str = "mcp-testbench-runner", dockerfile_path: str = None):
        self.image_name = image_name
        self.dockerfile_path = dockerfile_path or Path(__file__).parent / "Dockerfile"
        self.container_id = None

    def build_image(self) -> None:
        """Build the Docker image using the provided Dockerfile."""
        cmd = f"docker build -t {shlex.quote(self.image_name)} -f {shlex.quote(str(self.dockerfile_path))} ."
        subprocess.run(cmd, shell=True, check=True)

    def run_container(self, target_path: str, cpu: str = "2", memory: str = "2g", isolated: bool = True) -> str:
        """Run the container mounting the target MCP server directory.

        Args:
            target_path: Path to mount in container
            cpu: CPU limit
            memory: Memory limit
            isolated: If True, use --network none for full isolation (recommended)
                     If False, expose port 8000 for testing (use with caution)

        Returns the container ID."""
        mount = f"{shlex.quote(target_path)}:/app"

        if isolated:
            # Full isolation - no network access
            # Note: This prevents the container from making outbound requests
            network_opts = "--network none"
            port_opts = ""
        else:
            # Testing mode - expose port for host access
            # Warning: This reduces isolation but allows testing
            network_opts = ""
            port_opts = "-p 8000:8000"

        cmd = (
            f"docker run -d --rm {network_opts} {port_opts} "
            f"--cpus {cpu} --memory {memory} "
            f"-v {mount} -w /app {shlex.quote(self.image_name)}"
        )
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        self.container_id = result.stdout.strip()
        return self.container_id

    def exec_in_container(self, command: str) -> str:
        """Execute a command inside the running container and return stdout."""
        if not self.container_id:
            raise RuntimeError("Container not started")
        cmd = f"docker exec {shlex.quote(self.container_id)} {command}"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def stop_container(self) -> None:
        """Stop the running container if it exists."""
        if self.container_id:
            subprocess.run(f"docker stop {shlex.quote(self.container_id)}", shell=True, check=False)
            self.container_id = None

    def health_check(self, endpoint: str = "/health", timeout: int = 30) -> bool:
        """Poll the health endpoint inside the container until it returns 200 or times out.
        Returns True on success, False on failure."""
        import time
        import http.client
        for _ in range(timeout):
            try:
                # Assuming the container forwards port 8000 to host
                conn = http.client.HTTPConnection("localhost", 8000, timeout=2)
                conn.request("GET", endpoint)
                resp = conn.getresponse()
                if resp.status == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

# Example usage (not executed in CI):
# if __name__ == "__main__":
#     mgr = DockerManager()
#     mgr.build_image()
#     cid = mgr.run_container("/path/to/mcp_server")
#     print("Container", cid)
#     healthy = mgr.health_check()
#     print("Healthy?", healthy)
#     mgr.stop_container()
