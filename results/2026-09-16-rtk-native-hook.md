# Native RTK hook result — 16 September 2026

## Verdict

**The native hook actually executes RTK on both tested Codex runtimes. It is not approved for blanket production adoption: command-prefix policy matching changes, and reviewed-issue savings are unmeasured.** Keep installed stable RTK unchanged. A narrowly read-only/policy-preserving hook treatment remains a possible later experiment; do not silently add global rules or enable every rewritten command.

This is a completed capability/safety investigation, not merely a prepared test. Four subscription-authenticated Luna/low invocations completed. A subsequent zero-inference audit resolved a collector visibility problem using only those exact saved rollouts. No further inference was launched after the four-invocation cap.

## Identity and evidence

Public authority: #11, source/review: PR #13. PR #12 remains merged; broader startup optimisation stays deferred.

- Candidate: official develop prerelease `dev-0.50.0-rc.431`, released 13 September 2026; exact source `5626e94a63a34d2792cdaa63a0613eda1d4abb1b`. The embedded binary reports `rtk 0.48.0`; this is NOT a stable-version upgrade and must not replace installed stable 0.49.0 by default.
- Candidate archive SHA256: `003057bcede4e1b519c957f22edae29782cf80382a0e03191ed3f7a277b75e83`; executable SHA256: `5a7ffea710be19b8a6a5dac5f5a8be88b23441f21c1fdb2750f6d8ce20b63585`.
- Zero-inference preflight executed lab `aeb16b588694ef19178bddfead8e842bc4a7ef35`: **55 lab tests, 15 real hook-protocol cases passed**.
- First live-gate setup executed `07c58348167271282043d45b0244d3ec19a37fa5`: **61 lab tests passed**, but per-hook state was not effective; stopped before inference. The launcher then encoded path-like hook keys inside a TOML state value rather than quoted dotted CLI keys. No trust bypass or global change was used.
- Actual four-arm live source: `e8f29884c85cf538a05188f4f1d1e8a97d5ce164`; **61 lab tests passed**. The workflow ended failure because its completion-event-only collector could not verify staging denial. Preserve that outcome; it is not a clean automated gate pass.
- Owned-rollout audit source: `7070ce21992ccf617647823df867e85ffaf45450`; completed successfully without another model call. It validates exact trace hashes and reads only the four matching session IDs.

All four private artifacts were downloaded, SHA256-verified and inspected. ZIP digests, in stage order:

```
85d071f2ab93a7022b0908d7c43f3ec37f1b6a31066b84c80a15a4cf8aff5856
3b296f940ec3f7bc16153a3502f2866d14615258e8eafb9d8d0e43468dea1fbc
75787b09b4e4f4a78a8df42af05b44184e8b995c83f871c2237a0505b09aac9d
92bc31625311945c7a5bbe6e535b56ebf72cc34c86bf25d91d58181d53e3a325
```

Exact private run/job/queue receipts, raw events, hook commands and paths remain in the existing private controller discussion/artifacts. Result-document revisions are not executed-source identities.

## What was actually verified

| Observation | Standalone CLI 0.154.0 | Desktop-bundled core 0.154.0-alpha.6.2 via app-server |
| --- | --- | --- |
| Exact session-scoped trial hook trusted; unrelated hook states unchanged | Verified | Verified |
| Hook-off: native hook calls / rewrites | 0 / 0 | 0 / 0 |
| Hook-on: native hook calls / rewrites | 3 / 3 | 3 / 3 |
| Pinned RTK execution proven by unpredictable output marker | Status, diff and attempted staging | Status, diff and attempted staging |
| Necessary explicitly selected skill / hidden-marker answer | Correct off and on | Correct off and on |
| New numeric coefficient read correctly | 0.000125 off and on | 0.000125 off and on |
| Recorded policy | Read-only, approval never | Read-only, approval never |
| Disposable staging attempt | Filesystem denial off and on | Filesystem denial off and on |
| Git index and protected global config/hooks | Unchanged | Unchanged |

The model generated raw commands; the trial delegate passed native RTK's hook response through unchanged. Actual output proved that the resulting command executed the pinned binary. The execution marker/adapter is diagnostic overhead, not a production optimisation.

The needed skill contained an unpredictable result prefix unavailable in the task prompt. All four answers included it and the value read from the diff. The inspected developer messages contained zero `Available skills` markers under the suppression flag. That narrow observation does not prove every possible catalogue/tool surface is absent, nor that all production coordinator/reviewer skills have been qualified. Serena was not replaced or disabled; its fixture metadata directory appeared in status output, but semantic Serena capability is not established by this test.

