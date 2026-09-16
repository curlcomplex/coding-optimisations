# RTK coding-task A/B — 16 September 2026

## Decision

**The actual coding/review benchmark executed. No quality-preserving token-saving win is established for the tested automatic-routing variant.** The hook was enabled and invoked, but produced **zero additional rewrites**: agents already used RTK explicitly, while remaining commands were compound or outside the deliberately narrow inspection scope. Keep the production setup unchanged.

This is not a successful completion of the proposed eight-trial matrix. **Five coding implementations and five fresh independent reviews completed**, including both repetitions of the C++ off/on pair and one unpaired TypeScript control. The predeclared observed-token budget stopped the batch before the remaining three trials. No extension or further model calls were launched. The quantitative matched comparison below uses only the four C++ trials; the TypeScript control and its cost are retained separately, not hidden or pooled into a false balanced comparison.

A reviewer found a genuine C++ edge case in the first control. Post-run deterministic replay of that exact finding on **all four** saved C++ patches reproduced it in every patch, including the three that other reviews accepted. Consequently, the C++ **tokens-per-quality-accepted-issue metric is undefined (zero accepted after uniform audit)**. The raw token differences below must not be promoted as successful-task savings.

## Exact identity and inspected evidence

Authority: issue #11; source and result PR: #13, branch `11-rtk-fidelity`. PR #12 is already merged. Executed lab source: **`291c8f8279ecfd15cde66aae9a9eaed96b19ee52`**. This result document was added afterwards and is not an executed-source identity.

Private Mac controller job reached its terminal state with retained artifacts. Its final status is **budget-stopped**, represented by a nonzero process exit and red workflow, not an infrastructure crash or a successful full matrix. Exact controller/run/job/queue receipts are recorded in the private controller discussion.

Downloaded private artifact ZIP SHA256: **`04006002bafa9317534c4c8e5500dad50d7bf0322eca9996d705fe914cf14e79`**. Downloaded bytes and ZIP CRC were verified. Actual contents were inspected: all five source patches, review verdicts, test reports, hook audit records and ten model event/usage files. Each patch and model trace matched its recorded SHA256. Independently recomputed request sums matched retained cumulative input/output for all ten invocations.

Mac lab suite: **72 passed**, no failures/errors, 1.938 seconds. These are harness/fixture-mechanics tests, not 72 accepted coding tasks.

## Controlled comparison

Both arms retained the current Codex configuration, Serena MCP, subscription authentication, per-role prompts, permissions and repository skill-catalogue suppression. Both filtered shell output with the **same installed stable RTK 0.49.0**, SHA256 `055ef1cd1aa0afb96c854bddf43d24af10dcac5a6288ed44519cb1cc10b093a9`. RTK stores were isolated per trial; the common normalized existing RTK config had telemetry/tracking disabled in both arms. Existing global configuration/hooks/AGENTS hashes remained unchanged.

Treatment alone enabled the native-hook processor from `dev-0.50.0-rc.431`, source `5626e94a63a34d2792cdaa63a0613eda1d4abb1b`, executable SHA256 `5a7ffea710be19b8a6a5dac5f5a8be88b23441f21c1fdb2750f6d8ce20b63585`. It did **not** replace the stable filtering binary. The trial delegate limited automatic rewriting to simple non-mutating local inspection commands; compound commands, mutations and unsupported commands passed through. This explicit safety-scoped variant is **not the unrestricted native RTK hook**. It cannot establish that a wider properly policy-preserving integration would have no benefit.

Runtime: desktop-bundled core **0.154.0-alpha.6.2 through first-party app-server**, not a driven Desktop GUI session. Worker: **Terra medium**; independent fresh reviewer: **Luna medium**. Models were matched by role in both arms, and requested identities appeared in the owned rollout metadata; these choices are not a new fixed production worker policy. Both arms used workspace-write with network disabled and no approval escalation. Existing model/agent machinery was reused; no paid auxiliary service.

The tasks were substantive **synthetic issue-shaped fixtures**, not copied production CURLOP source:

- C++ sample-rate-correct, continuous parameter smoothing with state retargeting, block equivalence, zero-time and nonfinite handling. The frozen suite ran 2,192 numerical checks.
- TypeScript held-row automation with pointer ownership/priority, current target selection, address-scoped deduplication, value/coordinate validation and independent output objects. Seven named tests included a 400-step reference sequence.

The complete frozen task specifications are in `harness/issue_fixtures.py` at the executed revision. They are executable renderings of issue #11, not another planning authority. No actual Faust render, browser screenshot, audio certification or production integration is claimed.

All four C++ trials started at the same fixture Git commit `5049654a1b686a11fc8b55a00b1a50d9c7cf912e`. TypeScript control started at `931ea23f3035e03c59a0c5ab10ba892254e981b6`. Source changes were allowed only under `src/`; unchanged test/spec/config hashes and unchanged reviewer source were verified. Each broken starting fixture failed its original tests. All five implementations passed those original tests afterwards. Independent review was a separate real model invocation and its entire cost was counted.

## Matched C++ measurements: all attempts plus reviews

Input includes its cached subset; generated output includes its reasoning subset. Total is input plus generated output, without adding either subset twice.

| Attempt | Input | Cached subset | Generated output | Reasoning subset | Total | Provider requests | Model wall seconds | Original review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Repetition 1, off | 591,838 | 523,520 | 5,880 | 2,513 | 597,718 | 23 | 170.949 | Rejected |
| Repetition 1, on | 610,403 | 539,648 | 5,126 | 1,415 | 615,529 | 24 | 152.171 | Accepted |
| Repetition 2, on | 568,150 | 497,408 | 5,437 | 2,021 | 573,587 | 21 | 140.487 | Accepted |
| Repetition 2, off | 607,311 | 544,256 | 5,706 | 1,688 | 613,017 | 22 | 149.764 | Accepted |
| **Off total** | **1,199,149** | **1,067,776** | **11,586** | **4,201** | **1,210,735** | **45** | **320.713** | See uniform audit |
| **On total** | **1,178,553** | **1,037,056** | **10,563** | **3,436** | **1,189,116** | **45** | **292.658** | See uniform audit |

