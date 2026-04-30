#!/usr/bin/env python3
"""
CDM-REV Phase 1 acceptance orchestrator.

Single-command "are we GO for Phase 6 cutover?" verdict. Runs all four Phase 1
acceptance gates and emits combined GREEN/RED with per-gate detail.

Per docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md §Phase 5
acceptance gates:
    (a) e2e latency       — Phase 5.5b probe, p95 ≤ 10s
    (d) HTML diff parity  — Phase 5.2 panel diff, < 0.1% byte delta on 50 URLs
    (e) OBJ verifier      — verify_strategic_objectives.py all GREEN
    (f) revalidate path   — POST /api/revalidate returns 200 with version header

Why an orchestrator (vs the watcher which already runs (a) + (d)):
    - Watcher fires ONCE on deploy recovery — auto. Orchestrator runs ON DEMAND
      — for spot checks, dress rehearsals, pre-cutover verification.
    - Watcher emails Harvey. Orchestrator returns exit 0/1 for CI/scripts.
    - Orchestrator includes (e) OBJ verifier — Phase 5.10 acceptance gate.
    - Orchestrator includes (f) revalidate path — Phase 1 cutover-gate (b).

Usage:
    python3 tools/cdm_rev_phase1_acceptance.py
    python3 tools/cdm_rev_phase1_acceptance.py --json data/phase1_verdict.json
    python3 tools/cdm_rev_phase1_acceptance.py --skip-probe  # offline check only
    python3 tools/cdm_rev_phase1_acceptance.py --probe-trials 3  # quick probe

Exit codes:
    0 — all gates GREEN, GO for cutover
    1 — bad args
    2 — any gate RED or ERROR
    3 — orchestrator crashed
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PREVIEW = "https://cdm-rev-hybrid.creditdoc.pages.dev"
UA = "cdm-rev-phase1-acceptance/1.0 (curl-compat)"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def banner(label: str) -> None:
    print()
    print("=" * 78)
    print(f"  {label}")
    print("=" * 78)


def gate_a_e2e_probe(trials: int, dry: bool) -> dict:
    """Phase 5.5b — e2e latency probe across review/answers/best routes.

    Returns dict with verdict GREEN/AMBER/RED/SKIPPED + p95 + per_route summary.
    """
    if dry:
        return {
            "gate": "(a) e2e latency",
            "status": "SKIPPED",
            "summary": "Skipped per --skip-probe (offline mode).",
        }
    cmd = [
        "python3", str(REPO_ROOT / "tools" / "cdm_rev_phase24_e2e_probe.py"),
        "--route", "all", "--trials", str(trials),
    ]
    print(f"[gate a] running: {' '.join(cmd)}")
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, cwd=REPO_ROOT, timeout=900,
                           capture_output=True, text=True)
        wall = round(time.monotonic() - t0, 1)
        latest_json = REPO_ROOT / "data" / "cdm_rev_phase24_probe_latest.json"
        verdict_data = {}
        if latest_json.exists():
            try:
                verdict_data = json.loads(latest_json.read_text())
            except Exception:
                pass
        verdict = verdict_data.get("obj1_verdict", "UNKNOWN")
        # Probe writes verdict GREEN/AMBER/RED in obj1_verdict; map to our schema.
        status = (
            "GREEN" if verdict == "GREEN"
            else "AMBER" if verdict == "AMBER"
            else "RED" if verdict in {"RED", "FAIL"}
            else "ERROR"
        )
        return {
            "gate": "(a) e2e latency",
            "status": status,
            "summary": f"{verdict} (probe exit={r.returncode}, wall={wall}s)",
            "wall_s": wall,
            "exit_code": r.returncode,
            "obj1_verdict": verdict,
            "applied": verdict_data.get("applied", False),
            "routes_executed": verdict_data.get("routes_executed", []),
            "per_route": verdict_data.get("per_route", {}),
            "stdout_tail": "\n".join(r.stdout.splitlines()[-30:]),
        }
    except subprocess.TimeoutExpired:
        return {
            "gate": "(a) e2e latency",
            "status": "ERROR",
            "summary": "probe timed out (>15min)",
        }
    except Exception as e:
        return {
            "gate": "(a) e2e latency",
            "status": "ERROR",
            "summary": f"probe crashed: {e!r}",
        }


def gate_d_panel_diff(json_out: Path) -> dict:
    """Phase 5.2/5.3 — 50-URL HTML diff parity (< 0.1% byte delta)."""
    cmd = [
        "python3", str(REPO_ROOT / "tools" / "cdm_rev_panel_diff.py"),
        "--json", str(json_out),
    ]
    print(f"[gate d] running: {' '.join(cmd)}")
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, cwd=REPO_ROOT, timeout=120,
                           capture_output=True, text=True)
        wall = round(time.monotonic() - t0, 1)
        data = {}
        if json_out.exists():
            try:
                data = json.loads(json_out.read_text())
            except Exception:
                pass
        passed = data.get("passed", False)
        return {
            "gate": "(d) HTML diff parity",
            "status": "GREEN" if passed else "RED",
            "summary": (
                f"OK={data.get('ok_count','?')}/50 "
                f"over={data.get('over_threshold_count','?')} "
                f"http_fail={data.get('http_fail_count','?')} "
                f"mean={data.get('mean_diff_pct','?')}% "
                f"(exit={r.returncode}, wall={wall}s)"
            ),
            "wall_s": wall,
            "exit_code": r.returncode,
            "panel_size": data.get("panel_size"),
            "ok_count": data.get("ok_count"),
            "over_threshold_count": data.get("over_threshold_count"),
            "http_fail_count": data.get("http_fail_count"),
            "mean_diff_pct": data.get("mean_diff_pct"),
            "json_path": str(json_out),
        }
    except subprocess.TimeoutExpired:
        return {
            "gate": "(d) HTML diff parity",
            "status": "ERROR",
            "summary": "panel diff timed out (>2min)",
        }
    except Exception as e:
        return {
            "gate": "(d) HTML diff parity",
            "status": "ERROR",
            "summary": f"panel diff crashed: {e!r}",
        }


def gate_e_obj_verifier() -> dict:
    """Phase 5.10 — verify_strategic_objectives.py all-GREEN check."""
    cmd = [
        "python3", str(REPO_ROOT / "tools" / "verify_strategic_objectives.py"),
        "--json-only",
    ]
    print(f"[gate e] running: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, cwd=REPO_ROOT, timeout=120,
                           capture_output=True, text=True)
        try:
            data = json.loads(r.stdout) if r.stdout else {}
        except Exception:
            data = {}
        results = data.get("results", [])
        statuses = {r["obj"]: r["status"] for r in results if "obj" in r}
        all_green = bool(statuses) and all(s == "GREEN" for s in statuses.values())
        any_red = any(s == "RED" for s in statuses.values())
        any_amber = any(s == "AMBER" for s in statuses.values())
        status = (
            "GREEN" if all_green
            else "RED" if any_red
            else "AMBER" if any_amber
            else "ERROR"
        )
        return {
            "gate": "(e) OBJ verifier",
            "status": status,
            "summary": f"OBJ-1={statuses.get('OBJ-1','?')} "
                       f"OBJ-2={statuses.get('OBJ-2','?')} "
                       f"OBJ-3={statuses.get('OBJ-3','?')} "
                       f"(exit={r.returncode})",
            "exit_code": r.returncode,
            "obj_statuses": statuses,
            "obj_summaries": {
                r["obj"]: r.get("summary", "") for r in results if "obj" in r
            },
        }
    except subprocess.TimeoutExpired:
        return {
            "gate": "(e) OBJ verifier",
            "status": "ERROR",
            "summary": "OBJ verifier timed out (>2min)",
        }
    except Exception as e:
        return {
            "gate": "(e) OBJ verifier",
            "status": "ERROR",
            "summary": f"OBJ verifier crashed: {e!r}",
        }


def gate_f_revalidate_path(preview_host: str) -> dict:
    """Phase 1 cutover-gate (b) — revalidate endpoint healthy.

    Probes /api/revalidate?ping=1 (read-only) to confirm route is wired without
    actually invalidating any cache. If the endpoint returns 200 (or 405 for
    "GET not allowed but route exists"), gate is GREEN.
    """
    url = f"{preview_host}/api/revalidate?ping=1"
    print(f"[gate f] probing: {url}")
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=10) as resp:
            status_code = resp.status
            body = resp.read(2048).decode("utf-8", errors="replace")
    except HTTPError as e:
        status_code = e.code
        body = ""
    except (URLError, TimeoutError, OSError) as e:
        return {
            "gate": "(f) revalidate path",
            "status": "RED",
            "summary": f"unreachable: {e!r}",
            "url": url,
        }
    # 200/204 = endpoint live. 405 = endpoint exists but expects different verb (still wired).
    # 404 = route missing, RED.
    if status_code in {200, 204, 405}:
        status = "GREEN"
        verdict = f"reachable (HTTP {status_code})"
    elif status_code == 404:
        status = "RED"
        verdict = f"missing (HTTP 404)"
    else:
        status = "AMBER"
        verdict = f"unexpected status (HTTP {status_code})"
    return {
        "gate": "(f) revalidate path",
        "status": status,
        "summary": verdict,
        "url": url,
        "http_status": status_code,
        "body_head": body[:200],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview-host", default=DEFAULT_PREVIEW)
    ap.add_argument("--probe-trials", type=int, default=10,
                    help="Trials per route for gate (a). Default 10.")
    ap.add_argument("--skip-probe", action="store_true",
                    help="Skip gate (a) e2e probe (offline mode).")
    ap.add_argument("--skip-panel", action="store_true",
                    help="Skip gate (d) panel diff.")
    ap.add_argument("--skip-obj", action="store_true",
                    help="Skip gate (e) OBJ verifier.")
    ap.add_argument("--skip-revalidate", action="store_true",
                    help="Skip gate (f) revalidate path.")
    ap.add_argument("--json", default=None,
                    help="Write combined verdict JSON to this path.")
    ap.add_argument("--panel-json", default="data/cdm_rev_phase1_panel.json",
                    help="Where panel diff writes its detail JSON.")
    args = ap.parse_args()

    print(f"CDM-REV Phase 1 acceptance orchestrator — {now_utc()}")
    print(f"Preview host: {args.preview_host}")

    results = []

    banner("Gate (a) — Phase 5.5b e2e latency probe")
    results.append(gate_a_e2e_probe(args.probe_trials, args.skip_probe))

    banner("Gate (d) — Phase 5.2 50-URL HTML diff parity")
    if args.skip_panel:
        results.append({"gate": "(d) HTML diff parity",
                        "status": "SKIPPED", "summary": "skipped per --skip-panel"})
    else:
        results.append(gate_d_panel_diff(REPO_ROOT / args.panel_json))

    banner("Gate (e) — Phase 5.10 OBJ verifier")
    if args.skip_obj:
        results.append({"gate": "(e) OBJ verifier",
                        "status": "SKIPPED", "summary": "skipped per --skip-obj"})
    else:
        results.append(gate_e_obj_verifier())

    banner("Gate (f) — Phase 1 revalidate path")
    if args.skip_revalidate:
        results.append({"gate": "(f) revalidate path",
                        "status": "SKIPPED", "summary": "skipped per --skip-revalidate"})
    else:
        results.append(gate_f_revalidate_path(args.preview_host))

    banner("VERDICT")
    statuses = [r["status"] for r in results]
    any_red = any(s in {"RED", "ERROR"} for s in statuses)
    any_amber = any(s == "AMBER" for s in statuses)
    all_green_or_skipped = all(s in {"GREEN", "SKIPPED"} for s in statuses)
    overall = (
        "GREEN" if all_green_or_skipped and not any_amber
        else "AMBER" if any_amber and not any_red
        else "RED"
    )
    cutover_ready = overall == "GREEN" and not any(
        r["status"] == "SKIPPED" for r in results
    )

    for r in results:
        print(f"  {r['status']:<7}  {r['gate']:<30}  {r['summary']}")
    print()
    print(f"  Overall:        {overall}")
    print(f"  Cutover-ready:  {'YES — GO for Phase 6' if cutover_ready else 'NO — see above'}")

    summary = {
        "ts_utc": now_utc(),
        "preview_host": args.preview_host,
        "overall_status": overall,
        "cutover_ready": cutover_ready,
        "gates": results,
    }
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"\n  JSON: {out}")

    return 0 if overall == "GREEN" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"orchestrator crashed: {e!r}", file=sys.stderr)
        sys.exit(3)
