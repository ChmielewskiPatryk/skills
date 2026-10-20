#!/usr/bin/env python3
"""Generate the Claude Code sessions dashboard (~/.claude/projects transcripts) as an Artifact page."""
import glob, html, json, os, re, sys, time
from collections import Counter, defaultdict
from datetime import datetime

CLAUDE = os.path.expanduser("~/.claude")
DEFAULT_OUT = os.path.join(CLAUDE, "dashboard", "index.html")
URL_FILE = os.path.join(CLAUDE, "dashboard", "artifact_url")  # URL of the published artifact, reused on every run
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
CMD_RE = re.compile(r"<command-name>/?([^<]+)</command-name>.*?<command-args>(.*?)</command-args>", re.S)
SKILL_RE = re.compile(r"Base directory for this skill: \S*/skills/([\w.-]+)")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
# artifacts of the feasibility -> plan -> implementation flow
ART_RE = re.compile(r"/(ANALIZA_WYKONALNOSCI|IMPLEMENTATION_PLAN)/(\.analiza/)?([^/]+)$")
ART_REF_RE = re.compile(r"(ANALIZA_WYKONALNOSCI|IMPLEMENTATION_PLAN)/([\w.-]+?\.(?:md|MD|html))(?![\w/])")
TASK_KEY_RE = re.compile(r"(KRYPTO|KWDT|KWD|SME)-(\d+(?:-\d+)*)(?!\d)")
STAGES = [("feas", "🔍 Wykonalność"), ("plan", "📋 Plan"), ("impl", "🛠 Implementacja"),
          ("review", "🔎 Review"), ("smoke", "🧪 Smoke test"), ("retro", "🔁 Retro")]
SKILL_STAGE = {"analyzing-confluence-feasibility": "feas", "explaining-confluence-analysis": "feas",
               "planning-jira-implementation": "plan", "reviewing-java-commits": "review",
               "smoke-testing-locally": "smoke", "running-task-retro": "retro"}
HOST_RE = re.compile(r"https?://[\w.-]*(jira|confluence)[\w.-]*")
HOSTS = {"jira": os.environ.get("JIRA_URL"), "confluence": os.environ.get("CONFLUENCE_URL")}  # else first seen in prompts


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
         "branches": Counter(), "cwd": None, "start": None, "end": None, "keys": Counter(), "assistant": 0, "mem": {}, "skills": set(),
         "writes": {}, "refs": Counter(), "page": None}
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
            s["cwd0"] = s.get("cwd0") or o["cwd"]  # session start dir; "cwd" drifts with cd
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
                    n, inp = b.get("name") or "", b.get("input") or {}
                    if n == "Skill" and inp.get("skill"):
                        s["skills"].add(inp["skill"].split(":")[-1])
                    if n in WRITE_TOOLS and (inp.get("file_path") or inp.get("notebook_path")):
                        s["writes"][inp.get("file_path") or inp.get("notebook_path")] = s["end"]
                    if n.endswith("confluence_get_page") and inp.get("page_id") and not s["page"]:
                        s["page"] = str(inp["page_id"])
                    for m in ART_REF_RE.findall(json.dumps(inp, ensure_ascii=False)):
                        s["refs"][m] += 1
                    for f, kind in mem_touches(b.get("name"), b.get("input") or {}):
                        prev = s["mem"].get(f)
                        if not prev or kind == "write":
                            s["mem"][f] = (kind, s["end"])
        if t == "user" and not o.get("isMeta") and "toolUseResult" not in o:
            txt = user_text(o.get("message") or {}).strip()
            cmd = CMD_RE.search(txt)
            if cmd and (":" in cmd.group(1) or cmd.group(2).strip()):  # slash command / skill with args
                txt = ("/%s %s" % (cmd.group(1).strip(), cmd.group(2).strip())).strip()
            if txt and not NOISE_RE.match(txt):
                s["prompts"].append((s["end"], txt))
                for m in KEY_RE.finditer(txt):
                    s["keys"][m.group(0)] += 1
                for m in ART_REF_RE.findall(txt):
                    s["refs"][m] += 1
                for m in HOST_RE.finditer(txt):
                    HOSTS[m.group(1)] = HOSTS[m.group(1)] or m.group(0)
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


