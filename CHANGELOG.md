# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-05-28

Initial public release.

### Added
- Core framework: pydantic types, pluggable provider adapters (Anthropic, OpenAI, deterministic mock), async runner with concurrency control.
- Eight attack categories as surrogate-only triggers, each traceable to a published source: DAN, PAIR, GCG-TRANSFER, CRESCENDO, INDIRECT-INJECTION, ENCODE, MANY-SHOT, XSTEST-FALSE.
- Datasets: `attacks_smoke` (10 items), `attacks_full` (50 items), `benigns_smoke` (10), `benigns_full` (30).
- Five baseline defenses: `keyword_filter_v1`, `system_prompt_hardener_v1`, `heuristic_injection_detector_v1`, `length_guard_v1`, `classifier_guard_v1`.
- Scoring with bootstrap 95% confidence intervals; ASR, FRR, composite AERIS Score.
- LLM-as-judge with a versioned rubric, plus a heuristic baseline judge.
- Self-contained HTML report generator (`aeris report`).
- Reproducibility manifest (`manifest.json`) written with every run.
- Safety controls: forbidden-substring audit on every attack template, mandatory `--i-have-permission-to-test` flag.
- Docs: threat model, methodology, safety posture, responsible disclosure, results-writeup template.
- CI: lint (ruff), type-check (mypy strict), tests (pytest) on Python 3.10–3.12, plus an end-to-end smoke run against the mock provider.

### Safety
- All attack templates are surrogate triggers whose successful completion does not yield a usable harm artifact (see `docs/safety_posture.md`).
- No CBRN, malware, CSAM, or targeted-harm content. No novel attacks — published patterns only.
