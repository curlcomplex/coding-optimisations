# Benchmark Protocol

## Primary metric

Total model tokens per successfully completed task, including recoveries and repair turns, using the most complete accounting exposed by subscription-authenticated Codex.

Raw counters are retained. We do not assume API billing counters map exactly to weekly subscription allowance.

## Controlled variables

For each A/B pair keep constant:

- benchmark fixture and starting commit
- issue/task specification
- worker-model selection policy
- reasoning level for a selected model
- sandbox and permissions
- correctness tests and acceptance gates
- reviewer/evaluator policy

The treatment changes exactly one optimisation.

## Measurements

Capture where available input, cached input, output, reasoning and total reported tokens; wall-clock duration; tool calls; recovery/retry/repair turns; task success; deterministic test results; and independent review result.

Count optimisation overhead, including setup prompts, MCP/tool schemas, auxiliary model calls, indexing, retrieval retries and repair work.

## Repetition

Do not infer a percentage from one run. Repeat paired trials and report distributions/variance. A candidate is not accepted if apparent savings rely on weakened correctness gates.

## Baselines

1. Harness smoke baseline: subscription-authenticated Codex on the self-hosted Mac runner.
2. Working baseline: RTK + Serena + issue-scoped worker conventions.
3. Candidate: working baseline + exactly one proposed optimisation.

The working baseline is the decision baseline.
