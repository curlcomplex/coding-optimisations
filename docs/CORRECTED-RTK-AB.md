# Corrected RTK A/B invariant — issue #11

The previous plain-vs-normal-RTK cohort is retained as non-authoritative for RTK savings because the arms had different task-visible AGENTS instructions. Do not use its +44.2% result as the RTK saving/cost estimate.

## Experimental variable

A/B changes **only the shell-result setup**:

- A: supported shell commands return ordinary/raw output.
- B: the same supported shell commands are transparently routed through pinned RTK and return RTK output/recovery references.

Everything model-visible before the first tool call is byte-identical: same system/developer configuration, repo files, `.codex/config.toml`, AGENTS.md, ISSUE.md, task prompt, model, reasoning, Serena exposure, tool schemas, permissions and starting commit. The agent is not told which arm it is in and is never instructed to use or avoid RTK. No arm-specific committed file exists. The RTK shim/hook/config lives outside the task workspace and is not readable by the task unless ordinary tool execution exposes it.

The benchmark is intentionally isolated. It does not need to reproduce the owner's production RTK configuration. It needs one well-defined RTK treatment and a valid control.

## Correctness and accounting

Use the same frozen issue fixtures and deterministic tests in both arms. Fresh independent reviewer receives the same reviewer prompt/config in both arms and cannot see arm identity. Count implementation + review provider input/cached/output/reasoning, all requests, recoveries/retries, failures and wall time. RTK-induced behavioral changes after tool results are part of the treatment effect. Do not force identical command sequences in the live A/B.

Verify before spending inference that a sentinel prompt/config hash is identical across arms and only the external shell-result route differs. If any task-visible byte differs before the first tool result, fail the run.

Run paired repetitions with reversed arm order. Preserve failed trials. Quality gates cannot differ. Report paired deltas and variance; do not infer weekly allowance from raw tokens.

Status: protocol correction only; no result until a new immutable harness implementing this invariant is reviewed and executed through the existing private controller/queue.
