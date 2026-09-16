# RTK first slice — issue #11

PR #12 merged as `ae6d5326dee795d57751855b378ba9fb45521657`. Its repository setting is source-integrated, not yet proof of effective Desktop/CLI context. Do not repeat the old startup optimisation matrix.

## Existing-tool preflight and scope

Reuse real RTK subcommands (`err`, `test`, `git diff`, `git status`, `recall`), Python unittest, and the established private resource-aware controller queue. RTK's built-in gain counters do not enforce preservation of this project's numeric diagnostics, exact exit codes, or reviewed-task correctness. The small lab script supplies those assertions; it is not a replacement coding harness or scheduler. No Codex model invocation is made by this slice.

Control binary: currently installed RTK, immutable hash recorded at execution. Candidate: official stable v0.49.0 (11 September 2026), source `b1c0dc00649c50fbe8930f849c800d4d6ca12091`. The Apple Silicon archive is pinned in code to SHA256 `bbbfebabb22686993a80da731aa4d5d35116fb8ae24abb00608efa028e13ae01`; the archive is inspected and one regular executable is written to private test storage, not installed globally.

Both binaries receive separate disposable HOME/config/data directories. Preserve filtering/recovery choices from the existing standard macOS RTK config while redirecting known writable store paths and disabling tracking/telemetry equally. Record the normalized configuration hash. This normalized replay environment is NOT asserted to be the full live Codex workflow. Verify installed-version config discovery before claiming production equivalence.

Nine checks per binary: synthetic Clang stderr; CTest-like failure; TypeScript error; web-UI test assertion; custom nonzero exit with exact audio numbers; successful tests; two successive same-path changed Git diffs; Unicode Git status. Synthetic diagnostics are labelled as such, not actual product build/audio/UI results. Exact stdout/stderr and recovery evidence remain private. Recoverability is necessary, not proof an agent would request the omitted facts.

## Bounds and gates

- Model calls: **zero**. No API key, auth access, Codex home change, global RTK init/install, or production source changes.
- Whole script deadline: 300 seconds; subprocess default: 15 seconds; download: 40 seconds; archive: at most 10 MB; executable member: at most 50 MB.
- Every emitted critical fact must be inline or recovered byte-exactly from an advertised recall reference. Exit values must be preserved, not merely classified nonzero. Timeout/malformed setup fails closed.
- The first implementation understands SQLite `rtk recall` references, not legacy tee-path hints. Missing facts with a tee-only hint require checking that explicit coverage gap before blaming the binary; do not call them universally unrecoverable or accept the full candidate gate without qualification.
- No model-token or subscription-savings claim from byte counts. Failed cases remain in the result.
- Same installed/candidate version is reported as a no-op version comparison; no invented upgrade win.
- Run the full existing lab unittest suite on the Mac as well as the new tests. Local new-suite results alone are not a Mac binary result.

## Next, separately

Only after fidelity and actual required-capability checks, freeze real issue fixtures/model/reasoning/review policy and run the bounded live screening in #11. Desktop automatic interception remains separate from direct binary-wrapper fidelity. Native Codex hook work was merged upstream in rtk-ai/rtk#3552 on 13 September, after stable 0.49.0. That is a distinct prerelease integration treatment and must be pinned/qualified separately, not silently bundled into a stable version test.

Primary sources: https://github.com/rtk-ai/rtk/releases/tag/v0.49.0 ; https://github.com/rtk-ai/rtk/blob/v0.49.0/src/core/config.rs ; https://github.com/rtk-ai/rtk/blob/v0.49.0/src/core/retriever.rs ; https://github.com/rtk-ai/rtk/pull/3552 .

Current execution/results are tracked in #11 and this slice's PR. Preparation is not dispatch; dispatch is not completion; binary fidelity is not reviewed-task savings.
