# Defense Registry

A defense is a small, composable component that wraps the target model.
We ship four baselines so users have a measurable starting point, and
document the known limits of each.

| Name | Layer | What it catches | Known limits |
|---|---|---|---|
| `keyword_filter_v1` | Input | Hand-written "ignore previous instructions" patterns. | Trivially bypassed by paraphrase, encoding, or any sentence-level rewording. Baseline only. |
| `system_prompt_hardener_v1` | Input | Adds spotlighting delimiters and an explicit instruction to treat tool content as data. | Spotlight delimiters can themselves be attacked (`INJECTION-002` demonstrates this). |
| `heuristic_injection_detector_v1` | Input (tool content) | Common injection signatures in `tool`/`function` messages. | Signature-based; sophisticated injections that paraphrase the trigger phrases will pass. |
| `length_guard_v1` | Input + Output | Many-shot context exhaustion and pathologically long outputs. | A real attacker can stay under the threshold. Useful in defense-in-depth, useless alone. |
| `classifier_guard_v1` | Input (async) | LLM-as-classifier over user input; flags jailbreak/injection attempts holistically rather than by keyword. | Adds one model call per request (latency + token cost). Only as good as the classifier model; a strong adaptive attacker can still evade. Inherits the classifier's own biases. |
| `classifier_guard_v1` | Input | Uses an LLM as a binary SAFE/UNSAFE classifier over user input (Llama-Guard / constitutional-classifier style). | Adds a full model call per request (latency + cost). Inherits the classifier model's own blind spots. The classifier is itself attackable. |

## What's intentionally not shipped

- **Production classifier weights** (Llama Guard, ShieldGemma model checkpoints). `classifier_guard_v1` wraps *any* LLM you point it at as a zero-shot classifier, which is a reasonable baseline and needs no GPU. A fine-tuned dedicated classifier would outperform it — that's left as an integration exercise, since the dependency story (model weights, serving infra) is heavier than the rest of the framework.
- **Output-content filters keyed on specific harm categories.** These belong in a separate, harm-category-specific repo with appropriate trust & safety review. Out of scope here.
- **Rate limiting / auth.** Those are infra concerns, not model-robustness concerns.

## Adding a defense

Implement the `Defense` protocol in `src/aeris/defenses.py`:

```python
@dataclass
class MyDefense:
    name: str = "my_defense_v1"
    def pre(self, messages): return messages, ["my_defense_v1:passed"]
    def post(self, text): return text, []
```

Then register it in `build_pipeline` and add an entry to this file with:
- What attack categories it claims to catch
- Measured ASR change on `configs/headline.yaml` (point estimate + 95% CI)
- Known bypasses
- Latency / token cost
