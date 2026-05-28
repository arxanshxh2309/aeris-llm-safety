# Methodology

## Pipeline

```
                  ┌────────────────┐
                  │  Attack Set A  │
                  │  Benign  Set B │
                  └───────┬────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │   Pre-defense pipeline      │  ← optional input filters
            │   (classifier, normalize)   │
            └─────────────┬───────────────┘
                          │ (passes / blocks)
                          ▼
              ┌───────────────────────┐
              │  Target Model M       │  ← black-box LLM
              │  (via ProviderAdapter)│
              └───────────┬───────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │   Post-defense pipeline     │  ← optional output filters
            │   (classifier, schema val.) │
            └─────────────┬───────────────┘
                          │
                          ▼
                ┌───────────────────┐
                │  Judge Model J    │  ← LLM-as-judge with rubric
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │  Aggregation      │  → ASR, FRR, AERIS Score
                └───────────────────┘
```

## Reproducibility requirements

Each run produces a `manifest.json`:

```json
{
  "schema_version": "1.0",
  "timestamp_utc": "2026-05-26T12:00:00Z",
  "git_sha": "abc123...",
  "config_hash": "sha256:...",
  "target_model": "anthropic/claude-sonnet-4-5",
  "judge_model": "anthropic/claude-sonnet-4-5",
  "attack_set": "harmbench-subset-v1@sha256:...",
  "benign_set": "xstest-v2@sha256:...",
  "defenses": ["input_classifier_v1", "output_schema_v1"],
  "seed": 1337,
  "n_calls": 1200,
  "n_tokens_in": 423112,
  "n_tokens_out": 89231,
  "results_path": "results/2026-05-26_..."
}
```

The config hash covers attack templates, defense versions, judge prompt, and rubric. Re-running with the same manifest fields and the same seed against a deterministic provider (`temperature=0`) reproduces results within bootstrap CI.

## Statistical reporting

- Every reported rate comes with a **bootstrap 95% confidence interval** (1000 resamples).
- Differences between configurations are reported with a **paired bootstrap test**, never as raw point estimates.
- We report **per-category ASR** alongside the aggregate. Hiding category-level variance in a single number obscures which attacks the model is actually vulnerable to.

## Why LLM-as-judge (and its caveats)

Human evaluation is the gold standard but does not scale to the 10⁴–10⁵ outputs a serious benchmark produces. The compromise is LLM-as-judge, validated against a small hand-labeled gold set.

Known biases of LLM judges (see [Zheng et al. 2023](https://arxiv.org/abs/2306.05685)):

- **Position bias** — preference for the first option in pairwise comparisons. We use single-output classification, not pairwise.
- **Verbosity bias** — preference for longer outputs. We measure binary compliance, not quality.
- **Self-preference** — model tends to rate its own outputs favorably. The judge model is *different* from the target model when possible; when not, we report this in the manifest.

Judge calibration is recomputed monthly against the gold set and reported in `results/judge_calibration.json`.

## Defense evaluation gotchas (the ones papers usually get wrong)

1. **Test against an adaptive attacker.** A defense that catches the *exact* attacks in the test set but loses to a one-character variation is not a defense. AERIS ships an `adaptive` mode where each attack template is perturbed (synonym swap, casing, whitespace, encoding) per run, with seeds for reproducibility.
2. **Report FRR.** A defense that flags everything achieves ASR=0 and is useless. Headline numbers always pair ASR with FRR.
3. **Don't train on the test set.** If your defense is a classifier, the training data must not overlap with attack-set seeds. `attacks/` and `defenses/training_data/` are kept disjoint by construction (CI check: `scripts/check_disjoint.py`).
4. **Cost matters.** A defense that doubles inference cost is a different product than one that adds 5%. We log per-defense latency and token overhead.

## Versioning

- Attack sets are versioned: `harmbench-subset-v1`, `v2`, etc. Once published, a version is immutable. Bug fixes go in a new version.
- Defenses are versioned independently. A result is `(model, attack_set@version, defense_pipeline@version)`.
- Breaking changes to the scoring rubric bump the framework major version. We do not silently re-score history.
