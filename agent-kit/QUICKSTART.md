# Instructor Quickstart

This kit connects an MCP-capable agent to Ovidius ILIAS. It needs Node 22.12+,
Python 3.12+, and Google Chrome; it does not need Docker or a database.

```bash
./install.sh
./start.sh
```

Configure your agent using `mcp-config/installed/`, copy `skill/ilias-portal/` into
the agent's skill directory, then ask:

> Check my ILIAS setup and refresh my courses.

Complete university login and MFA only in the visible browser window. The kit stores
only resulting session cookies, never university credentials.

## Post a supplied grade

Provide the exact course, exercise, assignment, participant login, and values to
enter. The agent resolves the exact participant, shows current and proposed values,
requires confirmation, posts once, and reports `verified: true` only after ILIAS
confirms the write.

```bash
./stop.sh
```

See `INSTALL.md` for agent-specific setup and troubleshooting.
