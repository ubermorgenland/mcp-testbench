# MCP Testbench

![MCP Security Score](https://img.shields.io/badge/Security-B-green)

**Docker-isolated security testing for Model Context Protocol (MCP) servers.**

MCP Testbench is a comprehensive security testing harness that runs MCP servers in isolated Docker containers and performs automated vulnerability scanning, fuzzing, and penetration testing.

## Why MCP Testbench?

With critical vulnerabilities like CVE-2025-6514 (CVSS 9.6) and CVE-2025-49596 (CVSS 9.4) affecting MCP servers, security testing is no longer optional. MCP Testbench provides:

- **🌐 Universal Testing**: Works with **both stdio** (local) and **HTTP** (remote) MCP servers
- **🔒 Docker Isolation**: Test potentially malicious servers safely with `--network none`
- **🔍 CVE Scanning**: Automatic detection of known vulnerabilities
- **⚡ Fuzzing Engine**: Protocol conformance testing with malformed inputs
- **🛡️ Injection Testing**: Prompt injection, SQL injection, XSS, and path traversal tests
- **📊 Security Scoring**: Simple A-F grades with shields.io badges for READMEs
- **🚀 CI/CD Ready**: JSON reports and GitHub Actions integration

**Proven Results**: Found critical F-grade vulnerabilities in popular MCP servers like time-mcp and docker-mcp.

## Installation

### CLI Installation

```bash
pip install mcp-testbench
```

Or from source:

```bash
git clone https://github.com/ubermorgenland/mcp-testbench
cd mcp-testbench
pip install -e .
```

### GitHub Action

Add to `.github/workflows/security.yml`:

```yaml
- name: MCP Security Scan
  uses: ubermorgenland/mcp-testbench@v1
  with:
    target: 'http://localhost:8000'
```

See [GITHUB_ACTION.md](GITHUB_ACTION.md) for complete guide.

## Quick Start

### Testing Stdio MCP Servers (Local)

Most MCP servers use stdio transport (npx commands). Test any stdio server:

```bash
# Test time-mcp
mcp-testbench run --stdio "npx time-mcp"

# Test docker-mcp
mcp-testbench run --stdio "npx @edjl/docker-mcp"

# Test GitHub MCP server
mcp-testbench run --stdio "npx @modelcontextprotocol/server-github"

# With verbose output
mcp-testbench run --stdio "npx time-mcp" --verbose

# Custom output directory
mcp-testbench run --stdio "npx time-mcp" --output ./security-reports
```

**Real Results**: We tested popular MCP servers:
- `time-mcp`: **F grade** (5 crashes, 36% failure rate)
- `docker-mcp`: **F grade** (12 crashes, 86% failure rate)

Both fail on basic input validation. [See detailed crash analysis](CRASH_ANALYSIS.md).

### Testing HTTP MCP Servers (Remote)

Test remote MCP servers over HTTP:

```bash
# Test local HTTP server
mcp-testbench run http://localhost:8000

# Test production deployment
mcp-testbench run https://mcp.yourcompany.com/

# With custom output
mcp-testbench run http://localhost:8000 --output ./security-reports
```

### Docker Isolated Testing (Recommended)

For maximum security, run tests in Docker:

```bash
mcp-testbench run --docker --docker-path /path/to/mcp-server
```

This mounts your MCP server in an isolated container with:
- `--network none` (no network access)
- `--cpus 2` (CPU limit)
- `--memory 2g` (memory limit)

## Output

MCP Testbench generates:

1. **JSON Report**: Detailed test results with vulnerability details
2. **Security Badge**: shields.io markdown badge for your README
3. **Terminal Summary**: Human-readable results with risk levels

### Example Badge

Add this to your MCP server's README:

```markdown
![MCP Security Score](./mcp_testbench_report/SECURITY_BADGE.md)
```

## Security Tests

### CVE Scanner
- Checks for CVE-2025-6514 (mcp-remote RCE)
- Checks for CVE-2025-49596 (MCP Inspector RCE)
- Identifies vulnerable server versions

### Fuzzing Engine
- Invalid JSON payloads
- Oversized inputs (100KB+ strings)
- Deeply nested objects (1000+ levels)
- Unicode exploits and null bytes
- Type confusion attacks
- Protocol conformance testing

### Injection Testing
- **Prompt Injection**: Tool poisoning attacks
- **Command Injection**: Shell command execution attempts
- **Path Traversal**: File system access tests
- **SQL Injection**: Database query manipulation
- **XSS**: Cross-site scripting payloads

## Architecture

```
CLI → TestEngine → PluginRegistry → [CVEScanner, Fuzzer, PromptInjection]
                                                    ↓
                                              Reporter → JSON + Badge
```

### Plugin System

MCP Testbench uses a plugin architecture for extensibility:

```python
from engine import Plugin
import httpx

class CustomPlugin(Plugin):
    async def run(self, client: httpx.AsyncClient) -> dict:
        # Your test logic here
        response = await client.get("/")
        return {
            "status": "completed",
            "custom_metric": response.status_code
        }
```

Save to `plugins/custom_plugin.py` and it will be automatically discovered.

## Security Scoring

- **A (Bright Green)**: No vulnerabilities, passes all tests
- **B (Green)**: Minor issues, no critical vulnerabilities
- **C (Yellow)**: Moderate risk, some tests failed
- **D (Orange)**: High risk, multiple vulnerabilities or plugin errors
- **F (Red)**: Critical vulnerabilities detected

## Docker Isolation

MCP Testbench runs tests in isolated containers with:

```bash
docker run --network none --cpus 2 --memory 2g
```

This prevents malicious MCP servers from:
- Making network requests
- Consuming excessive resources
- Accessing host filesystem
- Compromising the testing environment

## Roadmap

- [x] GitHub Action for CI/CD ✅
- [x] Docker isolation mode ✅
- [ ] Rate limiting tests
- [ ] Log sanitization checks
- [ ] Input validation tests
- [ ] Real-time CVE feed integration
- [ ] Observability metrics
- [ ] Registry signing verification

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## References

- [MCP Security is still Broken (Reddit)](https://reddit.com/r/mcp) - 345 upvotes
- CVE-2025-6514: Critical RCE in mcp-remote (CVSS 9.6)
- CVE-2025-49596: RCE in MCP Inspector (CVSS 9.4)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)

---

**Built by the ApInference Team** | [Website](https://apinference.com) | [Twitter](https://twitter.com/ApInference)
