#!/usr/bin/env python3
"""
CreditDoc City Guide Generator — autonomous pipeline for 5 cities/day.

Pulls city data from FDIC locations (regulator.db), state data from Supabase,
generates unique editorial + localized Q&A via OpenAI, inserts into Supabase
city_guides table with status=ready_for_index.

Usage:
  python3 tools/creditdoc_city_guide_generator.py --batch 5
  python3 tools/creditdoc_city_guide_generator.py --city "Houston" --state "TX"
  python3 tools/creditdoc_city_guide_generator.py --list-next 20
  python3 tools/creditdoc_city_guide_generator.py --stats
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timezone

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from creditdoc_content_guardrails import reject_if_unsafe, supplied_fact_values
from creditdoc_content_repair import repair_unsafe_json

PROJECT_DIR = os.path.join(SCRIPT_DIR, "..", "creditdoc")
REGULATOR_DB = os.path.join(PROJECT_DIR, "data", "regulator.db")
CREDITDOC_DB = os.path.join(PROJECT_DIR, "data", "creditdoc.db")
SUPABASE_ENV = os.path.join(SCRIPT_DIR, ".supabase-creditdoc.env")
CITIES_CSV = os.path.join(PROJECT_DIR, "US Cities", "us_all_places_by_population.csv")

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

import csv

def _load_city_populations():
    """Load all 31K+ cities from the master CSV instead of a hardcoded 221-city dict."""
    pops = {}
    if os.path.exists(CITIES_CSV):
        with open(CITIES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    place = row["Place Name"].replace(" city", "").replace(" town", "").replace(" village", "").strip()
                    state_name = row["State"].strip()
                    pop = int(row["Population"])
                    state_abbr = next((k for k, v in US_STATES.items() if v == state_name), None)
                    if state_abbr:
                        pops[(place, state_abbr)] = pop
                except (ValueError, KeyError, StopIteration):
                    continue
    return pops

CITY_POPULATIONS = _load_city_populations()


def load_supabase_env():
    env = {}
    for line in open(SUPABASE_ENV):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v.strip('"').strip("'")
    return env


def supabase_headers(env):
    return {
        "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        "Content-Type": "application/json",
    }


def get_existing_slugs(env):
    hdr = supabase_headers(env)
    r = requests.get(
        f"{env['SUPABASE_URL'].rstrip('/')}/rest/v1/city_guides",
        headers=hdr,
        params={"select": "slug"},
    )
    r.raise_for_status()
    return {row["slug"] for row in r.json()}


def make_slug(city, state_abbr):
    slug = f"{city}-{state_abbr}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def get_city_queue(existing_slugs, limit=50):
    """Build priority queue using DataForSEO opportunity scores when available,
    falling back to population + branch_count if keyword data hasn't been pulled yet.

    Opportunity scoring: (volume × CPC_intent) / sqrt(competition_difficulty)
    See tools/creditdoc_city_keyword_priority.py for the pull script.
    """
    # Try keyword opportunity scoring first
    keyword_db = os.path.join(PROJECT_DIR, "data", "keyword_volume.db")
    opportunity_scores = {}
    if os.path.exists(keyword_db):
        try:
            kconn = sqlite3.connect(keyword_db)
            rows = kconn.execute("""
                SELECT city, state, opportunity_score, total_volume
                FROM city_opportunity_rank
                WHERE opportunity_score > 0
                ORDER BY opportunity_score DESC
            """).fetchall()
            kconn.close()
            for city, state, opp, vol in rows:
                opportunity_scores[(city, state)] = (opp, vol)
        except Exception:
            pass

    conn = sqlite3.connect(REGULATOR_DB)
    rows = conn.execute("""
        SELECT city, state, COUNT(*) as branch_count
        FROM fdic_locations
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city, state
        ORDER BY COUNT(*) DESC
    """).fetchall()
    conn.close()

    queue = []
    for city, state, branch_count in rows:
        if state not in US_STATES:
            continue
        city_title = city.title()
        slug = make_slug(city_title, state)
        if slug in existing_slugs:
            continue
        pop = CITY_POPULATIONS.get((city_title, state), 0)

        # Use keyword opportunity score if available, else fall back to population
        has_keyword_data = (city_title, state) in opportunity_scores
        if has_keyword_data:
            opp, vol = opportunity_scores[(city_title, state)]
            score = opp
        else:
            score = pop * 0.7 + branch_count * 1000 * 0.3

        queue.append({
            "city": city_title,
            "state_abbr": state,
            "state_name": US_STATES[state],
            "slug": slug,
            "population": pop if pop > 0 else None,
            "branch_count": branch_count,
            "score": score,
            "has_keyword_data": has_keyword_data,
        })

    # Two-tier sort: keyword-scored cities FIRST (by opportunity), then population-fallback
    queue.sort(key=lambda x: (x["has_keyword_data"], x["score"]), reverse=True)
    return queue[:limit]


def get_state_data(state_abbr, env):
    hdr = supabase_headers(env)
    r = requests.get(
        f"{env['SUPABASE_URL'].rstrip('/')}/rest/v1/states",
        headers=hdr,
        params={"abbr": f"eq.{state_abbr}", "select": "body_inline,name"},
    )
    r.raise_for_status()
    data = r.json()
    if data and data[0].get("body_inline"):
        return data[0]["body_inline"]
    return {}


def get_local_stats(city, state_abbr):
    """Pull local statistics from regulator.db."""
    stats = {}
    conn = sqlite3.connect(REGULATOR_DB)

    # FDIC branch count + bank names
    branches = conn.execute(
        "SELECT branch_name, COUNT(*) FROM fdic_locations WHERE UPPER(city)=? AND state=? GROUP BY branch_name ORDER BY COUNT(*) DESC LIMIT 10",
        (city.upper(), state_abbr),
    ).fetchall()
    stats["top_banks"] = [{"name": b[0], "branches": b[1]} for b in branches]
    stats["total_branches"] = sum(b[1] for b in branches)
    stats["total_institutions"] = len(branches)

    # FDIC total for the city
    total = conn.execute(
        "SELECT COUNT(*) FROM fdic_locations WHERE UPPER(city)=? AND state=?",
        (city.upper(), state_abbr),
    ).fetchone()[0]
    stats["total_branches"] = total

    # SBA loans in state
    sba = conn.execute(
        "SELECT COUNT(*), ROUND(SUM(gross_approval)/1000000, 1) FROM sba_loans WHERE borrower_state=?",
        (state_abbr,),
    ).fetchone()
    stats["sba_loans_count"] = sba[0] if sba else 0
    stats["sba_total_approved_m"] = sba[1] if sba else 0

    # CFPB complaints in state
    cfpb = conn.execute(
        "SELECT COUNT(*) FROM cfpb_complaints WHERE state=?", (state_abbr,)
    ).fetchone()
    stats["cfpb_complaints_state"] = cfpb[0] if cfpb else 0

    conn.close()
    return stats


def _money_variants_from_millions(amount_m):
    """Return display variants for a dollar amount stored in millions."""
    try:
        amount = float(amount_m or 0)
    except (TypeError, ValueError):
        return set()
    if amount <= 0:
        return set()

    values = {
        f"${amount:g}M",
        f"${amount:g} M",
        f"${amount:,.1f} million",
    }
    if amount >= 1000:
        billions = amount / 1000
        rounded_b = round(billions)
        floor_one_decimal_b = int(billions * 10) / 10
        values.update({
            f"${rounded_b:g}",
            f"${rounded_b:g}B",
            f"${rounded_b:g}B+",
            f"${billions:g} billion",
            f"${floor_one_decimal_b:.1f} billion",
            f"${billions:.1f} billion",
            f"${billions:.2f} billion",
            f"${rounded_b:g} billion",
            f"${rounded_b:g} billion+",
        })
    return values


def _city_guardrail_allowed_values(city_info, state_data, local_stats):
    """Build the city-guide allow-list from prompt facts and public program facts.

    The shared guardrail protects against invented company prices, BBB/Google
    ratings, APRs, and guarantees. City guides also contain public law, SBA,
    FDIC, and CFPB facts, so this function explicitly allows those sourced facts
    without loosening company-specific validation.
    """
    allowed = supplied_fact_values([city_info, state_data, local_stats])

    income = state_data.get("median_household_income")
    if income:
        try:
            allowed.add(f"${int(float(str(income).replace(',', ''))):,}")
        except (TypeError, ValueError):
            pass

    sba_total_m = local_stats.get("sba_total_approved_m")
    allowed.update(_money_variants_from_millions(sba_total_m))

    # Standard public SBA/federal program figures commonly referenced in city
    # guides. These are not provider-specific offers or invented company claims.
    allowed.update({
        "$5 million",
        "$50,000",
        "$500,000",
        "$2,000",
        "$700",
        "$600",
        "$500",
        "$300",
        "$100",
        "$28",
        "$15",
        "28% APR",
        "28%",
        "35%",
        "30%",
        "400% APR",
        "400%",
        "391% APR",
        "391%",
        "390% APR",
        "390%",
        "300% APR",
        "300%",
        "25%",
        "18% interest",
        "18%",
        "15% interest",
        "15%",
        "12%",
        "10% interest",
        "10%",
        "6%",
    })

    return allowed


def _city_source_context(city_info, state_data, local_stats):
    return json.dumps(
        {
            "city_info": city_info,
            "state_data": state_data,
            "local_stats": local_stats,
            "allowed_public_program_context": [
                "SBA 7(a), 504, Microloan, SBA Express, and Disaster Loan program limits",
                "state usury/payday law summaries supplied in state_data",
                "FDIC/SBA/CFPB public statistics supplied in local_stats",
                "general credit education such as utilization percentages",
            ],
        },
        ensure_ascii=False,
        default=str,
    )


def get_lender_count_for_state(state_abbr):
    """Count indexed lenders in the state from creditdoc.db."""
    try:
        conn = sqlite3.connect(CREDITDOC_DB)
        row = conn.execute(
            "SELECT COUNT(*) FROM lenders WHERE state=? AND processing_status='ready_for_index'",
            (state_abbr,),
        ).fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


AI_ENV_FILES = (
    os.path.join(PROJECT_DIR, "..", ".env"),
    os.path.expanduser("~/.hermes/.env"),
)
OPENAI_KEY_FILE = os.path.join(SCRIPT_DIR, ".openai-api-key")


def _read_env_value(paths, key):
    """Read one key from simple KEY=value env files without exporting secrets."""
    for path in paths:
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k == key:
                        return v.strip().strip('"').strip("'")
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return ""


def _read_key_file(path):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
                return line
    except Exception:
        return ""
    return ""


def _get_api_config():
    """Return an OpenAI fallback (api_key, base_url, model, provider) tuple if primary routing fails."""
    openai_key = (
        os.environ.get("OPENAI_API_KEY", "")
        or _read_env_value(AI_ENV_FILES, "OPENAI_API_KEY")
        or _read_key_file(OPENAI_KEY_FILE)
    )
    if openai_key:
        model = os.environ.get("OPENAI_MODEL", "") or _read_env_value(AI_ENV_FILES, "OPENAI_MODEL") or "gpt-4.1"
        return openai_key, "https://api.openai.com", model, "openai"

    raise RuntimeError("No OpenAI key found for city guide generation.")


def _call_openai_json(api_key, base_url, model, prompt, max_tokens=4000):
    """Call OpenAI with JSON mode for city-guide structured output."""
    r = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _parse_city_json(text, city_slug):
    """Parse model JSON and save bad output for diagnosis if parsing fails."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        debug_path = f"/tmp/creditdoc_city_guide_debug_{city_slug}.txt"
        with open(debug_path, "w") as f:
            f.write(text)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


