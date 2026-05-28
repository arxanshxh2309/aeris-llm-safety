# Responsible Disclosure

## When you find a real vulnerability

If you run AERIS against a production LLM and find a robust, novel weakness — not just a known jailbreak that hasn't been patched yet, but something genuinely new — here is the path we recommend.

### 1. Verify it's actually novel

Check:
- HarmBench results dashboard
- The provider's recent transparency reports
- arXiv (search "jailbreak", "prompt injection", the model name)
- TensorTrust and Garak project issue trackers

Most "discoveries" reproduce something published. That doesn't make the finding worthless — confirming a known weakness still exists is useful data — but it changes whether it's a disclosure or a benchmark result.

### 2. Document carefully

In a private document (not a public issue):
- The attack template (you can keep the harm-eliciting completion private)
- ASR over $n \ge 30$ trials
- Whether common defenses (Llama Guard, output classifiers) mitigate
- Estimated severity: which provider policies does it violate, what could a real attacker do with this

### 3. Contact the provider

Use the official channel:
- Anthropic: https://www.anthropic.com/responsible-disclosure-policy
- OpenAI: https://openai.com/security
- Google DeepMind / Vertex AI: https://bughunters.google.com/
- xAI / Perplexity: check their current disclosure pages — these change

Give them at least **90 days** before publishing publicly. This is standard practice in security research.

### 4. Publish after the window

Once the provider has had a reasonable window — or has remediated and given you permission — you can publish:
- As a paper (arXiv is standard)
- As a blog post
- As a PR to `attacks/REGISTRY.md` here (only after disclosure and patch, and only if the attack is a *category*, not actionable harm content)

### What not to do

- **Don't post the working attack on Twitter/Reddit/Discord before disclosure.** Production LLMs are deployed to hundreds of millions of users; a public attack creates an immediate window for exploitation.
- **Don't sell the attack.** This includes selling to "AI red team" companies that don't have a coordinated disclosure relationship with the provider.
- **Don't extort the provider.** This is a crime in most jurisdictions.
- **Don't use the attack to harm a third party.** "Demonstrating the attack works" by producing actual harm content for a specific target is itself harmful and removes the framing of legitimate research.

## What AERIS maintainers will do

If we find a vulnerability while developing this project:

1. We pause work on that area until disclosure.
2. We do not commit working PoCs to this repository.
3. We file the disclosure with the affected provider within 7 days.
4. After remediation, we may add a *category* template (not the specific working payload) to `attacks/REGISTRY.md` so future work can measure the class of attack.

This policy is informed by [Google Project Zero's disclosure norms](https://googleprojectzero.blogspot.com/p/vulnerability-disclosure-policy.html) and the broader security-research community's coordinated-disclosure consensus.
