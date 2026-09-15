# Skill catalogue qualification — 15 September 2026

## Status

**Prepared and submitted; runtime measurement remains blocked. No optimisation accepted or applied.**

Reviewed experiment source: `6a752e98e85ec36858da85910328ee2a83e17256`.

| Gate | Evidence |
| --- | --- |
| New targeted offline tests | 11 passed locally |
| Existing + new suite on Mac | Not started at checkpoint |
| A-B-A-B-A smoke matrix | Not started at checkpoint |
| Explicit skill on/off | Unknown |
| Implicit skill on/off | Unknown |
| First-request token saving | Unknown, not zero |
| Live configuration adoption | Not applied |

The earlier controller attempt reached its timeout without producing an A/B result. The replacement and its read-only queue diagnostic are submitted through the established private Mac controller, but GitHub reports no assigned runner for either job. This does not establish that the machine is offline. The precise private job receipts and queue-diagnosis correction are recorded in the private controller discussion. No unrelated tasks or daemon state were reset.

## Corrected methodology

The previous explicit-skill test gave the expected answer in the prompt and could pass without loading a skill. The new test creates unpredictable markers present only in temporary skill bodies and exercises both explicit and implicit invocation with catalogue-on controls.

Five smoke invocations change only `skills.include_instructions`, with the same model, reasoning, fixture and fixed read-only sandbox. The harness separately reconciles per-request transcript counters against complete exec-turn totals. Missing or inconsistent per-request data remain unknown. Cached input and reasoning are not added twice; subscription allowance savings are not inferred.

The harness bounds each model invocation, verifies ChatGPT login, forbids API-key fallback, preserves private raw traces and sanitised partial results, and checks the live config hash. It never writes production configuration. Qualification is CLI-only; desktop equivalence and the wider Serena/MCP acceptance gates remain separate.

## Resume

Use the already-submitted private diagnostic/qualification jobs, not another duplicate. Inspect actual Pueue state before diagnosing the hang or cancelling anything. Retrieve the sanitised `safe.json` from the completed qualification run, inspect the correctness and discovery gates, and then update this report with measured results. A green preparation/test step is not an optimisation result.
