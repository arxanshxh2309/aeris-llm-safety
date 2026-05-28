# Example run (mock provider)

This directory is a committed example so the report renderer and output
format are visible without running anything.

**These numbers are not real.** They were produced against `mock/echo`, a
deterministic stub provider whose responses are chosen by a hash of the
input. The mock exists so the framework can be tested in CI with no API
keys and no cost. The ASR / FRR figures here are illustrative of the
*format*, not of any model's actual robustness.

To produce real numbers, run against a real provider:

```bash
python -m aeris run \
  --config configs/headline.yaml \
  --model anthropic/claude-sonnet-4-5 \
  --i-have-permission-to-test
```

Files:
- `manifest.json` — reproducibility manifest
- `records.jsonl` — one line per (item, response, verdict)
- `summary.json` — aggregated metrics with bootstrap CIs
- `report.html` — open in a browser