def art_nodes(name):
    keys = ["k:%s-%s" % (p, n) for p, ns in TASK_KEY_RE.findall(name) for n in ns.split("-")]
    if keys:
        return keys
    stem = re.sub(r"^IMPLEMENTATION_PLAN_|_?IMPLEMENTATION_PLAN$|-analiza$", "", os.path.splitext(name)[0], flags=re.I)
    return ["n:" + stem.upper()]


def first_h1(path):
    try:
        for line in open(path, errors="replace"):
            if line.startswith("# "):
                return re.split(r"\s[–—-]\s|:\s", line[2:].strip(), maxsplit=1)[-1]
    except Exception:
        pass
    return None


def tasks(sessions):
    """Group sessions into tasks: feasibility -> plan -> implementation (-> review/smoke/retro).

    Links: Jira keys in artifact file names, the main Confluence page of a skill session,
    artifact files referenced by later sessions, the session's dominant Jira key."""
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(nodes):
        for a in nodes[1:]:
            par[find(a)] = find(nodes[0])

    by_name, orphans = {}, {}
    for s in sessions:
        s["arts"] = []
        for path, t in s["writes"].items():
            m = ART_RE.search(path)
            if m:
                kind = "feas" if m.group(1) == "ANALIZA_WYKONALNOSCI" else "plan"
                s["arts"].append((path, kind, bool(m.group(2)), art_nodes(m.group(3)), t))
                by_name.setdefault(m.group(3), (kind, art_nodes(m.group(3)), path))
        nodes = [n for a in s["arts"] for n in a[3]]
        flow = {SKILL_STAGE.get(k) for k in s["skills"]} & {"feas", "plan"}
        if nodes and s["page"] and flow:
            nodes.append("p:" + s["page"])
        if nodes:
            union(nodes)
    # artifacts referenced on disk but written outside the transcripts (e.g. deleted sessions)
    for s in sessions:
        for d, name in s["refs"]:
            path = os.path.join(s.get("cwd0") or "/", d, name)
            if name not in by_name and os.path.isfile(path):
                kind = "feas" if d == "ANALIZA_WYKONALNOSCI" else "plan"
                by_name[name] = (kind, art_nodes(name), path)
                orphans[path] = (kind, art_nodes(name))
                union(art_nodes(name))

    groups = defaultdict(lambda: {"stages": defaultdict(list), "files": defaultdict(dict), "nodes": set(), "sessions": set()})
    for s in sessions:
        roots = {find(n) for a in s["arts"] for n in a[3]}
        if not roots:
            # only artifacts of the repo the session works in (not e.g. skill development sessions)
            refs = sorted(((by_name[r][0] == "plan", c), r) for (_, r), c in s["refs"].items()
                          if r in by_name and s.get("cwd0") and by_name[r][2].startswith(s["cwd0"].rstrip("/") + "/"))
            key = s["keys"].most_common(1)
            if s["page"] and "p:" + s["page"] in par and set(SKILL_STAGE.get(k) for k in s["skills"]) & {"feas", "plan"}:
                roots = {find("p:" + s["page"])}
            elif refs:
                roots = {find(by_name[refs[-1][1]][1][0])}
            elif key and key[0][1] >= 2 and "k:" + key[0][0] in par:
                roots = {find("k:" + key[0][0])}
        for r in roots:
            g = groups[r]
            kinds = {a[1] for a in s["arts"] if find(a[3][0]) == r}
            kinds |= {SKILL_STAGE[k] for k in s["skills"] if k in SKILL_STAGE and not kinds}
            if any(not ART_RE.search(f) and not re.search(r"/memory/|/\.claude/|^/tmp/", f) for f in s["writes"]):
                kinds.add("impl")
            for k in kinds or {"impl"}:
                g["stages"][k].append(s)
                if k in ("feas", "plan"):
                    for path, kind, cache, nodes, t in s["arts"]:
                        if kind == k and find(nodes[0]) == r:
                            g["files"][k][path] = (cache, t)
            g["sessions"].add(s["id"])
            s.setdefault("tasks", []).append(r)
    for x in list(par):
        if find(x) in groups:
            groups[find(x)]["nodes"].add(x)
    for path, (kind, nodes) in orphans.items():
        if find(nodes[0]) in groups:
            groups[find(nodes[0])]["files"][kind].setdefault(path, (False, os.path.getmtime(path)))
    out = []
    for r, g in groups.items():
        keys = sorted(n[2:] for n in g["nodes"] if n[0] in "kn")
        g["label"] = " · ".join(keys) or r[2:]
        g["id"] = "t-" + re.sub(r"[^\w-]", "_", keys[0] if keys else r)
        g["page"] = next((n[2:] for n in g["nodes"] if n[0] == "p"), None)
        g["end"] = max(s["end"] or 0 for st in g["stages"].values() for s in st)
        title = None
        for k in ("feas", "plan"):
            for path, (cache, t) in sorted(g["files"][k].items(), key=lambda kv: -(kv[1][1] or 0)):
                if not cache and not title:
                    title = first_h1(path)
        g["title"] = title or next((x["title"] or x["ai_title"] for k in ("feas", "plan") for x in g["stages"][k]
                                    if x["title"] or x["ai_title"]), None)
        out.append(g)
    out.sort(key=lambda g: -g["end"])
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


