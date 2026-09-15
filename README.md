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

The first execution target is the existing self-hosted macOS GitHub Actions runner. No OpenAI API key is required or permitted for the benchmark path.

Hosted GitHub runner support is deliberately deferred until the self-hosted subscription-authenticated path is measured and stable.
