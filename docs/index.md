# MCP Testbench Documentation

![MCP Security Score](https://img.shields.io/badge/Security-B-green)

**Universal security testing for Model Context Protocol (MCP) servers.**

## What is MCP Testbench?

MCP Testbench is a comprehensive security testing tool that finds vulnerabilities in MCP servers before attackers do. It works with **both stdio (local) and HTTP (remote)** MCP servers, making it the only universal MCP security testing solution.

## Quick Start

### Test Any MCP Server in 30 Seconds

```bash
# Install
pip install mcp-testbench

# Test stdio server (most common)
mcp-testbench run --stdio "npx time-mcp"

# Test HTTP server
mcp-testbench run http://localhost:8000
```

### View Results

```bash
# Summary shows in terminal
# Detailed JSON report: ./mcp_testbench_report/mcp_testbench_report.json
# Security badge: ./mcp_testbench_report/SECURITY_BADGE.md

# View detailed crashes:
cat ./mcp_testbench_report/mcp_testbench_report.json | python -m json.tool
```

## Real Results

We tested popular MCP servers and found critical vulnerabilities:

| Server | Grade | Issues | Status |
|--------|-------|---------|--------|
| **time-mcp** | F | 5 timeouts (36%) | ❌ Critical DoS |
| **docker-mcp** | F | 12 crashes (86%) | ❌ Critical |

Both fail on:
- Empty payloads → timeout/crash
- Invalid JSON structure → timeout/crash
- Missing required fields → timeout/crash
- Huge strings (100KB) → timeout/crash
- Unicode exploits → timeout/crash

[See detailed crash analysis →](crash-analysis.md)

## Why MCP Testbench?

### For Developers
- ✅ **30-second security audit** - Know your vulnerabilities instantly
- ✅ **No manual testing** - Automated fuzzing, CVE scanning, injection tests
- ✅ **Specific fixes** - Get exact code examples to fix issues
- ✅ **CI/CD integration** - GitHub Actions ready

### For Security Teams
- ✅ **Universal testing** - Stdio and HTTP support
- ✅ **Docker isolation** - Test malicious servers safely
- ✅ **CVE scanning** - Detect known vulnerabilities (CVE-2025-6514, CVE-2025-49596)
- ✅ **Compliance ready** - JSON reports with detailed findings

## Documentation

### Getting Started
- [Installation Guide](installation.md)
- [Quick Start Tutorial](quickstart.md)
- [CLI Reference](cli-reference.md)

### Testing
- [Testing Stdio Servers](testing-stdio.md)
- [Testing HTTP Servers](testing-http.md)
- [Docker Isolation Mode](docker-mode.md)
- [Understanding Results](understanding-results.md)

### Advanced
- [GitHub Actions Integration](github-actions.md)
- [Plugin Development](plugin-development.md)
- [Crash Analysis Examples](crash-analysis.md)
- [Security Scoring System](scoring.md)

### Resources
- [GitHub Repository](https://github.com/ubermorgenland/mcp-testbench)
- [Report a Bug](https://github.com/ubermorgenland/mcp-testbench/issues)
- [ApInference](https://apinference.com)

## Support

- **GitHub Issues**: [github.com/ubermorgenland/mcp-testbench/issues](https://github.com/ubermorgenland/mcp-testbench/issues)
- **Twitter**: [@ApInference](https://twitter.com/ApInference)
- **Email**: info@apinference.com

---

**Built by Ubermorgen Ltd** | [ApInference](https://apinference.com)
