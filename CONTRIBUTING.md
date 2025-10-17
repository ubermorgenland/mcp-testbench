# Contributing to MCP Testbench

Thank you for your interest in contributing to MCP Testbench! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- **Clear title** describing the issue
- **Steps to reproduce** the bug
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, MCP server being tested)
- **Logs or screenshots** if applicable

### Suggesting Features

We welcome feature suggestions! Please open an issue with:
- **Use case**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you've thought about

### Contributing Code

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then:
   git clone git@github.com:YOUR_USERNAME/mcp-testbench.git
   cd mcp-testbench
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Make your changes**
   - Write clear, readable code
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   ```bash
   # Test with stdio server
   python cli.py run --stdio "npx time-mcp"

   # Test with HTTP server
   python cli.py run http://localhost:8000

   # Ensure no regressions
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: clear description of changes"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub.

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js (for testing stdio MCP servers)
- Docker (optional, for Docker mode testing)

### Install for Development
```bash
# Clone repository
git clone git@github.com:ubermorgenland/mcp-testbench.git
cd mcp-testbench

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python cli.py run --stdio "npx time-mcp"
```

## Code Style

### Python
- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable names
- Maximum line length: 100 characters
- Use type hints where appropriate

### Example:
```python
async def run_test(client: httpx.AsyncClient) -> dict:
    """Run security test against MCP server.

    Args:
        client: HTTP client for making requests

    Returns:
        Dictionary with test results
    """
    response = await client.get("/")
    return {"status": "completed"}
```

### Documentation
- Add docstrings to all public functions
- Update README if adding new features
- Include examples in docstrings

## Plugin Development

Want to add a new security test? Create a plugin!

### Plugin Structure
```python
# plugins/my_plugin.py
from engine import Plugin
import httpx

class MyPlugin(Plugin):
    """Description of what this plugin tests."""

    async def run(self, client: httpx.AsyncClient) -> dict:
        """Run the security test.

        Args:
            client: HTTP client for requests

        Returns:
            dict: Test results with 'status' and findings
        """
        # Your test logic here
        return {
            "status": "completed",
            "vulnerabilities_found": 0,
            "risk_level": "LOW"
        }
```

### Plugin Guidelines
- One plugin = one security concern
- Return consistent JSON structure
- Include `risk_level`: NONE, LOW, MEDIUM, HIGH, CRITICAL
- Add tests for your plugin
- Document what the plugin checks

## Testing Guidelines

### Manual Testing
```bash
# Test stdio mode
python cli.py run --stdio "npx time-mcp" --verbose

# Test HTTP mode
python cli.py run http://localhost:8000 --verbose

# Test Docker mode (if applicable)
python cli.py run --docker --docker-path ./test-server
```

### What to Test
- ✅ Plugin discovers and runs successfully
- ✅ Handles errors gracefully
- ✅ Generates valid JSON report
- ✅ Security badge is created
- ✅ No crashes on edge cases

## Pull Request Guidelines

### PR Title Format
```
Add: Feature description
Fix: Bug description
Update: Documentation/refactor description
```

### PR Description Should Include
- **What**: What does this PR do?
- **Why**: Why is this change needed?
- **How**: How does it work?
- **Testing**: How did you test this?
- **Screenshots**: If UI changes (for docs/reports)

### Example PR Description
```markdown
## What
Adds rate limiting detection plugin to identify MCP servers without rate limits.

## Why
Rate limiting is a common security concern. This helps developers identify if their server is vulnerable to DoS attacks.

## How
- New plugin: `plugins/rate_limiter.py`
- Sends 100 requests in 1 second
- Checks if any are rejected/throttled
- Reports risk level based on results

## Testing
- Tested against time-mcp (no rate limiting detected - MEDIUM risk)
- Tested against mock server with rate limits (correctly detected - LOW risk)
- All existing tests still pass
```

## Code Review Process

1. Maintainers will review your PR
2. Address feedback with new commits
3. Once approved, PR will be merged
4. You'll be credited in release notes!

## Reporting Security Vulnerabilities

**Do not open public issues for security vulnerabilities.**

Instead, email: **info@apinference.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We'll respond within 48 hours.

## Community Guidelines

### Be Respectful
- Be kind and patient
- Accept constructive criticism
- Focus on what's best for the community

### Be Collaborative
- Help others learn
- Share knowledge
- Credit others' work

### Be Professional
- Use inclusive language
- Keep discussions on-topic
- Respect maintainers' decisions

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/ubermorgenland/mcp-testbench/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/ubermorgenland/mcp-testbench/issues)
- **Twitter**: [@ApInference](https://twitter.com/ApInference)
- **Email**: info@apinference.com

## Areas We Need Help With

### Current Priorities
- [ ] Additional security test plugins
- [ ] Support for more MCP server types
- [ ] Performance improvements for large tests
- [ ] Better error messages
- [ ] More comprehensive documentation
- [ ] Integration with CI/CD platforms beyond GitHub Actions

### Good First Issues
Check issues labeled [`good first issue`](https://github.com/ubermorgenland/mcp-testbench/labels/good%20first%20issue) - these are beginner-friendly!

## Recognition

Contributors will be:
- Listed in release notes
- Credited in the README
- Added to the contributors list on GitHub

Significant contributors may be invited to become maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the project).

---

## Questions?

Don't hesitate to ask! Open a discussion or reach out to the maintainers.

**Thank you for contributing to MCP Testbench!** 🎉

---

**Maintained by**: Ubermorgen Ltd
**Product**: ApInference
**Repository**: https://github.com/ubermorgenland/mcp-testbench
