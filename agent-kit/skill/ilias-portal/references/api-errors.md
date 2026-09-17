# API Error Recovery Guide

## Missing local token

Run `./install.sh` to provision `agent/credentials/.env.local`, then restart MCP.
Do not create or send a university password in chat.

## ILIAS session expired

Call `ilias_refresh_courses` once, complete MFA in the visible browser, then retry
the original operation once.

## Local service errors

Run `./start.sh`, inspect `.run/backend.log`, and use the health-check script. The
service must be available only on `127.0.0.1:8010`.

## Optional Markdown renderer

Use `ilias_publish_slides` for existing PDFs and files. If Markdown-to-PDF reports
that the optional renderer is unavailable, install the authoring add-on only with an
installed Chrome executable or explicit consent for a browser download.
