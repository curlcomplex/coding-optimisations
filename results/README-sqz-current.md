# Current sqz benchmark evidence — 16 September 2026

## Latest: additional exact-repeat dedup after RTK

**Completed and artifact-audited. No additional compression or demonstrated whole-task benefit; do not adopt this adapter.** See `2026-09-16-sqz-dedup.md`.

Eight implementations plus eight fresh reviews, identical initial model-visible instructions/prompts/setup and starting source within each fixture. Runtime tests: 4/4 in both arms. Original independent reviews: 4/4 baseline, 3/4 sqz. Provider totals including review: 1,817,736 baseline versus 1,721,880 sqz; generated output: 17,702 versus 17,372. These raw differences are NOT established savings: sqz saw four eligible outputs and removed zero additional bytes in the coding cohort. The repeat/expansion mechanism passed separately before inference. The recorded review rejection concerns an unpinned TypeScript library target, not an established sqz-caused regression. Preserve its cost and original verdict.

Executed lab source `ef8d88f8c3501736ccc2cacb3543d23f8669075c`; 94 Mac lab tests passed. Private artifact SHA256 `c2ae1f343f8789b423e7cb80006c0a5366b74027094c502b19848de5f1633101` was downloaded, verified and inspected. Report commits are not the executed source. This is the tested RTK-output adapter, not automatic interception of every shell/MCP result.

## Earlier, separate standalone shell-compression prototype

Retained in `2026-09-16-sqz-ab.md` and `2026-09-16-sqz-build-notes.md`. It compared sqz to raw shell output, not RTK+Serena plus dedup. Four originally accepted outputs in each arm; 661,690 versus 678,184 provider tokens, 12,574 versus 13,118 output tokens; eight rewritten commands. Its generic compression/hook/cache design is distinct from the latest per-role exact-dedup adapter. Do not pool cohorts or treat this prototype as an approved production integration.

Both completed sqz cohorts together consumed 4,879,490 model tokens and 60,766 generated output tokens across 32 role invocations. Build/receipt work made no model calls. No subscription-allowance percentage is inferred. No global configuration change or production adoption; PR #15 remains draft under issue #11.
