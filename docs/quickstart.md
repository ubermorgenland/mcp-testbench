# Quick Start Guide

Get your MCP server security audit in under 2 minutes.

## Installation

```bash
pip install mcp-testbench
```

## Your First Test

### Stdio MCP Server (Most Common)

Most MCP servers use stdio transport. Test any npx-based server:

```bash
mcp-testbench run --stdio "npx time-mcp"
```

**Output:**
```
📡 Stdio Mode: Enabled
📝 Command: npx time-mcp

=================================================================
SECURITY TEST RESULTS
=================================================================

📋 Fuzzer
  🔴 Crashes: 5
  🔴 Risk Level: HIGH

🛡️  Security Badge:
   ![MCP Security Score](https://img.shields.io/badge/Security-F-red)
```

### HTTP MCP Server

Test remote or local HTTP servers:

```bash
mcp-testbench run http://localhost:8000
```

## Understanding Your Results

### Terminal Output

The terminal shows a summary:
- **CVE Scanner**: Known vulnerabilities
- **Fuzzer**: Crashes from malformed input
- **Prompt Injection**: Injection attack vulnerabilities
- **Security Grade**: A (best) to F (critical issues)

### Detailed JSON Report

```bash
# View full report
cat mcp_testbench_report/mcp_testbench_report.json | python -m json.tool

# Extract just crashes
cat mcp_testbench_report/mcp_testbench_report.json | jq '.plugins.Fuzzer.test_results[] | select(.crash == true)'
```

### Security Badge

Add to your README:

```markdown
![MCP Security](./mcp_testbench_report/SECURITY_BADGE.md)
```

## Common Test Scenarios

### Test Before Deployment

```bash
# Test locally first
mcp-testbench run --stdio "npx your-mcp-server"

# If passes, deploy
# Then test production
mcp-testbench run https://mcp.yourcompany.com/
```

### Test After Fixing Issues

```bash
# Run initial test
mcp-testbench run --stdio "npx your-server" --output ./before

# Fix issues in your code
# ...

# Test again
mcp-testbench run --stdio "npx your-server" --output ./after

# Compare
diff before/mcp_testbench_report.json after/mcp_testbench_report.json
```

### CI/CD Testing

Add to `.github/workflows/security.yml`:

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install MCP Testbench
        run: pip install mcp-testbench

      - name: Run Security Tests
        run: mcp-testbench run --stdio "npx your-mcp-server"

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: mcp_testbench_report/
```

## What Gets Tested?

### CVE Scanner
- CVE-2025-6514 (mcp-remote RCE)
- CVE-2025-49596 (MCP Inspector RCE)
- Server version detection

### Fuzzer (14 tests)
- Empty payloads
- Invalid JSON
- Missing required fields
- Type confusion
- Huge strings (100KB+)
- Deeply nested objects
- Unicode exploits

### Prompt Injection (5 tests)
- Tool override attempts
- Command injection
- Path traversal
- SQL injection
- XSS payloads

## Interpreting Grades

| Grade | Meaning | Action |
|-------|---------|--------|
| **A** | No issues found | ✅ Production ready |
| **B** | Minor issues | 🟡 Review and fix |
| **C** | Moderate risk | 🟠 Fix before production |
| **D** | High risk | 🔴 Do not deploy |
| **F** | Critical issues | ⛔ Fix immediately |

## Real Example: time-mcp

```bash
$ mcp-testbench run --stdio "npx time-mcp"

📋 Fuzzer
  🔴 Crashes: 5/14 (36%)
  🔴 Risk Level: HIGH

🛡️  Security Badge: F
```

**Issues found:**
1. Empty Payload → 500 crash
2. Array Instead of Object → 500 crash
3. Missing Method → 500 crash
4. Huge String → 500 crash
5. Unicode Exploit → 500 crash

[See detailed fixes →](crash-analysis.md)

## Next Steps

- [CLI Reference](cli-reference.md) - All command options
- [Understanding Results](understanding-results.md) - Deep dive into reports
- [Testing Stdio Servers](testing-stdio.md) - Stdio-specific guide
- [Docker Isolation](docker-mode.md) - Maximum security testing

## Need Help?

- [GitHub Issues](https://github.com/ubermorgenland/mcp-testbench/issues)
- [Twitter @ApInference](https://twitter.com/ApInference)
- Email: info@apinference.com
