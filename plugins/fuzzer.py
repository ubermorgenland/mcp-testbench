"""Fuzzing engine plugin - tests MCP protocol conformance with malformed inputs."""
import httpx
from typing import Dict, List
import json
from engine import Plugin


# Fuzzing payloads for JSON-RPC protocol testing
FUZZ_PAYLOADS = [
    # Protocol conformance tests
    {"name": "Empty Payload", "payload": "", "content_type": "application/json"},
    {"name": "Invalid JSON", "payload": "{invalid json", "content_type": "application/json"},
    {"name": "Null Payload", "payload": None, "content_type": "application/json"},
    {"name": "Array Instead of Object", "payload": "[]", "content_type": "application/json"},
    {"name": "Missing Method", "payload": '{"jsonrpc": "2.0", "id": 1}', "content_type": "application/json"},
    {"name": "Invalid Method Type", "payload": '{"jsonrpc": "2.0", "method": 123, "id": 1}', "content_type": "application/json"},
    {"name": "Missing JSONRPC Version", "payload": '{"method": "tools/list", "id": 1}', "content_type": "application/json"},
    {"name": "Invalid JSONRPC Version", "payload": '{"jsonrpc": "3.0", "method": "tools/list", "id": 1}', "content_type": "application/json"},

    # Oversized payloads
    {"name": "Huge String", "payload": '{"jsonrpc": "2.0", "method": "test", "params": {"data": "' + 'A' * 100000 + '"}, "id": 1}', "content_type": "application/json"},
    {"name": "Deeply Nested", "payload": '{"a":' * 1000 + '1' + '}' * 1000, "content_type": "application/json"},

    # Special characters
    {"name": "Unicode Exploit", "payload": '{"jsonrpc": "2.0", "method": "\\u0000\\u0001\\u0002", "id": 1}', "content_type": "application/json"},
    {"name": "Null Bytes", "payload": '{"jsonrpc": "2.0", "method": "test\\x00", "id": 1}', "content_type": "application/json"},

    # Type confusion
    {"name": "String ID Instead of Number", "payload": '{"jsonrpc": "2.0", "method": "tools/list", "id": "not_a_number"}', "content_type": "application/json"},
    {"name": "Params as String", "payload": '{"jsonrpc": "2.0", "method": "tools/list", "params": "not_an_object", "id": 1}', "content_type": "application/json"},
]


class Fuzzer(Plugin):
    """Fuzzes MCP server endpoints with malformed inputs."""

    async def run(self, client: httpx.AsyncClient) -> Dict:
        """Run fuzzing tests."""
        test_results = []
        crashes = 0
        timeouts = 0
        unexpected_responses = 0

        for test in FUZZ_PAYLOADS:
            try:
                # Prepare payload
                if test["payload"] is None:
                    data = None
                elif isinstance(test["payload"], str) and test["payload"]:
                    # Try to parse as JSON if it looks like JSON
                    if test["payload"].strip().startswith('{') or test["payload"].strip().startswith('['):
                        try:
                            data = json.loads(test["payload"])
                        except:
                            data = test["payload"]
                    else:
                        data = test["payload"]
                else:
                    data = test["payload"]

                # Send fuzz payload
                response = await client.post(
                    "/",
                    json=data if data != "" else None,
                    content=data if data == "" else None,
                    headers={"Content-Type": test["content_type"]},
                    timeout=3
                )

                # Analyze response
                is_crash = response.status_code == 500
                is_timeout = response.status_code == 504
                is_unexpected = response.status_code not in [200, 400, 404, 405, 500, 504]

                if is_crash:
                    crashes += 1
                if is_timeout:
                    timeouts += 1
                if is_unexpected:
                    unexpected_responses += 1

                test_results.append({
                    "test_name": test["name"],
                    "status_code": response.status_code,
                    "crash": is_crash,
                    "timeout": is_timeout,
                    "unexpected": is_unexpected,
                    "response_size": len(response.content)
                })

            except httpx.TimeoutException:
                timeouts += 1
                test_results.append({
                    "test_name": test["name"],
                    "status": "timeout",
                    "crash": False
                })
            except Exception as e:
                # Connection lost or broken pipe means server crashed
                is_server_crash = "Connection lost" in str(e) or "Broken pipe" in str(e) or "pipe closed" in str(e).lower()
                if is_server_crash:
                    crashes += 1
                test_results.append({
                    "test_name": test["name"],
                    "error": str(e),
                    "crash": is_server_crash
                })

        # Calculate risk
        total_issues = crashes + timeouts + unexpected_responses
        if total_issues > 5:
            risk_level = "HIGH"
        elif total_issues > 2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "status": "completed",
            "tests_run": len(FUZZ_PAYLOADS),
            "crashes": crashes,
            "timeouts": timeouts,
            "unexpected_responses": unexpected_responses,
            "total_issues": total_issues,
            "test_results": test_results,
            "risk_level": risk_level
        }
