# Coding Optimisations: agent contract

Read README.md and docs/BENCHMARK-PROTOCOL.md. GitHub Issues are task authority; immutable commits, actual job results and inspected artifacts are execution evidence.

## Repository-local context

The automatic skill catalogue is suppressed only for this lab. Explicitly select/load the skills required by the task or role; do not restore the full catalogue or remove necessary delegation/review capabilities. Freeze the qualified local profile identically across A/B arms. See docs/REPO-CONTEXT.md for scope, verification and rollback; broad startup optimisation remains deferred in #9.

## Runner routing

The owner's Mac is already a working GitHub Actions target through an established private controller. Read docs/RUNNER-ROUTING.md and issue #2 before dispatching work. Inspect private controller workflow/job metadata through the authorised GitHub connection; do not infer runner absence from this public repository's queue or from only Faust-expr's default hosted workflow.

Never register another runner, change credentials, change repository visibility, create a second machine queue, expose the Mac to public/fork PRs, or copy private controller source/hostnames/personal paths into this public lab. No model/API jobs directly from public pull_request or pull_request_target events. Use reviewed immutable lab SHAs through the existing trusted private route. Native/benchmark execution must respect its shared machine-wide queue; repo-local Actions concurrency does not replace that queue.

## Budget and experiments

No API keys or API billing. Verify actual ChatGPT login and fail closed rather than silently falling back. Never read, print, copy or upload auth.json. Raw event traces/configuration can contain private data; do not publish them wholesale. Do not change the user's live RTK/Serena setup or custom delegation skill while testing a candidate.

RTK + Serena + minimal fresh issue workers is the decision baseline. Worker model selection is per issue, not fixed to Terra; keep model/reasoning and selection policy equivalent across paired arms. Start with existing-tool preflight and exactly one reversible candidate. Preserve tests, independent review and all repair costs. Treat missing/malformed accounting as unknown/invalid, never as zero. Distinguish cached input, input, output and reasoning counters without double counting; never infer subscription allowance from raw token counts without evidence.

Report preflight, smoke, baseline and A/B status separately. A green diagnostic is not a successful model run or a completed optimisation. Record actual queue/job/source identities, failures and applicability. Hosted-runner subscription support remains deferred in issue #3. Do not merge changes into the user's production machine/repositories without approval.
