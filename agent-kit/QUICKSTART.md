# Instructor Quickstart

This kit connects an MCP-capable agent to Ovidius ILIAS. University credentials
and MFA are entered only in the visible university browser window.

## Install and start

```bash
./install.sh
./scripts/provision-interactive-auth.sh
./start.sh
```

Configure your agent with the generated file under `mcp-config/installed/`, copy
`skill/ilias-portal/` into the agent's skills directory, and restart the agent.

Ask the agent:

> Check my ILIAS setup and refresh my courses.

Complete university login and MFA if a browser window opens.

## Post a supplied grade

Provide the exact course, exercise, assignment, participant login, and values you
want entered. For example:

> In course 123, for the exercise at https://ovidius.uni-tuebingen.de/goto.php/exc/456,
> assignment 7, set exact ILIAS login `student_login` to `passed`, mark `1.3`,
> and comment `Good work`.

The agent will first show the resolved participant and current values. Review the
before/after summary and confirm before it writes. A successful result explicitly
says `verified: true` and includes the ILIAS grading URL.

The agent only enters values you supply. It does not calculate, recommend, infer,
or choose grades. It also refuses partial participant-logins, stale current
values, ambiguous targets, batch grading by default, and unverified writes.

## Stop

```bash
./stop.sh
```

See `INSTALL.md` for agent-specific setup and troubleshooting.