Observed raw total difference: **-1.79%**; generated-output difference: **-8.83%**. These are descriptive differences in a tiny, quality-failing cohort, **not attributable RTK savings**. The total paired difference changes sign: on is **2.98% higher** in repetition 1 and **6.43% lower** in repetition 2. Per-arm total-token sample standard deviations are 10,818 (off) and 29,657 (on), with only two observations each. No statistical reliability or equivalence claim is justified.

Implementation-generated output alone **increased** from 6,851 to 7,096 tokens (+3.58%). Review-generated output decreased from 4,735 to 3,467. Different navigation, retry and review behavior matters more here than the tiny combined total difference. The higher apparent review acceptance in the on arm does not survive uniform source audit.

## Actual additional interception: zero

Hook-on trials invoked the native trial delegate **12 and 16 times**, but both recorded **0 rewrites**. Stable RTK was actually called **19 and 14 times** respectively. Controls called stable RTK **9 and 19 times**. Actual hook audit contents were inspected, not inferred solely from configuration or counters.

Observed hook inputs consisted of already-RTK-prefixed operations, compounds/pipelines that the tested wrapper intentionally excluded, and unsupported commands such as the plain test runner. The conclusion is narrow: **this variant did not perform additional output compression on these tasks**. Do not remove RTK from the control or force artificial raw commands/rereads to manufacture headroom. A future compound-aware treatment would be a different factor requiring its own policy preservation and coverage evidence.

Serena was genuinely used in both arms for symbol overview/search/references/diagnostics. Its failed symbol-body edit operations and subsequent recovery through file editing were visible in the traces and included in all token counters. It was not merely configured and silently omitted from the workflow. Tool usage varied naturally; no model or review calls were excluded to make one arm look cheaper.

## Uniform post-run quality audit

The first independent reviewer rejected the C++ patch because `current - target` can overflow for finite opposite-sign values near `DBL_MAX`; with zero smoothing time, multiplying the resulting infinity by zero yields NaN instead of snapping to the target.

All four actual C++ patches used the same vulnerable recurrence without a zero-time direct-assignment branch. A **zero-model-call local C++ replay**, compiling each saved patch independently, reproduced `finite=0, snaps=0`, exit 1, on all four. This replay was local Linux/Clang evidence, not another Mac model run; source-level correspondence is direct. The original frozen tests and recorded model reviews were not retroactively edited. This is a supplemental audit applied uniformly to every comparable patch, not an arm-specific new acceptance rule.

Original C++ review outcomes remain: off 1/2 accepted, on 2/2 accepted. **Audited C++ outcomes: off 0/2 acceptable, on 0/2 acceptable.** Do not publish the harness's original per-accepted ratios as a valid win. Its partial all-arm aggregate also mixes the unpaired TypeScript control; that aggregate is bookkeeping, not a balanced comparison.

A minimal reproducer is retained in `tests/rtk_zero_time_audit.cpp` alongside this report. Before any future batch, incorporate the discovered boundary into its frozen deterministic acceptance suite and strengthen the reference solution. Do not weaken the contract or ignore the defect to obtain successful-task denominators.

## Unpaired task, budget and all observed consumption

The TypeScript **off** trial and fresh review completed, passed all original tests and independent review, source/test integrity intact. Its cost was **643,612 total tokens**: 638,649 input, 578,816 cached subset, 4,963 generated output and 1,509 reasoning subset; 23 provider requests, 139.946 model-wall seconds. It has no treatment partner and provides **no TypeScript savings comparison**.

All five task attempts and five reviews in this batch consumed **3,043,463 provider-reported tokens**, comprising **3,016,351 input**, **2,683,648 cached subset**, **27,112 generated output**, **9,146 reasoning subset**, **113 provider requests**, and **753.317 summed model-wall seconds**. The observed-token stop was checked before starting the next implementation/review unit, so the last unit crossed the 3M threshold by 43,463 before the batch stopped. It was not a hard per-request cap. No unbounded retries or extensions followed.

The earlier defective short-fixture caller timed out before retaining usable accounting; its cost remains **unknown**, not zero. Earlier capability probes and this ChatGPT preparation/research session are not included in the new batch's totals. This is therefore not complete programme accounting. There is **no measured weekly subscription allowance conversion**; cached-token API pricing is not used to invent one.

## Tracking and next-use constraints

No candidate adoption, production tool install, global hook/rule mutation, source-project change or PR13 merge. Keep RTK stable and current SQLite recall unchanged. The larger eight-trial matrix is explicitly incomplete, the tested safe hook variant has zero observed additive coverage, and the primary matched quality-adjusted metric is undefined.

Issue #11 retains the next actionable findings: a compound-aware policy-preserving native-hook variant is a separate candidate; future batch budgeting should reserve complete off/on pairs rather than stop after an unpaired control; discovered reviewer defects must be replayed uniformly; and the zero-time numerical regression must enter future frozen fixture tests. None of these authorize further subscription spend automatically.

The private work inventory executed: two registered detached controller worktrees, current checkout clean and historical catalogue controller with two existing dirty entries. Both reported ahead one/behind one against stale origin metadata. GitHub inventory returned401, so merge candidates/open PRs/unassociated PRs are unknown, not zero. Exact private paths and raw inventories remain private.
