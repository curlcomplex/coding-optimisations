# sqz A/B treatment — issue #11

Treatment source: sqz commit `9461782e6b5998bda68b49c92c864cf4900848b2`, built locally in disposable storage. Upstream quality benchmark must pass before inference. The live treatment uses an external Codex PreToolUse adapter so task-visible startup context and prompts remain identical; eligible simple shell commands are piped through sqz `compress --cmd ... --no-abbrev`, with the original pipeline exit status preserved. The agent is not told arm identity.

This is an isolated first-round sqz test, not production installation and not sqz's documented AGENTS/MCP Codex integration. It deliberately avoids adding sqz instructions/tool schemas to one arm. Each trial has its own sqz database; references are never shared across fresh workers. RTK is not layered into this isolated treatment, so this result measures sqz's transparent shell-result treatment against raw shell output, not a claimed residual gain over an active RTK hook.

Fixtures, prompts, model/reasoning, tests and independent review follow the corrected #11 invariant. Two fixtures x two repetitions x two arms. All failed attempts remain countable. Results: `results/2026-09-16-sqz-ab.md`.
