# Security Policy

Lectio Lab / ILIAS Portal Agent Kit is a single-instructor, local-only tool built
for a university course project — not a versioned multi-tenant service. The
sections below reflect that, rather than the generic GitHub template.

## Supported versions

There's no version support matrix here. Only the current code on `main`, and the
latest release zip under [`dist/`](dist/), is supported. If you're on an older
tagged build, please update before reporting an issue against it.

## Where the actual security model lives

The concrete security model — localhost-only binding, bearer-token auth, how ILIAS
session cookies are stored and protected, the download-proxy allowlist, and what's
excluded from the packaged kit — is documented in
[`agent-kit/SECURITY.md`](agent-kit/SECURITY.md). Read that first; this file is
about how to report a problem, not what the protections are.

## Reporting a vulnerability

This is a student project without a dedicated security team, so please be
patient — but every report is read and taken seriously.

- **Preferred:** open a private report through GitHub's own flow — this repo's
  **Security** tab → **Report a vulnerability**. That keeps the report private
  until it's fixed.
- If that flow isn't available to you, open a regular issue and just say you
  have a security report to make without details, and we'll follow up privately.

What to expect:

- An acknowledgement within about a week — best-effort, since there's no formal
  SLA behind this.
- If confirmed, a fix is prioritized and a note goes into the changelog once it
  ships. Reporters are credited if they'd like to be.
- If declined (for example, something that only matters if you already have local
  shell access to the instructor's own machine — see below), you'll get an
  explanation of why.

## Out of scope

Given the local-only, single-instructor design, a few things are intentionally
not treated as vulnerabilities here:

- Anyone who already has local shell access to the instructor's own machine — the
  tool is designed to run as that user, with that user's trust.
- The instructor's ILIAS login itself. Authentication and MFA always happen
  through the university's real ILIAS login page in a visible browser window,
  never through this tool, so a login weakness there is a university ILIAS issue,
  not an issue with this kit.
