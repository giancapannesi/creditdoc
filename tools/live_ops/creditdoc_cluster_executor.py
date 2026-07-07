#!/usr/bin/env python3
"""
CreditDoc Cluster Content Executor

Reads CLUSTER_MAP.json (40 clusters, priority-ranked), picks the next unpublished
cluster, calls the shared OpenAI text provider with a prompt built from the cluster definition, validates
the returned JSON, writes to the cluster_answers DB table, runs the compliance gate,
exports to JSON for the Astro build, commits, and pushes.

Fail-loud: any failure alerts Telegram + logs to Memory Palace via mempalace MCP
(handled at orchestration layer — this script writes the trigger).

Usage:
    python3 tools/creditdoc_cluster_executor.py --preview           # default
    python3 tools/creditdoc_cluster_executor.py --apply             # commit + push
    python3 tools/creditdoc_cluster_executor.py --asset <cluster_id>
    python3 tools/creditdoc_cluster_executor.py --status            # show queue state
    python3 tools/creditdoc_cluster_executor.py --skip <cluster_id> # mark as skipped

State: creditdoc/data/cluster_state.json
Log:   logs/cluster_executor.log
"""
import argparse, json, os, sys, subprocess, datetime, re, traceback, sqlite3, hashlib
from pathlib import Path

BASE = Path("/srv/BusinessOps")
CREDITDOC = BASE / "creditdoc"
sys.path.insert(0, str(CREDITDOC))
sys.path.insert(0, str(BASE / "tools"))

from tools.creditdoc_db import CreditDocDB  # noqa: E402
from creditdoc_content_guardrails import reject_if_unsafe  # noqa: E402
from creditdoc_content_repair import repair_unsafe_json  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None

CLUSTER_MAP_PATH = BASE / "CreditDoc Project Improvement" / "CLUSTER_MAP.json"
STATE_PATH = CREDITDOC / "data" / "cluster_state.json"
PROMPT_TEMPLATE = BASE / "tools" / "templates" / "cluster_asset_prompt.md"
SEO_WEB_PATH = CREDITDOC / "data" / "seo_web.yaml"
LOG_PATH = BASE / "logs" / "cluster_executor.log"
EXECUTION_LOG = BASE / "CreditDoc Project Improvement" / "EXECUTION_LOG.md"

# Pillar + banner category inference from cluster ID prefix
PILLAR_MAP = {
    "cs": ("credit-score", "credit-monitoring"),
    "cr": ("credit-repair", "credit-repair"),
    "cb": ("build-credit", "build-credit"),
    "cc": ("credit-cards", "build-credit"),
    "cm": ("credit-monitoring", "credit-monitoring"),
    "pl": ("personal-loans", "personal-loans"),
    "bl": ("business-loans", "business-loans"),
    "debt": ("debt-relief", "credit-repair"),
    "brand": ("personal-loans", "personal-loans"),
}


def _now_iso():
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def log(msg):
    line = f"[{_now_iso()}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def telegram_alert(title, body):
    # Disabled per founder request (2026-05-08) — too many alerts, signal lost in noise
    # Events are still logged to cluster_executor.log
    log(f"[alert-suppressed] {title}: {body[:200]}")


