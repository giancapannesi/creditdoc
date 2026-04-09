#!/usr/bin/env python3
"""
CreditDoc Database API — Single source of truth for all CreditDoc data.

ALL scripts that modify CreditDoc data MUST use this module.
Direct JSON file writes are forbidden after migration.

Usage:
    from creditdoc_db import CreditDocDB

    db = CreditDocDB()

    # Read
    lender = db.get_lender('credit-saint')
    lenders = db.get_lenders_by_category('credit-repair')
    blog = db.get_blog_post('how-to-fix-credit')

    # Write (auto-logged to audit_log)
    db.update_lender('credit-saint', {'cfpb_data': {...}}, updated_by='cfpb_enricher')
    db.update_lender_status('some-lender', 'ready_for_index', updated_by='engine')
    db.add_blog_post({...}, updated_by='blog_generator')

    # Export changed data to JSON files for Astro build
    changed = db.export_changed_lenders()
    db.export_all_content()

    # Protection
    db.update_lender('credit-saint', {...}, updated_by='engine')
    # → raises ProtectedProfileError (credit-saint is protected)
    db.update_lender('credit-saint', {...}, updated_by='founder')
    # → works (founder override)

CLI:
    python3 tools/creditdoc_db.py stats
    python3 tools/creditdoc_db.py get <slug>
    python3 tools/creditdoc_db.py audit <slug>
    python3 tools/creditdoc_db.py export-changed
    python3 tools/creditdoc_db.py export-all
    python3 tools/creditdoc_db.py changed-since <ISO-timestamp>
"""

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


# ─── Paths ───────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "tools" else SCRIPT_DIR
DB_PATH = PROJECT_DIR / "data" / "creditdoc.db"
LENDERS_DIR = PROJECT_DIR / "src" / "content" / "lenders"
CONTENT_DIR = PROJECT_DIR / "src" / "content"
LOGOS_DIR = PROJECT_DIR / "public" / "logos"


# ─── Persistence Rules ──────────────────────────────────────────────
# PERSISTENT FIELDS — editorial content that must NEVER be lost or silently
# overwritten by automation. Three levels of protection:
#
#   1. SET (empty → value): Allowed for any script. Adding new content is fine.
#   2. REPLACE (value → different value): Requires force=True OR updated_by='founder'.
#      This prevents the engine from silently overwriting good content.
#   3. WIPE (value → empty/null): ALWAYS BLOCKED except updated_by='founder'.
#      Nothing good comes from wiping editorial content.
#
# How to update a persistent field legitimately:
#   a) Founder:      db.update_lender(slug, {...}, updated_by='founder')
#   b) Script (approved): db.update_lender(slug, {...}, updated_by='X', force=True)
#   c) Script (default): Only SET works. Replace/wipe is blocked silently.
#
# These are the fields that drive SEO and affiliate revenue. Losing them = losing
# the work that went into them.
PERSISTENT_FIELDS = {
    # Editorial content
    "description_short",
    "description_long",
    "meta_description",
    "diagnosis",
    "typical_results_timeline",
    # Lists (internal linking lives here — money keywords)
    "pros",
    "cons",
    "best_for",
    "services",
    "similar_lenders",
    # Ratings
    "rating_breakdown",
    # Pricing (hard-researched data)
    "pricing",
    # Logos — once found, persist forever
    "logo_url",
    # Company data (once verified, don't lose it)
    "company_info",
    # Affiliate monetization
    "affiliate_url",
    "affiliate_program",
}

# TRANSIENT FIELDS — can be updated freely by any script.
# These track state, not content.
TRANSIENT_FIELDS = {
    "last_updated",
    "last_engine_run",
    "processing_status",
    "enrichment_attempts",
    "has_been_enriched",
    "quality_score",
    "review_status",
    "no_index",
    "data_source",
    "website_needs_review",
    "qc_passed_at",
    # Location data — can be updated if improved
    "website_url",
    "website",
    "phone",
    "address",
    "contact",
    "google_rating",
    "google_reviews_count",
    "states_served",
    "cities_served",
    # Additive data (never removed, but can grow)
    "cfpb_data",
    "bbb_data",
    "rating",  # derived from rating_breakdown, can recalculate
}


