# Runner routing

## Established route

Reviewed lab commit -> trusted private Actions controller -> existing Mac runner -> existing shared machine queue -> private raw evidence -> deliberately sanitised lab result.

The lab remains the source/issue authority. The controller is an execution adapter, not a second project-management system. Runner registration, exact labels, machine identity and queue implementation are recorded in the owner's private controller; inspect those authorised sources rather than guessing or copying private configuration here.

Faust-expr issue #30 documents the same public-source/private-controller separation. Its default GitHub-hosted workflow does not describe every available execution route. A queued job in this new public repository never proves the owner's Mac is absent or offline.

## Verified checkpoint: 15 September 2026

A newly launched private Actions preflight ran on the existing Mac, checked out this lab at an immutable SHA, queried the established queue and verified Codex CLI 0.144.0 with ChatGPT login. RTK and uv were discoverable. A task was already active in the shared queue; the read-only diagnostic did not launch competing benchmark work or model inference. The exact run and raw evidence remain private.

This establishes routing and login availability only. An actual subscription-authenticated `codex exec`, Serena activation, complete working-baseline configuration, robust accounting and repeated A/B measurements remain separate gates in issue #2.

## Safety

Do not use a public/fork PR to execute on the Mac. Do not add a direct self-hosted workflow here or register a second service. The initial public probe/smoke workflows were removed because they were misrouted and lacked the trusted-controller boundary.

Keep private code, credentials, machine paths, raw agent traces and live configuration out of this repository. Controller checkouts must not disturb the owner's development worktrees; use dedicated execution storage and preserve unrelated state. Run benchmark workloads through the existing shared queue, without cancellation or queue bypass. No API key fallback, paid model calls, global installs or production tool/skill edits.

Hosted subscription execution is deferred in issue #3. Neither public CI success nor repository visibility establishes support for it.
