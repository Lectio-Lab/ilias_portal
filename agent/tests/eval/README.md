# Agent Eval Harness

Golden prompts for testing ILIAS Portal agent skill + MCP integration in Cursor.

## How to run

1. Ensure backend is running and credentials are configured (see [agent/README.md](../../README.md))
2. Open Cursor Agent Mode
3. Run each prompt from `prompts.jsonl` one at a time
4. Record which MCP tools were called and whether the workflow succeeded

## Scoring

For each prompt, check:

| Metric | Pass criteria |
|--------|---------------|
| Tool selection | Called expected tool(s) from `expected_tools` |
| Call count | Total tool calls ≤ `max_calls` |
| Confirmation | Write prompts (`requires_confirmation: true`) — agent asked user before calling |
| Errors | Zero unrecoverable API errors |

## Improvement loop

1. Run all prompts, log failures to `results/` (gitignored)
2. For mis-selected tools → improve tool descriptions in `agent/mcp-server/src/index.ts`
3. For wrong workflows → improve `.cursor/skills/ilias-portal/SKILL.md`
4. Re-run failed prompts only
5. Do not modify `prompts.jsonl` without team review (immutable judge)

## Example log format

```json
{
  "prompt": "Show me all my ILIAS courses",
  "tools_called": ["ilias_list_courses"],
  "call_count": 1,
  "passed": true,
  "notes": ""
}
```

Save logs to `agent/tests/eval/results/YYYY-MM-DD.jsonl`.
