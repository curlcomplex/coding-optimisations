# Coding Optimisations

An evidence-driven lab for making agentic software development **faster, cheaper, more controllable and more future-proof without trading away correctness**.

The near-term job is to audit and improve the user's real coding stack rather than chase headline token claims. The long-term goal is broader: learn which parts of modern coding-agent harnesses are actually valuable, measure what each capability costs, and assemble a development pipeline tuned to the kinds of software the owner builds.

That may remain an optimised Codex workflow, use different harnesses for different workers, or eventually become a custom pipeline that can target ChatGPT-subscription models, other hosted models, and capable local models. The repository should accumulate reusable evidence and components so future model/provider changes do not force the workflow to start over.

## Optimisation layers

Work from the least disruptive/highest-confidence changes outward:

1. **Native context hygiene** — progressive disclosure, caching, scoped skills/MCP/apps, obsolete-instruction removal, compact Markdown/context representation and clean issue handoffs.
2. **Tool/output efficiency** — RTK-style output reduction, reversible result compression, selective retrieval and avoiding repeated model work.
3. **Harness efficiency** — compare Codex with Pi and other harnesses using equivalent capabilities and accepted-task cost, not bare-prompt marketing numbers.
4. **Orchestration efficiency** — issue-scoped workers, model routing, parallelism, verification and review chosen for total successful-task efficiency.
5. **Custom pipeline components** — retain the best measured pieces behind simple interfaces rather than depending on one vendor's accumulated harness.
6. **Local/hybrid execution** — make future local models or mixed local/hosted workers first-class candidates when they can satisfy the same quality gates.

Token count is not the only objective. Track model-specific cost weighting, caching, wall time, failure/repair rate, tool reliability, privacy, maintainability and **tokens/cost per successfully completed and independently accepted task**. Input, cached input, output and reasoning counters remain separate; do not optimise one counter by silently moving cost elsewhere.

## Decision baseline

The control is the real working stack, not vanilla Codex:

- Codex with ChatGPT subscription authentication
- RTK
- Serena
- GitHub Issues as task authority
- fresh issue-scoped worker sessions
- worker model chosen per issue, biased toward lower token use where verification preserves quality

Historical persistent-goal/global instructions are **not assumed to be required**. Issue #9 audits whether they are still used before retaining or removing them.

Optimisations are accepted only when repeated A/B runs show better successful-task efficiency while preserving the same correctness and review gates.

## Current tracks

- **#6** — measured Codex baseline/context attribution.
- **#8** — Pi harness A/B against an equivalently capable native Codex baseline.
- **#9** — native Codex context minimisation: progressive disclosure, skill/MCP exposure, memory/catalogue scoping and obsolete global instructions.

## Execution

**The Mac already exists as an Actions target. Use the established private controller, not a direct self-hosted workflow in this public repository.** The controller checks out a reviewed immutable lab commit and respects the resource-aware machine queue. See [runner routing](docs/RUNNER-ROUTING.md) and [issue #2](https://github.com/curlcomplex/coding-optimisations/issues/2).

Subscription-authenticated Codex CLI execution through the Mac `cli-test` lane is qualified. No OpenAI API key is required or permitted for the benchmark path. Hosted subscription execution remains explicitly deferred in [issue #3](https://github.com/curlcomplex/coding-optimisations/issues/3).

Raw private traces, authentication stores and machine-specific details stay in the trusted private controller. Publish only deliberately sanitised measurements and conclusions here.
