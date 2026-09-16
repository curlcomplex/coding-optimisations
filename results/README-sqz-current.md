# Current sqz first-round verdict

Completed 16 September 2026. See `2026-09-16-sqz-ab.md` and `2026-09-16-sqz-build-notes.md`.

For the isolated transparent shell-compression treatment on ordinary bounded C++/UI issue workers: 4/4 accepted in each arm; sqz treatment used 678,184 total provider-reported tokens versus 661,690 raw-shell control (+2.49%), with 13,118 versus 12,574 output tokens (+4.33%). Eight shell commands were actually rewritten. Verdict: reject this treatment for this workload; no production adoption. This is not an RTK+sqz residual result and does not rule out a separate log-heavy workload test.
