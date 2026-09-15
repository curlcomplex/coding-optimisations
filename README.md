# Coding Optimisations

Audit and test agentic coding speed-up and token-usage efficiency strategies with evidence rather than headline claims.

## Decision baseline

The control is the real working stack, not vanilla Codex:

- Codex with ChatGPT subscription authentication
- RTK
- Serena
- GitHub Issues as task authority
- fresh issue-scoped worker sessions with persistent goals
- worker model chosen per issue, biased toward lower token use where verification preserves quality

Optimisations are accepted only when repeated A/B runs show lower total token use per successfully completed task while preserving the same correctness and review gates.

## Execution

**The Mac already exists as an Actions target. Use the established private controller, not a direct self-hosted workflow in this public repository.** The controller checks out a reviewed immutable lab commit and respects the existing machine-wide queue. See [runner routing](docs/RUNNER-ROUTING.md) and [issue #2](https://github.com/curlcomplex/coding-optimisations/issues/2).

A fresh private read-only preflight on 15 September 2026 successfully checked out this lab on the Mac and verified the existing Codex CLI ChatGPT login. This does not yet qualify a model call, Serena activation, a complete baseline or token-saving results. Exact machine identities and private diagnostic logs remain in the private controller.

No OpenAI API key is required or permitted for the benchmark path. Hosted subscription execution is explicitly deferred in [issue #3](https://github.com/curlcomplex/coding-optimisations/issues/3).

The initial public self-hosted PR workflows have been removed: they were misrouted and are not an acceptable route to the owner's machine. The harness and fixture remain as bootstrap source; their accounting must be hardened and the actual subscription smoke must pass before claiming a benchmark.
