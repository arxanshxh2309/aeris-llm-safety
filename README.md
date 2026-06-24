# AERIS — A Defensive Red-Teaming Framework for Large Language Models

> A reproducible benchmark and defense suite for measuring how reliably an LLM resists adversarial inputs — prompt injection, jailbreaks, harmful-content elicitation, and indirect attacks via tool use.

**Status:** Research prototype • **License:** MIT • **Targets:** OpenAI, Anthropic, Google, xAI, Perplexity APIs (and any HTTP-compatible LLM)

---

## Why this exists

Frontier LLMs (ChatGPT, Claude, Gemini, Grok, Perplexity) are deployed to hundreds of millions of users. They are also routinely tricked into producing outputs their developers explicitly tried to prevent. The published academic work on this — from MIT CSAIL, Stanford CRFM, Harvard's Berkman Klein, Anthropic, and OpenAI — has converged on a few hard truths:

1. **Single-prompt robustness is solved-ish; multi-turn and indirect injection are not.** ([Greshake et al. 2023](https://arxiv.org/abs/2302.12173), [Wei, Haghtalab, Steinhardt 2023](https://arxiv.org/abs/2307.02483))
2. **Defenses must be evaluated against adaptive attackers**, not fixed test sets. ([Tramèr et al. 2020](https://arxiv.org/abs/2002.08347))
3. **Refusal is not the same as safety.** A model that refuses everything is useless; a model that refuses only when it should is the real target. ([Röttger et al. XSTest, 2023](https://arxiv.org/abs/2308.01263))

AERIS is a small, careful contribution to point (1) and (2) — a framework that lets a researcher run a fixed attack suite against any LLM, measure how often it fails, layer on defenses, and re-measure. It is **purely defensive**: it ships no novel attack payloads, only published ones, and its purpose is to make models safer to deploy.

## What's in the box

```
aeris-llm-safety/
├── src/aeris/            Core library — adapters, runner, defenses, judge, scoring, report
├── attacks/              Catalogued, published attack templates (with citations)
├── defenses/             Input/output filters, classifier-based guardrails
├── datasets/             Prompts: smoke + full attack/benign sets (surrogate triggers only)
├── configs/              YAML experiment definitions (smoke, smoke_defended, headline)
├── tests/                35 tests — scoring, defenses, providers, attack-safety audit, e2e
├── scripts/              CLI helpers (quickstart)
├── results/              Run artifacts (manifest.json, records.jsonl, summary.json, report.html)
└── docs/                 Threat model, methodology, safety posture, responsible disclosure
```

## Headline experiment

Run a frontier model through 8 published attack categories, with and without AERIS defenses in front of it, and produce a leaderboard.

```bash
python -m aeris.run --config configs/headline.yaml --model anthropic/claude-sonnet-4-5
# → results/2026-05-26_claude-sonnet-4-5/report.html
```

Output: per-attack attack success rate (ASR), false-refusal rate on benign prompts (FRR), and a single composite **AERIS Score** (ASR↓ + FRR↓, weighted). Every run also writes a self-contained `report.html` — an editorial-style dashboard with the headline score, per-category breakdown bars, defense-action histogram, and sample failures. Regenerate it any time with `aeris report <run_dir>`.

## Threat model (the part most projects skip)

See [`docs/threat_model.md`](docs/threat_model.md). Briefly: attacker has black-box query access, no gradient access, may control content that the LLM ingests as context (RAG documents, tool outputs, web pages). Out of scope: model-weight extraction, training-time poisoning, side channels. This matters because it scopes which defenses are even meaningful — a defense against gradient-based attacks is irrelevant for a closed-API model.

## Safety posture — what this project will NOT do

This repository is explicitly designed to be **non-harmful**:

- **No novel attacks.** Every attack template is from a published paper, cited in `attacks/REGISTRY.md`. We do not develop new jailbreaks.
- **No CBRN, no CSAM, no targeted-harm payloads.** Attack templates probe *categories* (e.g., "refuse to give bomb instructions") using surrogate refusal-trigger prompts from HarmBench, not actual weapon synthesis instructions. The attack inputs are designed so that even if the model fails, the *output* is not useful to a real adversary.
- **Refusal-trigger surrogates.** We measure whether the model *would have* complied, not whether it produces dangerous content. See `docs/safety_posture.md`.
- **No live exfiltration tooling.** The indirect-injection harness simulates compromised tool outputs in a sandbox; it does not target real third-party services.
- **Rate-limited, logged, and auditable.** All runs produce a manifest. The CLI refuses to run against an endpoint without an explicit `--i-have-permission-to-test` flag.

## Quickstart

```bash
git clone https://github.com/arxanshxh2309/aeris-llm-safety
cd aeris-llm-safety
pip install -e ".[dev]"
cp .env.example .env  # add API keys for any providers you want to test

# Dry-run against the mock provider — no API calls, deterministic
python -m aeris.run --config configs/smoke.yaml --model mock/echo --i-have-permission-to-test

# Real run (uses your API key, ~$2 in tokens for the smoke config)
python -m aeris.run --config configs/smoke.yaml --model anthropic/claude-haiku-4-5 --i-have-permission-to-test
```

## Reading the rest

If you want to understand the project end-to-end, read in this order:

1. [`docs/threat_model.md`](docs/threat_model.md) — what we defend against and what we don't
2. [`docs/methodology.md`](docs/methodology.md) — how we score, why those metrics
3. [`attacks/REGISTRY.md`](attacks/REGISTRY.md) — every attack, its source paper, its rationale
4. [`defenses/REGISTRY.md`](defenses/REGISTRY.md) — every defense, what it catches, what it misses
5. [`docs/results_writeup.md`](docs/results_writeup.md) — what we found running this on real models

## Citation

```bibtex
@software{aeris_llm_safety_2026,
  title  = AERIS: A Defensive Red-Teaming Framework for Large Language Models,
  author = ARYAN SHAH,
  year   = 2026,
  url    = https://github.com/arxanshxh2309/aeris-llm-safety/
}
```

## Acknowledgments

This work builds on the public benchmarks and methodology of [HarmBench](https://www.harmbench.org/) (Mazeika et al., 2024), [XSTest](https://github.com/paul-rottger/exaggerated-safety) (Röttger et al., 2023), [TensorTrust](https://tensortrust.ai/) (Toyer et al., 2023), and the indirect-injection threat-modeling work of [Greshake et al. (2023)](https://arxiv.org/abs/2302.12173). The defenses are inspired by [Llama Guard](https://arxiv.org/abs/2312.06674), [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails), and Anthropic's [constitutional classifiers](https://www.anthropic.com/research/constitutional-classifiers) work.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
