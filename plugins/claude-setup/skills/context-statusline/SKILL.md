---
name: context-statusline
description: Configures ccstatusline so the Claude Code status line shows context window usage (token count and percentage). Use when the user wants to see context usage, token count, or context percentage in the status line.
disable-model-invocation: true
---

# Show context usage in the status line

Claude Code doesn't show context window usage by default. Set up [`ccstatusline`](https://www.npmjs.com/package/ccstatusline) so the status line shows a bold yellow token count followed by a dimmed percentage, e.g. `186.2k (17.3%)`.

## 1. Configure ccstatusline

Create `~/.config/ccstatusline/settings.json` (create the directory if missing). If the file already exists, show the user its current content and ask before overwriting.

```json
{
  "version": 3,
  "lines": [
    [
      {
        "id": "1",
        "type": "context-length",
        "color": "yellow",
        "bold": true,
        "rawValue": true
      },
      {
        "id": "2",
        "type": "custom-text",
        "customText": "(",
        "color": "brightBlack",
        "merge": "no-padding"
      },
      {
        "id": "3",
        "type": "context-percentage",
        "color": "brightBlack",
        "rawValue": true,
        "merge": "no-padding"
      },
      {
        "id": "4",
        "type": "custom-text",
        "customText": ")",
        "color": "brightBlack",
        "merge": "no-padding"
      }
    ],
    [],
    []
  ],
  "flexMode": "full-minus-40",
  "compactThreshold": 60,
  "colorLevel": 2,
  "defaultSeparator": " ",
  "inheritSeparatorColors": false,
  "globalBold": false,
  "powerline": {
    "enabled": false,
    "separators": [" "],
    "separatorInvertBackground": [false],
    "startCaps": [],
    "endCaps": [],
    "autoAlign": false
  }
}
```

`"merge": "no-padding"` glues the parentheses to the percentage, `"defaultSeparator": " "` adds the space after the token count, and `"rawValue": true` strips widget labels.

## 2. Update Claude Code settings

Add this to `~/.claude/settings.json` (create the file if missing). Merge it into the existing JSON — preserve every other setting. If a `statusLine` is already configured, ask the user before replacing it.

```json
{
  "statusLine": {
    "type": "command",
    "command": "npx ccstatusline@latest"
  }
}
```

## 3. Tell the user how to verify

The user must fully restart Claude Code. After restart the status line should show something like `186.2k (17.3%)`, updating as the context window fills.
