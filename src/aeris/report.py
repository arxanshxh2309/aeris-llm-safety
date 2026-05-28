"""HTML report generation.

Reads a run directory (manifest.json + records.jsonl + summary.json)
and produces report.html — a single self-contained file with no
external dependencies. The CSS and JS are inline. Open in any browser.

Design notes are in the template; the short version is: editorial /
research-paper aesthetic, dark theme with terminal-green accent, serif
display type, monospace data. No purple gradients.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from jinja2 import Template

from .scoring import load_records, score_run

_TEMPLATE = Template(r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AERIS Report — {{ target }}</title>
<style>
  :root {
    --bg: #0c0d10;
    --bg-elev: #14161b;
    --ink: #e8e6df;
    --ink-mute: #8b8a85;
    --rule: #25272d;
    --accent: #7af7c1;
    --warn: #f6a96b;
    --bad: #f07a7a;
    --good: #7af7c1;
    --serif: 'EB Garamond', 'Iowan Old Style', 'Palatino Linotype', Georgia, serif;
    --mono: 'JetBrains Mono', 'Berkeley Mono', ui-monospace, SFMono-Regular, monospace;
  }
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');
  * { box-sizing: border-box; }
  html, body { background: var(--bg); color: var(--ink); margin: 0; padding: 0; }
  body {
    font-family: var(--serif);
    font-size: 18px;
    line-height: 1.55;
    font-feature-settings: "kern", "liga", "onum";
  }
  .grain {
    position: fixed; inset: 0; pointer-events: none; opacity: 0.04; z-index: 100;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  }
  .wrap {
    max-width: 880px;
    margin: 0 auto;
    padding: 80px 32px 120px;
  }
  header {
    border-bottom: 1px solid var(--rule);
    padding-bottom: 32px;
    margin-bottom: 48px;
  }
  .kicker {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 16px;
  }
  h1 {
    font-family: var(--serif);
    font-weight: 500;
    font-size: 52px;
    line-height: 1.05;
    letter-spacing: -0.02em;
    margin: 0 0 24px;
  }
  h1 em {
    font-style: italic;
    color: var(--ink-mute);
    font-weight: 400;
  }
  .meta {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 6px 28px;
    font-family: var(--mono);
    font-size: 13px;
    color: var(--ink-mute);
  }
  .meta dt { color: var(--ink-mute); }
  .meta dd { margin: 0; color: var(--ink); }
  section { margin: 64px 0; }
  h2 {
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--accent);
    font-weight: 500;
    margin: 0 0 24px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--rule);
  }
  /* Headline score block. */
  .score {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 24px;
    margin-bottom: 32px;
  }
  .score-card {
    border: 1px solid var(--rule);
    padding: 24px 24px 20px;
    background: var(--bg-elev);
    position: relative;
  }
  .score-card .label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-mute);
  }
  .score-card .value {
    font-family: var(--serif);
    font-size: 56px;
    font-weight: 500;
    line-height: 1;
    margin: 12px 0 6px;
    letter-spacing: -0.02em;
  }
  .score-card .ci {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--ink-mute);
  }
  .score-card.aeris .value { color: var(--accent); }
  /* Per-category bars. */
  .bars { font-family: var(--mono); font-size: 13px; }
  .bar-row {
    display: grid;
    grid-template-columns: 200px 1fr 90px;
    gap: 16px;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px dashed var(--rule);
  }
  .bar-row:last-child { border-bottom: none; }
  .bar-row .cat { color: var(--ink); }
  .bar {
    height: 12px;
    background: var(--bg-elev);
    border: 1px solid var(--rule);
    position: relative;
    overflow: hidden;
  }
  .bar > .fill {
    position: absolute;
    inset: 0 auto 0 0;
    background: var(--bad);
    transition: width 1.2s cubic-bezier(.2,.7,.2,1);
  }
  .bar > .fill.good { background: var(--good); }
  .bar-row .n { color: var(--ink-mute); text-align: right; }
  .bar-row .num { color: var(--ink); white-space: nowrap; }
  /* Body prose. */
  p { max-width: 70ch; }
  p.lede {
    font-size: 22px;
    line-height: 1.45;
    color: var(--ink);
    margin: 0 0 24px;
  }
  p.note {
    font-style: italic;
    color: var(--ink-mute);
    font-size: 15px;
  }
  code, .mono { font-family: var(--mono); font-size: 14px; color: var(--ink); }
  /* Sample table. */
  .samples { font-family: var(--mono); font-size: 12px; }
  .sample {
    padding: 16px 0;
    border-bottom: 1px dashed var(--rule);
    display: grid;
    grid-template-columns: 80px 110px 1fr;
    gap: 20px;
  }
  .sample .id { color: var(--ink-mute); }
  .sample .v { font-weight: 500; }
  .sample .v.compliant_with_attack { color: var(--bad); }
  .sample .v.refused { color: var(--good); }
  .sample .v.hedged { color: var(--warn); }
  .sample .v.judge_error, .sample .v.off_topic { color: var(--ink-mute); }
  .sample .text {
    color: var(--ink);
    line-height: 1.5;
    font-family: var(--serif);
    font-size: 14px;
    max-height: 4.5em;
    overflow: hidden;
  }
  footer {
    margin-top: 96px;
    padding-top: 32px;
    border-top: 1px solid var(--rule);
    font-family: var(--mono);
    font-size: 12px;
    color: var(--ink-mute);
    display: flex;
    justify-content: space-between;
  }
  /* Page-load stagger. */
  section, header { animation: rise 0.6s cubic-bezier(.2,.7,.2,1) backwards; }
  header { animation-delay: 0.0s; }
  section:nth-of-type(1) { animation-delay: 0.1s; }
  section:nth-of-type(2) { animation-delay: 0.2s; }
  section:nth-of-type(3) { animation-delay: 0.3s; }
  section:nth-of-type(4) { animation-delay: 0.4s; }
  @keyframes rise {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @media (max-width: 720px) {
    h1 { font-size: 36px; }
    .score { grid-template-columns: 1fr; }
    .bar-row { grid-template-columns: 100px 1fr 70px; }
    .sample { grid-template-columns: 60px 80px 1fr; }
  }
</style>
</head>
<body>
<div class="grain"></div>
<div class="wrap">

<header>
  <div class="kicker">AERIS · Defensive red-teaming report</div>
  <h1>{{ target }}<br><em>against {{ n_attacks }} adversarial probes, {{ n_benigns }} benign controls</em></h1>
  <dl class="meta">
    <dt>run_id</dt><dd>{{ manifest.run_id }}</dd>
    <dt>timestamp</dt><dd>{{ manifest.timestamp_utc }}</dd>
    <dt>config_hash</dt><dd>{{ manifest.config_hash[:24] }}…</dd>
    <dt>attack_set</dt><dd>{{ manifest.attack_set_id }}</dd>
    <dt>benign_set</dt><dd>{{ manifest.benign_set_id }}</dd>
    <dt>judge_model</dt><dd>{{ manifest.judge_model }}</dd>
    <dt>defenses</dt><dd>{{ manifest.defenses | join(', ') if manifest.defenses else '— baseline (none) —' }}</dd>
    <dt>seed</dt><dd>{{ manifest.seed }}</dd>
  </dl>
</header>

<section>
  <h2>Headline</h2>
  <p class="lede">
    Of <strong>{{ n_attacks }}</strong> adversarial probes, the model complied with
    <strong>{{ "%.0f" | format(summary.asr.point * 100) }}%</strong>.
    Of <strong>{{ n_benigns }}</strong> benign requests, it incorrectly refused
    <strong>{{ "%.0f" | format(summary.frr.point * 100) }}%</strong>.
    The composite AERIS Score (lower attack success and lower over-refusal, weighted 0.7 / 0.3) is
    <strong style="color: var(--accent);">{{ "%.2f" | format(summary.aeris_score) }}</strong>.
  </p>

  <div class="score">
    <div class="score-card aeris">
      <div class="label">AERIS Score</div>
      <div class="value">{{ "%.2f" | format(summary.aeris_score) }}</div>
      <div class="ci">α-weight = {{ summary.alpha_weight }}</div>
    </div>
    <div class="score-card">
      <div class="label">Attack Success Rate</div>
      <div class="value" style="color: var(--bad);">{{ "%.1f" | format(summary.asr.point * 100) }}%</div>
      <div class="ci">95% CI [{{ "%.2f" | format(summary.asr.lo) }}, {{ "%.2f" | format(summary.asr.hi) }}] · n={{ summary.asr.n }}</div>
    </div>
    <div class="score-card">
      <div class="label">False Refusal Rate</div>
      <div class="value" style="color: var(--warn);">{{ "%.1f" | format(summary.frr.point * 100) }}%</div>
      <div class="ci">95% CI [{{ "%.2f" | format(summary.frr.lo) }}, {{ "%.2f" | format(summary.frr.hi) }}] · n={{ summary.frr.n }}</div>
    </div>
  </div>

  <p class="note">
    Read these together. A model that refuses everything achieves ASR=0 and is useless.
    A model that complies with everything achieves FRR=0 and is dangerous.
    The AERIS Score collapses the trade-off; the components above are the honest numbers.
  </p>
</section>

<section>
  <h2>Attack Success by Category</h2>
  <div class="bars">
    {% for cat, vals in summary.by_category.items() %}
    <div class="bar-row">
      <div class="cat">{{ cat }}</div>
      <div class="bar"><div class="fill{{ ' good' if vals.asr < 0.2 else '' }}" style="width: {{ (vals.asr * 100) | round(1) }}%"></div></div>
      <div class="num">{{ "%.0f" | format(vals.asr * 100) }}% <span class="n">n={{ vals.n }}</span></div>
    </div>
    {% endfor %}
  </div>
</section>

<section>
  <h2>Defense Actions</h2>
  {% if defense_action_counts %}
  <p>Across this run, {{ defense_actions_total }} defense events were recorded:</p>
  <div class="bars">
    {% for action, count in defense_action_counts %}
    <div class="bar-row">
      <div class="cat">{{ action }}</div>
      <div class="bar"><div class="fill good" style="width: {{ (count / defense_action_max * 100) | round(1) }}%"></div></div>
      <div class="num">{{ count }}</div>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p class="note">No defenses were active in this run (baseline). To see this section populated,
  re-run with one of the configs under <code>configs/</code> that includes a defense pipeline.</p>
  {% endif %}
</section>

<section>
  <h2>Sample failures</h2>
  <p class="note">A handful of items where the model complied with an attack, hedged, or where the judge couldn't classify cleanly. These are the cases worth eyeballing in the raw <code>records.jsonl</code>.</p>
  <div class="samples">
    {% for s in samples %}
    <div class="sample">
      <div class="id">{{ s.item_id }}</div>
      <div class="v {{ s.verdict }}">{{ s.verdict }}</div>
      <div class="text">{{ s.text }}</div>
    </div>
    {% endfor %}
    {% if not samples %}
    <p class="note">No notable failures in this run.</p>
    {% endif %}
  </div>
</section>

<footer>
  <span>aeris-llm-safety · v{{ version }}</span>
  <span>generated from manifest.json + records.jsonl</span>
</footer>

</div>
</body>
</html>
""")


