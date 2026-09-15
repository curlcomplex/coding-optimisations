# Baseline slice 1 — Codex startup/context overhead

Date: 2026-09-15
Model requested: `gpt-5.6-luna`, reasoning `low`
Execution: ChatGPT-subscription-authenticated Codex CLI 0.144.0 through the private Mac controller's `cli-test` lane.
Task: unchanged deterministic smoke fixture; shell reads the two input lines and model returns their sum. All three trials passed the same correctness/tool gate.

## A–B–A result

| Trial | Context | Input | Cached input | Output | Reasoning output | Codex wall time |
|---|---|---:|---:|---:|---:|---:|
| A1 | live user Codex home | 37,926 | 25,088 | 136 | 44 | 8,989 ms |
| B1 | isolated minimal Codex home | 21,413 | 0 | 144 | 51 | 12,684 ms |
| A2 | live user Codex home | 37,933 | 18,176 | 143 | 51 | 9,258 ms |

Live mean input: **37,929.5**. Isolated input: **21,413**, a reduction of **16,516.5 input tokens / 43.55%** relative to the live mean for this tiny task.

This is a real measured context-overhead difference, not yet an optimiser result. The isolated trial removes the user's normal Codex-home configuration/cache surface and therefore is intentionally not the working baseline. It demonstrates that a large part of the ~38k input count is environment/context overhead rather than the task prompt itself. More attribution is required before deciding what can be removed without losing RTK/Serena or workflow quality.

The isolated trial was slower and had zero cached input, so raw input-token reduction must not be interpreted as equivalent subscription savings or latency improvement. Cached-input economics/allowance treatment remains unknown.

## Additional findings

- Live `models_cache.json` had seven model records and none contained the `base_instructions` field expected by CLI 0.144.0, matching the previously observed nonblocking cache-schema warning. The isolated home avoided the stale live cache surface; the user's live cache was not edited.
- Legacy task 885 still reports Running but exposes no task PID in the inspected status detail. Absence of a PID is not enough evidence to kill it; it remains unresolved and nonblocking under the resource-aware queue.
- The user's long-lived CURLOP runtime task remained Running throughout and did not block any of the three CLI trials.

## Evidence / safety note

The private controller run was `34978209915`. A private Actions artifact was initially produced from the whole experiment directory. Because that directory contained a local auth symlink used by the isolated CODEX_HOME, the artifact was treated as potentially credential-bearing and immediately deleted via follow-up run `34978414656`; the experiment-owned isolated home/symlink was also removed. Live `~/.codex` was not modified. Future artifacts must stage only explicitly sanitised result files and must never include CODEX_HOME or auth symlinks.

No API key or API billing was used. No percentage here is a claim about weekly subscription allowance.