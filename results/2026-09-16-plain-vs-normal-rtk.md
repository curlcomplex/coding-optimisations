# Plain Codex+Serena vs normal RTK+Serena — completed A/B, 16 September 2026

## Result

**On this fixed reviewed coding cohort, normal RTK did not save model tokens. It increased them.**

Eight implementation attempts completed: two C++ repetitions and two TypeScript/UI repetitions, each with plain and RTK arms. Every implementation passed the strengthened deterministic tests and every fresh independent review accepted the patch. Worker: GPT-5.6 Terra medium. Reviewer: GPT-5.6 Luna medium. Same bundled Codex engine, Serena configured, automatic skill catalogue suppressed, no native automatic RTK hook.

| Metric | Plain Codex + Serena | Normal RTK + Serena | RTK delta |
| --- | ---: | ---: | ---: |
| Accepted issues | 4/4 | 4/4 | equal quality gate |
| Provider total tokens | 887,553 | 1,279,499 | **+44.2%** |
| Input tokens | 874,753 | 1,262,481 | **+44.3%** |
| Cached input subset | 750,080 | 1,109,248 | +47.9% |
| Generated output | 12,800 | 17,018 | **+33.0%** |
| Reasoning subset | 4,422 | 6,646 | +50.3% |
| Provider requests | 50 | 67 | **+34.0%** |
| Worker+review wall time | 326.1 s | 441.6 s | **+35.4%** |
| Tokens / accepted issue | 221,888 | 319,875 | **+44.2%** |

RTK wrapper execution count was 47 across the four treatment trials and zero in control. One RTK UI trial legitimately chose not to use RTK at all; it passed all implementation/test/review gates and is counted as an accepted treatment result because normal RTK is an available workflow tool, not a requirement to wrap every task. The harness originally stopped on that optional-use assertion; the remaining UI repetition-2 pair was completed separately without changing the task, models, tests or acceptance criteria. Combining the immutable completed rows gives the fixed eight-trial cohort above.

## Interpretation

This is evidence against assuming RTK saves whole-task tokens automatically in this workflow. On these small-to-medium synthetic C++ and web-UI fixes, the RTK arms made more provider requests and consumed more input/output despite compressed command results. The likely mechanism visible in the traces is extra tool interaction/command decomposition overwhelming the bytes saved by individual compressed outputs. This is a measured cohort result, not a claim that RTK can never help: workloads with very large compiler/test/diff output may behave differently.

Do not convert RTK's per-command compression/gain counters into whole-task savings. For the tested workload, the measured whole-task effect went in the opposite direction.

## Quality / protocol notes

The C++ fixture included the independently discovered zero-time `DBL_MAX -> -DBL_MAX` regression before this cohort, closing the quality hole from the previous native-hook experiment. Original tests/specs were protected and externally rerun; reviewer source mutation was prohibited; diff checks passed. The control arm removed RTK from task PATH and explicitly used ordinary shell commands. The treatment used installed stable RTK 0.49.0 and the existing recover-if-needed convention. Serena remained configured in both arms.

The two arm-specific AGENTS contracts necessarily differ only in shell workflow wording (plain shell vs existing RTK wrapper). That instruction overhead is part of the actual RTK treatment. Starting source/tests/issues are otherwise identical within fixture; Git commit IDs differ because AGENTS is committed.

## Evidence

Primary six-row run: private controller run 35116780055 / queue task 1033, artifact SHA256 `17a6b15318a96612daa5606f8a9fce89630f6da5c87ee157f1885f7596c25632` (downloaded and digest-verified). It completed both C++ pairs and UI repetition-1 pair before the optional-use assertion stopped the harness after the valid RTK UI result.

Completion pair: private controller run 35118033609 / queue task 1036, successful, artifact SHA256 `19c703d7e709d6e7ceb04946dd3d889bc74db68508ded856d121bdaeda8cdbb5` (downloaded and digest-verified). It completed UI repetition 2, RTK then plain.

All provider accounting used input + output as total; cached input is a subset of input and reasoning is a subset of output. No API billing was used and no mapping to weekly subscription allowance is claimed. Global Codex/RTK configuration remained unchanged. Raw traces remain private.
