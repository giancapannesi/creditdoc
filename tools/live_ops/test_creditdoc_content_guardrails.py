#!/usr/bin/env python3
"""Regression tests for CreditDoc generated-content guardrails.

This is intentionally dependency-free so cron/verifier jobs can run it on the
VPS without pytest. It protects against the recurring class of failures where
LLM-generated content invents current provider facts or misattributes sourced
values in comparison pages.
"""

from __future__ import annotations

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from creditdoc_content_guardrails import reject_if_unsafe, supplied_fact_values  # noqa: E402
from creditdoc_city_guide_generator import _city_guardrail_allowed_values  # noqa: E402


def assert_fails(label: str, text: object, expected_substring: str, **kwargs: object) -> None:
    failures = reject_if_unsafe(text, **kwargs)
    joined = "\n".join(failures)
    if expected_substring not in joined:
        raise AssertionError(f"{label}: expected failure containing {expected_substring!r}, got {failures!r}")


def assert_passes(label: str, text: object, **kwargs: object) -> None:
    failures = reject_if_unsafe(text, **kwargs)
    if failures:
        raise AssertionError(f"{label}: expected no failures, got {failures!r}")


def main() -> int:
    assert_fails(
        "natural monthly price and google rating",
        "Lexington Law is $99 per month. It has 4.9 out of 5 on Google.",
        "$99",
    )
    assert_fails(
        "named loan apr",
        "Acme personal loans are 12% APR.",
        "12% APR",
    )
    assert_fails(
        "approval odds",
        "Acme approves 95% of applicants.",
        "95%",
    )
    assert_fails(
        "money-back guarantee",
        "Lexington Law offers a money-back guarantee.",
        "money-back guarantee",
    )
    assert_passes(
        "legal educational mapr context",
        "The Military Lending Act caps covered loans at 36% MAPR for covered borrowers.",
    )
    assert_passes(
        "city guide sourced sba and law facts",
        {
            "body": (
                "California processed 43,459 SBA loans totaling over $27.3 billion. "
                "SBA 7(a) loans can be up to $5 million, microloans can be up to "
                "$50,000, and SBA Express can be up to $500,000. Payday loan fees "
                "are capped at $15 per $100, and residents should keep utilization "
                "under 30%."
            )
        },
        allowed_values=_city_guardrail_allowed_values(
            {"city": "Visalia", "state_abbr": "CA", "state_name": "California", "slug": "visalia-ca"},
            {
                "median_household_income": 91905,
                "usury_cap": "10% interest cap",
                "payday_loan_status": "Payday loans allowed with fees capped at $15 per $100",
            },
            {"sba_total_approved_m": 27372.6, "sba_loans_count": 43459},
        ),
    )
    assert_passes(
        "city guide sourced punctuation variant",
        "Florida caps interest rates at 18% for loans under $500,000, with a 25% criminal usury threshold.",
        allowed_values={"18%", "$500,000", "25%"},
    )

    source_a = "Name: Alpha\nMonthly Price: $99\nRating: 4.8/5 (100 reviews)"
    source_b = "Name: Beta\nMonthly Price: Contact for pricing\nRating: 3.2/5 (12 reviews)"
    comparison_kwargs = {
        "allowed_values": supplied_fact_values([source_a, source_b]),
        "entity_allowed_values": {
            "Alpha": supplied_fact_values([source_a]),
            "Beta": supplied_fact_values([source_b]),
        },
    }
    assert_passes(
        "right-company sourced values",
        {"summary": "Alpha costs $99 per month. Alpha has 4.8 out of 5 on Google."},
        **comparison_kwargs,
    )
    assert_fails(
        "wrong-company sourced value",
        {"summary": "Beta costs $99 per month."},
        "misattributed sourced value",
        **comparison_kwargs,
    )
    assert_passes(
        "comparison sentence with entity-matched ratings",
        {"summary": "Alpha has a 4.8 out of 5 rating, while Beta has a 3.2 out of 5 rating."},
        **comparison_kwargs,
    )
    assert_fails(
        "comparison sentence with crossed rating",
        {"summary": "Beta has a 4.8 out of 5 rating, while Alpha has a 3.2 out of 5 rating."},
        "misattributed sourced value",
        **comparison_kwargs,
    )
    bbb_source = "Name: Gamma\nBBB Rating: A+ (Accredited)\nMonthly Price: Contact for pricing"
    bbb_kwargs = {
        "allowed_values": supplied_fact_values([bbb_source]),
        "entity_allowed_values": {"Gamma": supplied_fact_values([bbb_source])},
    }
    assert_passes(
        "bbb rating source format canonicalizes",
        {"summary": "Gamma has a BBB A+ rating."},
        **bbb_kwargs,
    )
    google_source = "Name: 007 Credit Agent\nCreditDoc Rating: 4.3/5\nGoogle Rating: 4.7/5 (176 reviews)\nBBB Rating: NR"
    google_kwargs = {"allowed_values": supplied_fact_values([google_source])}
    assert_passes(
        "imported google source value",
        {"summary": "007 Credit Agent has a Google rating of 4.7 out of 5 from 176 reviews."},
        **google_kwargs,
    )
    assert_fails(
        "invented google source value",
        {"summary": "007 Credit Agent has a Google rating of 4.9 out of 5 from 999 reviews."},
        "4.9 out of 5",
        **google_kwargs,
    )

    print("OK: CreditDoc content guardrail regression tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
