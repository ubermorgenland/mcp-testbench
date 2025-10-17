from pathlib import Path
from .docker_manager import DockerManager

def main():
    mgr = DockerManager()
    # Build image (ignore errors if already built)
    try:
        mgr.build_image()
    except Exception:
        pass
    # Run container mounting this directory (dummy server)
    cid = mgr.run_container(str(Path(__file__).parent))
    healthy = mgr.health_check()
    print(f"Container {cid} health: {healthy}")
    mgr.stop_container()

if __name__ == "__main__":
    main()