def generate_city_content(city_info, state_data, local_stats):
    """Use OpenAI to generate unique editorial + localized Q&A."""
    city = city_info["city"]
    state = city_info["state_name"]
    state_abbr = city_info["state_abbr"]
    pop = city_info.get("population") or "unknown"

    # Extract useful state context
    credit_repair_laws = state_data.get("credit_repair_laws", {})
    if isinstance(credit_repair_laws, dict):
        cr_summary = f"Statute: {credit_repair_laws.get('statute', 'N/A')}. Bond required: {credit_repair_laws.get('bond', 'N/A')}."
    else:
        cr_summary = str(credit_repair_laws) if credit_repair_laws else "No specific state law found."

    usury_cap = state_data.get("usury_cap", "varies")
    payday_status = state_data.get("payday_loan_status", "unknown")
    consumer_protection = state_data.get("consumer_protection_agency", "State Attorney General")
    consumer_url = state_data.get("consumer_protection_url", "")
    avg_credit_score = state_data.get("avg_credit_score", "")
    median_income = state_data.get("median_household_income", "")

    top_banks_str = ", ".join(
        [f"{b['name']} ({b['branches']} branches)" for b in local_stats.get("top_banks", [])[:5]]
    ) or "various local and national banks"

    prompt = f"""You are a financial content writer for CreditDoc.co, a credit and lending directory.
Write content for a local city guide page for {city}, {state} ({state_abbr}).

CITY FACTS:
- Population: {pop}
- State average credit score: {avg_credit_score}
- State median household income: {median_income}
- FDIC-insured banking locations in {city}: {local_stats.get('total_branches', 'N/A')}
- Top banks by branch count: {top_banks_str}
- SBA loans in {state_abbr}: {local_stats.get('sba_loans_count', 'N/A')} loans totaling ${local_stats.get('sba_total_approved_m', 'N/A')}M
- CFPB complaints in {state_abbr}: {local_stats.get('cfpb_complaints_state', 'N/A')}
- Usury cap: {usury_cap}
- Payday loan status: {payday_status}
- Credit repair laws: {cr_summary}
- Consumer protection: {consumer_protection}
- Consumer protection URL: {consumer_url}

SOURCE AND FACT RULES:
- Use only the city/state/local facts listed above and official/state/federal resource details supplied in the source context.
- Do NOT invent current prices, fees, APRs, BBB ratings, Google ratings, star ratings, or guarantees for any local company, lender, card, app, or service.
- Do NOT invent local organization names, street addresses, phone numbers, URLs, office names, ratings, or credentials.
- If a provider-specific price/rate/rating/guarantee is not supplied in the facts above, omit it.
- If a specific local resource is not supplied, use the state consumer protection agency, SBA/SCORE/HUD official lookup paths, or conservative "verify directly" language.
- General legal caps and state-law summaries are allowed when tied to the state data above.

OUTPUT FORMAT — Return a single JSON object with these exact keys:

1. "editorial" — A 400-600 word editorial in HTML paragraphs (<p>...</p>) about {city}'s financial landscape.
   Cover: cost of living context, credit access disparities across neighborhoods (name 2-3 specific neighborhoods),
   local economic drivers, banking access, and what residents should know about credit in {city}.
   Be specific to {city} — mention real neighborhoods, employers, and economic facts.
   DO NOT use generic filler. Every sentence must be specific to {city}.

2. "credit_tips" — Array of 6 strings. Actionable credit improvement tips specific to {city}/{state}.
   Reference state laws, official agencies, and verified resources by name when supplied.

3. "local_questions" — Array of 7 objects, each with "q" (question) and "a" (HTML answer with <p> tags).
   Questions MUST be localized: "What is the best credit repair company in {city}?" not generic.
   Answers must reference {state} law when supplied, official resources when supplied, and include internal links:
   - <a href='https://www.creditdoc.co/best/best-credit-repair-companies/'>best credit repair companies</a>
   - <a href='https://www.creditdoc.co/best/best-personal-loan-lenders/'>best personal loan lenders</a>
   - <a href='https://www.creditdoc.co/best/best-sba-loans/'>best SBA loans</a>
   - <a href='https://www.creditdoc.co/best/best-debt-relief-companies/'>best debt relief companies</a>
   - <a href='https://www.creditdoc.co/best/best-secured-credit-cards/'>best secured credit cards</a>
   Questions should cover: credit repair, credit score improvement, SBA loans, debt consolidation,
   credit unions, payday loan alternatives, and identity theft protection — all localized to {city}.

4. "local_resources" — Array of 2-5 objects with "name", "type", "phone", "address", "url".
   Only include organizations, addresses, phones, and URLs that are supplied above or are official state/federal resources.
   If exact street address or phone is not supplied, omit that field instead of guessing.
   Acceptable safer entries include the supplied consumer protection agency, SBA district-level office if supplied,
   HUD housing counseling lookup, SCORE chapter lookup, and official state legal-aid or attorney-general resources.

5. "consumer_protection" — Object with "agency", "phone", "url", "filing_info".
   The state consumer protection agency for {state}. Use only supplied/official contact info; omit unknown fields.

6. "sba_info" — Object with "office", "address", "phone", "programs" (array of strings).
   The SBA district office serving {city}. Use only supplied/official info; omit unknown fields.

7. "seo_title" — STRICTLY 50-58 chars (HARD MAX 58). Must be UNIQUE and target real search intent.
   Include {city} and {state_abbr}. Count characters carefully — Google truncates at 60.
   Examples (all under 58 chars):
   - "Denver, CO Credit Repair: Top Services (2026)"
   - "Houston, TX Credit & Lending Guide | CreditDoc"
   - "Phoenix, AZ Credit Repair — Free Resources"
   - "Chicago Credit Guide: Repair & Local Lenders"
   DO NOT exceed 58 characters. DO NOT use generic titles — each must be unique and click-worthy.

8. "meta_description" — 145-155 chars. Write a compelling, specific description that makes searchers click.
   Include {city}, {state_abbr}, a specific benefit or stat, and a call-to-action.
   WRONG: "Find credit repair and lending in Dallas, TX. Compare lenders with CreditDoc."
   RIGHT: "Dallas, TX has 847 FDIC-insured branches and 12 HUD-approved credit counselors. Compare the best credit repair companies and lenders near you."

Return ONLY the JSON object, no markdown fences, no explanation."""

    try:
        sys.path.insert(0, SCRIPT_DIR)
        from creditdoc_oauth import call_ai
        text = call_ai(prompt, model="gpt-4.1", max_tokens=4000, timeout_secs=120)
    except Exception as primary_error:
        api_key, base_url, model, provider = _get_api_config()
        if provider == "openai":
            text = _call_openai_json(api_key, base_url, model, prompt)
        else:
            raise RuntimeError(f"Unsupported city guide AI provider after primary failure: {provider}") from primary_error
    try:
        parsed = _parse_city_json(text, city_info["slug"])
        allowed_values = _city_guardrail_allowed_values(city_info, state_data, local_stats)
        guardrail_failures = reject_if_unsafe(parsed, allowed_values=allowed_values)
        if guardrail_failures:
            parsed, guardrail_failures = repair_unsafe_json(
                parsed,
                guardrail_failures,
                content_type="city guide",
                source_context=_city_source_context(city_info, state_data, local_stats),
                allowed_values=allowed_values,
                max_tokens=4000,
            )
        if guardrail_failures:
            raise ValueError("CreditDoc city guardrails failed after content repair: " + " | ".join(guardrail_failures[:8]))
        return parsed
    except json.JSONDecodeError:
        openai_key = (
        os.environ.get("OPENAI_API_KEY", "")
        or _read_env_value(AI_ENV_FILES, "OPENAI_API_KEY")
        or _read_key_file(OPENAI_KEY_FILE)
    )
        if not openai_key:
            raise
        openai_model = os.environ.get("OPENAI_MODEL", "") or _read_env_value(AI_ENV_FILES, "OPENAI_MODEL") or "gpt-4.1"
        repair_prompt = f"""Repair this malformed city-guide response into valid JSON only.

Requirements:
- Return one JSON object only.
- Preserve the same keys and substantive content.
- Escape strings correctly.
- Do not add markdown fences.

Malformed response:
{text}
"""
        repaired = _call_openai_json(openai_key, "https://api.openai.com", openai_model, repair_prompt)
        parsed = _parse_city_json(repaired, city_info["slug"])
        allowed_values = _city_guardrail_allowed_values(city_info, state_data, local_stats)
        guardrail_failures = reject_if_unsafe(parsed, allowed_values=allowed_values)
        if guardrail_failures:
            parsed, guardrail_failures = repair_unsafe_json(
                parsed,
                guardrail_failures,
                content_type="city guide",
                source_context=_city_source_context(city_info, state_data, local_stats),
                allowed_values=allowed_values,
                max_tokens=4000,
            )
        if guardrail_failures:
            raise ValueError("CreditDoc city guardrails failed after repair: " + " | ".join(guardrail_failures[:8]))
        return parsed


