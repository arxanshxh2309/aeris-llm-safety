# Security Policy

## Reporting a vulnerability

If you discover that this project itself has a security issue — for example, that it can be used to escalate harm beyond what its documented scope intends, or that it could leak API keys or other secrets — please **do not** open a public issue.

Email: security@example.com (replace with your real address)

Expect a response within 72 hours. We follow a 90-day coordinated disclosure timeline by default.

## Reporting an LLM vulnerability you found *using* this project

This repository is a research tool. If you use it to discover a real weakness in a production LLM (ChatGPT, Claude, Gemini, Grok, Perplexity, etc.), report it to **that provider** first:

- Anthropic: https://www.anthropic.com/responsible-disclosure-policy
- OpenAI: https://openai.com/security/disclosure (and their HackerOne / Bugcrowd programs)
- Google: https://bughunters.google.com/
- xAI: check current company disclosure channels
- Perplexity: check current company disclosure channels

Do not post novel jailbreaks publicly before giving the provider a reasonable window to remediate. The 90-day timeline used in mainstream security disclosure is a sensible default.

## What this project will not help you with

- Targeting a specific provider's API at scale without their consent (this likely violates their TOS regardless of intent)
- Producing actual harmful content (the framework deliberately uses surrogate triggers; see `docs/safety_posture.md`)
- Extracting model weights, training data, or system prompts from production systems

If your use case requires any of the above, this is not the right tool.
