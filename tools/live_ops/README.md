# CreditDoc Live Operations Tool Mirrors

This directory tracks selected live scripts from `/srv/BusinessOps/tools`.

The live content engines and verifiers are executed from `/srv/BusinessOps/tools`
by cron. That directory is not currently a git repository, so important changes
must be mirrored here whenever they are made live.

Mirrored files in this folder are committed snapshots for review, rollback
reference, and repeat-proofing. If a live script changes, update the matching
file here in the same work session and commit the mirror with the handoff notes.

Current mirrored guardrail set:

- `creditdoc_content_guardrails.py`
- `creditdoc_city_guide_generator.py`
- `creditdoc_comparison_generator.py`
- `test_creditdoc_content_guardrails.py`
- `creditdoc_content_engine_daily_verify.py`