def render_report(run_dir: Path) -> Path:
    """Render report.html into run_dir. Returns the path."""
    from . import __version__

    manifest = json.loads((run_dir / "manifest.json").read_text())
    records = load_records(run_dir / "records.jsonl")
    summary = score_run(records)

    n_attacks = sum(1 for r in records if r.category != "BENIGN")
    n_benigns = sum(1 for r in records if r.category == "BENIGN")

    # Defense action histogram.
    counter: Counter[str] = Counter()
    for r in records:
        for a in r.defense_actions:
            # Bucket by first two colon-separated segments to keep
            # the chart readable.
            key = ":".join(a.split(":")[:2])
            counter[key] += 1
    action_pairs = counter.most_common(12)
    action_max = max((c for _, c in action_pairs), default=1)
    action_total = sum(c for _, c in action_pairs)

    # Sample failures (compliant_with_attack, hedged, judge_error).
    failures = [
        {
            "item_id": r.item_id,
            "verdict": r.judge.verdict.value if hasattr(r.judge.verdict, "value") else str(r.judge.verdict),
            "text": (r.response.text or "")[:240].replace("\n", " "),
        }
        for r in records
        if str(getattr(r.judge.verdict, "value", r.judge.verdict)) in (
            "compliant_with_attack", "hedged", "judge_error"
        )
    ][:8]

    html = _TEMPLATE.render(
        target=manifest["target_model"],
        manifest=manifest,
        summary=summary,
        n_attacks=n_attacks,
        n_benigns=n_benigns,
        defense_action_counts=action_pairs,
        defense_action_max=action_max,
        defense_actions_total=action_total,
        samples=failures,
        version=__version__,
    )
    out = run_dir / "report.html"
    out.write_text(html)
    return out
