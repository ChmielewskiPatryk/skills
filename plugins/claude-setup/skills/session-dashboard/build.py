#!/usr/bin/env python3
"""Generate a static HTML dashboard of Claude Code sessions (~/.claude/projects transcripts)."""
import glob, html, json, os, re, sys, time
from collections import Counter, defaultdict
from datetime import datetime

CLAUDE = os.path.expanduser("~/.claude")
DEFAULT_OUT = os.path.join(CLAUDE, "dashboard", "index.html")
KEY_RE = re.compile(r"\b(KRYPTO|KWDT|KWD|SME)-\d+\b")
NOISE_RE = re.compile(r"^\s*<(command-|local-command|system-reminder|task-notification|bash-)")


def ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def user_text(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


MEM_RE = re.compile(r"/memory/(project_[\w.-]+\.md)")
WRITE_RE = re.compile(r"(>|tee |sed -i|mv |cp )[^\n]*/memory/project_")
SKILL_RE = re.compile(r"Base directory for this skill: \S*/skills/([\w.-]+)")


def mem_touches(name, inp):
    if name in ("Write", "Edit", "Read"):
        m = MEM_RE.search(inp.get("file_path") or "")
        if m:
            yield m.group(1), "read" if name == "Read" else "write"
    elif name == "Bash":
        cmd = inp.get("command") or ""
        kind = "write" if WRITE_RE.search(cmd) else "read"
        for f in set(MEM_RE.findall(cmd)):
            yield f, kind


def live_sessions():
    live = {}
    for f in glob.glob(os.path.join(CLAUDE, "sessions", "*.json")):
        try:
            o = json.load(open(f))
        except Exception:
            continue
        alive = os.path.exists("/proc/%d" % o.get("pid", 0))
        prev = live.get(o["sessionId"])
        if prev and prev["alive"] and not alive:
            continue
        live[o["sessionId"]] = {"alive": alive, "status": o.get("status"), "name": o.get("name"), "kind": o.get("kind")}
    return live


def parse(path):
    s = {"id": os.path.basename(path)[:-6], "title": None, "ai_title": None, "prompts": [], "last_prompt": None,
         "branches": Counter(), "cwd": None, "start": None, "end": None, "keys": Counter(), "assistant": 0, "mem": {}, "skills": set()}
    for line in open(path, errors="replace"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        t = o.get("type")
        if t == "custom-title":
            s["title"] = o.get("customTitle") or s["title"]
        elif t == "ai-title":
            s["ai_title"] = o.get("aiTitle")
        elif t == "last-prompt":
            s["last_prompt"] = o.get("lastPrompt")
        if o.get("isSidechain"):
            continue
        if o.get("timestamp"):
            x = ts(o["timestamp"])
            if x:
                s["start"] = min(s["start"] or x, x)
                s["end"] = max(s["end"] or x, x)
        if o.get("cwd"):
            s["cwd"] = o["cwd"]
        if o.get("gitBranch") and o["gitBranch"] != "HEAD":
            s["branches"][o["gitBranch"]] += 1
        if t == "user":
            for m in SKILL_RE.finditer(user_text(o.get("message") or {})):
                s["skills"].add(m.group(1))
        if t == "assistant":
            s["assistant"] += 1
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    if b.get("name") == "Skill" and (b.get("input") or {}).get("skill"):
                        s["skills"].add(b["input"]["skill"].split(":")[-1])
                    for f, kind in mem_touches(b.get("name"), b.get("input") or {}):
                        prev = s["mem"].get(f)
                        if not prev or kind == "write":
                            s["mem"][f] = (kind, s["end"])
        if t == "user" and not o.get("isMeta") and "toolUseResult" not in o:
            txt = user_text(o.get("message") or {}).strip()
            if txt and not NOISE_RE.match(txt):
                s["prompts"].append((s["end"], txt))
                for m in KEY_RE.finditer(txt):
                    s["keys"][m.group(0)] += 1
    for m in KEY_RE.finditer(" ".join(filter(None, [s["title"], s["ai_title"]]))):
        s["keys"][m.group(0)] += 3
    for b in s["branches"]:
        for m in KEY_RE.finditer(b):
            s["keys"][m.group(0)] += 2
    return s


def memories():
    out = []
    for f in sorted(glob.glob(os.path.join(CLAUDE, "projects", "*", "memory", "project_*.md"))):
        txt = open(f, errors="replace").read()
        name = re.search(r"^name:\s*(.+)$", txt, re.M)
        desc = re.search(r"^description:\s*(.+)$", txt, re.M)
        body = txt.split("---", 2)[-1].strip()
        out.append({"file": f, "name": name.group(1).strip() if name else os.path.basename(f),
                    "desc": desc.group(1).strip() if desc else "", "body": body,
                    "keys": sorted(set(m.group(0) for m in KEY_RE.finditer(txt))), "mtime": os.path.getmtime(f)})
    return out


def fmt(t):
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "?"


def ago(t):
    if not t:
        return "?"
    d = time.time() - t
    for n, u in ((86400, "d"), (3600, "h"), (60, "min")):
        if d >= n:
            return "%d %s temu" % (d // n, u)
    return "teraz"


def e(x):
    return html.escape(x or "")


def clip(x, n):
    x = re.sub(r"\s+", " ", x or "").strip()
    return x if len(x) <= n else x[: n - 1] + "…"


def render(live_reload=False):
    live = live_sessions()
    sessions = []
    for p in glob.glob(os.path.join(CLAUDE, "projects", "*", "*.jsonl")):
        s = parse(p)
        if not s["prompts"] and not s["ai_title"]:
            continue
        s["live"] = live.get(s["id"])
        sessions.append(s)
    sessions.sort(key=lambda s: s["end"] or 0, reverse=True)
    mems = memories()

    # --- cards: running sessions
    running = [s for s in sessions if s["live"] and s["live"]["alive"]]
    cards = []
    for s in running:
        st = s["live"]["status"] or "?"
        title = s["title"] or s["ai_title"] or clip(s["prompts"][0][1] if s["prompts"] else "", 60)
        last = s["prompts"][-1][1] if s["prompts"] else s["last_prompt"]
        cards.append(f"""<div class="card {e(st)}"><div class="top"><span class="badge {e(st)}">{e(st)}</span>
<span class="name">{e(s['live']['name'])}</span><span class="muted">{ago(s['end'])}</span></div>
<h3>{e(title)}</h3><div class="muted">{e(', '.join(s['keys']) or '')} {e(' · '.join(list(s['branches'])[-2:]))}</div>
<p class="last">↳ {e(clip(last, 220))}</p><code>claude --resume {s['id']}</code></div>""")

    # --- memory entries -> sessions that wrote/read them
    touched = defaultdict(list)
    for x in sessions:
        for f, (kind, t) in x["mem"].items():
            touched[f].append((kind, t or x["end"] or 0, x))
    cards_mem = []
    for m in sorted(mems, key=lambda m: -m["mtime"]):
        f = os.path.basename(m["file"])
        tl = sorted(touched.get(f, []), key=lambda k: (k[0] == "write", k[1]), reverse=True)
        items = []
        for i, (kind, t, x) in enumerate(tl[:6]):
            lv = x["live"] if x["live"] and x["live"]["alive"] else None
            badge = '<span class="badge %s">%s</span> ' % (e(lv["status"]), e(lv["status"])) if lv else ""
            title = x["title"] or x["ai_title"] or clip(x["prompts"][0][1] if x["prompts"] else "", 60)
            items.append(f"""<li class="{'main' if i == 0 else ''}">{badge}<a href='#s-{x['id']}'>{e(title)}</a>
<span class="muted">{'✏️ zapis' if kind == 'write' else '👁 odczyt'} · {fmt(x['end'])}</span><br><code>claude --resume {x['id']}</code></li>""")
        q = " ".join([m["name"], m["desc"], f] + [k[2]["ai_title"] or "" for k in tl]).lower()
        cards_mem.append(f"""<div class="ticket" data-q="{e(q)}"><div class="top"><b>{e(m['name'])}</b><span class="muted">memory {ago(m['mtime'])}</span></div>
<p class="last">{e(m['desc'])}</p><details><summary>pełna notatka</summary><pre>{e(m['body'])}</pre></details>
<ul>{''.join(items) or '<li class="muted">nie znaleziono sesji (zapis spoza transkryptów)</li>'}</ul></div>""")

    # --- session table
    rows = []
    skill_count = Counter(k for s in sessions for k in s["skills"])
    for s in sessions:
        lv = s["live"]
        st = (lv["status"] if lv and lv["alive"] else "") or ""
        title = s["title"] or s["ai_title"] or clip(s["prompts"][0][1] if s["prompts"] else "", 80)
        first = s["prompts"][0][1] if s["prompts"] else ""
        last = s["prompts"][-1][1] if s["prompts"] else (s["last_prompt"] or "")
        plist = "".join(f"<li><span class='muted'>{fmt(t)}</span> {e(clip(p, 400))}</li>" for t, p in s["prompts"])
        proj = (s["cwd"] or "").replace("/home/ubuntu/", "~/")
        q = " ".join([title, first, last, proj, " ".join(s["keys"]), " ".join(s["branches"]), (lv or {}).get("name") or ""]).lower()
        rows.append(f"""<tr id="s-{s['id']}" data-q="{e(q)}" data-live="{1 if st else 0}" data-skills="{e(' '.join(sorted(s['skills'])))}">
<td>{('<span class="badge %s">%s</span>' % (e(st), e(st))) if st else ''}</td>
<td class="nowrap">{fmt(s['end'])}<br><span class="muted">{ago(s['end'])}</span></td>
<td><b>{e(title)}</b><br><span class="muted">{e(proj)} · {e(', '.join(list(s['branches'])[-3:]))}</span>
<details><summary>{len(s['prompts'])} promptów · ostatni: {e(clip(last, 140))}</summary><ol>{plist}</ol>
<code>claude --resume {s['id']}</code></details></td>
<td>{' '.join('<span class="key">%s</span>' % e(k) for k, _ in s['keys'].most_common(4))}
{' '.join('<span class="skill">%s</span>' % e(k) for k in sorted(s['skills']))}</td></tr>""")

    page = f"""<!doctype html><html lang="pl"><head><meta charset="utf-8"><title>Claude sessions</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
:root{{--bg:#f7f7f5;--fg:#1d1d1b;--mut:#77756f;--card:#fff;--bd:#e3e1db;--acc:#c96442;--busy:#d08700;--idle:#2e8b57}}
@media(prefers-color-scheme:dark){{:root{{--bg:#1c1b19;--fg:#ecebe6;--mut:#9a978f;--card:#262522;--bd:#3a3834}}}}
body{{font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:20px 28px}}
h1{{margin:0 0 4px}} h2{{margin:28px 0 10px;font-size:17px}} h3{{margin:6px 0;font-size:15px}}
.muted{{color:var(--mut);font-size:12px}} code{{font-size:11px;background:var(--bd);padding:2px 5px;border-radius:4px;user-select:all}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}}
.card,.ticket{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px}}
.card.busy{{border-left:4px solid var(--busy)}} .card.idle{{border-left:4px solid var(--idle)}}
.top{{display:flex;gap:8px;align-items:center;justify-content:space-between}} .name{{font-weight:600;flex:1}}
.badge{{font-size:11px;padding:1px 7px;border-radius:9px;background:var(--bd)}} .badge.busy{{background:var(--busy);color:#fff}} .badge.idle{{background:var(--idle);color:#fff}}
.skill{{display:inline-block;font-size:11px;border:1px solid var(--acc);color:var(--acc);border-radius:4px;padding:0 5px;margin:1px}}
.last{{font-size:13px;margin:6px 0}} .key{{display:inline-block;font-size:11px;background:var(--acc);color:#fff;border-radius:4px;padding:0 5px;margin:1px}}
table{{width:100%;border-collapse:collapse;background:var(--card)}} td{{border-top:1px solid var(--bd);padding:8px;vertical-align:top}}
.nowrap{{white-space:nowrap}} details summary{{cursor:pointer;color:var(--mut);font-size:12px}} ol{{font-size:12px;max-height:320px;overflow:auto}}
pre{{white-space:pre-wrap;font-size:12px;max-height:300px;overflow:auto}} ul{{margin:6px 0;padding-left:18px;font-size:13px}}
select{{font-size:14px;padding:6px;border:1px solid var(--bd);border-radius:6px;background:var(--card);color:var(--fg)}}
input{{font-size:14px;padding:6px 10px;width:340px;border:1px solid var(--bd);border-radius:6px;background:var(--card);color:var(--fg)}}
a{{color:var(--acc)}} li{{margin:4px 0}} li.main code{{background:var(--acc);color:#fff}} tr:target{{outline:2px solid var(--acc)}}
</style></head><body>
<h1>Claude Code — sesje</h1><div class="muted">wygenerowano {fmt(time.time())} · {len(sessions)} sesji · {len(running)} uruchomionych</div>
<h2>Teraz uruchomione ({len(running)})</h2><div class="grid">{''.join(cards) or '<span class="muted">brak</span>'}</div>
<h2>Praca z pamięci ({len(cards_mem)})</h2><input id="tq" placeholder="filtr…" oninput="f('.ticket',this.value)"><p></p><div class="grid">{''.join(cards_mem)}</div>
<h2>Wszystkie sesje</h2><input id="q" placeholder="szukaj: ticket, branch, tekst promptu…" oninput="fs()">
<select id="sk" onchange="fs()"><option value="">wszystkie skille</option>{''.join('<option value="%s">%s (%d)</option>' % (e(k), e(k), n) for k, n in sorted(skill_count.items()))}</select>
<label class="muted"><input id="lo" type="checkbox" style="width:auto" onchange="fs()"> tylko uruchomione</label>
<p></p><table><tbody>{''.join(rows)}</tbody></table>
<script>{AUTO if live_reload else ''}function fs(){{const v=q.value.toLowerCase(),k=sk.value,l=lo.checked;document.querySelectorAll('tbody tr').forEach(r=>r.style.display=(r.dataset.q||'').includes(v)&&(!k||r.dataset.skills.split(' ').includes(k))&&!(l&&r.dataset.live=='0')?'':'none')}}function f(sel,v){{v=v.toLowerCase();document.querySelectorAll(sel).forEach(r=>r.style.display=(r.dataset.q||'').includes(v)?'':'none')}}</script>
</body></html>"""
    stats = "sessions=%d running=%d memory=%d linked=%d" % (len(sessions), len(running), len(cards_mem), sum(os.path.basename(m["file"]) in touched for m in mems))
    return page, stats


# serve mode: reload every 30s unless user is searching or has something expanded
AUTO = ("setInterval(()=>{if(document.hidden||[...document.querySelectorAll('input:not([type=checkbox]),select')].some(i=>i.value)||lo.checked"
        "||document.querySelector('details[open]'))return;location.reload()},30000);")


def serve(host, port):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] not in ("/", "/index.html"):
                self.send_error(404)
                return
            body = render(live_reload=True)[0].encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    print("serving http://%s:%d" % (host, port), flush=True)
    ThreadingHTTPServer((host, port), H).serve_forever()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=DEFAULT_OUT)
    ap.add_argument("--serve", action="store_true", help="run HTTP server, page regenerated on every request")
    ap.add_argument("--host", default=os.environ.get("DASH_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("DASH_PORT", "8765")))
    a = ap.parse_args()
    if a.serve:
        serve(a.host, a.port)
        return
    page, stats = render()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(page)
    print(a.out)
    print(stats)


if __name__ == "__main__":
    main()
