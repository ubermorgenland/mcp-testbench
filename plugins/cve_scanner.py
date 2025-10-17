"""CVE scanner plugin - checks for known vulnerabilities in MCP servers."""
import httpx
from typing import Dict
from engine import Plugin


# Known MCP CVEs from research
KNOWN_CVES = {
    "CVE-2025-6514": {
        "cvss": 9.6,
        "description": "Critical RCE in mcp-remote",
        "indicators": ["/remote/", "mcp-remote"],
        "severity": "CRITICAL"
    },
    "CVE-2025-49596": {
        "cvss": 9.4,
        "description": "RCE in MCP Inspector",
        "indicators": ["mcp-inspector", "/inspector/"],
        "severity": "CRITICAL"
    }
}


class CVEScanner(Plugin):
    """Scans for known CVEs in MCP servers."""

    async def run(self, client: httpx.AsyncClient) -> Dict:
        """Check for known vulnerability indicators."""
        vulnerabilities_found = []

        try:
            # Check server headers and responses for CVE indicators
            response = await client.get("/")
            response_text = response.text.lower()
            headers = {k.lower(): v.lower() for k, v in response.headers.items()}

            # Check for CVE indicators
            for cve_id, cve_info in KNOWN_CVES.items():
                for indicator in cve_info["indicators"]:
                    if indicator.lower() in response_text or any(indicator.lower() in v for v in headers.values()):
                        vulnerabilities_found.append({
                            "cve_id": cve_id,
                            "cvss": cve_info["cvss"],
                            "description": cve_info["description"],
                            "severity": cve_info["severity"]
                        })
                        break

            # Check for common MCP server identification
            server_header = headers.get("server", "")
            x_powered_by = headers.get("x-powered-by", "")

            return {
                "status": "completed",
                "vulnerabilities_found": len(vulnerabilities_found),
                "vulnerabilities": vulnerabilities_found,
                "server_info": {
                    "server_header": server_header,
                    "x_powered_by": x_powered_by
                },
                "risk_level": "CRITICAL" if vulnerabilities_found else "NONE"
            }

        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "error": "Server did not respond in time"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