def insert_city_guide(city_info, content, env):
    """Insert a city guide into Supabase."""
    hdr = supabase_headers(env)
    hdr["Prefer"] = "return=representation"

    body_inline = {
        "editorial": content["editorial"],
        "credit_tips": content["credit_tips"],
        "local_questions": content["local_questions"],
        "local_resources": content["local_resources"],
        "consumer_protection": content["consumer_protection"],
        "sba_info": content["sba_info"],
    }

    payload = {
        "slug": city_info["slug"],
        "city": city_info["city"],
        "state_abbr": city_info["state_abbr"],
        "state_name": city_info["state_name"],
        "population": city_info.get("population"),
        "body_inline": body_inline,  # dict, NOT json.dumps
        "seo_title": content.get("seo_title", f"Credit & Lending in {city_info['city']}, {city_info['state_abbr']} | CreditDoc")[:60],
        "meta_description": content.get("meta_description", "")[:160],
        "status": "ready_for_index",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Try state-level stats from Supabase states table
    # (median_income, avg_credit_score etc. will be populated from state data if available)

    r = requests.post(
        f"{env['SUPABASE_URL'].rstrip('/')}/rest/v1/city_guides",
        headers=hdr,
        json=payload,
    )

    if r.status_code in (200, 201):
        result = r.json()
        return result[0] if isinstance(result, list) else result
    elif r.status_code == 409:
        print(f"  [SKIP] {city_info['slug']} already exists")
        return None
    else:
        print(f"  [ERROR] {r.status_code}: {r.text[:300]}")
        r.raise_for_status()


def send_alert(subject, body):
    """Send completion alert via Harvey email."""
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from agentmail import AgentMail

        api_key = _read_key_file(os.path.join(SCRIPT_DIR, ".agentmail-api-key"))
        if not api_key:
            raise RuntimeError("AgentMail API key file is missing or empty")

        client = AgentMail(api_key=api_key)
        client.inboxes.messages.send(
            "longleader503@agentmail.to",
            to="gian.eao@gmail.com",
            subject=subject,
            text=re.sub(r"<[^>]+>", "", body),
            html=body,
        )
    except Exception as e:
        print(f"  [WARN] Could not send email alert: {subject} ({type(e).__name__}: {e})")


def cmd_stats(env):
    """Show pipeline stats."""
    existing = get_existing_slugs(env)
    print(f"City guides in Supabase: {len(existing)}")
    for slug in sorted(existing):
        print(f"  - {slug}")

    queue = get_city_queue(existing, limit=10)
    print(f"\nNext {len(queue)} cities in queue:")
    for c in queue:
        pop_str = f"{c['population']:,}" if c['population'] else "?"
        print(f"  {c['city']}, {c['state_abbr']} (pop {pop_str}, {c['branch_count']} FDIC branches)")


def cmd_list_next(env, limit):
    """List next N cities in queue."""
    existing = get_existing_slugs(env)
    queue = get_city_queue(existing, limit=limit)
    print(f"Next {len(queue)} cities (of {len(CITY_POPULATIONS):,} tracked):")
    for i, c in enumerate(queue, 1):
        pop_str = f"{c['population']:,}" if c['population'] else "?"
        print(f"  {i:3d}. {c['city']}, {c['state_abbr']} — pop {pop_str}, {c['branch_count']} FDIC branches, score {c['score']:.0f}")


def cmd_generate(env, batch_size=5, specific_city=None, specific_state=None):
    """Generate city guide(s)."""
    existing = get_existing_slugs(env)

    if specific_city and specific_state:
        slug = make_slug(specific_city, specific_state)
        if slug in existing:
            print(f"[SKIP] {slug} already exists in Supabase")
            return
        cities = [{
            "city": specific_city.title(),
            "state_abbr": specific_state.upper(),
            "state_name": US_STATES.get(specific_state.upper(), specific_state),
            "slug": slug,
            "population": CITY_POPULATIONS.get((specific_city.title(), specific_state.upper())),
            "branch_count": 0,
        }]
    else:
        cities = get_city_queue(existing, limit=batch_size)

    if not cities:
        print("[DONE] No cities remaining in queue")
        return

    print(f"Generating {len(cities)} city guide(s)...\n")
    successes = []
    failures = []

    for i, city_info in enumerate(cities, 1):
        city = city_info["city"]
        state_abbr = city_info["state_abbr"]
        print(f"[{i}/{len(cities)}] {city}, {state_abbr}...")

        try:
            # Gather data
            state_data = get_state_data(state_abbr, env)
            local_stats = get_local_stats(city, state_abbr)
            lender_count = get_lender_count_for_state(state_abbr)

            print(f"  Data: {local_stats['total_branches']} branches, {local_stats.get('sba_loans_count', 0)} SBA loans, {lender_count} indexed lenders in {state_abbr}")

            # Generate content via OpenAI
            print("  Generating content via OpenAI...")
            content = generate_city_content(city_info, state_data, local_stats)

            # Validate
            editorial_len = len(content.get("editorial", ""))
            q_count = len(content.get("local_questions", []))
            print(f"  Content: {editorial_len} chars editorial, {q_count} questions, {len(content.get('credit_tips', []))} tips")

            if editorial_len < 500:
                print(f"  [WARN] Editorial too short ({editorial_len} chars), regenerating...")
                content = generate_city_content(city_info, state_data, local_stats)
                editorial_len = len(content.get("editorial", ""))

            # Insert into Supabase
            result = insert_city_guide(city_info, content, env)
            if result:
                print(f"  [OK] https://www.creditdoc.co/credit-guide/{city_info['slug']}/")
                successes.append(city_info)

            # Rate limit AI/API calls.
            if i < len(cities):
                time.sleep(3)

        except Exception as e:
            print(f"  [FAIL] {e}")
            traceback.print_exc()
            failures.append({"city": city_info, "error": str(e)})

    # Summary
    print(f"\n{'='*60}")
    print(f"Generated: {len(successes)} | Failed: {len(failures)}")
    for s in successes:
        print(f"  ✓ https://www.creditdoc.co/credit-guide/{s['slug']}/")
    for f in failures:
        print(f"  ✗ {f['city']['city']}, {f['city']['state_abbr']}: {f['error'][:100]}")

    if failures and not successes:
        sys.exit(1)

    # Email alert
    if successes:
        urls = "".join(
            f"<li><a href='https://www.creditdoc.co/credit-guide/{s['slug']}/'>{s['city']}, {s['state_abbr']}</a></li>"
            for s in successes
        )
        send_alert(
            f"CreditDoc: {len(successes)} new city guide(s) published",
            f"<h3>New City Guides</h3><ul>{urls}</ul><p>Failed: {len(failures)}</p>",
        )


def main():
    parser = argparse.ArgumentParser(description="CreditDoc City Guide Generator")
    parser.add_argument("--batch", type=int, default=10, help="Number of cities to generate (default 10)")
    parser.add_argument("--city", type=str, help="Generate for a specific city")
    parser.add_argument("--state", type=str, help="State abbreviation (with --city)")
    parser.add_argument("--list-next", type=int, metavar="N", help="List next N cities in queue")
    parser.add_argument("--stats", action="store_true", help="Show pipeline stats")
    args = parser.parse_args()

    env = load_supabase_env()

    if args.stats:
        cmd_stats(env)
    elif args.list_next:
        cmd_list_next(env, args.list_next)
    elif args.city:
        if not args.state:
            print("ERROR: --state required with --city")
            sys.exit(1)
        cmd_generate(env, specific_city=args.city, specific_state=args.state)
    else:
        cmd_generate(env, batch_size=args.batch)


if __name__ == "__main__":
    main()
