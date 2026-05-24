import copy
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_advisor import get_fix_suggestion
from matcher import match_vulnerabilities
from scanner import STORAGE_DIR, count_files, generate_sbom, semgrep_analysis

app = FastAPI(title="SBOM Supply-Chain Security System", version="0.7.0")

REPORT_SUFFIX = "_report.json"
SCAN_JOBS: dict[str, dict[str, Any]] = {}
SCAN_JOBS_LOCK = threading.Lock()
SCAN_PHASES = [
    ("SBOM", "SBOM Asset Extraction"),
    ("SAST", "SAST Source Audit"),
    ("CVE", "CVE Vulnerability Matching"),
    ("REPORT", "Report Consolidation"),
]
STAGE_PROGRESS = {
    "pending": 6,
    "running": 62,
    "completed": 100,
    "failed": 100,
    "skipped": 100,
}


class ScanRequest(BaseModel):
    path: str = Field(..., description="Local path or docker:image")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_job_stages() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": label,
            "status": "pending",
            "percent": STAGE_PROGRESS["pending"],
            "message": "",
        }
        for key, label in SCAN_PHASES
    ]


def create_scan_job(target: str) -> dict[str, Any]:
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    now = utc_now_iso()
    return {
        "job_id": job_id,
        "target": target,
        "status": "queued",
        "phase": "QUEUED",
        "phase_index": -1,
        "percent": 0,
        "message": "Scan job queued.",
        "error": None,
        "created_at": now,
        "started_at": None,
        "updated_at": now,
        "finished_at": None,
        "report_id": None,
        "report": None,
        "logs": [f"[{now}] QUEUED {target}"],
        "stages": build_job_stages(),
    }


