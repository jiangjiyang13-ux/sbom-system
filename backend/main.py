from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime, timezone
import time
import json
import os

from scanner import generate_sbom, semgrep_analysis, STORAGE_DIR, count_files
from matcher import match_vulnerabilities
from ai_advisor import get_fix_suggestion

app = FastAPI(title="SBOM Supply-Chain Security System", version="0.6.0")

REPORT_SUFFIX = "_report.json"

class ScanRequest(BaseModel):
    path: str = Field(..., description="Local path or docker:image")

@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}

@app.post("/api/scan")
async def scan(req: ScanRequest):
    start_time = time.time()
    raw_path = req.path.strip()
    is_docker = raw_path.lower().startswith("docker:")
    ts = int(time.time())

    print(f"\n[ENGINE] New Scan Initiated: {raw_path}")

    # 1. Path Check & File Count
    files_scanned = 0
    if not is_docker:
        target_path = Path(raw_path).expanduser().resolve()
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Target path not found: {raw_path}")
        files_scanned = count_files(str(target_path))
        print(f"[ENGINE] Target identified as directory. Files to scan: {files_scanned}")
    else:
        print(f"[ENGINE] Target identified as Docker image.")

    # 2. SBOM Generation (Syft)
    print(f"[ENGINE] Step 1/3: Running Syft...")
    sbom_path, comp_count, sbom_err = generate_sbom(raw_path)
    
    if sbom_err:
        print(f"[ENGINE] Syft Failed: {sbom_err}")
        # We don't raise here, we want to return what we have (or the error in report)

    # 3. Static Analysis (Semgrep)
    static_findings = []
    if not is_docker and not sbom_err:
        print(f"[ENGINE] Step 2/3: Running Semgrep...")
        static_findings = semgrep_analysis(str(Path(raw_path).expanduser().resolve()))
        for f in static_findings:
            f["ai_fix"] = f"### 🛡️ AI FIX\nAvoid dangerous call in `{f['file']}`. Message: {f['message']}"

    # 4. Vulnerabilities (Grype)
    vulns = {"summary": {"critical":0, "high":0, "medium":0, "low":0, "total":0}, "details": []}
    if sbom_path:
        print(f"[ENGINE] Step 3/3: Running Grype...")
        vulns = match_vulnerabilities(sbom_path)
        for v in vulns.get("details", []):
            if v.get("severity") in ("HIGH", "CRITICAL"):
                v["ai_fix"] = get_fix_suggestion(v)

    # 5. Policy Evaluation
    policy_status = "PASS"
    reasons = []
    if vulns["summary"]["critical"] > 0 or vulns["summary"]["high"] > 0:
        policy_status = "FAIL"
        reasons.append(f"Detected {vulns['summary']['critical']} Critical and {vulns['summary']['high']} High CVEs.")
    if any(f["severity"] == "ERROR" for f in static_findings):
        policy_status = "FAIL"
        reasons.append("Semgrep detected critical security code patterns.")

    report = {
        "target": raw_path,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - start_time, 2),
        "policy": {"status": policy_status, "reasons": reasons},
        "scan_info": {
            "files_scanned": files_scanned,
            "component_count": comp_count,
            "sbom_path": sbom_path,
            "error": sbom_err
        },
        "static_analysis": static_findings,
        "vulnerabilities": vulns
    }

    report_file = STORAGE_DIR / f"scan_{ts}{REPORT_SUFFIX}"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[ENGINE] Scan completed in {report['duration_seconds']}s. Status: {policy_status}")
    return report

@app.get("/api/history")
async def list_history():
    reports = []
    for f in sorted(STORAGE_DIR.glob(f"*{REPORT_SUFFIX}"), reverse=True):
        try:
            with open(f) as fp:
                d = json.load(fp)
            reports.append({
                "report_id": f.stem,
                "target": d.get("target"),
                "scanned_at": d.get("scanned_at"),
                "policy_status": d.get("policy", {}).get("status", "UNKNOWN"),
                "critical": d.get("vulnerabilities", {}).get("summary", {}).get("critical", 0),
                "high": d.get("vulnerabilities", {}).get("summary", {}).get("high", 0),
                "total_vulns": d.get("vulnerabilities", {}).get("summary", {}).get("total", 0),
                "component_count": d.get("scan_info", {}).get("component_count", 0),
                "files_scanned": d.get("scan_info", {}).get("files_scanned", 0)
            })
        except: pass
    return {"reports": reports}

@app.get("/api/history/{report_id}")
async def get_report(report_id: str):
    f = STORAGE_DIR / f"{report_id}.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")
    with open(f) as fp:
        return json.load(fp)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
