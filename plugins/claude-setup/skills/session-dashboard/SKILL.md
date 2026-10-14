---
name: session-dashboard
description: Use when the user asks for a dashboard/overview of their Claude Code sessions — what they worked on, which sessions are running, which memory entries belong to which session, how to resume ("nad czym pracowałem", "gubię się w sesjach", /session-dashboard).
---

# Session dashboard

Scripts live next to this file (the skill's base directory, shown when the skill loads).

1. Run `<skill base dir>/start.sh` — starts the live server (http://localhost:8765, page rebuilt on every request, auto-reload every 30s) if not already running and opens it in the browser (Windows browser from WSL, `xdg-open` otherwise). Port: env `DASH_PORT`.
2. Reply in one line: the URL. Nothing else unless the user asked a question about their sessions.

Only if the user explicitly wants a static file: `python3 <skill base dir>/build.py <out.html>`.
To stop the server: `pkill -f 'session-dashboard/build.py --serve'`.

Data sources (read-only): `~/.claude/projects/*/*.jsonl` (transcripts), `~/.claude/sessions/*.json` (running sessions, liveness via `/proc/<pid>`), `~/.claude/projects/*/memory/project_*.md`.

Sections: running sessions (busy/idle, last prompt, `claude --resume <id>`), memory entries (project_*.md + sessions that wrote/read them, newest writer highlighted, each with `claude --resume <id>`), full session list — text search, filter by invoked skill (Skill tool or slash command), running-only toggle.
