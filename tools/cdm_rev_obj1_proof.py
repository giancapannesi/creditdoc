#!/usr/bin/env python3
"""OBJ-1 incremental-update proof: DB row update at T+0 → URL serves new HTML at T+≤10s.

Sentinel test on /state/wyoming/. Reverts after measurement.
"""
import os
import sys
import time
import random
import subprocess
import urllib.request
from pathlib import Path

ENV_FILE = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")
WORKER_URL = "https://creditdoc.fancy-glitter-38f7.workers.dev/state/wyoming/"
STATE_CODE = "WY"

def load_env():
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def psql(env, sql, capture=True):
    cmd = ["psql", env["SUPABASE_DB_URL"], "-tAc", sql]
    e = os.environ.copy()
    e["PGPASSWORD"] = env.get("SUPABASE_DB_PASSWORD", "")
    r = subprocess.run(cmd, capture_output=capture, text=True, env=e)
    if r.returncode != 0:
        err = r.stderr if r.stderr else "(no stderr)"
        print(f"psql error: {err}", file=sys.stderr)
        sys.exit(1)
    return (r.stdout or "").strip()

def fetch(url):
    req = urllib.request.Request(url, headers={
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) cdm-rev-obj1-proof/1.0",
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"__ERR__:{e}"

def main():
    env = load_env()
    sentinel = f"OBJ1-TEST-{int(time.time())}-{random.randint(1000,9999)}"
    print(f"[obj1] sentinel = {sentinel}")

    # Capture original
    original = psql(env, f"""
SELECT COALESCE(body_inline->>'consumer_rights_summary', '__NULL__')
FROM states WHERE code = '{STATE_CODE}';
""")
    print(f"[obj1] captured original ({len(original)} chars)")

    # Update with sentinel
    new_val = f"{sentinel} :: {original if original != '__NULL__' else ''}"
    new_val_sql = new_val.replace("'", "''")
    t_update = time.time()
    psql(env, f"""
UPDATE states
SET body_inline = jsonb_set(
  COALESCE(body_inline, '{{}}'::jsonb),
  '{{consumer_rights_summary}}',
  to_jsonb('{new_val_sql}'::text)
)
WHERE code = '{STATE_CODE}';
""", capture=False)
    print(f"[obj1] DB updated at t=0")

    # Poll URL up to 30s
    delta = None
    for i in range(30):
        time.sleep(1)
        url = f"{WORKER_URL}?_cb={random.randint(1,1_000_000)}"
        body = fetch(url)
        if sentinel in body:
            delta = time.time() - t_update
            print(f"[obj1] sentinel SEEN at t={delta:.2f}s (poll #{i+1})")
            break
        else:
            print(f"[obj1] poll #{i+1} t={time.time()-t_update:.1f}s — not yet")

    # Revert
    if original == "__NULL__":
        psql(env, f"""
UPDATE states
SET body_inline = body_inline - 'consumer_rights_summary'
WHERE code = '{STATE_CODE}';
""", capture=False)
    else:
        orig_sql = original.replace("'", "''")
        psql(env, f"""
UPDATE states
SET body_inline = jsonb_set(
  body_inline, '{{consumer_rights_summary}}', to_jsonb('{orig_sql}'::text)
)
WHERE code = '{STATE_CODE}';
""", capture=False)
    print(f"[obj1] reverted to original")

    # Verdict
    if delta is None:
        print(f"\nVERDICT: RED — sentinel NOT seen within 30s")
        sys.exit(2)
    elif delta <= 10:
        print(f"\nVERDICT: GREEN — t={delta:.2f}s ≤ 10s (OBJ-1 hard line)")
        sys.exit(0)
    elif delta <= 30:
        print(f"\nVERDICT: AMBER — t={delta:.2f}s (>10s, ≤30s)")
        sys.exit(1)
    else:
        print(f"\nVERDICT: RED — t={delta:.2f}s > 30s")
        sys.exit(2)

if __name__ == "__main__":
    main()
