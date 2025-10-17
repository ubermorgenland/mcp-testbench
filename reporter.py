import json
import os
from pathlib import Path

SHIELDS_URL = "https://img.shields.io/badge/Security-{score}-{color}"

def compute_score(results: dict) -> str:
    """Compute security score based on test results.

    Scoring logic:
    - F: Critical CVEs found (CVSS >= 9.0)
    - D: High risk vulnerabilities or multiple plugin errors
    - C: Medium risk issues or crashes detected
    - B: Low risk, minor issues only
    - A: No issues found, all tests passed
    """
    score = 100  # Start with perfect score

    for plugin_res in results.get("plugins", {}).values():
        # Plugin execution errors
        if plugin_res.get("error"):
            score -= 20
            continue

        # CVE Scanner results
        if "vulnerabilities_found" in plugin_res:
            vuln_count = plugin_res.get("vulnerabilities_found", 0)
            if vuln_count > 0:
                # Check for critical CVEs
                for vuln in plugin_res.get("vulnerabilities", []):
                    if vuln.get("cvss", 0) >= 9.0:
                        return "F"  # Critical CVE = instant fail
                score -= vuln_count * 15

        # Fuzzer results
        if "crashes" in plugin_res:
            crashes = plugin_res.get("crashes", 0)
            timeouts = plugin_res.get("timeouts", 0)
            score -= crashes * 10
            score -= timeouts * 5

        # Risk level penalties
        risk_level = plugin_res.get("risk_level", "NONE")
        risk_penalties = {
            "CRITICAL": 30,
            "HIGH": 20,
            "MEDIUM": 10,
            "LOW": 5,
            "NONE": 0
        }
        score -= risk_penalties.get(risk_level, 0)

    # Convert score to letter grade
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"

def color_for_score(score: str) -> str:
    return {
        "A": "brightgreen",
        "B": "green",
        "C": "yellow",
        "D": "orange",
        "F": "red",
    }.get(score, "lightgrey")

def write_report(results: dict, out_dir: str = ".") -> Path:
    """Write a JSON report and a markdown badge.

    Returns the path to ``SECURITY_BADGE.md``.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    json_file = out_path / "mcp_testbench_report.json"
    json_file.write_text(json.dumps(results, indent=2))
    score = compute_score(results)
    color = color_for_score(score)
    badge_md = f"![MCP Security Score]({SHIELDS_URL.format(score=score, color=color)})"
    badge_file = out_path / "SECURITY_BADGE.md"
    badge_file.write_text(badge_md)
    return badge_file
