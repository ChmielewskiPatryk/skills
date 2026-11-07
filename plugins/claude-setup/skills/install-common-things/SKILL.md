---
name: install-common-things
description: Installs the user's standard Claude Code setup on a new machine — currently the two-line status bar (model, context %, session cost, 5h rate limit bar, directory, worktree, git branch with staged/modified counts). Use when the user runs /install-common-things or asks to set up their usual Claude Code things on a new computer.
disable-model-invocation: true
---

# Install common things

Installs the user's usual Claude Code setup. Each section below is one "thing"; install all of them unless the user names specific ones. Before each step that overwrites something, check what is there.

When done, report briefly what was installed, what was skipped and why.

## 1. Status bar

Source: <https://ianodad.medium.com/claude-code-status-bar-setup-60f3f1c1c532>, with two fixes: the directory falls back to `.workspace.current_dir // .cwd` outside a worktree, and the 7-day rate limit variables are defined, so the commented `7d` line works once uncommented.

Result (after restart):

```
🤖 Opus | 🧠 42% | 💰 $1.23 | ⏱️ 5h ███████░░░ 74% resets 8:33AM
📁 projekty | 🌳 no worktree | 🌿 main +1 ~2
```

### 1.1 jq

Check `jq --version`. If missing, install it: `sudo apt-get install -y jq` (Debian/Ubuntu; without sudo when running as root), `brew install jq` (macOS). If installing fails, stop this section and tell the user.

### 1.2 Script

Copy `assets/statusline-command.sh` (next to this SKILL.md) to `~/.claude/statusline-command.sh` and `chmod +x` it. If the target already exists and differs, show the diff and ask before overwriting.

### 1.3 settings.json

Set `statusLine` in `~/.claude/settings.json` (create the file with `{}` if missing), preserving every other key:

```json
"statusLine": {
  "type": "command",
  "command": "sh ~/.claude/statusline-command.sh",
  "padding": 0
}
```

If a different `statusLine` is already configured, tell the user what it is and ask before replacing it. Back up the file first as `~/.claude/settings.json.bak-statusline`. Merge with jq, e.g.:

```sh
tmp=$(mktemp) && jq '.statusLine={"type":"command","command":"sh ~/.claude/statusline-command.sh","padding":0}' ~/.claude/settings.json > "$tmp" && mv "$tmp" ~/.claude/settings.json
```

### 1.4 Verify

```sh
echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":42},"cost":{"total_cost_usd":1.23},"workspace":{"current_dir":"'"$PWD"'"},"rate_limits":{"five_hour":{"used_percentage":74,"resets_at":1793000000}}}' | sh ~/.claude/statusline-command.sh
```

It should print two lines like the example above (ANSI colour codes show raw in captured output; that's fine). Tell the user to restart Claude Code.

### Customising

- 7-day limit: uncomment the `# rate_limit_str=...7d` line.
- Bar width: `width=10` in `make_bar()`.
- Colour thresholds in `format_rl()`: yellow at 70%, red at 90%.
