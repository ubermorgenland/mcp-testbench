#!/usr/bin/env python3
"""Command-line interface for MCP Testbench."""
import argparse
import asyncio
import sys
from pathlib import Path

from engine import TestEngine
from reporter import write_report
from docker_manager import DockerManager


def print_banner():
    """Print the MCP Testbench banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                      MCP TESTBENCH                            ║
║           Docker-Isolated Security Testing for MCP            ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_summary(results: dict):
    """Print a human-readable summary of test results."""
    print("\n" + "="*65)
    print("SECURITY TEST RESULTS")
    print("="*65)

    for plugin_name, result in results['plugins'].items():
        print(f"\n📋 {plugin_name}")
        print("-" * 65)

        if 'error' in result:
            print(f"  ❌ ERROR: {result['error']}")
            continue

        if 'status' in result:
            status_emoji = "✅" if result['status'] in ['completed', 'success'] else "⚠️"
            print(f"  {status_emoji} Status: {result['status']}")

        # Plugin-specific details
        if 'vulnerabilities_found' in result:
            vuln_emoji = "🔴" if result['vulnerabilities_found'] > 0 else "🟢"
            print(f"  {vuln_emoji} Vulnerabilities Found: {result['vulnerabilities_found']}")

        if 'crashes' in result:
            crash_emoji = "🔴" if result['crashes'] > 0 else "🟢"
            print(f"  {crash_emoji} Crashes: {result['crashes']}")

        if 'timeouts' in result:
            timeout_emoji = "⚠️" if result['timeouts'] > 0 else "🟢"
            print(f"  {timeout_emoji} Timeouts: {result['timeouts']}")

        if 'risk_level' in result:
            risk_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🔴",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "NONE": "🟢"
            }.get(result['risk_level'], "⚪")
            print(f"  {risk_emoji} Risk Level: {result['risk_level']}")

    print("\n" + "="*65)


async def run_tests_docker(target_path: str, output_dir: str, verbose: bool = False):
    """Run tests in Docker-isolated environment."""
    print(f"\n🐳 Docker Mode: Enabled")
    print(f"📁 Target Path: {target_path}")
    print(f"📁 Output Directory: {output_dir}")

    docker_mgr = DockerManager()

    try:
        # Build Docker image
        print("\n⏳ Building Docker image...")
        docker_mgr.build_image()
        print("✅ Docker image built successfully")

        # Run container (isolated=False to allow testing from host)
        print("\n⏳ Starting isolated container...")
        container_id = docker_mgr.run_container(target_path, isolated=False)
        print(f"✅ Container started: {container_id[:12]}")
        print("⚠️  Note: Container running with port forwarding for testing")

        # Wait for server to be ready
        print("\n⏳ Waiting for MCP server to be ready...")
        healthy = docker_mgr.health_check()

        if not healthy:
            print("⚠️  Warning: Health check failed, but continuing with tests...")
        else:
            print("✅ MCP server is healthy")

        # Run tests against containerized server
        print("\n⏳ Running security tests...\n")
        engine = TestEngine("http://localhost:8000")

        if verbose:
            print(f"Discovered {len(engine.registry.plugins)} plugins:")
            for plugin_cls in engine.registry.plugins:
                print(f"  • {plugin_cls.__name__}")
            print()

        results = await engine.run_all()

        return results

    finally:
        # Always stop container
        print("\n⏳ Stopping container...")
        docker_mgr.stop_container()
        print("✅ Container stopped")


async def run_tests(target_url: str, output_dir: str, verbose: bool = False, docker: bool = False, docker_path: str = None, stdio: str = None):
    """Run all security tests against the target MCP server."""

    # Docker mode
    if docker:
        if not docker_path:
            print("❌ Error: --docker-path is required when using --docker mode")
            sys.exit(1)
        results = await run_tests_docker(docker_path, output_dir, verbose)
    # Stdio mode
    elif stdio:
        print(f"\n📡 Stdio Mode: Enabled")
        print(f"📝 Command: {stdio}")
        print(f"📁 Output Directory: {output_dir}")
        print("\n⏳ Starting MCP server and running security tests...\n")

        # Parse command
        import shlex
        stdio_cmd = shlex.split(stdio)

        # Initialize engine with stdio command
        engine = TestEngine(stdio_cmd=stdio_cmd)

        if verbose:
            print(f"Discovered {len(engine.registry.plugins)} plugins:")
            for plugin_cls in engine.registry.plugins:
                print(f"  • {plugin_cls.__name__}")
            print()

        # Run all tests
        results = await engine.run_all()
    else:
        # HTTP mode
        print(f"\n🎯 Target: {target_url}")
        print(f"📁 Output Directory: {output_dir}")
        print("\n⏳ Running security tests...\n")

        # Initialize engine and run tests
        engine = TestEngine(base_url=target_url)

        if verbose:
            print(f"Discovered {len(engine.registry.plugins)} plugins:")
            for plugin_cls in engine.registry.plugins:
                print(f"  • {plugin_cls.__name__}")
            print()

        # Run all tests
        results = await engine.run_all()

    # Print summary
    print_summary(results)

    # Generate report
    badge_file = write_report(results, output_dir)

    print(f"\n📄 Report saved to: {badge_file.parent}")
    print(f"   • JSON: {badge_file.parent / 'mcp_testbench_report.json'}")
    print(f"   • Badge: {badge_file}")

    # Read and display badge
    with open(badge_file) as f:
        badge_content = f.read()
        print(f"\n🛡️  Security Badge:\n   {badge_content}")

    print("\n✅ Testing complete!")

    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Testbench - Docker-isolated security testing for MCP servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test HTTP MCP server
  mcp-testbench run http://localhost:8000

  # Test stdio MCP server (local)
  mcp-testbench run --stdio "npx time-mcp"

  # Test stdio with verbose output
  mcp-testbench run --stdio "npx @modelcontextprotocol/server-github" --verbose

  # Test remote MCP server
  mcp-testbench run https://mcp.stripe.com/

  # Docker-isolated testing
  mcp-testbench run --docker --docker-path /path/to/mcp-server

  # Custom output directory
  mcp-testbench run --stdio "npx docker-mcp" --output ./reports
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run security tests')
    run_parser.add_argument(
        'target',
        nargs='?',
        help='Target MCP server URL (e.g., http://localhost:8000) - not required in Docker mode'
    )
    run_parser.add_argument(
        '-o', '--output',
        default='./mcp_testbench_report',
        help='Output directory for reports (default: ./mcp_testbench_report)'
    )
    run_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    run_parser.add_argument(
        '--docker',
        action='store_true',
        help='Run tests in Docker-isolated container (requires --docker-path)'
    )
    run_parser.add_argument(
        '--docker-path',
        help='Path to MCP server directory to mount in Docker container'
    )
    run_parser.add_argument(
        '--stdio',
        help='Run tests against stdio MCP server (e.g., "npx time-mcp")'
    )

    # Version command
    parser.add_argument(
        '--version',
        action='version',
        version='mcp-testbench 0.1.0'
    )

    args = parser.parse_args()

    if args.command == 'run':
        print_banner()

        # Validate arguments
        if not args.docker and not args.stdio and not args.target:
            print("❌ Error: target URL is required when not using --docker or --stdio mode")
            sys.exit(1)

        try:
            asyncio.run(run_tests(
                args.target,
                args.output,
                args.verbose,
                docker=args.docker,
                docker_path=args.docker_path,
                stdio=args.stdio
            ))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            if args.verbose:
                traceback.print_exc()
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