def snapshot_job(job: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(job)


def append_job_log(job: dict[str, Any], message: str) -> None:
    timestamp = utc_now_iso()
    job["updated_at"] = timestamp
    job["logs"].append(f"[{timestamp}] {message}")
    job["logs"] = job["logs"][-16:]


def recalculate_job_percent(job: dict[str, Any]) -> None:
    if not job["stages"]:
        job["percent"] = 0
        return
    total = sum(stage["percent"] for stage in job["stages"])
    job["percent"] = round(total / len(job["stages"]))


def update_job_stage(
    job: dict[str, Any],
    stage_key: str,
    status: str,
    message: str,
    *,
    job_status: str = "running",
) -> None:
    for index, stage in enumerate(job["stages"]):
        if stage["key"] == stage_key:
            stage["status"] = status
            stage["percent"] = STAGE_PROGRESS[status]
            stage["message"] = message
            job["phase"] = stage_key
            job["phase_index"] = index
            job["status"] = job_status
            job["message"] = message
            job["updated_at"] = utc_now_iso()
            recalculate_job_percent(job)
            return
    raise KeyError(f"Unknown stage key: {stage_key}")


def set_job_failed(job: dict[str, Any], message: str) -> None:
    job["status"] = "failed"
    job["error"] = message
    job["message"] = message
    job["finished_at"] = utc_now_iso()
    job["updated_at"] = job["finished_at"]
    append_job_log(job, f"FAILED {message}")


def build_report(
    raw_path: str,
    start_time: float,
    files_scanned: int,
    comp_count: int,
    sbom_path: str | None,
    sbom_err: str | None,
    static_findings: list[dict[str, Any]],
    vulns: dict[str, Any],
) -> dict[str, Any]:
    policy_status = "PASS"
    reasons = []
    if vulns["summary"]["critical"] > 0 or vulns["summary"]["high"] > 0:
        policy_status = "FAIL"
        reasons.append(
            f"Detected {vulns['summary']['critical']} Critical and {vulns['summary']['high']} High CVEs."
        )
    if any(f.get("severity") == "ERROR" for f in static_findings):
        policy_status = "FAIL"
        reasons.append("Semgrep detected critical security code patterns.")

    return {
        "target": raw_path,
        "scanned_at": utc_now_iso(),
        "duration_seconds": round(time.time() - start_time, 2),
        "policy": {"status": policy_status, "reasons": reasons},
        "scan_info": {
            "files_scanned": files_scanned,
            "component_count": comp_count,
            "sbom_path": sbom_path,
            "error": sbom_err,
        },
        "static_analysis": static_findings,
        "vulnerabilities": vulns,
    }


def persist_report(report: dict[str, Any]) -> str:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    report_id = f"scan_{int(time.time())}"
    report_file = STORAGE_DIR / f"{report_id}{REPORT_SUFFIX}"
    with open(report_file, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)
    return report_file.stem


def execute_scan_pipeline(raw_path: str, job: dict[str, Any] | None = None) -> tuple[dict[str, Any], str]:
    start_time = time.time()
    target = raw_path.strip()
    is_docker = target.lower().startswith("docker:")
    files_scanned = 0
    comp_count = 0
    sbom_path = None
    sbom_err = None
    static_findings: list[dict[str, Any]] = []
    vulns = {"summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}, "details": []}

    print(f"\n[ENGINE] New Scan Initiated: {target}")

    if job is not None:
        job["status"] = "running"
        job["started_at"] = utc_now_iso()
        job["updated_at"] = job["started_at"]
        job["message"] = "Validating scan target."
        append_job_log(job, f"VALIDATE {target}")

    if not is_docker:
        target_path = Path(target).expanduser().resolve()
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Target path not found: {target}")
        files_scanned = count_files(str(target_path))
        print(f"[ENGINE] Target identified as directory. Files to scan: {files_scanned}")
        if job is not None:
            append_job_log(job, f"FILES {files_scanned}")
    else:
        print("[ENGINE] Target identified as Docker image.")
        if job is not None:
            append_job_log(job, "DOCKER target detected")

    print("[ENGINE] Step 1/4: Running Syft...")
    if job is not None:
        update_job_stage(job, "SBOM", "running", "Running Syft dependency extraction.")
        append_job_log(job, "SBOM Running Syft")
    sbom_path, comp_count, sbom_err = generate_sbom(target)
    if sbom_err:
        print(f"[ENGINE] Syft Failed: {sbom_err}")
        if job is not None:
            update_job_stage(job, "SBOM", "failed", sbom_err)
            append_job_log(job, f"SBOM Failed {sbom_err}")
    else:
        if job is not None:
            update_job_stage(job, "SBOM", "completed", f"Captured {comp_count} components.")
            append_job_log(job, f"SBOM Completed {comp_count} components")

    if not is_docker and not sbom_err:
        print("[ENGINE] Step 2/4: Running Semgrep...")
        if job is not None:
            update_job_stage(job, "SAST", "running", "Running Semgrep source audit.")
            append_job_log(job, "SAST Running Semgrep")
        static_findings = semgrep_analysis(str(Path(target).expanduser().resolve()))
        for finding in static_findings:
            finding["ai_fix"] = (
                f"### 🛠️ AI FIX\nAvoid dangerous call in `{finding['file']}`. "
                f"Message: {finding['message']}"
            )
        if job is not None:
            update_job_stage(job, "SAST", "completed", f"Found {len(static_findings)} source findings.")
            append_job_log(job, f"SAST Completed {len(static_findings)} findings")
    else:
        skip_message = "Skipped for docker target." if is_docker else "Skipped because SBOM failed."
        if job is not None:
            update_job_stage(job, "SAST", "skipped", skip_message)
            append_job_log(job, f"SAST {skip_message}")

    if sbom_path:
        print("[ENGINE] Step 3/4: Running Grype...")
        if job is not None:
            update_job_stage(job, "CVE", "running", "Matching vulnerabilities with Grype.")
            append_job_log(job, "CVE Running Grype")
        vulns = match_vulnerabilities(sbom_path)
        for vuln in vulns.get("details", []):
            if vuln.get("severity") in ("HIGH", "CRITICAL"):
                vuln["ai_fix"] = get_fix_suggestion(vuln)
        if job is not None:
            total_vulns = vulns.get("summary", {}).get("total", 0)
            update_job_stage(job, "CVE", "completed", f"Matched {total_vulns} vulnerabilities.")
            append_job_log(job, f"CVE Completed {total_vulns} matches")
    else:
        if job is not None:
            update_job_stage(job, "CVE", "skipped", "Skipped because no SBOM artifact was produced.")
            append_job_log(job, "CVE Skipped because no SBOM was produced")

    print("[ENGINE] Step 4/4: Consolidating report...")
    if job is not None:
        update_job_stage(job, "REPORT", "running", "Evaluating policy and writing report.")
        append_job_log(job, "REPORT Writing final report")

    report = build_report(
        target,
        start_time,
        files_scanned,
        comp_count,
        sbom_path,
        sbom_err,
        static_findings,
        vulns,
    )
    report_id = persist_report(report)

    if job is not None:
        update_job_stage(job, "REPORT", "completed", f"Report {report_id} generated.", job_status="completed")
        job["status"] = "completed"
        job["report_id"] = report_id
        job["report"] = report
        job["finished_at"] = utc_now_iso()
        job["updated_at"] = job["finished_at"]
        append_job_log(job, f"COMPLETE {report_id}")

    print(f"[ENGINE] Scan completed in {report['duration_seconds']}s. Status: {report['policy']['status']}")
    return report, report_id


def run_scan_job(job_id: str, raw_path: str) -> None:
    with SCAN_JOBS_LOCK:
        job = SCAN_JOBS[job_id]
    try:
        execute_scan_pipeline(raw_path, job=job)
    except HTTPException as exc:
        set_job_failed(job, str(exc.detail))
    except Exception as exc:  # pragma: no cover
        set_job_failed(job, str(exc))


def get_job_or_404(job_id: str) -> dict[str, Any]:
    with SCAN_JOBS_LOCK:
        job = SCAN_JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Scan job not found: {job_id}")
        return snapshot_job(job)


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}


@app.post("/api/scan")
async def scan(req: ScanRequest):
    report, _report_id = execute_scan_pipeline(req.path)
    return report


@app.post("/api/scan-jobs")
async def create_scan(req: ScanRequest):
    job = create_scan_job(req.path.strip())
    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job["job_id"]] = job
    worker = threading.Thread(target=run_scan_job, args=(job["job_id"], req.path), daemon=True)
    worker.start()
    return get_job_or_404(job["job_id"])


