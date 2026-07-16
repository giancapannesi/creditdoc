#!/usr/bin/env python3
"""
strip_astro_fingerprint.py

Phase 0a of the AstroKill migration.

Post-processes CreditDoc's `dist/` HTML output to remove Astro-specific
fingerprints. Content is preserved byte-for-byte apart from:

  1. Every `data-astro-cid-<hash>` attribute is removed from HTML tags
     (component-scoping marker; meaningless after render).
  2. Inline `<style>` blocks: every `[data-astro-cid-<hash>]` selector
     qualifier is removed so the class-only version still matches.
     (Astro adds these to scope styles to a specific component. Once we
     remove the attributes, the qualifiers become dead — but they also
     prevent the styles from matching anything. Removing them restores
     the styles to matching by class alone.)
  3. External CSS files under `dist/_astro/*.css`: same `[data-astro-cid]`
     selector-qualifier removal, so cookie banner and other component
     styles keep working.
  4. Every reference to `/_astro/<hash>.css` in HTML `<link>` tags is
     rewritten to `/styles.css` (no framework folder, no hash).
  5. The transformed CSS is written to `dist/styles.css` so the rewritten
     `<link>` tags resolve.

Nothing else is changed. Titles, meta tags, JSON-LD schema, body copy,
`<script>` tags, headers, footers — all pass through untouched.

Usage:
  # Preview on 3 review pages (writes byte-diffs to stdout, no files touched):
  python3 strip_astro_fingerprint.py --check-sample dist/review

  # Apply to ALL HTML files under a directory:
  python3 strip_astro_fingerprint.py --apply dist/review

  # Apply to entire dist (all page families):
  python3 strip_astro_fingerprint.py --apply dist

Every apply run writes a manifest report at
`reports/astro-strip/strip_<YYYY-MM-DD_HH-MM-SS>.json` listing:
  - files touched
  - fingerprints removed per file
  - any file skipped and why
  - errors
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

# The Astro-cid attribute pattern. Matches any variant, whitespace-safe.
# Examples:  data-astro-cid-3hh24ch5   data-astro-cid-garwan2p
# Attribute may be preceded by a space (typical) or come immediately after
# an open tag. Regex captures the leading whitespace so it collapses cleanly.
ASTRO_CID_ATTR_RE = re.compile(r'\s+data-astro-cid-[a-z0-9]+')

# The Astro-cid CSS-selector-qualifier pattern. Astro emits scoped selectors
# like ".cookie-banner[data-astro-cid-garwan2p]" both in inline <style> blocks
# and in dist/_astro/*.css. Removing just the "[data-astro-cid-...]" chunk
# collapses each selector back to its class-only form, which continues to
# match now that the HTML no longer has the attribute either.
# Note: this uses [ and ] literals inside a character class in the regex.
ASTRO_CID_SELECTOR_RE = re.compile(r'\[data-astro-cid-[a-z0-9]+\]')

# The Astro CSS reference pattern. Captures any /_astro/<name>.css file so
# we can rewrite them all to /styles.css, and separately track which physical
# files we need to copy out of dist/_astro/ into dist/.
ASTRO_CSS_HREF_RE = re.compile(r'/_astro/([A-Za-z0-9._-]+\.css)')

# Inline <style>...</style> block matcher for in-HTML style transforms.
INLINE_STYLE_BLOCK_RE = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.DOTALL)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIST = REPO_ROOT / 'dist'
DEFAULT_REPORT_DIR = REPO_ROOT / 'reports' / 'astro-strip'
STATIC_CSS_NAME = 'styles.css'


def strip_html(source: str) -> tuple[str, dict]:
    """Return (new_html, stats) with Astro fingerprints removed.

    Transform order:
      1. Inline <style> blocks: remove [data-astro-cid-*] selector qualifiers.
      2. Rewrite /_astro/*.css hrefs to /styles.css.
      3. Remove data-astro-cid-* attrs from all HTML tags.

    Order matters: attrs must be removed AFTER inline style transform,
    otherwise a bare `[data-astro-cid-xxx]` marker inside <style> that
    matches our attr regex could be over-eaten. Attr regex requires a
    leading whitespace so this is safe either way, but explicit order is
    clearer.
    """
    css_names: list[str] = []
    inline_selectors_removed = [0]

    # Step 1: transform inline <style> blocks — remove [data-astro-cid-*]
    # qualifiers so the class-only selector continues to match.
    def transform_style(match: re.Match) -> str:
        opening, body, closing = match.group(1), match.group(2), match.group(3)
        new_body, n = ASTRO_CID_SELECTOR_RE.subn('', body)
        inline_selectors_removed[0] += n
        return f'{opening}{new_body}{closing}'

    step1 = INLINE_STYLE_BLOCK_RE.sub(transform_style, source)

    # Step 2: rewrite /_astro/*.css hrefs.
    def note_css(match: re.Match) -> str:
        css_names.append(match.group(1))
        return f'/{STATIC_CSS_NAME}'

    step2, css_rewritten = ASTRO_CSS_HREF_RE.subn(note_css, step1)

    # Step 3: strip data-astro-cid-* attrs.
    step3, cid_removed = ASTRO_CID_ATTR_RE.subn('', step2)

    return step3, {
        'cid_removed': cid_removed,
        'inline_selectors_removed': inline_selectors_removed[0],
        'css_rewritten': css_rewritten,
        'css_names': sorted(set(css_names)),
    }


def transform_external_css(source: str) -> tuple[str, int]:
    """Remove [data-astro-cid-*] selector qualifiers from an external CSS file.

    Returns (new_css, count).
    """
    return ASTRO_CID_SELECTOR_RE.subn('', source)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def iter_html(root: Path):
    """Yield every .html file under `root` (recursive)."""
    for path in sorted(root.rglob('*.html')):
        yield path


def preview_diff(before: str, after: str, path: Path) -> str:
    """Small readable diff for a sample. Only lines that changed."""
    before_lines = before.splitlines(keepends=False)
    after_lines = after.splitlines(keepends=False)
    diff = difflib.unified_diff(
        before_lines, after_lines,
        fromfile=str(path), tofile=str(path) + ' [stripped]',
        lineterm='', n=1,
    )
    # Cap the diff to keep the preview readable.
    lines = list(diff)
    if len(lines) > 60:
        head = lines[:30]
        tail = lines[-15:]
        return '\n'.join(head + [f'... ({len(lines) - 45} lines snipped) ...'] + tail)
    return '\n'.join(lines)


def check_sample(root: Path, n: int = 3) -> int:
    """Preview mode — show byte-diffs on N sample files, write nothing."""
    files = list(iter_html(root))
    if not files:
        print(f'ERROR: no HTML files under {root}', file=sys.stderr)
        return 2

    step = max(1, len(files) // n)
    sample = files[::step][:n]
    print(f'Sampling {len(sample)} of {len(files)} HTML files under {root}\n')

    total_cid = total_css = 0
    all_css_names: set[str] = set()

    for path in sample:
        before = path.read_text(encoding='utf-8')
        after, stats = strip_html(before)
        total_cid += stats['cid_removed']
        total_css += stats['css_rewritten']
        all_css_names.update(stats['css_names'])

        print(f'=== {path.relative_to(REPO_ROOT)} ===')
        print(f'  size:      {len(before):,} -> {len(after):,} bytes '
              f'(delta {len(after) - len(before):+,})')
        print(f'  removed:   {stats["cid_removed"]} data-astro-cid attrs, '
              f'{stats["css_rewritten"]} /_astro/*.css refs')
        print(f'  content sha256 change: '
              f'{sha256(before)[:12]}... -> {sha256(after)[:12]}...')
        print(f'  diff (unified, capped):')
        diff_text = preview_diff(before, after, path.relative_to(REPO_ROOT))
        for line in diff_text.split('\n')[:40]:
            print(f'    {line}')
        print()

    print(f'--- sample summary ---')
    print(f'  total cid attrs removed: {total_cid}')
    print(f'  total css refs rewritten: {total_css}')
    print(f'  css files referenced:    {sorted(all_css_names)}')
    print()
    print('NOTHING WRITTEN. Re-run with --apply to persist changes.')
    return 0


def apply_strip(root: Path, dist_root: Path, report_dir: Path) -> int:
    """Full mode — rewrite every HTML file in-place, copy CSS to /styles.css."""
    files = list(iter_html(root))
    if not files:
        print(f'ERROR: no HTML files under {root}', file=sys.stderr)
        return 2

    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    report_path = report_dir / f'strip_{stamp}.json'

    all_css_names: set[str] = set()
    per_file_stats: list[dict] = []
    errors: list[dict] = []
    touched = 0
    unchanged = 0
    started = dt.datetime.utcnow()

    print(f'Applying strip to {len(files)} HTML files under {root}')

    for path in files:
        try:
            before = path.read_text(encoding='utf-8')
        except Exception as exc:
            errors.append({'path': str(path), 'stage': 'read', 'error': str(exc)})
            continue

        after, stats = strip_html(before)
        all_css_names.update(stats['css_names'])

        if after == before:
            unchanged += 1
            continue

        try:
            # Atomic-ish write: write to .tmp then rename.
            tmp = path.with_suffix('.html.tmp')
            tmp.write_text(after, encoding='utf-8')
            tmp.replace(path)
        except Exception as exc:
            errors.append({'path': str(path), 'stage': 'write', 'error': str(exc)})
            continue

        touched += 1
        per_file_stats.append({
            'path': str(path.relative_to(REPO_ROOT)),
            'cid_removed': stats['cid_removed'],
            'css_rewritten': stats['css_rewritten'],
            'size_before': len(before),
            'size_after': len(after),
        })

        if touched % 500 == 0:
            print(f'  ... {touched:,} files stripped')

    # Copy referenced CSS files into dist/styles.css AFTER stripping their
    # [data-astro-cid-*] selector qualifiers. Multiple review pages may
    # reference the same CSS filename; we write to a single dist/styles.css.
    # If more than one distinct source CSS is referenced across the corpus,
    # they get concatenated (rare — usually all pages share one).
    css_copies: list[dict] = []
    combined_css_parts: list[str] = []
    total_css_selectors_stripped = 0

    for name in sorted(all_css_names):
        src = dist_root / '_astro' / name
        try:
            if not src.exists():
                errors.append({'path': str(src), 'stage': 'css-transform',
                               'error': 'source CSS not found'})
                continue
            css_text = src.read_text(encoding='utf-8')
            new_css, n_stripped = transform_external_css(css_text)
            total_css_selectors_stripped += n_stripped
            combined_css_parts.append(new_css)
            css_copies.append({
                'from': str(src.relative_to(REPO_ROOT)),
                'source_bytes': src.stat().st_size,
                'transformed_bytes': len(new_css),
                'selectors_stripped': n_stripped,
            })
        except Exception as exc:
            errors.append({'path': str(src), 'stage': 'css-transform',
                           'error': str(exc)})

    if combined_css_parts:
        dst = dist_root / STATIC_CSS_NAME
        try:
            dst.write_text('\n'.join(combined_css_parts), encoding='utf-8')
            for entry in css_copies:
                entry['to'] = str(dst.relative_to(REPO_ROOT))
        except Exception as exc:
            errors.append({'path': str(dst), 'stage': 'css-write',
                           'error': str(exc)})

    finished = dt.datetime.utcnow()
    report = {
        'started_utc': started.isoformat(timespec='seconds') + 'Z',
        'finished_utc': finished.isoformat(timespec='seconds') + 'Z',
        'duration_sec': int((finished - started).total_seconds()),
        'root': str(root.relative_to(REPO_ROOT)),
        'files_total': len(files),
        'files_touched': touched,
        'files_unchanged': unchanged,
        'files_error': len(errors),
        'css_names_referenced': sorted(all_css_names),
        'css_copies': css_copies,
        'css_selectors_stripped_total': total_css_selectors_stripped,
        'errors': errors,
        # First 20 file stats for spot-checking. Full list omitted to keep report small.
        'sample_files': per_file_stats[:20],
    }
    report_path.write_text(json.dumps(report, indent=2))

    print()
    print(f'--- summary ---')
    print(f'  touched:   {touched:,}')
    print(f'  unchanged: {unchanged:,}')
    print(f'  errors:    {len(errors):,}')
    print(f'  css copied: {len(css_copies)} files')
    print(f'  duration:  {report["duration_sec"]}s')
    print(f'  report:    {report_path.relative_to(REPO_ROOT)}')
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-sample', metavar='PATH', type=Path,
                        help='preview strip on 3 sample files under PATH, write nothing')
    parser.add_argument('--apply', metavar='PATH', type=Path,
                        help='apply strip to every HTML file under PATH')
    parser.add_argument('--sample-n', type=int, default=3,
                        help='number of files to sample in --check-sample mode')
    parser.add_argument('--dist-root', type=Path, default=DEFAULT_DIST,
                        help='root of dist/ (for CSS copy destination)')
    parser.add_argument('--report-dir', type=Path, default=DEFAULT_REPORT_DIR,
                        help='where to write JSON reports')
    args = parser.parse_args(argv)

    if not args.check_sample and not args.apply:
        parser.print_help()
        return 2
    if args.check_sample and args.apply:
        print('ERROR: pass --check-sample OR --apply, not both', file=sys.stderr)
        return 2

    if args.check_sample:
        return check_sample(args.check_sample.resolve(), args.sample_n)
    return apply_strip(args.apply.resolve(), args.dist_root.resolve(),
                       args.report_dir.resolve())


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
