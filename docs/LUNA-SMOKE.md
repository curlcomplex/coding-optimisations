# Luna subscription smoke

Issue #4 is one bounded transport/accounting check, not a coding benchmark or RTK/Serena experiment. Use the existing trusted private controller and machine queue; no public self-hosted workflow, new runner, API key, automatic model fallback or production configuration changes.

Resolve Luna using the installed CLI's first-party App Server `model/list` (initialize/initialized handshake). Record the returned model identifier and reasoning effort rather than assuming a display name is a valid backend slug. `codex login status` must confirm the existing ChatGPT login before execution; no auth.json reading/copying. CLI capabilities must be checked against the installed version.

Execute the committed two-number fixture once, retain the real process exit code, JSONL stream and wall time privately, then validate the stored result without spending another model call:

```sh
python3 harness/collect_smoke.py PRIVATE/events.jsonl PRIVATE/summary.json --exit-code 0
python3 harness/verify_smoke.py PRIVATE/summary.json fixtures/smoke/expected.txt
python3 -m unittest discover -s tests -v
```

Replace `0` with the recorded process exit code, never an assumed success. The collector deliberately requires this argument; schema-1 summaries and old controller calls need migration before using the hardened verifier. The immutable original smoke run is not modified by this branch.

Schema 2 preserves raw usage, event counts, source SHA256 and exact answer; it rejects malformed/invalid events, missing usage, failure events, incomplete/multiple turns, duplicate completed items, invalid counters and unsuccessful process exits. A correct answer alone is insufficient. These checks are specific to the tiny one-turn smoke; tool failures/recovery in later coding tasks must be counted and evaluated, not silently discarded or universally treated as a failed task.

`input_plus_output_tokens` is the arithmetic sum of those two reported fields, not a proved subscription charge. Cached input is not added again. Optional reasoning fields remain as reported, never invented or automatically added on top of output. Missing measurements remain unknown. Raw traces can contain private information and are not automatically suitable for public release.

First-party format references: https://developers.openai.com/codex/noninteractive and https://developers.openai.com/codex/app-server . A Luna pass qualifies only this model/environment/task. RTK+Serena, representative coding tasks, repeated trials, independent review and model-specific quality remain later gates.
