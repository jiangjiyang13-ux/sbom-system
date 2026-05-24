import json
import subprocess
import os
from pathlib import Path

def match_vulnerabilities(sbom_path: str) -> dict:
    """Run grype on the generated SBOM and return structured vulnerability details with professional metrics."""
    sbom = Path(sbom_path).resolve()
    if not sbom.exists():
        return {"error": f"SBOM file not found: {sbom_path}"}

    print(f"[Matcher] Starting professional vulnerability scan for {sbom.name}...")
    
    try:
        proc = subprocess.run(
            ["grype", f"sbom:{str(sbom)}", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=300
        )

        if proc.returncode not in [0, 1]:
            return {"error": f"Grype failed (exit {proc.returncode}): {proc.stderr[:500]}"}

        if not proc.stdout.strip():
            return {"error": "Grype returned empty output"}

        data = json.loads(proc.stdout)
        matches = data.get("matches", [])
        vulnerabilities = []
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": len(matches)}

        for match in matches:
            vuln = match.get("vulnerability", {})
            artifact = match.get("artifact", {})
            
            # Extract professional metrics
            severity = vuln.get("severity", "unknown").lower()
            if severity in summary: summary[severity] += 1
            
            # Extract CVSS scoring details if available
            cvss = vuln.get("cvss", [])
            score = 0.0
            vector = "N/A"
            if cvss:
                score = cvss[0].get("metrics", {}).get("baseScore", 0.0)
                vector = cvss[0].get("vector", "N/A")

            vulnerabilities.append({
                "component": artifact.get("name"),
                "version": artifact.get("version"),
                "cve_id": vuln.get("id"),
                "severity": severity.upper(),
                "cvss_score": score,
                "cvss_vector": vector,
                "source": vuln.get("dataSource", "NVD/OSV"),
                "fix_versions": vuln.get("fix", {}).get("versions", []),
                "description": vuln.get("description", "No description available.")
            })

        return {"summary": summary, "details": vulnerabilities}

    except Exception as e:
        return {"error": str(e)}
