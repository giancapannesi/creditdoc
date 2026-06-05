import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_DIR / "tools"


def load_guardian_module():
    sys.path.insert(0, str(TOOLS_DIR))
    spec = importlib.util.spec_from_file_location(
        "creditdoc_guardian", TOOLS_DIR / "creditdoc_guardian.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeDB:
    def __init__(self, raw_data, public_data, checksum):
        self.public_data = public_data
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE lenders (slug TEXT, data TEXT, checksum TEXT, is_protected INTEGER)"
        )
        self.conn.execute(
            """CREATE TABLE audit_log (
               slug TEXT, table_name TEXT, field_changed TEXT,
               changed_by TEXT, changed_at TEXT, reason TEXT
            )"""
        )
        self.conn.execute(
            "INSERT INTO lenders VALUES (?, ?, ?, 1)",
            ("protected-lender", json.dumps(raw_data), checksum),
        )
        self.conn.commit()

    def get_lender_data(self, slug):
        if slug != "protected-lender":
            return None
        return dict(self.public_data)


class GuardianPublicExportTest(unittest.TestCase):
    def test_protected_healing_does_not_rewrite_public_export_shape(self):
        guardian = load_guardian_module()

        raw_db_data = {
            "slug": "protected-lender",
            "name": "Protected Lender",
            "seo_title": "Protected Lender Review",
            "last_engine_run": "2026-04-03",
        }
        public_export_data = {
            "slug": "protected-lender",
            "name": "Protected Lender",
            "seo_title": "Protected Lender Review",
            "brand_slug": None,
        }

        with tempfile.TemporaryDirectory() as tmp:
            original_lenders_dir = guardian.LENDERS_DIR
            original_log_path = guardian.LOG_PATH
            guardian.LENDERS_DIR = Path(tmp)
            guardian.LOG_PATH = Path(tmp) / "guardian.log"
            try:
                out = guardian.LENDERS_DIR / "protected-lender.json"
                out.write_text(json.dumps(public_export_data, indent=2))

                db = FakeDB(
                    raw_data=raw_db_data,
                    public_data=public_export_data,
                    checksum=guardian._checksum(raw_db_data),
                )

                result = guardian.heal_protected_profiles(db, dry_run=False)

                self.assertEqual(result["healed"], 0)
                self.assertEqual(json.loads(out.read_text()), public_export_data)
            finally:
                guardian.LENDERS_DIR = original_lenders_dir
                guardian.LOG_PATH = original_log_path

    def test_protected_healing_ignores_legacy_operational_shape(self):
        guardian = load_guardian_module()

        raw_db_data = {
            "slug": "protected-lender",
            "name": "Protected Lender",
            "seo_title": "Protected Lender Review",
            "last_engine_run": "2026-04-03",
        }
        public_export_data = {
            "slug": "protected-lender",
            "name": "Protected Lender",
            "seo_title": "Protected Lender Review",
            "brand_slug": None,
        }
        legacy_file_data = {
            "slug": "protected-lender",
            "name": "Protected Lender",
            "seo_title": "Protected Lender Review",
            "last_engine_run": "2026-04-03",
        }

        with tempfile.TemporaryDirectory() as tmp:
            original_lenders_dir = guardian.LENDERS_DIR
            original_log_path = guardian.LOG_PATH
            guardian.LENDERS_DIR = Path(tmp)
            guardian.LOG_PATH = Path(tmp) / "guardian.log"
            try:
                out = guardian.LENDERS_DIR / "protected-lender.json"
                out.write_text(json.dumps(legacy_file_data, indent=2))

                db = FakeDB(
                    raw_data=raw_db_data,
                    public_data=public_export_data,
                    checksum=guardian._checksum(raw_db_data),
                )

                result = guardian.heal_protected_profiles(db, dry_run=False)

                self.assertEqual(result["healed"], 0)
                self.assertEqual(json.loads(out.read_text()), legacy_file_data)
            finally:
                guardian.LENDERS_DIR = original_lenders_dir
                guardian.LOG_PATH = original_log_path


if __name__ == "__main__":
    unittest.main()