def load_clusters():
    """Read queued clusters from BOTH sources and return a unified list.

    Source A: CLUSTER_MAP.json (49 hand-curated, prefix-derived pillar)
    Source B: cluster_spec table (662 KE+SERP-derived, cluster_spec.pillar 1..7)

    Each entry tagged with `source` so downstream pillar resolution and
    state writes know how to handle it. Dedup happens in pick_next_cluster
    by cluster_id (NOT money_page — JSON intentionally has many cluster_ids
    targeting the same money_page for broader topical authority).
    """
    out = []

    # Source A: legacy JSON (NEVER STOP READING THIS — accumulate, don't swap)
    try:
        a = json.loads(CLUSTER_MAP_PATH.read_text())
        for c in a["clusters"]:
            out.append({**c, "source": "json"})
    except Exception as e:
        log(f"WARN load_clusters: JSON source failed: {e}")

    # Source B: cluster_spec table
    try:
        db_path = str(CREDITDOC / "data" / "creditdoc.db")
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT cluster_id, primary_keyword, pillar, money_page,
                       secondary_phrases, publish_priority, published_url,
                       serp_strategy, page_type_recommendation, serp_top_3
                  FROM cluster_spec
                 WHERE status = 'queued' AND published_url IS NULL
              ORDER BY publish_priority DESC, cluster_id ASC
            """).fetchall()
        for r in rows:
            mp = r["money_page"]
            mp_path = f"/best/{mp}/" if not mp.startswith("/") else mp
            out.append({
                "id": r["cluster_id"],
                "name": r["primary_keyword"],
                "pillar": r["pillar"],
                "money_page": mp_path,
                "sample_questions": json.loads(r["secondary_phrases"] or "[]"),
                "priority_score": r["publish_priority"] or 0,
                "serp_strategy": r["serp_strategy"] or "standard",
                "page_type_recommendation": r["page_type_recommendation"] or "",
                "serp_top_3": r["serp_top_3"] or "[]",
                "source": "cluster_spec",
            })
    except Exception as e:
        log(f"WARN load_clusters: cluster_spec source failed: {e}")

    json_n = sum(1 for c in out if c["source"] == "json")
    spec_n = sum(1 for c in out if c["source"] == "cluster_spec")
    log(f"load_clusters: {json_n} JSON + {spec_n} cluster_spec = {len(out)} total")
    return out


def load_state():
    if not STATE_PATH.exists():
        return {"published": [], "skipped": [], "failed": [], "last_run_at": None}
    return json.loads(STATE_PATH.read_text())


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def pillar_of(cluster):
    """Resolve pillar + banner from cluster dict (or legacy str cluster_id).

    cluster_spec rows: integer pillar 1..7 → mapped to legacy PILLAR_MAP labels
    JSON rows: prefix-string match on cluster_id (legacy behavior)
    """
    if isinstance(cluster, dict) and cluster.get("pillar") and cluster.get("source") == "cluster_spec":
        # Align cluster_spec pillars 1..7 with legacy PILLAR_MAP labels so the
        # corpus uses ONE set of pillar/banner names regardless of source.
        pillar_to_label = {
            1: ("business-loans", "business-loans"),       # small-business → bl
            2: ("personal-loans", "personal-loans"),        # personal-finance → pl
            3: ("credit-cards", "build-credit"),            # matches cc legacy
            4: ("build-credit", "build-credit"),            # credit-builder → cb
            5: ("credit-monitoring", "credit-monitoring"), # matches cm legacy
            6: ("credit-repair", "credit-repair"),          # matches cr legacy
            7: ("debt-relief", "credit-repair"),            # matches debt legacy
        }
        try:
            return pillar_to_label.get(int(cluster["pillar"]),
                                       ("financial-wellness", "credit-monitoring"))
        except (TypeError, ValueError):
            pass

    # Legacy / fallback — prefix match on cluster_id string
    cluster_id = cluster["id"] if isinstance(cluster, dict) else cluster
    for prefix, (pillar, banner) in PILLAR_MAP.items():
        if cluster_id.startswith(prefix + "-") or cluster_id == prefix:
            return pillar, banner
    return "financial-wellness", "credit-monitoring"


def pick_next_cluster(clusters, state, asset_override=None):
    """Pick highest-priority cluster from merged queue, dedup by cluster_id.

    Skip rules:
      1. cluster_id in state['published']/['skipped'] (legacy state file)
      2. cluster_id in cluster_answers WHERE status='published' (DB authoritative)

    Note: dedup is NOT by money_page. JSON has multiple cluster_ids per
    money_page by design (e.g. bl-best, bl-rates, bl-apply all link to
    /best/best-small-business-loans/). That's the topical-authority compounding
    Jammi's accumulate-rule preserves.
    """
    db_path = str(CREDITDOC / "data" / "creditdoc.db")
    try:
        with sqlite3.connect(db_path) as conn:
            published_cluster_ids = {r[0] for r in conn.execute(
                "SELECT cluster_id FROM cluster_answers WHERE status='published' AND cluster_id IS NOT NULL"
            )}
    except Exception as e:
        log(f"WARN pick_next_cluster: cluster_answers query failed, falling back to state-only dedup: {e}")
        published_cluster_ids = set()

    blocked_ids = set(state["published"]) | set(state["skipped"]) | published_cluster_ids

    if asset_override:
        for c in clusters:
            if c["id"] == asset_override:
                return c
        raise ValueError(f"cluster '{asset_override}' not in merged queue")

    candidates = [c for c in clusters if c["id"] not in blocked_ids]
    if not candidates:
        return None
    candidates.sort(key=lambda c: c.get("priority_score", 0) or 0, reverse=True)
    return candidates[0]


VOICE_PROFILES = [
    (
        "Write as a professional financial advisor — measured, precise, citing specific numbers "
        "and regulations. Prefer 'consider' over 'you should.' Use industry terms but define them "
        "on first use. Slightly formal but never stiff."
    ),
    (
        "Write as a practical small-business finance educator explaining things clearly to a friend at a coffee shop. "
        "Use third-person examples such as 'a contractor applying for an equipment loan...' or 'a borrower comparing an SBA loan...'. "
        "Short punchy sentences. Contractions. No jargon without explaining it."
    ),
    (
        "Write as a consumer-protective educator — think CFPB blog meets personal finance teacher. "
        "Emphasize what to watch out for, what questions to ask lenders, red flags. Slightly cautious "
        "tone. Use 'you' often. Concrete action steps."
    ),
    (
        "Write as a data-driven analyst who loves tables and comparisons. Lead with numbers, "
        "use credit-score tiers and APR ranges in every section. Efficient prose — say it once, "
        "say it clearly. Prefer bullet lists and tables over long paragraphs."
    ),
    (
        "Write as a warm, plain-English consumer finance educator. Be empathetic without pretending to have personally had the reader's credit problem. "
        "Mix practical steps with "
        "encouragement. Short paragraphs. Conversational but never sloppy."
    ),
]


def _load_seo_web():
    if yaml is None or not SEO_WEB_PATH.exists():
        return None
    try:
        return yaml.safe_load(SEO_WEB_PATH.read_text())
    except Exception as e:
        log(f"WARN _load_seo_web: {e}")
        return None


def _resolve_intent_description(seo_web, pillar_num):
    if not seo_web or not pillar_num:
        return "A US consumer seeking lending or credit guidance."
    pillars = seo_web.get("pillars", {})
    p = pillars.get(int(pillar_num), pillars.get(str(pillar_num)))
    if not p:
        return "A US consumer seeking lending or credit guidance."
    intents = p.get("intents", {})
    if not intents:
        return f"A borrower exploring {p.get('name', 'financial')} options."
    first_intent = next(iter(intents.values()), {})
    return first_intent.get("description", f"A borrower exploring {p.get('name', 'financial')} options.")


def _pick_voice_profile(cluster_id):
    idx = int(hashlib.md5(cluster_id.encode()).hexdigest(), 16) % len(VOICE_PROFILES)
    return VOICE_PROFILES[idx]


QUESTION_STARTERS = (
    "are ", "can ", "could ", "do ", "does ", "did ", "how ", "is ", "should ",
    "what ", "when ", "where ", "which ", "who ", "why ", "will ",
)


def _normalize_question(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def _sentence_case_question(text):
    text = _normalize_question(text)
    if not text:
        return text
    text = text[0].upper() + text[1:]
    text = re.sub(r"\bi\b", "I", text)
    acronym_map = {
        "sba": "SBA",
        "mca": "MCA",
        "apr": "APR",
        "fico": "FICO",
        "irs": "IRS",
        "ftc": "FTC",
        "cfpb": "CFPB",
        "llc": "LLC",
    }
    for raw, fixed in acronym_map.items():
        text = re.sub(rf"\b{raw}\b", fixed, text, flags=re.I)
    return text


def _is_question_like(text):
    q = _normalize_question(text).lower().rstrip("?")
    return q.startswith(QUESTION_STARTERS) or "?" in text


def _question_score(text):
    """Prefer exact FAQ-style questions over head terms in a cluster queue."""
    q = _normalize_question(text).lower()
    score = 0
    if _is_question_like(q):
        score += 20
    if q.endswith("?"):
        score += 4
    if q.startswith(("how ", "what ", "can ", "does ", "is ", "should ", "which ")):
        score += 6
    if any(term in q for term in ("reddit", "2022", "2023", "2024", "2025", "2026", "forbes")):
        score -= 8
    if q.startswith(("best ", "top ", "compare ")):
        score -= 6
    # Keep the page narrow; very long candidates tend to be keyword strings.
    wc = len(q.split())
    if 4 <= wc <= 12:
        score += 4
    elif wc > 16:
        score -= 5
    return score


def _ensure_question(text):
    text = _normalize_question(text)
    if not text:
        return "What should borrowers know before comparing financing options?"
    lower = text.lower().rstrip("?")
    original_lower = lower
    phrase_fixes = {
        "can credit card balance transfer": "Can you transfer a credit card balance?",
        "are credit card balance transfer bad": "Are credit card balance transfers bad?",
        "are credit card balance transfers a good idea": "Are credit card balance transfers a good idea?",
        "are small business loans": "What are small business loans?",
        "how do i get small business loan": "How do I get a small business loan?",
        "where to apply for small business loan": "Where can you apply for a small business loan?",
        "where can i apply for small business loan": "Where can I apply for a small business loan?",
        "what credit score you need to get a business loan": "What credit score do you need to get a business loan?",
        "does credit repair companies work": "Do credit repair companies work?",
        "does credit repair services work": "Do credit repair services work?",
    }
    if lower in phrase_fixes:
        return phrase_fixes[lower]
    article_patterns = (
        (r"\bget small business loan\b", "get a small business loan"),
        (r"\bapply for small business loan\b", "apply for a small business loan"),
        (r"\bget restaurant business loan\b", "get a restaurant business loan"),
        (r"\bdump truck business loan\b", "a dump truck business loan"),
        (r"\bstart up business loan\b", "startup business loan"),
        (r"\bstart up\b", "startup"),
    )
    for pattern, replacement in article_patterns:
        lower = re.sub(pattern, replacement, lower)
    if lower != original_lower:
        text = lower + ("?" if text.endswith("?") else "")
    if lower.startswith("can credit card transfer balance to "):
        destination = lower.replace("can credit card transfer balance to ", "", 1)
        return _sentence_case_question(f"Can you transfer a credit card balance to {destination}?")
    if lower.startswith("can i transfer credit card balance to "):
        destination = lower.replace("can i transfer credit card balance to ", "", 1)
        return _sentence_case_question(f"Can I transfer a credit card balance to {destination}?")
    if text.endswith("?"):
        return _sentence_case_question(text)
    if lower.startswith(QUESTION_STARTERS):
        return _sentence_case_question(text + "?")
    if lower.startswith(("best ", "top ")):
        return _sentence_case_question("What are the " + lower + "?")
    if lower.startswith("compare "):
        return _sentence_case_question("How should you " + lower + "?")
    return _sentence_case_question("What should you know about " + lower + "?")


def select_primary_question(cluster):
    """Turn a cluster queue row into one dedicated answer-page target."""
    candidates = []
    for q in cluster.get("sample_questions", []) or []:
        if isinstance(q, str) and q.strip():
            candidates.append(q)
    name = cluster.get("name", "")
    if name:
        candidates.append(name)

    if not candidates:
        return _ensure_question("")

    best = max(candidates, key=_question_score)
    return _ensure_question(best)


def select_supporting_questions(cluster, primary_question, limit=6):
    primary_norm = re.sub(r"[^a-z0-9]+", " ", primary_question.lower()).strip()
    out = []
    seen = {primary_norm}
    ranked = sorted(
        [q for q in (cluster.get("sample_questions", []) or []) if isinstance(q, str) and q.strip()],
        key=_question_score,
        reverse=True,
    )
    for q in ranked:
        candidate = _ensure_question(q)
        norm = re.sub(r"[^a-z0-9]+", " ", candidate.lower()).strip()
        if norm in seen:
            continue
        seen.add(norm)
        out.append(candidate)
        if len(out) >= limit:
            break
    return out


def _dedicated_page_recommendation(text):
    text = _normalize_question(text)
    if not text:
        return "Standard dedicated /answers/ page."
    replacements = {
        "Standard /answers/ cluster page.": "Standard dedicated /answers/ page.",
        "Standard /answers/ cluster page with a /best/ money-page CTA.": "Standard dedicated /answers/ page with a /best/ money-page CTA.",
        "cluster page": "dedicated answer page",
        "Cluster page": "Dedicated answer page",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def build_prompt(cluster):
    template = PROMPT_TEMPLATE.read_text()
    pillar, banner = pillar_of(cluster)
    primary_question = select_primary_question(cluster)
    supporting_questions = select_supporting_questions(cluster, primary_question)
    question_bullets = "\n".join(f"- {q}" for q in supporting_questions) or "- None supplied"

    seo_web = _load_seo_web()
    pillar_num = cluster.get("pillar") if cluster.get("source") == "cluster_spec" else None
    intent_desc = _resolve_intent_description(seo_web, pillar_num)
    voice = _pick_voice_profile(cluster["id"])

    serp_strategy = cluster.get("serp_strategy", "standard")
    page_type_rec = _dedicated_page_recommendation(
        cluster.get("page_type_recommendation", "Standard dedicated /answers/ page.")
    )
    serp_top_3 = cluster.get("serp_top_3", "[]")
    if isinstance(serp_top_3, str):
        try:
            serp_top_3 = ", ".join(json.loads(serp_top_3))
        except Exception:
            serp_top_3 = serp_top_3

    prompt = (
        template
        .replace("{{CLUSTER_NAME}}", cluster["name"])
        .replace("{{CLUSTER_ID}}", cluster["id"])
        .replace("{{PILLAR}}", pillar)
        .replace("{{MONEY_PAGE}}", cluster["money_page"])
        .replace("{{BANNER_CATEGORY}}", banner)
        .replace("{{PRIMARY_QUESTION}}", primary_question)
        .replace("{{QUESTIONS}}", question_bullets)
        .replace("{{INTENT_DESCRIPTION}}", intent_desc)
        .replace("{{SERP_STRATEGY}}", serp_strategy)
        .replace("{{PAGE_TYPE_RECOMMENDATION}}", page_type_rec)
        .replace("{{SERP_TOP_3}}", serp_top_3)
        .replace("{{VOICE_PROFILE}}", voice)
    )
    return prompt, pillar, banner, primary_question


def call_openai_text(prompt, timeout=600):
    """Invoke the shared CreditDoc OpenAI text provider."""
    sys.path.insert(0, str(BASE / "tools"))
    from creditdoc_oauth import call_ai
    return call_ai(prompt, model="gpt-4.1", max_tokens=8192, timeout_secs=timeout)


def extract_json(text):
    """Extract a JSON object from provider output."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in provider output")
    return text[start : end + 1]


