# Native RTK hook gate — issue #11 / PR #13

## Candidate identity

Official develop prerelease `dev-0.50.0-rc.431`, published 13 September 2026, exact source `5626e94a63a34d2792cdaa63a0613eda1d4abb1b`. macOS arm64 archive SHA256 `003057bcede4e1b519c957f22edae29782cf80382a0e03191ed3f7a277b75e83`; actual binary SHA256 `5a7ffea710be19b8a6a5dac5f5a8be88b23441f21c1fdb2750f6d8ce20b63585`.

The binary reports `rtk 0.48.0`; the tag is not a stable-version upgrade. This develop snapshot qualifies the new native hook only. Do not replace the installed stable 0.49.0, assume its newer filters are present here, or call this the full working baseline. Any eventual production candidate must retain the stable baseline's required capabilities and fidelity.

Primary sources: https://github.com/rtk-ai/rtk/pull/3552 ; https://github.com/rtk-ai/rtk/releases/tag/dev-0.50.0-rc.431 ; https://github.com/rtk-ai/rtk/blob/5626e94a63a34d2792cdaa63a0613eda1d4abb1b/hooks/codex/README.md ; https://developers.openai.com/codex/hooks ; https://developers.openai.com/codex/app-server .

## Completed zero-inference preflight

Executed lab `aeb16b588694ef19178bddfead8e842bc4a7ef35`: 55 full lab tests and 15 native RTK protocol cases passed. Both installed Codex runtimes exposed hooks/list and model/list: standalone 0.154.0 and desktop-bundled 0.154.0-alpha.6.2, with Luna/low available. Artifact downloaded and inspected, ZIP digest `85d071f2ab93a7022b0908d7c43f3ec37f1b6a31066b84c80a15a4cf8aff5856`. Exact run/job/queue receipts remain private.

The trial hook is initially untrusted. The live launcher uses only the supported session-layer state for this exact command/currentHash. It verifies that other hooks' trust/enablement/hash state remains unchanged; it never uses a blanket hook-trust bypass. No credentials or global configuration are copied or modified.

## Live slice, immutable source 07c58348167271282043d45b0244d3ec19a37fa5

Maximum four invocations: standalone CLI off/on and desktop-bundled app-server off/on. Luna/low; 120-second invocation/turn bounds; no automatic fallback or additional batch. Actual ChatGPT login and exact Codex/RTK binary hashes are rechecked. Model inference starts only after exact trial-hook trust and unrelated-hook state checks.

All arms use the same disposable Git fixture and explicitly selected necessary skill with an unpredictable marker unavailable in the prompt. The skill requires separate raw status/diff calls and one harmless staging attempt expected to fail under read-only permissions; no escalation, workaround or retry. The Git index is hashed before/after; any mutation stops the remaining arms. This verifies an explicit required skill with the catalogue suppressed, not every production coordination/review skill or Serena.

The thin hook delegate records native input/output privately without changing its response. A PATH shim emits an unpredictable execution marker before executing the exact pinned RTK binary. The marker distinguishes real execution from a displayed rewrite. This is diagnostic instrumentation, not a production integration or optimisation. Its token/latency overhead is included and prevents interpreting this tiny test as a whole-task savings benchmark.

A separate first-party execpolicy rule check compares raw and wrapped command matching without executing the sample command. A mismatch is a policy-integration caveat, not proof that every permission or sandbox boundary was bypassed. Read-only file-denial observations and rule matching must be reported separately.

Retain every failed/partial invocation and exposed input/cached/output/reasoning counters; reconcile cumulative and per-request records without double counting subsets. Missing usage is unknown. Do not equate model tokens with subscription allowance or infer quality from a recoverable store.

## Limits

A bundled binary launched via app-server is not the running Desktop GUI. The same core version does not prove GUI-specific configuration, named permission profiles, hook selection or production delegation parity. No GUI adoption claim is permitted from this test alone. One off/on sample per runtime is capability/accounting evidence, not repeated reviewed-issue efficiency evidence.

No live RTK init/install, global hooks/config change, credentials copied, new queue/runner or production source edit. All raw event traces, hook payloads, paths and work inventory stay private. Publish only deliberate summaries. Actual current execution/results are tracked in #11 and the result report; this document does not claim live success.