def home(p):
    return (p or "").replace("/home/ubuntu/", "~/").replace("/root/", "~root/")


def stitle(x, n=60):
    return x["title"] or x["ai_title"] or clip(x["prompts"][0][1] if x["prompts"] else "", n)


def file_line(path, note=""):
    name, d = os.path.basename(path), os.path.dirname(path) + "/"
    ok = os.path.exists(path)
    nm = e(name)
    gone = "" if ok else ' <span class="gone">usunięty</span>'
    mt = f' · {ago(os.path.getmtime(path))}' if ok else ""
    return f"""<div class="file">📄 <b>{nm}</b>{gone}<span class="muted">{e(note)}{mt}</span><br><code title="{e(path)}">{e(home(d))}</code></div>"""


def render_tasks(groups):
    out = []
    for g in groups:
        alive = [x for st in g["stages"].values() for x in st if x["live"] and x["live"]["alive"]]
        cols = []
        for k, label in STAGES:
            ss = sorted({x["id"]: x for x in g["stages"][k]}.values(), key=lambda x: x["end"] or 0)
            if not ss and k not in ("feas", "plan", "impl"):
                continue
            files = [file_line(f, " kopia analizy" if c else "") for f, (c, t) in
                     sorted(g["files"][k].items(), key=lambda kv: (kv[1][0], -(kv[1][1] or 0)))]
            items = []
            for x in ss:
                lv = x["live"] if x["live"] and x["live"]["alive"] else None
                badge = '<span class="badge %s">%s</span> ' % (e(lv["status"]), e(lv["status"])) if lv else ""
                extra = ""
                if k == "impl":
                    code = sorted(f for f in x["writes"] if not ART_RE.search(f) and not re.search(r"/memory/|/\.claude/|^/tmp/", f))
                    if code:
                        extra = f"<details><summary>{len(code)} zmienionych plików</summary><ol>{''.join('<li><code>%s</code></li>' % e(home(f)) for f in code)}</ol></details>"
                mem = [f for f in x["writes"] if "/memory/project_" in f]
                extra += "".join(f"<div class='muted'>🧠 {e(os.path.basename(f))}</div>" for f in mem)
                items.append(f"""<li>{badge}<a href="#s-{x['id']}">{e(stitle(x, 50))}</a> <span class="muted">{fmt(x['end'])}</span>
<br><code>claude --resume {x['id']}</code>{extra}</li>""")
            body = "".join(files) + (f"<ul>{''.join(items)}</ul>" if items else "")
            cols.append(f"""<div class="stage {'done' if ss or files else 'todo'}"><div class="sh">{label}</div>{body or '<span class="muted">—</span>'}</div>""")
        cf, jr = (HOSTS[k] and HOSTS[k].rstrip("/") for k in ("confluence", "jira"))
        page = (f' · <a href="{e(cf)}/pages/viewpage.action?pageId={g["page"]}" target="_blank">Confluence</a>'
                if g["page"] and cf else "")
        jira = " ".join(f'<a class="key" href="{e(jr)}/browse/{e(n[2:])}" target="_blank">{e(n[2:])}</a>' if n[0] == "k" and jr
                        else f'<span class="key">{e(n[2:])}</span>' for n in sorted(g["nodes"]) if n[0] in "kn")
        q = " ".join([g["label"], g["title"] or ""] + [stitle(x) for st in g["stages"].values() for x in st]
                     + [os.path.basename(f) for fs in g["files"].values() for f in fs]).lower()
        badge = ('<span class="badge %s">%s</span>' % (e(alive[0]["live"]["status"]), e(alive[0]["live"]["status"]))) if alive else ""
        out.append(f"""<div class="task" id="{g['id']}" data-q="{e(q)}"><div class="top"><span>{jira} {badge}</span>
<span class="muted">ostatnio {ago(g['end'])}{page}</span></div><h3>{e(g['title'] or g['label'])}</h3>
<div class="flow">{'<div class="arrow">→</div>'.join(cols)}</div></div>""")
    return "".join(out)


