# Results Writeup

> This document is a *template* for the results section of a paper or report using AERIS. Replace the placeholders with your own measured numbers.

## Setup

- Target model(s): `<model spec>`, e.g. `anthropic/claude-sonnet-4-5`
- Judge model: `<usually a different model to avoid self-preference bias>`
- Attack set: `aeris-smoke-v1@<hash>` (10 items across 8 categories)
- Benign set: `xstest-style-v1@<hash>` (10 items)
- Defenses tested: baseline (none) vs. full pipeline (`system_prompt_hardener_v1`, `keyword_filter_v1`, `heuristic_injection_detector_v1`, `length_guard_v1`)
- Seed: 1337
- Run cost: approximately $X in tokens

## Headline numbers

| Model | Defenses | AERIS Score | ASR (95% CI) | FRR (95% CI) |
|---|---|---|---|---|
| Model A | none | 0.XX | 0.XX [0.XX, 0.XX] | 0.XX [0.XX, 0.XX] |
| Model A | full pipeline | 0.XX | 0.XX [0.XX, 0.XX] | 0.XX [0.XX, 0.XX] |
| Model B | none | 0.XX | 0.XX [0.XX, 0.XX] | 0.XX [0.XX, 0.XX] |
| Model B | full pipeline | 0.XX | 0.XX [0.XX, 0.XX] | 0.XX [0.XX, 0.XX] |

## Per-category ASR (baseline / defended)

| Category | Model A baseline | Model A defended | Δ |
|---|---|---|---|
| DAN | 0.XX | 0.XX | -0.XX |
| PAIR | 0.XX | 0.XX | -0.XX |
| GCG-TRANSFER | 0.XX | 0.XX | -0.XX |
| CRESCENDO | 0.XX | 0.XX | -0.XX |
| INDIRECT-INJECTION | 0.XX | 0.XX | -0.XX |
| ENCODE | 0.XX | 0.XX | -0.XX |
| MANY-SHOT | 0.XX | 0.XX | -0.XX |

## Observations to look for

When you write up real results, organize the discussion around questions like:

1. **Where does the model fail without defenses?** Which category has the highest ASR? Is it the one we'd expect from the published literature, or something different? If different, hypothesize why.

2. **What does each defense buy you?** Run the headline experiment with each defense individually, not just the full pipeline. A defense whose individual impact is below the bootstrap CI of the baseline is not actually doing anything measurable.

3. **What does each defense cost?** Token overhead, latency, and FRR change. A defense that costs 20% in FRR is rarely worth it.

4. **Where do defenses fail?** Indirect injection variants that paraphrase the trigger phrases will likely defeat `heuristic_injection_detector_v1`. Encode attacks will defeat `keyword_filter_v1`. Document the specific bypass items in your run.

5. **Judge agreement.** Run the judge twice with `temperature=0`; the two passes should agree. If they don't, the judge is unreliable for this task and the numbers above need a wider CI.

## Reproducing

```bash
# Baseline
python -m aeris run \
  --config configs/smoke.yaml \
  --model anthropic/claude-sonnet-4-5 \
  --i-have-permission-to-test

# Defended
python -m aeris run \
  --config configs/smoke_defended.yaml \
  --model anthropic/claude-sonnet-4-5 \
  --i-have-permission-to-test
```

Each run writes a manifest with the config hash and the attack/benign set hash. Anyone with the same AERIS version, the same API access, and `temperature=0` should reproduce within the bootstrap CIs.