@app.get("/api/scan-jobs/{job_id}")
async def get_scan_job(job_id: str):
    return get_job_or_404(job_id)


@app.get("/api/history")
async def list_history():
    reports = []
    for report_file in sorted(STORAGE_DIR.glob(f"*{REPORT_SUFFIX}"), reverse=True):
        try:
            with open(report_file, encoding="utf-8") as fp:
                data = json.load(fp)
            reports.append(
                {
                    "report_id": report_file.stem,
                    "target": data.get("target"),
                    "scanned_at": data.get("scanned_at"),
                    "policy_status": data.get("policy", {}).get("status", "UNKNOWN"),
                    "critical": data.get("vulnerabilities", {}).get("summary", {}).get("critical", 0),
                    "high": data.get("vulnerabilities", {}).get("summary", {}).get("high", 0),
                    "total_vulns": data.get("vulnerabilities", {}).get("summary", {}).get("total", 0),
                    "component_count": data.get("scan_info", {}).get("component_count", 0),
                    "files_scanned": data.get("scan_info", {}).get("files_scanned", 0),
                }
            )
        except Exception:
            pass
    return {"reports": reports}


@app.get("/api/history/{report_id}")
async def get_report(report_id: str):
    report_file = STORAGE_DIR / f"{report_id}.json"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")
    with open(report_file, encoding="utf-8") as fp:
        return json.load(fp)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
