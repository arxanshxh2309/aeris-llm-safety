# Contributing

Thanks for your interest in AERIS. A few ground rules before you open a PR.

## Things we accept

- **New defenses**, with measured ASR / FRR impact on `configs/headline.yaml` (post the run manifest in the PR)
- **New attack categories from published sources**, as surrogate triggers (see `docs/safety_posture.md`)
- **Provider adapters** for additional LLM APIs
- **Better statistics** — confidence interval methods, judge calibration, anything that makes the numbers more honest
- **Documentation improvements**
- **Bug fixes**

## Things we will close without merging

- **Novel attacks not derived from published work.** If you've discovered a new technique, publish it through normal channels (preprint + disclosure to affected providers) first.
- **Attack templates that fail the surrogate-trigger criterion** in `docs/safety_posture.md`.
- **Defenses without measurement.** "Should help" is not a contribution. Run `configs/headline.yaml` with and without your defense and post numbers.
- **Code that increases ASR without a clear reason** (e.g., removing a defense).

## PR checklist

- [ ] `ruff check src tests` passes
- [ ] `mypy src` passes
- [ ] `pytest` passes
- [ ] For new attack templates: citation in `attacks/REGISTRY.md`, item is a surrogate trigger
- [ ] For new defenses: entry in `defenses/REGISTRY.md` with measured numbers
- [ ] For interface changes: update relevant docs in `docs/`

## Reviewer guidance

When reviewing an attack-template PR, check:
1. Is there a citation to a published source?
2. Does successful completion of this prompt produce a usable harm artifact? If yes, **reject**.
3. Does the prompt mention a specific real person, real company target, or real infrastructure? If yes, **reject**.
4. Does the prompt contain any of the substrings audited in `src/aeris/attacks.py::_FORBIDDEN_SUBSTRINGS`? If yes, the CI will catch it, but flag in review too.

When reviewing a defense PR, check:
1. Was the headline experiment actually run? Manifest attached?
2. Does FRR move in the wrong direction? A defense that drops ASR by 5% but increases FRR by 20% is a regression.
3. Is the latency / token cost documented?
