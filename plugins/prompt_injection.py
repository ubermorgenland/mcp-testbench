"""Prompt injection test plugin - tests for tool poisoning vulnerabilities."""
import httpx
from typing import Dict, List
from engine import Plugin


# Common prompt injection patterns for MCP testing
INJECTION_PAYLOADS = [
    # Tool poisoning attacks
    {
        "name": "Tool Override",
        "payload": '{"method": "tools/list", "params": {"__proto__": {"malicious": true}}}',
        "description": "Attempts to override tool definitions"
    },
    {
        "name": "Command Injection",
        "payload": '{"method": "tools/call", "params": {"name": "exec", "arguments": {"command": "; cat /etc/passwd"}}}',
        "description": "Tests for command injection in tool execution"
    },
    {
        "name": "Path Traversal",
        "payload": '{"method": "resources/read", "params": {"uri": "file://../../etc/passwd"}}',
        "description": "Tests for path traversal in resource access"
    },
    {
        "name": "SQL Injection",
        "payload": '{"method": "tools/call", "params": {"arguments": {"query": "SELECT * FROM users WHERE id=1 OR 1=1--"}}}',
        "description": "Tests for SQL injection vulnerabilities"
    },
    {
        "name": "XSS Payload",
        "payload": '{"method": "prompts/get", "params": {"name": "<script>alert(\'XSS\')</script>"}}',
        "description": "Tests for XSS vulnerabilities in prompt handling"
    }
]


class PromptInjection(Plugin):
    """Tests MCP server for prompt injection vulnerabilities."""

    async def run(self, client: httpx.AsyncClient) -> Dict:
        """Run prompt injection tests."""
        test_results = []
        vulnerabilities = 0

        for test in INJECTION_PAYLOADS:
            try:
                # Send injection payload
                response = await client.post(
                    "/",
                    json=test["payload"],
                    timeout=5
                )

                # Check for vulnerability indicators
                vulnerable = False
                indicators = []

                # Check for error messages that might indicate successful injection
                if response.status_code == 500:
                    indicators.append("Server error triggered")
                    vulnerable = True

                # Check response for sensitive data
                response_text = response.text.lower()
                if any(marker in response_text for marker in ["root:", "/etc/passwd", "syntax error", "sql"]):
                    indicators.append("Sensitive data or error leaked")
                    vulnerable = True

                # Check if payload was executed (status 200 might mean it was processed)
                if response.status_code == 200 and len(response.text) > 0:
                    indicators.append("Payload may have been processed")

                test_results.append({
                    "test_name": test["name"],
                    "description": test["description"],
                    "vulnerable": vulnerable,
                    "status_code": response.status_code,
                    "indicators": indicators
                })

                if vulnerable:
                    vulnerabilities += 1

            except httpx.TimeoutException:
                test_results.append({
                    "test_name": test["name"],
                    "description": test["description"],
                    "status": "timeout",
                    "vulnerable": False
                })
            except Exception as e:
                test_results.append({
                    "test_name": test["name"],
                    "description": test["description"],
                    "error": str(e),
                    "vulnerable": False
                })

        return {
            "status": "completed",
            "tests_run": len(INJECTION_PAYLOADS),
            "vulnerabilities_found": vulnerabilities,
            "test_results": test_results,
            "risk_level": "HIGH" if vulnerabilities > 2 else "MEDIUM" if vulnerabilities > 0 else "LOW"
        }
