# Architecture

This document describes how the pieces fit together. The design goal was
small, explicit modules that each do one thing, composed by a thin runner.
If you understand `types.py`, the rest follows.

## Module map

```
                         ┌──────────────┐
                         │   cli.py     │  typer entry point: `aeris run`
                         └──────┬───────┘
                                │ builds + invokes
                                ▼
                         ┌──────────────┐
                         │  runner.py   │  orchestration only — no policy
                         └──┬────┬────┬──┘
            ┌───────────────┘    │    └───────────────┐
            ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐     ┌──────────────┐
    │  attacks.py  │    │ defenses.py  │     │  judge.py    │
    │ load + audit │    │ pre/post     │     │ LLM-as-judge │
    │ YAML sets    │    │ pipeline     │     │ + heuristic  │
    └──────────────┘    └──────────────┘     └──────┬───────┘
            │                    │                  │
            └────────┬───────────┴──────────────────┘
                     ▼                    ▼
              ┌──────────────┐    ┌──────────────┐
              │ providers.py │    │  scoring.py  │  ASR/FRR + bootstrap CI
              │ adapters     │    └──────┬───────┘
              │ mock/anthr./ │           │
              │ openai       │           ▼
              └──────────────┘    ┌──────────────┐
                                  │  report.py   │  self-contained HTML
                                  └──────────────┘

         everything speaks in the dataclasses defined in types.py
```

## Data flow for one item

1. `attacks.load_attack_set` reads a YAML file, validates each entry against
   `AttackItem`, and runs `_audit_attack_set` (the forbidden-substring tripwire).
2. `runner._run_one` builds a fresh defense pipeline for the item, then:
   - **input defenses** run in order. A defense may raise `BlockedError`
     (short-circuit → counted as a refusal, no model call).
   - if not blocked, the **provider adapter** calls the target model.
   - **output defenses** run in reverse order (outermost-last-in, first-out).
3. `judge.Judge.judge` classifies the response into a `Verdict`
   (compliant / refused / hedged / off-topic / error).
4. The `RunRecord` is written to `records.jsonl`.
5. After all items, `runner` writes `manifest.json`.
6. `scoring.score_run` aggregates records into ASR, FRR, per-category rates,
   each with a bootstrap 95% CI, written to `summary.json`.
7. `report.render_report` reads all three and emits `report.html`.

## Why these boundaries

- **`types.py` is the contract.** Every module imports from it; no module
  invents its own dict shape. Changing the pipeline means changing a type,
  which the type checker then forces you to handle everywhere.
- **`runner.py` has no policy.** It does not know what makes an attack an
  attack or what makes a defense good. It only wires components. This means
  you can swap any component (a new judge, a new provider) without touching
  orchestration.
- **Providers are async + lazy.** SDK imports happen inside methods so the
  package installs and runs (on the mock provider) with zero provider SDKs
  present. CI exercises the full pipeline without API keys or cost.
- **Defenses are sync by default, async by exception.** The `Defense`
  protocol is synchronous (`pre`/`post`) because most defenses are cheap
  string operations. A defense that needs an LLM call (the classifier guard)
  exposes an optional `apre` coroutine; the runner prefers it when present.
  This keeps the common case simple without blocking the expensive case.

## Extending

| You want to… | Touch | Don't touch |
|---|---|---|
| Add a provider (e.g. Gemini) | `providers.py` (one class + factory entry) | anything else |
| Add a defense | `defenses.py` (one class + registry entry), `defenses/REGISTRY.md` | runner, scoring |
| Add an attack category | `datasets/*.yaml`, `attacks/REGISTRY.md` | code, unless a new `AttackCategory` enum value is needed |
| Change the metric | `scoring.py` (+ bump framework major version per `docs/methodology.md`) | everything upstream |
| Restyle the report | `report.py` template only | data flow |

## What is deliberately absent

- No database. Runs are files on disk. This is a research tool; if you need a
  results store, wrap it.
- No web server. The report is a static file you open or host yourself.
- No model training. The target is always a black box. See `docs/threat_model.md`.
- No global mutable state. Each item builds its own pipeline; runs are
  reproducible from `(config, seed, dataset hash)`.
