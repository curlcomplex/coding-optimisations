# Security

- Never commit, upload, print or artifact `$CODEX_HOME/auth.json` or equivalent ChatGPT/Codex credentials.
- The self-hosted runner uses credentials already available to its macOS execution account.
- No OpenAI API keys are used for benchmark execution.
- Benchmark artifacts contain usage/results only, not authentication material.
- Third-party optimisation tools must document network/telemetry behaviour before entering the baseline.
- Candidate experiments should be reversible and isolated from production repositories.
