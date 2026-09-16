# Repository-local context baseline

Owner clarification, 16 September 2026: remove unrelated optional startup context only for coding-optimisations, retain the capabilities each role needs, then freeze that configuration for both A/B arms. This is a small baseline setup change under #11, not a restart of the broad deferred #9 optimisation programme.

## Smallest supported change

`.codex/config.toml` sets `skills.include_instructions = false`. Codex documents trusted project-scoped configuration; the setting controls the automatic skills instructions/catalogue block. It does not uninstall skills, change global configuration, remove the core Codex prompt, or prove that every plugin/tool instruction disappears.

Use explicit skill selection in the task/role handoff where a skill is required. Do not reload the entire catalogue or all skill bodies to replace the block we removed. Preserve the installed delegation and independent-review mechanisms; resolve their actual current skill identities privately rather than inventing new ones. A plain coding fixture may need no skill body. Coordinator and reviewer roles may need different skills. Record the selected skills and their source hashes in the private execution manifest and hold them constant for each matched role across A/B. Explicit selections and any small routing instruction still count as baseline input.

This is NOT a security allowlist: non-selected skills remain installed and potentially invocable. It removes automatic exposure while making the required subset explicit. If the desktop build cannot resolve an explicitly selected required skill, do not call the profile qualified.

Do not use project-local `[[skills.config]]` as an assumed selective-disable solution. Upstream issue openai/codex#20210 reports that those rules are ignored at project scope. Source inspected at `8f38d5a877da8c5c2c0b5158e72bb5f2290a3157`, `codex-rs/config/src/skills_config.rs`, still reads per-skill rules only from User and SessionFlags layers. CLI `-c` rules are a session-specific alternative, not proof of a desktop per-project allowlist. Current upstream source is not runtime evidence for the installed desktop/CLI builds.

## What stays unchanged

Keep RTK, Serena, GitHub Issue authority, the current fresh-worker/model-selection policy, necessary tool discovery, exact build/test/audio/UI evidence and independent review. Keep AGENTS.md and the benchmark/runner safety contracts. Do not disable all MCP servers, overwrite model instructions, change models/reasoning, move auth, change CODEX_HOME, archive global skills, or alter any other repository. The previously approved #10 cleanup is not undone or repeated.

Other unused plugin/catalogue surfaces may be scoped only when their exact supported repository setting and absence from required capabilities are established. Do not turn this into another catalogue audit or speculative blanket disablement.

## Scope matters

Project configuration requires a trusted project and a session working directory within its configuration scope. Check effective configuration in a NEW Codex Desktop thread and in the actual CLI/controller launch path separately. Existing thread history is not retroactively reduced.

Fixtures launched in external temporary directories or separate source checkouts do not automatically inherit this lab's `.codex/config.toml`. The private controller must either launch within the intended trusted lab scope or pass the equivalent supported session override to BOTH benchmark arms. Do not write the setting into the source project's production checkout or the user's global configuration. Record the effective setting, selected skills, working-directory scope and common instruction hashes in the private manifest; publish only deliberately sanitised identities/counts.

## Bounded acceptance, not another optimisation campaign

First inspect effective configuration and model-visible context without inference where the installed client supports it. Confirm the catalogue is absent, required safety instructions remain, and an unrelated repository retains its normal configuration. For any existing usable capability evidence, reuse the exact matching client/version/config evidence rather than repeating it.

Where runtime verification is still needed, use only a bounded targeted capability check through the established private controller and current shared resource queue. Confirm an explicitly selected necessary skill genuinely loads (a hidden marker unavailable in the task prompt prevents false passes), and that required RTK/Serena/review paths still work. Use the existing collector; no new runner, scheduler or harness. Record desktop and CLI status independently. Do not dispatch the old five-run startup A/B matrix as a prerequisite for #11.

If scope/capabilities fail, retain the current known-working baseline, record the blocker and proceed with the larger candidate work under that stable baseline. Never silently remove required capabilities or claim that source/config parsing is runtime success. Once the small profile is qualified, assign its baseline ID and freeze it for the whole batch. Do not mix results from old and new baseline identities.

Rollback is reverting this repository config and the accompanying short AGENTS routing paragraph, then using a fresh session; restore any paired controller session override as well. No global installation or authentication changes are involved.

## Primary references (checked 16 September 2026)

- https://developers.openai.com/codex/config-reference/ — trusted project-scoped configuration.
- https://developers.openai.com/codex/app/settings/ — desktop configuration surfaces; runtime parity still requires verification.
- https://github.com/openai/codex/issues/20210 — project-local selective skill-filter limitation.
- https://github.com/openai/codex/blob/8f38d5a877da8c5c2c0b5158e72bb5f2290a3157/codex-rs/config/src/skills_config.rs — include_instructions and accepted per-skill rule layers.
- https://github.com/openai/codex/blob/8f38d5a877da8c5c2c0b5158e72bb5f2290a3157/codex-rs/ext/skills/src/extension.rs — separate catalogue contribution and skill invocation/tool paths.

Status: proposed repository config, not an installed-Mac result or measured token saving. See #11 and this change's PR for current validation evidence.
