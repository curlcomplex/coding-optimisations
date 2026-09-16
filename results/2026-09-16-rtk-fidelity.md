# RTK fidelity result — 16 September 2026

## Verdict

**Completed Mac fidelity gate; no new stable-version treatment exists on this machine.** The installed RTK is already `rtk 0.49.0`, byte-identical to the checksum-pinned official arm64 release. SQLite recall is already selected. Do not spend subscription usage comparing those identical binaries or call existing recall an unimplemented upgrade.

PR #12 is merged at `ae6d5326dee795d57751855b378ba9fb45521657`. Executed RTK test source: `b71b469e44528fda2c318197c0ab089db73ae540`, in PR #13 under issue #11. The existing private Mac controller and current master resource-aware queue were used; exact controller/run/job/task receipts remain in the private controller discussion. The actual CLI lane was empty at the pre-submit check; this is a dated observation, not a claim about future queue state.

Private artifact was downloaded and inspected, not merely listed. ZIP SHA256: `d969d63165fad195c0cbe0256a426cf9b27b2af91f0f03c3afe330cebe8f9ce2`. The downloaded bytes matched this digest. Raw stdout/stderr and configuration paths remain private.

## Observed results

| Check | Result |
| --- | --- |
| Full lab unittest suite on Mac | **50 passed**, 0 failed/errors; 0.316 seconds |
| Installed RTK fidelity cases | **9/9 passed** |
| Official stable RTK fidelity cases | **9/9 passed** |
| Installed and candidate binary SHA256 | Both `055ef1cd1aa0afb96c854bddf43d24af10dcac5a6288ed44519cb1cc10b093a9` |
| Actual recovery setting | SQLite, already present |
| Advertised recall byte-exactness | 5/5 per arm |
| Nonzero exit values | 1, 8, 2, 1 and 17 preserved; success 0 preserved |
| Same-path changed diffs | Both versions of the changed value observed, no stale value substituted |
| Unicode status filename | Preserved |
| Installed binary and original RTK config | Hash/bytes unchanged after run |
| Model calls made by this slice | **0** |
| Whole-task model tokens / subscription savings | **Not measured** |
| Effective Desktop / full issue-worker baseline | **Not qualified by this run** |

The fixture matrix has six synthetic command-output cases and three real disposable Git operations per arm. It is not a CURLOP build, Faust render, browser test or independent coding-task review. Eighteen new local gate-mechanics tests were passed before dispatch; the Mac's 50-test count includes the existing accounting/catalogue tests and those 18, not 50 separate RTK product scenarios.

## Important quality finding

In **both identical binaries**, the synthetic Clang case reduced 5,450 raw bytes to 128 bytes across filtered stdout/stderr. The compact view retained the compiler error and file/line but omitted the following note's exact coefficients, `0.000125` and `0.125000`. The advertised recall command returned the complete 5,450 bytes byte-for-byte.

This passes the declared **recoverability** gate, not an inline-fidelity or reasoning-quality gate. An agent that never requests recall would miss those facts. Reading the full recall after the compact result would deliver 5,578 output bytes, exceeding the original 5,450, before counting the extra model turn/tool payload. That is an output-byte accounting example, not a provider-token or subscription calculation. Live tests must therefore measure whether the agent retrieves the missing evidence when needed and count that recovery overhead. No 97% whole-task-savings claim is justified.

The other four failure fixtures retained all selected critical facts inline and also exposed byte-exact full recall. The successful tiny test summary grew from 45 to 46 bytes. All filtered contents matched between the installed and official copies; differing milliseconds in a single run are not a speed comparison.

## What changes in the test queue

- **Skip the stable version-only live A/B:** same version and same binary hash.
- **Skip treating SQLite recall activation as a new optimisation:** already enabled.
- The separate native Codex hook update remains a real candidate: upstream PR rtk-ai/rtk#3552 merged on **13 September**, after stable 0.49.0. Qualify a pinned post-merge revision/package, exact installed Codex/Desktop support, hook selection and approval/sandbox preservation before a bounded hook-on/off comparison on the same candidate binary. Do not conflate hook activation with a version update or globally run `rtk init`.
- sqz remains a separate subsequent experiment only on a residual dedup surface not already covered by RTK/Serena.

## Evidence limits and safety

No global tool installation, config mutation, auth access, API/model calls or source-project changes. Both RTK replay arms used separate disposable stores and the same normalized config with telemetry/tracking disabled. This proves the binary replay route, not automatic interception in Codex Desktop. The merged lab skills setting was parsed as false; no claim that a fresh Desktop/CLI model request applied it was made. Required-skill/Serena capability checks and real issue/review comparisons remain distinct gates.

The private work report executed but its GitHub lookup returned HTTP401 in the credential-free controller checkout; merge/open-PR counts are unknown, not zero. No credential change was attempted. Its worktree inventory covers the controller checkout, not a complete audit of the owner's development repositories.
