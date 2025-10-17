import importlib
import importlib.util
import pkgutil
import asyncio
import json as json_lib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type, Optional

import httpx

# ---------------------------------------------------------------------------
# Plugin base class
# ---------------------------------------------------------------------------

class Plugin(ABC):
    """Base class for all test plugins.

    Sub‑classes must implement ``run`` which receives either an ``httpx.AsyncClient``
    (for HTTP mode) or a ``StdioClient`` (for stdio mode) and returns a dict of results.
    """

    @abstractmethod
    async def run(self, client) -> Dict:
        """Execute the plugin logic and return a result dictionary."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stdio client wrapper for MCP servers
# ---------------------------------------------------------------------------

class StdioClient:
    """Wrapper for stdio-based MCP servers to provide HTTP-like interface."""

    def __init__(self, process: asyncio.subprocess.Process):
        self.process = process
        self._request_id = 0

    async def post(self, path: str, json: dict = None, **kwargs):
        """Send JSON-RPC request via stdin, read response from stdout."""
        self._request_id += 1

        # Prepare JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": json.get("method") if json else "initialize",
            "params": json.get("params", {}) if json else {}
        }

        # Send to stdin
        request_str = json_lib.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()

        # Read from stdout (with timeout)
        try:
            line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=5.0
            )
            response_data = json_lib.loads(line.decode())

            # Create HTTP-like response object
            class StdioResponse:
                def __init__(self, data):
                    # JSON-RPC errors should return 200/400, not 500
                    # Only return 500 if the response is malformed or missing jsonrpc
                    if "error" in data and "jsonrpc" in data:
                        self.status_code = 400  # JSON-RPC error (properly handled)
                    elif "result" in data:
                        self.status_code = 200  # Success
                    else:
                        self.status_code = 500  # Malformed response (actual crash)
                    self._data = data
                    self.headers = {}

                @property
                def text(self):
                    return json_lib.dumps(self._data)

                @property
                def content(self):
                    return self.text.encode()

                def json(self):
                    return self._data

            return StdioResponse(response_data)

        except asyncio.TimeoutError:
            class TimeoutResponse:
                status_code = 504
                text = json_lib.dumps({"error": "timeout"})
                content = text.encode()
                headers = {}
                def json(self):
                    return {"error": "timeout"}
            return TimeoutResponse()
        except Exception as e:
            class ErrorResponse:
                status_code = 500
                text = json_lib.dumps({"error": str(e)})
                content = text.encode()
                headers = {}
                def json(self):
                    return {"error": str(e)}
            return ErrorResponse()

    async def get(self, path: str, **kwargs):
        """GET request simulation for stdio."""
        return await self.post(path, json={"method": "ping"}, **kwargs)

# ---------------------------------------------------------------------------
# Plugin registry – discovers plugins in the ``mcp_testbench.plugins`` package
# ---------------------------------------------------------------------------

class PluginRegistry:
    def __init__(self, plugins_dir: Path = None):
        if plugins_dir is None:
            plugins_dir = Path(__file__).parent / "plugins"
        self.plugins_dir = plugins_dir
        self._plugins: List[Type[Plugin]] = []
        self.discover_plugins()

    def discover_plugins(self) -> None:
        """Import all Python modules in the plugins directory and collect Plugin subclasses."""
        if not self.plugins_dir.exists():
            return

        # Make the engine module available globally so plugins can import from it
        import sys
        sys.modules['engine'] = sys.modules[__name__]

        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            # Load module from file path
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find Plugin subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                        self._plugins.append(attr)

    @property
    def plugins(self) -> List[Type[Plugin]]:
        return self._plugins

# ---------------------------------------------------------------------------
# Core test engine – runs all discovered plugins and aggregates results
# ---------------------------------------------------------------------------

class TestEngine:
    def __init__(self, base_url: str = None, stdio_cmd: List[str] = None):
        self.base_url = base_url
        self.stdio_cmd = stdio_cmd
        self.registry = PluginRegistry()
        self.mode = "stdio" if stdio_cmd else "http"

    async def run_all(self) -> Dict:
        """Run every registered plugin and combine their result dicts.

        Returns a single dictionary with a top‑level ``plugins`` key mapping
        plugin class names to their individual result dictionaries.
        """
        if self.mode == "stdio":
            return await self._run_stdio()
        else:
            return await self._run_http()

    async def _run_http(self) -> Dict:
        """Run tests against HTTP MCP server."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            results: Dict[str, Dict] = {}
            for plugin_cls in self.registry.plugins:
                plugin = plugin_cls()
                name = plugin_cls.__name__
                try:
                    results[name] = await plugin.run(client)
                except Exception as exc:
                    results[name] = {"error": str(exc)}
            return {"plugins": results}

    async def _run_stdio(self) -> Dict:
        """Run tests against stdio MCP server."""
        # Start the MCP server process
        process = await asyncio.create_subprocess_exec(
            *self.stdio_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            # Give the server a moment to start
            await asyncio.sleep(1)

            # Create stdio client wrapper
            client = StdioClient(process)

            results: Dict[str, Dict] = {}
            for plugin_cls in self.registry.plugins:
                plugin = plugin_cls()
                name = plugin_cls.__name__
                try:
                    results[name] = await plugin.run(client)
                except Exception as exc:
                    results[name] = {"error": str(exc)}

            return {"plugins": results}

        finally:
            # Clean up process properly to avoid asyncio warnings
            try:
                # Close stdin first to signal EOF
                if process.stdin:
                    process.stdin.close()
                    await process.stdin.wait_closed()

                # Terminate process
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                # Force kill if terminate didn't work
                process.kill()
                await process.wait()
            except Exception:
                # Fallback: force kill
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass

if __name__ == "__main__":
    import asyncio, json
    engine = TestEngine()
    agg = asyncio.run(engine.run_all())
    print(json.dumps(agg, indent=2))
