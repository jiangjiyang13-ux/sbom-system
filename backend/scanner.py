import json
import os
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
VENV_BIN = Path(__file__).resolve().parent / "venv" / "bin"
SEMGREP_BIN = str(VENV_BIN / "semgrep")

@dataclass
class ScanResult:
    sbom_file: str | None = None
    sbom_component_count: int = 0
    sbom_error: str | None = None
    findings: list[dict] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration_ms: int = 0

def count_files(target_path: str) -> int:
    """Count actual files in a directory."""
    path = Path(target_path).resolve()
    if path.is_file(): return 1
    if not path.is_dir(): return 0
    return sum(1 for _ in path.rglob("*") if _.is_file())

def generate_sbom(target_path: str) -> tuple[str | None, int, str | None]:
    """Invoke syft binary to generate real CycloneDX SBOM."""
    target = Path(target_path).resolve()
    # Handle Docker vs Dir
    syft_target = target_path if target_path.startswith("docker:") else f"dir:{target}"
    
    if not target_path.startswith("docker:") and not target.exists():
        return None, 0, f"PATH_NOT_FOUND: {target}"

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    out_file = STORAGE_DIR / f"sbom_{ts}.json"

    print(f"[Scanner] Executing: syft {syft_target} -o cyclonedx-json")
    try:
        proc = subprocess.run(
            ["syft", syft_target, "-o", "cyclonedx-json", "--file", str(out_file)],
            capture_output=True, text=True, timeout=180,
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or f"Exit Code {proc.returncode}"
            return None, 0, f"SYFT_EXEC_ERR: {err[:500]}"
        
        if not out_file.exists():
            return None, 0, "SYFT_OUTPUT_MISSING"

        with open(out_file) as f:
            data = json.load(f)
        return str(out_file), len(data.get("components", [])), None
    except subprocess.TimeoutExpired:
        return None, 0, "SYFT_TIMEOUT"
    except Exception as e:
        return None, 0, f"SYFT_EXCEPTION: {str(e)}"

def semgrep_analysis(target_path: str) -> list[dict]:
    """Perform static analysis using Semgrep binary."""
    target = Path(target_path).resolve()
    if not target.exists():
        return []

    print(f"[Scanner] Executing: {SEMGREP_BIN} scan --config p/security-audit on {target}")
    try:
        proc = subprocess.run(
            [SEMGREP_BIN, "scan", "--config", "p/security-audit", "--json", str(target)],
            capture_output=True, text=True, timeout=300
        )
        
        # Semgrep returns 1 if findings found, that's OK
        if proc.returncode not in [0, 1]:
            print(f"[Scanner] Semgrep Error: {proc.stderr[:200]}")
            return []

        data = json.loads(proc.stdout)
        findings = []
        for result in data.get("results", []):
            findings.append({
                "file": result.get("path"),
                "line": result.get("start", {}).get("line"),
                "rule_id": result.get("check_id"),
                "severity": result.get("extra", {}).get("severity"),
                "message": result.get("extra", {}).get("message"),
                "content": result.get("extra", {}).get("lines", "").strip()[:200]
            })
        return findings
    except Exception as e:
        print(f"[Scanner] Semgrep Analysis Failed: {e}")
        return []