## Why the automated live job was red

The collector inspected CLI/app-server command-completion events. Those surfaces reported status and diff but did not include a command-completion item for the failed staging call. Therefore its `required_command_counts.add` remained zero and its exit-code-based denial check failed for all four arms.

The owned-rollout audit found the actual Code Mode `tools.exec_command` invocation and its corresponding tool response in every arm. Each reported failure to create the fixture's `.git/index.lock` with **Operation not permitted**. In both on arms the same failure output included the execution marker and RTK's failed-command summary. The bundled on arm additionally exposed **exit status 128**; exact exit status was not emitted into the retained outer tool output in the other three arms and must not be invented.

**Correction to the initial audit hypothesis:** this was not a demonstrated pre-execution policy rejection. Git actually attempted its lock-file write, the filesystem sandbox denied it, and the error remained visible to the model through Code Mode. Missing completion events did not mean a missing attempt. A future collector must reconcile nested Code Mode calls/results and distinguish absent, denied, failed, and unknown, rather than relying on a final answer or weakening the test. The original red result is retained; these separately audited observations establish the narrow mechanism/filesystem-denial facts.

## Concrete policy caveat

Both installed Codex runtimes' first-party execpolicy checker matched an explicit forbidden prefix rule for raw `git push`, but returned **no matching rule** for `rtk git push` with the same arguments. These were rule queries only: no push or remote mutation was executed.

This demonstrates a command-spelling/rule-matching gap, consistent with the upstream native-hook warning. It does not demonstrate that every permission or sandbox boundary is bypassed. The read-only lock-write denial above remained effective. However, rules covering an unwrapped command cannot be presumed to cover its RTK wrapper under ordinary writable sessions. Blanket hook adoption is blocked until the intended policy semantics are preserved or a properly qualified narrow command set is used.

## Provider-reported usage — all attempts included

Cached input is a subset of input; reasoning is a subset of output. Total below is input plus output, not a sum that counts the subsets twice.

| Diagnostic arm | Input | Cached input | Generated output | Reasoning subset | Total | Provider requests | Wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Standalone off | 51,365 | 39,936 | 397 | 75 | 51,762 | 4 | 22.737 |
| Standalone on | 51,442 | 41,984 | 373 | 62 | 51,815 | 4 | 23.409 |
| Bundled core off | 51,357 | 44,032 | 391 | 83 | 51,748 | 4 | 14.913 |
| Bundled core on | 25,643 | 22,016 | 349 | 72 | 25,992 | 2 | 13.320 |
| All four | **179,807** | **147,968** | **1,510** | **292** | **181,317** | **14** | **74.379** |

All four invocations exited zero, did not time out, and their saved per-request/cumulative usage reconciled. They remain diagnostic attempts, not completed-and-independently-reviewed coding issues. The failed pre-inference setup and the subsequent audit made zero model calls; their runtime/preparation overhead is not free. This table does not include this ChatGPT preparation/research session's unexposed usage and is not whole-programme accounting or a subscription-allowance estimate.

**Do not advertise the bundled on arm as a 50% RTK saving.** Its saved Code Mode input placed all three sequential shell calls into one script/model turn; the other arms used separate model turns. The reduction in provider round trips dominates this tiny example and is not attributable to compressed output. One off/on sample per different runtime also has cache/order/sampling confounds. Standalone totals were effectively unchanged. No repeated representative implementation/review test was performed, and the control deliberately requested raw commands to qualify interception rather than reproducing every current RTK convention.

## Next decision

Keep current stable RTK and its already enabled SQLite recall. Retain native hooks as **mechanism verified, policy/production qualification outstanding**, not an adopted optimisation. Preserve the Code Mode collector fix and policy-preserving/read-only hook variant as checklists in #11. The next separate larger-savings candidate remains sqz only where it adds a genuine residual dedup benefit over RTK and Serena. No further model batch is queued by this result.

Private controller inventory at the final audit: current Actions checkout detached/clean; historical catalogue controller detached with two existing dirty entries; both reported ahead one/behind one against stale local origin metadata. GitHub inventory returned401, so merge candidates and open PRs without worktrees are unknown, not zero. No worktree or credentials were changed to repair reporting.

Primary upstream references: https://github.com/rtk-ai/rtk/pull/3552 ; https://github.com/rtk-ai/rtk/blob/5626e94a63a34d2792cdaa63a0613eda1d4abb1b/hooks/codex/README.md ; https://developers.openai.com/codex/hooks .