# ─── Exceptions ──────────────────────────────────────────────────────
class ProtectedProfileError(Exception):
    """Raised when a non-founder tries to modify a protected profile."""
    pass


class PersistentFieldError(Exception):
    """Raised when a non-founder tries to overwrite a persistent field."""
    pass


class ProfileNotFoundError(Exception):
    """Raised when a slug doesn't exist in the database."""
    pass


def _is_empty(value):
    """Check if a field value is considered 'empty' (safe to set)."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


# ─── Helpers ─────────────────────────────────────────────────────────
def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _checksum(data):
    """Stable JSON checksum — sorted keys, compact separators."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── Main API ────────────────────────────────────────────────────────
class CreditDocDB:
    """Single interface for all CreditDoc data operations."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}. Run migrate first.")
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ═══════════════════════════════════════════════════════════════
    # LENDER READS
    # ═══════════════════════════════════════════════════════════════

    def get_lender(self, slug):
        """Get a single lender by slug. Returns dict with data + metadata."""
        row = self.conn.execute(
            """SELECT slug, data, category, processing_status, is_protected,
                      is_enriched, quality_score, logo_path, website_url,
                      checksum, created_at, updated_at, updated_by, exported_at
               FROM lenders WHERE slug = ?""",
            (slug,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_lender(row)

    def get_lender_data(self, slug):
        """Get just the JSON data for a lender (what goes in the file)."""
        row = self.conn.execute("SELECT data FROM lenders WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return None
        return json.loads(row["data"])

    def lender_exists(self, slug):
        """Check if a lender exists in the database."""
        row = self.conn.execute("SELECT 1 FROM lenders WHERE slug = ?", (slug,)).fetchone()
        return row is not None

    def is_protected(self, slug):
        """Check if a lender is founder-protected."""
        row = self.conn.execute(
            "SELECT is_protected FROM lenders WHERE slug = ?", (slug,)
        ).fetchone()
        return bool(row and row["is_protected"])

    def get_lenders_by_category(self, category, status=None):
        """Get all lenders in a category, optionally filtered by status."""
        if status:
            rows = self.conn.execute(
                "SELECT slug, data, category, processing_status, is_protected, is_enriched "
                "FROM lenders WHERE category = ? AND processing_status = ?",
                (category, status),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT slug, data, category, processing_status, is_protected, is_enriched "
                "FROM lenders WHERE category = ?",
                (category,),
            ).fetchall()
        return [{"slug": r["slug"], "data": json.loads(r["data"]),
                 "status": r["processing_status"], "protected": bool(r["is_protected"])}
                for r in rows]

    def get_lenders_by_status(self, status, limit=None):
        """Get lenders by processing status."""
        sql = "SELECT slug, category, is_enriched, quality_score FROM lenders WHERE processing_status = ?"
        params = [status]
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def count_lenders(self, status=None, category=None):
        """Count lenders, optionally filtered."""
        sql = "SELECT COUNT(*) as cnt FROM lenders WHERE 1=1"
        params = []
        if status:
            sql += " AND processing_status = ?"
            params.append(status)
        if category:
            sql += " AND category = ?"
            params.append(category)
        return self.conn.execute(sql, params).fetchone()["cnt"]

    def get_stats(self):
        """Get full database statistics."""
        stats = {}

        # Lender counts
        stats["total_lenders"] = self.conn.execute("SELECT COUNT(*) FROM lenders").fetchone()[0]
        stats["protected"] = self.conn.execute("SELECT COUNT(*) FROM lenders WHERE is_protected=1").fetchone()[0]
        stats["enriched"] = self.conn.execute("SELECT COUNT(*) FROM lenders WHERE is_enriched=1").fetchone()[0]

        # By status
        stats["by_status"] = {}
        for row in self.conn.execute(
            "SELECT processing_status, COUNT(*) as cnt FROM lenders GROUP BY processing_status ORDER BY cnt DESC"
        ).fetchall():
            stats["by_status"][row["processing_status"]] = row["cnt"]

        # By category (top 10)
        stats["by_category"] = {}
        for row in self.conn.execute(
            "SELECT category, COUNT(*) as cnt FROM lenders GROUP BY category ORDER BY cnt DESC LIMIT 15"
        ).fetchall():
            stats["by_category"][row["category"]] = row["cnt"]

        # Content counts
        for table in ["blog_posts", "comparisons", "wellness_guides", "listicles", "categories"]:
            stats[table] = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        # Logo count
        stats["logos"] = self.conn.execute("SELECT COUNT(*) FROM logos WHERE status='fetched'").fetchone()[0]

        # Audit log count
        stats["audit_entries"] = self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        # DB size
        stats["db_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 1)

        return stats

    # ═══════════════════════════════════════════════════════════════
    # LENDER WRITES
    # ═══════════════════════════════════════════════════════════════

    def update_lender(self, slug, fields: dict, updated_by: str,
                      reason: str = None, force: bool = False):
        """
        Update specific fields of a lender's data JSON.
        Logs every changed field to audit_log.

        Protection rules:
            1. Protected profiles (is_protected=1) reject writes unless updated_by='founder'.
            2. Persistent fields (descriptions, logos, pricing, etc.) can be SET when empty,
               but cannot be WIPED or REPLACED except:
               - updated_by='founder' (always allowed)
               - force=True (explicit opt-in for legitimate improvements)

        Args:
            slug: Lender slug
            fields: Dict of field_name → new_value to merge into data JSON
            updated_by: Who is making this change (e.g. 'engine', 'cfpb', 'founder')
            reason: Optional reason for the change
            force: If True, allows overwriting persistent fields (legitimate improvements).
                   Founder can always override; scripts must declare intent via force=True.

        Returns:
            dict: {
                'changed': int (fields actually changed),
                'blocked_wipe': list (fields that would have been wiped),
                'blocked_replace': list (fields that would have been overwritten),
                'unchanged': int (fields already at desired value)
            }
        """
        lender = self.get_lender(slug)
        if not lender:
            raise ProfileNotFoundError(f"Lender '{slug}' not found in database")

        is_founder = updated_by == "founder"

        # Protected profile check
        if lender["is_protected"] and not is_founder:
            raise ProtectedProfileError(
                f"'{slug}' is founder-protected. Only updated_by='founder' can modify it."
            )

        data = lender["data"]
        ts = _now()
        changes = 0
        blocked_wipe = []
        blocked_replace = []
        unchanged = 0

        for field, new_value in fields.items():
            old_value = data.get(field)

            # Skip if value hasn't actually changed
            if json.dumps(old_value, sort_keys=True) == json.dumps(new_value, sort_keys=True):
                unchanged += 1
                continue

            # ─── PERSISTENT FIELD PROTECTION ───────────────────────
            if field in PERSISTENT_FIELDS and not is_founder:
                old_is_empty = _is_empty(old_value)
                new_is_empty = _is_empty(new_value)

                # RULE 1: Never wipe a populated persistent field (even with force=True)
                # Only the founder can explicitly empty a persistent field.
                if not old_is_empty and new_is_empty:
                    blocked_wipe.append(field)
                    # Log the blocked attempt
                    self.conn.execute(
                        """INSERT INTO audit_log
                           (slug, table_name, field_changed, old_value, new_value,
                            changed_by, changed_at, reason)
                           VALUES (?, 'lenders', ?, ?, ?, ?, ?, ?)""",
                        (
                            slug,
                            f"BLOCKED_WIPE:{field}",
                            json.dumps(old_value)[:500] if old_value is not None else None,
                            None,
                            updated_by,
                            ts,
                            f"BLOCKED: attempt to wipe persistent field ({reason or 'no reason'})",
                        ),
                    )
                    continue

                # RULE 2: Replacing a populated persistent field requires force=True
                if not old_is_empty and not new_is_empty and not force:
                    blocked_replace.append(field)
                    # Log the blocked attempt
                    self.conn.execute(
                        """INSERT INTO audit_log
                           (slug, table_name, field_changed, old_value, new_value,
                            changed_by, changed_at, reason)
                           VALUES (?, 'lenders', ?, ?, ?, ?, ?, ?)""",
                        (
                            slug,
                            f"BLOCKED_REPLACE:{field}",
                            json.dumps(old_value)[:500] if old_value is not None else None,
                            json.dumps(new_value)[:500] if new_value is not None else None,
                            updated_by,
                            ts,
                            f"BLOCKED: persistent field replace without force=True ({reason or 'no reason'})",
                        ),
                    )
                    continue

                # RULE 3: Setting an empty field is always allowed (adding new content)
                # (Falls through to the normal change path below)

            # Log the change
            self.conn.execute(
                """INSERT INTO audit_log
                   (slug, table_name, field_changed, old_value, new_value, changed_by, changed_at, reason)
                   VALUES (?, 'lenders', ?, ?, ?, ?, ?, ?)""",
                (
                    slug,
                    field,
                    json.dumps(old_value)[:500] if old_value is not None else None,
                    json.dumps(new_value)[:500] if new_value is not None else None,
                    updated_by,
                    ts,
                    reason,
                ),
            )

            data[field] = new_value
            changes += 1

        if changes > 0:
            checksum = _checksum(data)

            # Update indexed columns from data
            category = data.get("category", lender["category"])
            processing_status = data.get("processing_status", lender["processing_status"])
            is_enriched = 1 if data.get("has_been_enriched") else lender["is_enriched"]
            quality_score = data.get("quality_score", lender["quality_score"]) or 0
            logo_path = data.get("logo_url", lender["logo_path"])
            website_url = data.get("website_url", "") or data.get("website", lender["website_url"])

            self.conn.execute(
                """UPDATE lenders SET
                      data = ?, category = ?, processing_status = ?,
                      is_enriched = ?, quality_score = ?, logo_path = ?,
                      website_url = ?, checksum = ?, updated_at = ?, updated_by = ?
                   WHERE slug = ?""",
                (
                    json.dumps(data, separators=(",", ":")),
                    category, processing_status, is_enriched, quality_score,
                    logo_path, website_url, checksum, ts, updated_by, slug,
                ),
            )
            self.conn.commit()
        elif blocked_wipe or blocked_replace:
            # Commit the blocked-attempt audit entries even if no real changes
            self.conn.commit()

        return {
            "changed": changes,
            "unchanged": unchanged,
            "blocked_wipe": blocked_wipe,
            "blocked_replace": blocked_replace,
        }

    def update_lender_status(self, slug, new_status, updated_by, reason=None):
        """Convenience method to change processing_status (transient field)."""
        return self.update_lender(slug, {"processing_status": new_status}, updated_by, reason)

    def create_lender(self, slug, data: dict, updated_by: str):
        """Insert a new lender profile."""
        if self.lender_exists(slug):
            raise ValueError(f"Lender '{slug}' already exists. Use update_lender() instead.")

        ts = _now()
        checksum = _checksum(data)

        self.conn.execute(
            """INSERT INTO lenders
               (slug, data, category, processing_status, is_protected,
                is_enriched, quality_score, logo_path, website_url,
                checksum, created_at, updated_at, updated_by)
               VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                slug,
                json.dumps(data, separators=(",", ":")),
                data.get("category", "unknown"),
                data.get("processing_status", "raw"),
                1 if data.get("has_been_enriched") else 0,
                data.get("quality_score", 0) or 0,
                data.get("logo_url", ""),
                data.get("website_url", "") or data.get("website", ""),
                checksum, ts, ts, updated_by,
            ),
        )

        # Audit log
        self.conn.execute(
            """INSERT INTO audit_log
               (slug, table_name, field_changed, new_value, changed_by, changed_at, reason)
               VALUES (?, 'lenders', 'CREATED', ?, ?, ?, 'New profile')""",
            (slug, slug, updated_by, ts),
        )
        self.conn.commit()

    def set_protected(self, slug, protected=True, updated_by="founder"):
        """Mark a profile as protected (founder only)."""
        if updated_by != "founder":
            raise ProtectedProfileError("Only founder can change protection status")

        ts = _now()
        self.conn.execute(
            "UPDATE lenders SET is_protected = ?, updated_at = ?, updated_by = ? WHERE slug = ?",
            (1 if protected else 0, ts, updated_by, slug),
        )
        self.conn.execute(
            """INSERT INTO audit_log
               (slug, table_name, field_changed, old_value, new_value, changed_by, changed_at, reason)
               VALUES (?, 'lenders', 'is_protected', ?, ?, 'founder', ?, ?)""",
            (slug, str(not protected), str(protected), ts, "Protection status changed"),
        )
        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════
    # CONTENT READS & WRITES
    # ═══════════════════════════════════════════════════════════════

    def get_blog_post(self, slug):
        row = self.conn.execute("SELECT data FROM blog_posts WHERE slug = ?", (slug,)).fetchone()
        return json.loads(row["data"]) if row else None

    def get_all_blog_posts(self, status=None):
        if status:
            rows = self.conn.execute("SELECT data FROM blog_posts WHERE status = ?", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT data FROM blog_posts").fetchall()
        return [json.loads(r["data"]) for r in rows]

    def add_blog_post(self, data: dict, updated_by: str):
        slug = data.get("slug", "")
        if not slug:
            raise ValueError("Blog post must have a 'slug' field")
        ts = _now()
        checksum = _checksum(data)
        status = data.get("status", "draft")
        self.conn.execute(
            """INSERT OR REPLACE INTO blog_posts (slug, data, status, checksum, updated_at, updated_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (slug, json.dumps(data, separators=(",", ":")), status, checksum, ts, updated_by),
        )
        self.conn.execute(
            """INSERT INTO audit_log (slug, table_name, field_changed, changed_by, changed_at, reason)
               VALUES (?, 'blog_posts', 'UPSERT', ?, ?, 'Blog post added/updated')""",
            (slug, updated_by, ts),
        )
        self.conn.commit()

    def add_comparison(self, data: dict, updated_by: str):
        slug = data.get("slug", "")
        if not slug:
            raise ValueError("Comparison must have a 'slug' field")
        ts = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO comparisons (slug, data, checksum, updated_at, updated_by)
               VALUES (?, ?, ?, ?, ?)""",
            (slug, json.dumps(data, separators=(",", ":")), _checksum(data), ts, updated_by),
        )
        self.conn.commit()

    def add_wellness_guide(self, data: dict, updated_by: str):
        slug = data.get("slug", "")
        if not slug:
            raise ValueError("Wellness guide must have a 'slug' field")
        ts = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO wellness_guides (slug, data, checksum, updated_at, updated_by)
               VALUES (?, ?, ?, ?, ?)""",
            (slug, json.dumps(data, separators=(",", ":")), _checksum(data), ts, updated_by),
        )
        self.conn.commit()

    def add_listicle(self, data: dict, updated_by: str):
        slug = data.get("slug", "")
        if not slug:
            raise ValueError("Listicle must have a 'slug' field")
        ts = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO listicles (slug, data, checksum, updated_at, updated_by)
               VALUES (?, ?, ?, ?, ?)""",
            (slug, json.dumps(data, separators=(",", ":")), _checksum(data), ts, updated_by),
        )
        self.conn.commit()

    def get_all_comparisons(self):
        return [json.loads(r["data"]) for r in self.conn.execute("SELECT data FROM comparisons").fetchall()]

    def get_all_wellness_guides(self):
        return [json.loads(r["data"]) for r in self.conn.execute("SELECT data FROM wellness_guides").fetchall()]

    def get_all_listicles(self):
        return [json.loads(r["data"]) for r in self.conn.execute("SELECT data FROM listicles").fetchall()]

    def get_all_categories(self):
        return [json.loads(r["data"]) for r in self.conn.execute("SELECT data FROM categories").fetchall()]

    # ═══════════════════════════════════════════════════════════════
    # LOGO OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def get_logo(self, slug):
        row = self.conn.execute("SELECT * FROM logos WHERE slug = ?", (slug,)).fetchone()
        return dict(row) if row else None

    def update_logo(self, slug, file_path, file_hash, source_url=None, updated_by="logo_fetcher"):
        """Record a logo in the database."""
        ts = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO logos (slug, file_path, file_hash, source_url, fetched_at, status)
               VALUES (?, ?, ?, ?, ?, 'fetched')""",
            (slug, file_path, file_hash, source_url, ts),
        )
        # Also update the lender's logo_path
        if self.lender_exists(slug):
            self.update_lender(slug, {"logo_url": file_path}, updated_by=updated_by, reason="Logo updated")
        self.conn.commit()

    def get_lenders_missing_logos(self, limit=None):
        """Get lenders that have no logo in the logos table."""
        sql = """
            SELECT l.slug, l.category, l.website_url
            FROM lenders l
            LEFT JOIN logos lg ON l.slug = lg.slug
            WHERE (lg.slug IS NULL OR lg.status = 'missing')
              AND l.processing_status IN ('ready_for_index', 'pending_approval')
              AND l.website_url != ''
        """
        if limit:
            sql += f" LIMIT {int(limit)}"
        return [dict(r) for r in self.conn.execute(sql).fetchall()]

    def get_logo_stats(self):
        """Get logo coverage statistics."""
        total = self.conn.execute(
            "SELECT COUNT(*) FROM lenders WHERE processing_status IN ('ready_for_index','pending_approval')"
        ).fetchone()[0]
        with_logo = self.conn.execute(
            "SELECT COUNT(*) FROM logos WHERE status = 'fetched'"
        ).fetchone()[0]
        missing = total - with_logo
        return {"total_visible": total, "with_logo": with_logo, "missing": missing,
                "coverage_pct": round(with_logo / total * 100, 1) if total > 0 else 0}

    # ═══════════════════════════════════════════════════════════════
    # AUDIT LOG
    # ═══════════════════════════════════════════════════════════════

    def get_audit_log(self, slug=None, limit=50):
        """Get recent audit log entries."""
        if slug:
            rows = self.conn.execute(
                "SELECT * FROM audit_log WHERE slug = ? ORDER BY changed_at DESC LIMIT ?",
                (slug, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ═══════════════════════════════════════════════════════════════
    # EXPORT — DB → JSON files for Astro build
    # ═══════════════════════════════════════════════════════════════

    def get_changed_lenders_since(self, since_ts):
        """Get slugs of lenders changed since a timestamp."""
        rows = self.conn.execute(
            "SELECT slug FROM lenders WHERE updated_at > ? OR exported_at IS NULL",
            (since_ts,),
        ).fetchall()
        return [r["slug"] for r in rows]

    def export_lender_to_json(self, slug, output_dir=None):
        """Export a single lender to its JSON file."""
        output_dir = Path(output_dir) if output_dir else LENDERS_DIR
        data = self.get_lender_data(slug)
        if not data:
            return False

        filepath = output_dir / f"{slug}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        ts = _now()
        self.conn.execute(
            "UPDATE lenders SET exported_at = ? WHERE slug = ?", (ts, slug)
        )
        self.conn.commit()
        return True

    def export_changed_lenders(self, output_dir=None):
        """Export only lenders that changed since last export. Returns count."""
        output_dir = Path(output_dir) if output_dir else LENDERS_DIR

        # Get lenders where updated_at > exported_at (or never exported)
        rows = self.conn.execute(
            """SELECT slug FROM lenders
               WHERE exported_at IS NULL OR updated_at > exported_at"""
        ).fetchall()

        slugs = [r["slug"] for r in rows]
        exported = 0
        for slug in slugs:
            if self.export_lender_to_json(slug, output_dir):
                exported += 1

        # Record the build
        ts = _now()
        self.conn.execute(
            """INSERT INTO builds (started_at, completed_at, lenders_exported, lenders_changed, status)
               VALUES (?, ?, ?, ?, 'completed')""",
            (ts, ts, exported, exported),
        )
        self.conn.commit()

        return exported

    def export_all_lenders(self, output_dir=None):
        """Export ALL lenders to JSON (full rebuild). Returns count."""
        output_dir = Path(output_dir) if output_dir else LENDERS_DIR

        rows = self.conn.execute("SELECT slug FROM lenders").fetchall()
        exported = 0
        for r in rows:
            if self.export_lender_to_json(r["slug"], output_dir):
                exported += 1

        ts = _now()
        self.conn.execute(
            """INSERT INTO builds (started_at, completed_at, lenders_exported, lenders_changed, status)
               VALUES (?, ?, ?, ?, 'completed')""",
            (ts, ts, exported, exported),
        )
        self.conn.commit()
        return exported

    def export_content_file(self, table, filename, output_dir=None):
        """Export a content table back to its JSON file."""
        output_dir = Path(output_dir) if output_dir else CONTENT_DIR
        rows = self.conn.execute(f"SELECT data FROM {table}").fetchall()
        items = [json.loads(r["data"]) for r in rows]

        filepath = output_dir / filename
        with open(filepath, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        # Mark as exported
        ts = _now()
        if table != "categories":
            self.conn.execute(f"UPDATE {table} SET exported_at = ?", (ts,))
        self.conn.commit()
        return len(items)

    def export_all_content(self, output_dir=None):
        """Export all content tables to JSON files."""
        mapping = {
            "blog_posts": "blog-posts.json",
            "comparisons": "comparisons.json",
            "wellness_guides": "wellness-guides.json",
            "listicles": "listicles.json",
            "categories": "categories.json",
        }
        results = {}
        for table, filename in mapping.items():
            results[table] = self.export_content_file(table, filename, output_dir)
        return results

    # ═══════════════════════════════════════════════════════════════
    # INTEGRITY CHECKS
    # ═══════════════════════════════════════════════════════════════

    def check_json_integrity(self, slug):
        """Compare DB checksum with actual JSON file on disk."""
        row = self.conn.execute(
            "SELECT checksum FROM lenders WHERE slug = ?", (slug,)
        ).fetchone()
        if not row:
            return {"status": "not_in_db"}

        filepath = LENDERS_DIR / f"{slug}.json"
        if not filepath.exists():
            return {"status": "json_missing", "db_checksum": row["checksum"]}

        with open(filepath) as f:
            file_data = json.load(f)
        file_checksum = _checksum(file_data)

        if file_checksum == row["checksum"]:
            return {"status": "match", "checksum": row["checksum"]}
        else:
            return {
                "status": "mismatch",
                "db_checksum": row["checksum"],
                "file_checksum": file_checksum,
            }

    # ═══════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _row_to_lender(self, row):
        return {
            "slug": row["slug"],
            "data": json.loads(row["data"]),
            "category": row["category"],
            "processing_status": row["processing_status"],
            "is_protected": bool(row["is_protected"]),
            "is_enriched": bool(row["is_enriched"]),
            "quality_score": row["quality_score"],
            "logo_path": row["logo_path"],
            "website_url": row["website_url"],
            "checksum": row["checksum"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "updated_by": row["updated_by"],
            "exported_at": row["exported_at"],
        }


# ─── CLI ─────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 creditdoc_db.py <command> [args]")
        print("Commands: stats, get <slug>, audit [slug], export-changed, export-all, changed-since <ts>, logo-stats")
        return

    cmd = sys.argv[1]
    db = CreditDocDB()

    if cmd == "stats":
        stats = db.get_stats()
        print(f"\n{'='*50}")
        print("CreditDoc Database Stats")
        print(f"{'='*50}")
        print(f"Total lenders:   {stats['total_lenders']:,}")
        print(f"Protected:       {stats['protected']}")
        print(f"Enriched:        {stats['enriched']:,}")
        print(f"DB size:         {stats['db_size_mb']} MB")
        print(f"Audit entries:   {stats['audit_entries']:,}")
        print(f"\nBy status:")
        for s, c in stats["by_status"].items():
            print(f"  {s}: {c:,}")
        print(f"\nBy category (top 15):")
        for cat, c in stats["by_category"].items():
            print(f"  {cat}: {c:,}")
        print(f"\nContent:")
        for t in ["blog_posts", "comparisons", "wellness_guides", "listicles", "categories"]:
            print(f"  {t}: {stats[t]}")
        print(f"  logos (fetched): {stats['logos']}")

    elif cmd == "get" and len(sys.argv) > 2:
        slug = sys.argv[2]
        lender = db.get_lender(slug)
        if lender:
            meta = {k: v for k, v in lender.items() if k != "data"}
            print(f"\nMetadata: {json.dumps(meta, indent=2)}")
            data = lender["data"]
            print(f"\nData fields: {list(data.keys())}")
            print(f"Category: {data.get('category')}")
            print(f"Name: {data.get('name')}")
            print(f"Status: {data.get('processing_status')}")
            print(f"Logo: {data.get('logo_url', 'none')}")
            print(f"Website: {data.get('website_url', 'none')}")
            desc = data.get("description_long", "")
            print(f"Description: {len(desc)} chars")
        else:
            print(f"Not found: {slug}")

    elif cmd == "audit":
        slug = sys.argv[2] if len(sys.argv) > 2 else None
        entries = db.get_audit_log(slug=slug, limit=20)
        if entries:
            for e in entries:
                print(f"[{e['changed_at']}] {e['slug']} | {e['field_changed']} | by {e['changed_by']} | {e.get('reason','')}")
        else:
            print("No audit entries found.")

    elif cmd == "export-changed":
        count = db.export_changed_lenders()
        print(f"Exported {count} changed lenders to JSON.")

    elif cmd == "export-all":
        count = db.export_all_lenders()
        print(f"Exported {count} lenders to JSON.")

    elif cmd == "changed-since" and len(sys.argv) > 2:
        ts = sys.argv[2]
        slugs = db.get_changed_lenders_since(ts)
        print(f"{len(slugs)} lenders changed since {ts}")
        for s in slugs[:20]:
            print(f"  {s}")
        if len(slugs) > 20:
            print(f"  ... and {len(slugs) - 20} more")

    elif cmd == "logo-stats":
        stats = db.get_logo_stats()
        print(f"\nLogo Coverage:")
        print(f"  Visible lenders: {stats['total_visible']:,}")
        print(f"  With logo:       {stats['with_logo']:,}")
        print(f"  Missing:         {stats['missing']:,}")
        print(f"  Coverage:        {stats['coverage_pct']}%")

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: stats, get <slug>, audit [slug], export-changed, export-all, changed-since <ts>, logo-stats")

    db.close()


if __name__ == "__main__":
    main()