def render():
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
    groups = tasks(sessions)
    task_of = defaultdict(list)
    for g in groups:
        for sid in g["sessions"]:
            task_of[sid].append(g)

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
        q = " ".join([title, first, last, proj, " ".join(s["keys"]), " ".join(s["branches"]), (lv or {}).get("name") or ""]
                     + [g["label"] for g in task_of[s["id"]]]).lower()
        rows.append(f"""<tr id="s-{s['id']}" data-q="{e(q)}" data-live="{1 if st else 0}" data-skills="{e(' '.join(sorted(s['skills'])))}">
<td>{('<span class="badge %s">%s</span>' % (e(st), e(st))) if st else ''}</td>
<td class="nowrap">{fmt(s['end'])}<br><span class="muted">{ago(s['end'])}</span></td>
<td><b>{e(title)}</b><br><span class="muted">{e(proj)} · {e(', '.join(list(s['branches'])[-3:]))}</span>
<details><summary>{len(s['prompts'])} promptów · ostatni: {e(clip(last, 140))}</summary><ol>{plist}</ol>
<code>claude --resume {s['id']}</code></details></td>
<td>{' '.join('<span class="key">%s</span>' % e(k) for k, _ in s['keys'].most_common(4))}
{' '.join('<span class="skill">%s</span>' % e(k) for k in sorted(s['skills']))}
{' '.join('<a class="tchip" href="#%s">📁 %s</a>' % (g['id'], e(g['label'])) for g in task_of[s['id']])}</td></tr>""")

    page = f"""<title>Claude sessions</title><meta name="claude:viewport-fit-sides" content="cover"><style>
:root{{--bg:#f7f7f5;--fg:#1d1d1b;--mut:#77756f;--card:#fff;--bd:#e3e1db;--acc:#c96442;--busy:#d08700;--idle:#2e8b57;--on:#fff;--gone:#b33}}
@media(prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1c1b19;--fg:#ecebe6;--mut:#9a978f;--card:#262522;--bd:#3a3834;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#1c1b19;--fg:#ecebe6;--mut:#9a978f;--card:#262522;--bd:#3a3834;color-scheme:dark}}
body{{font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding-block:20px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
h1{{margin:0 0 4px}} h2{{margin:28px 0 10px;font-size:17px}} h3{{margin:6px 0;font-size:15px;text-wrap:balance}}
.muted{{color:var(--mut);font-size:12px}} code{{font-size:11px;background:var(--bd);padding:2px 5px;border-radius:4px;user-select:all;overflow-wrap:anywhere}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(330px,100%),1fr));gap:12px}}
.card,.ticket{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px;min-width:0}}
.card.busy{{border-left:4px solid var(--busy)}} .card.idle{{border-left:4px solid var(--idle)}}
.top{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}} .name{{font-weight:600;flex:1}}
.badge{{font-size:11px;padding:1px 7px;border-radius:9px;background:var(--bd)}} .badge.busy{{background:var(--busy);color:var(--on)}} .badge.idle{{background:var(--idle);color:var(--on)}}
.skill{{display:inline-block;font-size:11px;border:1px solid var(--acc);color:var(--acc);border-radius:4px;padding:0 5px;margin:1px}}
.last{{font-size:13px;margin:6px 0;overflow-wrap:anywhere}} .key{{display:inline-block;font-size:11px;background:var(--acc);color:var(--on);border-radius:4px;padding:0 5px;margin:1px}}
.tbl{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;background:var(--card)}} td{{border-top:1px solid var(--bd);padding:8px;vertical-align:top;overflow-wrap:anywhere}}
.nowrap{{white-space:nowrap;font-variant-numeric:tabular-nums}} details summary{{cursor:pointer;color:var(--mut);font-size:12px}} ol{{font-size:12px;max-height:320px;overflow:auto}}
pre{{white-space:pre-wrap;font-size:12px;max-height:300px;overflow:auto}} ul{{margin:6px 0;padding-left:18px;font-size:13px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}}
select{{font-size:14px;padding:6px;border:1px solid var(--bd);border-radius:6px;background:var(--card);color:var(--fg);max-width:100%}}
input{{font-size:14px;padding:6px 10px;width:340px;max-width:100%;box-sizing:border-box;border:1px solid var(--bd);border-radius:6px;background:var(--card);color:var(--fg)}}
input:focus-visible,select:focus-visible,summary:focus-visible,a:focus-visible{{outline:2px solid var(--acc);outline-offset:1px}}
.task{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px;margin-bottom:12px}} .task:target{{outline:2px solid var(--acc)}}
.flow{{display:flex;gap:6px;align-items:stretch;flex-wrap:wrap}} .arrow{{align-self:center;color:var(--mut);font-size:18px}}
.stage{{flex:1;min-width:min(230px,100%);border:1px solid var(--bd);border-radius:8px;padding:8px;font-size:13px}} .stage.todo{{border-style:dashed;opacity:.6}}
.stage.done{{border-top:3px solid var(--idle)}} .sh{{font-weight:600;margin-bottom:6px}} .file{{margin:4px 0}} .stage ul{{padding-left:16px}}
.gone{{font-size:11px;color:var(--on);background:var(--gone);border-radius:4px;padding:0 4px}} a.key{{text-decoration:none}}
.tchip{{display:inline-block;font-size:11px;border:1px solid var(--idle);color:var(--idle);border-radius:4px;padding:0 5px;margin:1px;text-decoration:none}}
a{{color:var(--acc)}} li{{margin:4px 0}} li.main code{{background:var(--acc);color:var(--on)}} tr:target{{outline:2px solid var(--acc)}}
</style>
<h1>Claude Code — sesje</h1><div class="muted">wygenerowano {fmt(time.time())} · {len(sessions)} sesji · {len(running)} uruchomionych</div>
<h2>Teraz uruchomione ({len(running)})</h2><div class="grid">{''.join(cards) or '<span class="muted">brak</span>'}</div>
<h2>Zadania: wykonalność → plan → implementacja ({len(groups)})</h2><div class="bar"><input id="taq" placeholder="filtr zadań: klucz, tytuł, plik…" oninput="f('.task',this.value)"></div>
{render_tasks(groups) or '<span class="muted">brak</span>'}
<h2>Praca z pamięci ({len(cards_mem)})</h2><div class="bar"><input id="tq" placeholder="filtr…" oninput="f('.ticket',this.value)"></div><div class="grid">{''.join(cards_mem)}</div>
<h2>Wszystkie sesje</h2><div class="bar"><input id="q" placeholder="szukaj: ticket, branch, tekst promptu…" oninput="fs()">
<select id="sk" onchange="fs()"><option value="">wszystkie skille</option>{''.join('<option value="%s">%s (%d)</option>' % (e(k), e(k), n) for k, n in sorted(skill_count.items()))}</select>
<label class="muted"><input id="lo" type="checkbox" style="width:auto" onchange="fs()"> tylko uruchomione</label></div>
<div class="tbl"><table><tbody>{''.join(rows)}</tbody></table></div>
<script>function fs(){{const v=q.value.toLowerCase(),k=sk.value,l=lo.checked;document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!((r.dataset.q||'').includes(v)&&(!k||r.dataset.skills.split(' ').includes(k))&&!(l&&r.dataset.live=='0')))}}function f(sel,v){{v=v.toLowerCase();document.querySelectorAll(sel).forEach(r=>r.hidden=!(r.dataset.q||'').includes(v))}}</script>"""
    stats = "tasks=%d sessions=%d running=%d memory=%d linked=%d" % (len(groups), len(sessions), len(running), len(cards_mem), sum(os.path.basename(m["file"]) in touched for m in mems))
    return page, stats


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=DEFAULT_OUT)
    a = ap.parse_args()
    page, stats = render()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(page)
    print(a.out)
    print(stats)
    print("artifact_url=" + (open(URL_FILE).read().strip() if os.path.isfile(URL_FILE) else ""))


if __name__ == "__main__":
    main()
