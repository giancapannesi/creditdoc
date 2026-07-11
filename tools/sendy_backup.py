#!/usr/bin/env python3
"""Back up the local Sendy database and write a small inventory report."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SENDY_CONFIG = Path("/srv/sendy/includes/config.php")
BACKUP_ROOT = Path("/srv/BusinessOps/backups/sendy")
RETENTION_DAYS = 30


def load_config() -> dict[str, str]:
    text = SENDY_CONFIG.read_text()
    config: dict[str, str] = {}
    for key in ("dbHost", "dbUser", "dbPass", "dbName"):
        match = re.search(rf"\${key}\s*=\s*'([^']*)'", text)
        if not match:
            raise RuntimeError(f"{key} not found in {SENDY_CONFIG}")
        config[key] = match.group(1)
    port_match = re.search(r"\$dbPort\s*=\s*(\d+)", text)
    config["dbPort"] = port_match.group(1) if port_match else "3306"
    return config


def run(config: dict[str, str], args: list[str], *, output: Path | None = None) -> None:
    env = os.environ.copy()
    env["MYSQL_PWD"] = config["dbPass"]
    cmd = [
        args[0],
        f"-h{config['dbHost']}",
        f"-P{config['dbPort']}",
        f"-u{config['dbUser']}",
        *args[1:],
    ]
    if output:
        with output.open("w") as fh:
            subprocess.run(cmd, check=True, text=True, stdout=fh, env=env)
    else:
        subprocess.run(cmd, check=True, text=True, env=env)


def cleanup_old_backups() -> None:
    if not BACKUP_ROOT.exists():
        return
    cutoff = datetime.now(timezone.utc).timestamp() - (RETENTION_DAYS * 86400)
    for path in BACKUP_ROOT.iterdir():
        if path.is_dir() and path.stat().st_mtime < cutoff:
            shutil.rmtree(path)


def main() -> int:
    config = load_config()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    backup_dir = BACKUP_ROOT / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    dump_path = backup_dir / "sendy_full.sql"
    inventory_path = backup_dir / "sendy_inventory.tsv"
    checksums_path = backup_dir / "SHA256SUMS"

    run(
        config,
        [
            "mysqldump",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--no-tablespaces",
            config["dbName"],
        ],
        output=dump_path,
    )

    inventory_sql = """
SELECT l.id,l.app,l.name,COUNT(s.id) AS total,
       COALESCE(SUM(s.unsubscribed=0 AND s.bounced=0 AND s.complaint=0),0) AS active,
       COALESCE(SUM(s.unsubscribed=1),0) AS unsubscribed,
       COALESCE(SUM(s.bounced=1),0) AS bounced,
       COALESCE(SUM(s.complaint=1),0) AS complaints
FROM lists l LEFT JOIN subscribers s ON s.list=l.id
GROUP BY l.id,l.app,l.name ORDER BY l.id;
SELECT a.id,a.name,a.list,COUNT(e.id) AS email_count
FROM ares a LEFT JOIN ares_emails e ON e.ares_id=a.id
GROUP BY a.id,a.name,a.list ORDER BY a.id;
SELECT id,app_name,from_email,reply_to,smtp_host,smtp_port,smtp_ssl,
       CASE WHEN smtp_username='' THEN 'missing' ELSE 'present' END AS smtp_user,
       CASE WHEN smtp_password='' THEN 'missing' ELSE 'present' END AS smtp_pass
FROM apps ORDER BY id;
"""
    run(config, ["mysql", config["dbName"], "-e", inventory_sql], output=inventory_path)

    checksum = subprocess.run(
        ["sha256sum", str(dump_path), str(inventory_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    checksums_path.write_text(checksum.stdout)

    backup_dir.chmod(0o700)
    for path in backup_dir.iterdir():
        path.chmod(0o600)
    cleanup_old_backups()

    print(backup_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