REQUIRED_FIELDS = [
    "slug", "title", "h1", "meta_description", "questions_answered",
    "sections", "faq_schema", "internal_links", "primary_sources",
]


def _contains_meaningful_overlap(text, question):
    text_tokens = set(re.findall(r"[a-z0-9]+", (text or "").lower()))
    q_tokens = [
        t for t in re.findall(r"[a-z0-9]+", (question or "").lower())
        if t not in {"a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "is", "of", "or", "the", "to", "what", "when", "where", "which", "who", "why", "with", "you", "your"}
    ]
    if not q_tokens:
        return True
    return len(text_tokens.intersection(q_tokens)) >= max(2, min(5, len(set(q_tokens)) // 2))


def _h1_contains_primary_question_terms(h1, question):
    h1_tokens = set(re.findall(r"[a-z0-9]+", (h1 or "").lower()))
    q_tokens = {
        t for t in re.findall(r"[a-z0-9]+", (question or "").lower())
        if t not in {"a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "is", "of", "or", "the", "to", "what", "when", "where", "which", "who", "why", "with", "you", "your"}
    }
    return not q_tokens or q_tokens <= h1_tokens


def validate_shape(obj, primary_question=None):
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in obj:
            errors.append(f"missing field: {f}")
    if errors:
        return errors
    if not isinstance(obj["sections"], list) or len(obj["sections"]) < 5:
        errors.append(f"sections must be list with ≥5 items, got {len(obj.get('sections', []))}")
    if not isinstance(obj["faq_schema"], list) or not (4 <= len(obj["faq_schema"]) <= 8):
        errors.append(f"faq_schema must have 4-8 items, got {len(obj.get('faq_schema', []))}")
    if not isinstance(obj["internal_links"], list) or len(obj["internal_links"]) < 8:
        errors.append(f"internal_links must have ≥8 items, got {len(obj.get('internal_links', []))}")
    questions_answered = obj.get("questions_answered", [])
    if not isinstance(questions_answered, list) or not (1 <= len(questions_answered) <= 3):
        errors.append(f"questions_answered must have 1-3 items for dedicated answer pages, got {len(questions_answered or [])}")
    if primary_question:
        combined_title = f"{obj.get('title', '')} {obj.get('h1', '')}"
        if not _contains_meaningful_overlap(combined_title, primary_question):
            errors.append("title/h1 do not clearly target the primary question")
    if len(obj.get("title", "")) > 60:
        errors.append(f"title >60 chars: {len(obj['title'])}")
    md = obj.get("meta_description", "")
    if not (100 <= len(md) <= 160):
        errors.append(f"meta_description length out of 100-160: {len(md)}")
    return errors


NARRATOR_CLAIM_PATTERNS = [
    re.compile(r"\bwhen I (?:got|applied|needed|borrowed|paid|leased|opened)\b", re.I),
    re.compile(r"\bI remember\b.{0,120}\b(?:loan|credit|debt|business|equipment|mortgage|rate|term sheet|FICO)\b", re.I | re.S),
    re.compile(r"\bI learned this(?: the hard way)?\b", re.I),
    re.compile(r"\bmy first (?:business|SBA|mortgage|loan|credit card|credit line|line of credit)\b", re.I),
    re.compile(r"\bmy personal score\b", re.I),
    re.compile(r"\bI had a \d{3}\s*FICO\b", re.I),
    re.compile(r"\bthe bank laughed me out\b", re.I),
    re.compile(r"\bI paid it off\b", re.I),
    re.compile(r"\bI've been there\b", re.I),
    re.compile(r"\bI went through (?:credit|debt|loan|mortgage)\b", re.I),
]


def detect_narrator_claim_violations(obj):
    """Return first-person lived-experience claims that CreditDoc cannot verify.

    We allow normal direct address and hypothetical examples. We block answer
    pages that make CreditDoc sound like it personally applied for loans, had a
    FICO score, paid debt, or experienced a lender decision.
    """
    violations = []
    for idx, section in enumerate(obj.get("sections", []) or []):
        content = section.get("content", "") if isinstance(section, dict) else ""
        for pattern in NARRATOR_CLAIM_PATTERNS:
            match = pattern.search(content)
            if match:
                excerpt = " ".join(content[max(0, match.start() - 80):match.end() + 180].split())
                violations.append(f"section {idx + 1}: {excerpt[:260]}")
                break
    return violations


def basic_compliance(obj, target_money_page, primary_question=None):
    """Inline 10-check sanity gate. Full 65-point gate comes in Phase 5
    via cluster_compliance_check.py. Returns (score_out_of_10, failures)."""
    checks = []

    def c(ok, name):
        checks.append((ok, name))

    c(1 <= len(obj.get("h1", "")) <= 80, "h1 length 1-80")
    c(len(obj.get("title", "")) <= 60, "title ≤60 chars")
    c(100 <= len(obj.get("meta_description", "")) <= 160, "meta_description 100-160")
    c(len(obj.get("sections", [])) >= 5, "≥5 sections")
    c(1 <= len(obj.get("questions_answered", [])) <= 3, "1-3 questions_answered for dedicated page")
    if primary_question:
        c(_h1_contains_primary_question_terms(obj.get("h1", ""), primary_question), "h1 contains primary question terms")

    total_words = sum(len(s.get("content", "").split()) for s in obj.get("sections", []))
    c(total_words >= 1200, f"body ≥1200 words (got {total_words})")
    c(total_words <= 3500, f"body ≤3500 words (got {total_words})")

    c(4 <= len(obj.get("faq_schema", [])) <= 8, "FAQ 4-8 entries")
    c(len(obj.get("internal_links", [])) >= 8, "≥8 internal links")

    links = obj.get("internal_links", [])
    money_link_urls = [ln.get("url", "") for ln in links]
    c(
        any(target_money_page in u for u in money_link_urls),
        f"links to target money page {target_money_page}",
    )
    c(len(obj.get("primary_sources", [])) >= 2, "≥2 primary sources")

    narrator_violations = detect_narrator_claim_violations(obj)
    c(
        not narrator_violations,
        "critical: no fabricated first-person lived-experience claims",
    )

    guardrail_failures = reject_if_unsafe(obj)
    c(
        not guardrail_failures,
        "critical: no unsupported current prices, ratings, rates, guarantees, or certainty claims",
    )

    passed = sum(1 for ok, _ in checks if ok)
    failures = [name for ok, name in checks if not ok]
    if narrator_violations:
        failures.extend(f"narrator claim: {v}" for v in narrator_violations[:5])
        # Hard fail regardless of otherwise good shape/length/link checks.
        passed = min(passed, 7)
    if guardrail_failures:
        failures.extend(guardrail_failures[:8])
        passed = min(passed, 7)
    return passed, len(checks), failures


def git(*args, check=True):
    return subprocess.run(
        ["git", "-C", str(CREDITDOC), *args],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def append_execution_log(phase, task, slug, cluster, score, url, notes):
    EXECUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    header = "| Date | Phase | Task | Asset | Cluster | Score | URL | Notes |\n|---|---|---|---|---|---|---|---|\n"
    if not EXECUTION_LOG.exists():
        EXECUTION_LOG.write_text("# Cluster Execution Log\n\nAppend-only. Never edit old rows.\n\n" + header)
    with EXECUTION_LOG.open("a") as f:
        f.write(f"| {_now_iso()} | {phase} | {task} | {slug} | {cluster} | {score} | {url} | {notes} |\n")


def run(args):
    state = load_state()
    clusters = load_clusters()
    cluster = pick_next_cluster(clusters, state, asset_override=args.asset)
    if not cluster:
        log("queue empty — nothing to publish")
        return 0

    log(f"picked cluster id={cluster['id']} source={cluster.get('source','?')} name={cluster['name']!r} priority={cluster.get('priority_score')}")
    pillar, banner = pillar_of(cluster)
    log(f"pillar={pillar} banner={banner} money_page={cluster['money_page']}")

    prompt, _pillar, _banner, primary_question = build_prompt(cluster)
    log(f"prompt built ({len(prompt)} chars)")
    log(f"primary_question={primary_question!r}")

    if args.dry_run:
        log("DRY-RUN — not calling OpenAI, not writing DB, not committing")
        print("\n--- PROMPT PREVIEW (first 2000 chars) ---")
        print(prompt[:2000])
        print("\n--- END PREVIEW ---")
        return 0

    log("calling OpenAI text provider (may take 30-120s)...")
    try:
        raw = call_openai_text(prompt)
    except Exception as e:
        tb = traceback.format_exc()
        log(f"OPENAI TEXT PROVIDER FAILED: {e}")
        telegram_alert("Cluster executor — OpenAI text provider failed", f"cluster={cluster['id']}\n\n{e}\n\n{tb[-800:]}")
        state["failed"].append({"cluster_id": cluster["id"], "when": _now_iso(), "reason": str(e)})
        save_state(state)
        append_execution_log("3", "executor", "(none)", cluster["id"], "0/10", "", f"openai fail: {e}")
        return 2

    log(f"OpenAI returned {len(raw)} bytes")

    try:
        obj = json.loads(extract_json(raw))
    except Exception as e:
        log(f"JSON PARSE FAILED: {e}")
        telegram_alert(
            "Cluster executor — JSON parse failed",
            f"cluster={cluster['id']}\n\n{e}\n\nraw[:500]:\n{raw[:500]}",
        )
        state["failed"].append({"cluster_id": cluster["id"], "when": _now_iso(), "reason": "json_parse"})
        save_state(state)
        append_execution_log("3", "executor", "(none)", cluster["id"], "0/10", "", f"json parse fail")
        return 3

    # Auto-fix minor meta issues before validation. Do not auto-trim titles:
    # a chopped SEO title can publish as a bad search result, so overlong titles
    # must fail validation and be regenerated/fixed upstream.
    md = obj.get("meta_description", "")
    if len(md) > 160:
        obj["meta_description"] = md[:160].rsplit(" ", 1)[0].rstrip(" .,;:-")

    obj["page_format"] = "dedicated_question_answer"
    obj["primary_question"] = primary_question

    shape_errors = validate_shape(obj, primary_question)
    if shape_errors:
        log(f"SHAPE VALIDATION FAILED: {shape_errors}")
        telegram_alert(
            "Cluster executor — shape validation failed",
            f"cluster={cluster['id']}\nslug={obj.get('slug', '?')}\n\n" + "\n".join(shape_errors),
        )
        state["failed"].append({"cluster_id": cluster["id"], "when": _now_iso(), "reason": "shape", "errors": shape_errors})
        save_state(state)
        append_execution_log("3", "executor", obj.get("slug", "?"), cluster["id"], "0/10", "", f"shape fail: {len(shape_errors)}")
        return 4

    pre_guardrail_failures = reject_if_unsafe(obj)
    if pre_guardrail_failures:
        log(f"guardrail repair attempt: {len(pre_guardrail_failures)} failure(s)")
        try:
            obj, remaining_guardrail_failures = repair_unsafe_json(
                obj,
                pre_guardrail_failures,
                content_type="answer page",
                source_context=(
                    f"Cluster: {cluster['name']}\n"
                    f"Target money page: {cluster['money_page']}\n"
                    "Use evergreen education and supplied primary sources only. Do not add current company prices, APRs, ratings, review counts, guarantees, or approval odds."
                ),
                max_tokens=8192,
                timeout_secs=180,
            )
            if remaining_guardrail_failures:
                log(f"guardrail repair incomplete: {remaining_guardrail_failures[:5]}")
            else:
                log("guardrail repair succeeded")
        except Exception as e:
            log(f"guardrail repair failed: {type(e).__name__}: {e}")

        shape_errors = validate_shape(obj, primary_question)
        if shape_errors:
            log(f"SHAPE VALIDATION FAILED AFTER REPAIR: {shape_errors}")
            telegram_alert(
                "Cluster executor — shape validation failed after repair",
                f"cluster={cluster['id']}\nslug={obj.get('slug', '?')}\n\n" + "\n".join(shape_errors),
            )
            state["failed"].append({"cluster_id": cluster["id"], "when": _now_iso(), "reason": "shape_after_repair", "errors": shape_errors})
            save_state(state)
            append_execution_log("3", "executor", obj.get("slug", "?"), cluster["id"], "0/10", "", f"shape after repair fail: {len(shape_errors)}")
            return 4

    # Compliance gate
    passed, total, failures = basic_compliance(obj, cluster["money_page"], primary_question)
    score_str = f"{passed}/{total}"
    log(f"compliance: {score_str}  failures={failures}")
    min_passed = max(8, int(total * 0.85 + 0.999))

    obj["cluster_id"] = cluster["id"]
    obj["cluster_pillar"] = pillar
    obj["banner_category"] = banner
    obj["target_money_page"] = cluster["money_page"]
    obj["compliance_score"] = passed
    obj["compliance_passed"] = passed >= min_passed
    obj["author"] = "CreditDoc Editorial"

    slug = obj["slug"]

    if passed < min_passed:
        log(f"COMPLIANCE FAILED ({score_str}) — saving as draft, NOT publishing")
        obj["status"] = "draft"
        with CreditDocDB() as db:
            db.upsert_cluster_answer(slug, obj, updated_by="cluster_executor", force=True)
        telegram_alert(
            "Cluster executor — compliance failed",
            f"cluster={cluster['id']}\nslug={slug}\nscore={score_str}\n\nfailures:\n- " + "\n- ".join(failures),
        )
        state["failed"].append({"cluster_id": cluster["id"], "when": _now_iso(), "reason": "compliance", "score": passed, "slug": slug})
        save_state(state)
        append_execution_log("3", "executor", slug, cluster["id"], score_str, "", "compliance fail — left as draft")
        return 5

    # Publish — write to DB, then use the incremental build pipeline
    obj["status"] = "published"
    obj["published_at"] = _now_iso()
    obj["last_updated"] = _now_iso()
    with CreditDocDB() as db:
        db.upsert_cluster_answer(slug, obj, updated_by="cluster_executor", force=True)
    log(f"DB: wrote + published slug={slug}")

    if args.apply:
        # Use the existing incremental build pipeline — exports only changed rows,
        # stages only changed files, commits, pushes. Never bypass this.
        try:
            build_cmd = [
                sys.executable,
                str(CREDITDOC / "tools" / "creditdoc_build.py"),
                "--export-and-push",
            ]
            result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(result.stderr[:500])
            log(f"incremental build: {result.stdout.strip()}")
        except Exception as e:
            log(f"BUILD FAILED: {e}")
            telegram_alert("Cluster executor — build failed", f"slug={slug}\n\n{e}")
            append_execution_log("3", "executor", slug, cluster["id"], score_str, "", f"build fail: {e}")
            return 6

        # CDM-REV: /answers/[slug] reads from Supabase, not JSON. UPSERT new row.
        try:
            sync_cmd = [
                sys.executable,
                str(CREDITDOC / "tools" / "sync_cluster_answers_to_supabase.py"),
                "--apply",
            ]
            sync_res = subprocess.run(sync_cmd, capture_output=True, text=True, timeout=120)
            if sync_res.returncode != 0:
                raise RuntimeError(sync_res.stderr[:500] or sync_res.stdout[:500])
            log(f"supabase sync: {sync_res.stdout.strip().splitlines()[-1] if sync_res.stdout.strip() else 'ok'}")
        except Exception as e:
            log(f"SUPABASE SYNC FAILED: {e}")
            telegram_alert("Cluster executor — Supabase sync failed", f"slug={slug}\n\n{e}")
            append_execution_log("3", "executor", slug, cluster["id"], score_str, "", f"supabase sync fail: {e}")
            return 7
    else:
        log("NOT --apply → wrote to DB only (run creditdoc_build.py --export-and-push to deploy)")

    state["published"].append(cluster["id"])
    state["last_run_at"] = _now_iso()
    save_state(state)

    # If cluster came from cluster_spec, also mark the row published so the next
    # pick_next_cluster() correctly excludes it.
    if cluster.get("source") == "cluster_spec":
        try:
            db_path = str(CREDITDOC / "data" / "creditdoc.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    UPDATE cluster_spec
                       SET status = 'published',
                           published_url = ?,
                           published_at = ?
                     WHERE cluster_id = ?
                """, (
                    f"https://creditdoc.co/answers/{slug}/",
                    _now_iso(),
                    cluster["id"],
                ))
                conn.commit()
            log(f"cluster_spec: marked {cluster['id']} published → /answers/{slug}/")
        except Exception as e:
            # Non-fatal — legacy state file already updated; alert and continue
            log(f"WARN cluster_spec status update failed: {e}")
            telegram_alert("Cluster executor — cluster_spec update failed (non-fatal)",
                           f"cluster={cluster['id']}\nslug={slug}\n\n{e}")

    url = f"https://creditdoc.co/answers/{slug}/"
    telegram_alert(
        "Cluster executor — published",
        f"cluster={cluster['id']}\nslug={slug}\nscore={score_str}\n\n{url}",
    )
    append_execution_log("3", "executor", slug, cluster["id"], score_str, url, "published")
    log(f"DONE: {url}")
    return 0


def status():
    state = load_state()
    clusters = load_clusters()
    done = set(state["published"]) | set(state["skipped"])
    pending = [c for c in clusters if c["id"] not in done]
    print(f"Total clusters:  {len(clusters)}")
    print(f"Published:       {len(state['published'])}")
    print(f"Skipped:         {len(state['skipped'])}")
    print(f"Failed (log):    {len(state['failed'])}")
    print(f"Pending:         {len(pending)}")
    print(f"Last run:        {state.get('last_run_at') or '(never)'}")
    print()
    print("Next up (by priority):")
    pending.sort(key=lambda c: c.get("priority_score", 0), reverse=True)
    for c in pending[:10]:
        print(f"  {c['id']:25}  pri={c.get('priority_score', 0):6.0f}  {c['name']}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview", action="store_true", help="Print prompt only — no OpenAI call, no write")
    p.add_argument("--apply", action="store_true", help="Also git commit + push after publish (default: generate + write DB + export only)")
    p.add_argument("--asset", help="override: publish this cluster_id")
    p.add_argument("--skip", help="mark a cluster_id as skipped")
    p.add_argument("--status", action="store_true")
    args = p.parse_args()

    # dry_run ↔ preview for legacy naming inside run()
    args.dry_run = args.preview

    if args.status:
        status()
        return 0

    if args.skip:
        state = load_state()
        if args.skip not in state["skipped"]:
            state["skipped"].append(args.skip)
            save_state(state)
            print(f"marked {args.skip} as skipped")
        return 0

    try:
        rc = run(args)
        return rc
    except Exception as e:
        tb = traceback.format_exc()
        log(f"UNCAUGHT: {e}\n{tb}")
        telegram_alert("Cluster executor — UNCAUGHT", f"{e}\n\n{tb[-1000:]}")
        return 99


if __name__ == "__main__":
    sys.exit(main())
