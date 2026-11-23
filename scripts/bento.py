#!/usr/bin/env python3
"""Renders the bento-grid profile card (dark + light) as self-contained animated SVGs.

Standard library only, so it runs on a plain GitHub Actions runner.
  python3 scripts/bento.py            # live data (needs GH_TOKEN for the contribution calendar)
  python3 scripts/bento.py --demo     # sample contribution data, no network
"""
import base64
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
ICONS = json.loads((ROOT / "scripts" / "icons.json").read_text(encoding="utf-8"))
METRICS = json.loads((ROOT / "fonts" / "metrics.json").read_text(encoding="utf-8"))
DEMO = "--demo" in sys.argv

FONT_FILES = {"Inter": [(400, "inter-Regular.woff2"), (600, "inter-SemiBold.woff2"), (800, "inter-ExtraBold.woff2")],
              "JB": [(400, "jbmono-400.woff2"), (500, "jbmono-500.woff2")]}


# Colors are picked from the background photo (a sunset over wet sand), not from a generic palette.
# "tile" is the approximate color a glass tile ends up as, used only for icon-contrast checks.
THEMES = {
    "dark": dict(veil="#0d0a0c", veil_op=0.3, glass="#120c0e", glass_op=0.5, edge="#ffffff", edge_op=0.14,
                 tile="#2a1d1f", text="#fff6ef", muted="#dccbc1", faint="#a99189", a1="#ff9a6b", a2="#ffd38a",
                 good="#7ee0a1", node="#ffffff", node_op=0.07,
                 heat=["#2c2124", "#6e3b33", "#b65a3d", "#f08c5c", "#ffd38a"]),
    "light": dict(veil="#fff8f3", veil_op=0.4, glass="#ffffff", glass_op=0.6, edge="#ffffff", edge_op=0.9,
                  tile="#f7efe9", text="#2b1d17", muted="#5f4a40", faint="#937d72", a1="#c4532a", a2="#a7671a",
                  good="#1f8a4c", node="#ffffff", node_op=0.6,
                  heat=["#eee2da", "#f5c6a6", "#ec9a6b", "#d1673b", "#9b3e1b"]),
}

W, PAD, GAP = 1000, 20, 16
SNAKE_START, SNAKE_STEP, SNAKE_HOLD, SNAKE_LEN = 1.6, 0.045, 3.0, 6  # seconds, seconds per cell, pause, segments
INNER = W - PAD * 2

# ------------------------------------------------------------------ text helpers
def tw(text, font, size):
    m = METRICS[font]
    adv = m["adv"]
    return sum(adv.get(ch, m["upm"] * 0.55) for ch in text) * size / m["upm"]


def wrap(text, font, size, width):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if tw(cand, font, size) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def T(x, y, s, size, fill, font="Inter", weight=400, anchor="start", ls=0, extra=""):
    fam = "'Inter', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" if font == "Inter" else \
          "'JB', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    lsp = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{lsp}{extra}>{escape(s)}</text>')


def mkey(font, weight):
    if font == "Inter":
        return {400: "inter-400", 600: "inter-600", 800: "inter-800"}[weight]
    return {400: "mono-400", 500: "mono-500"}[weight]


def paragraph(x, y, text, size, fill, width, lh=1.45, weight=400, font="Inter"):
    lines = wrap(text, mkey(font, weight), size, width)
    return "".join(T(x, y + i * size * lh, ln, size, fill, font, weight) for i, ln in enumerate(lines)), len(lines)


def icon(name, x, y, size, color):
    ic = ICONS[name]
    s = size / 24
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.4f})"><path d="{ic["path"]}" fill="{color}"/></g>'


def rel_lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def brand(name, t):
    color = "#" + ICONS[name]["hex"]
    lum, bg = rel_lum(color), rel_lum(t["tile"])
    contrast = (max(lum, bg) + 0.05) / (min(lum, bg) + 0.05)
    if contrast >= 2.6:
        return color
    return t["text"]


# ------------------------------------------------------------------ data
def gql(query, variables, token):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                                          "User-Agent": "bento-profile"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def load_calendar():
    if DEMO or not os.environ.get("GH_TOKEN"):
        rnd = random.Random(7)
        today = dt.date(2026, 11, 22)
        start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
        days = []
        d = start
        while d <= today:
            base = 0.62 if d.weekday() < 5 else 0.3
            ramp = 0.6 + 0.4 * ((d - start).days / 371)
            n = 0 if rnd.random() > base * ramp else int(rnd.expovariate(1 / 7)) + 1
            days.append((d, n))
            d += dt.timedelta(days=1)
        mx = max(n for _, n in days)
        cal = [(d, n, 0 if n == 0 else min(4, 1 + int(3 * n / mx * 1.6))) for d, n in days]
        return cal
    q = """query($login:String!){ user(login:$login){ contributionsCollection{ contributionCalendar{
           totalContributions weeks{ contributionDays{ date contributionCount contributionLevel } } } } } }"""
    data = gql(q, {"login": CFG["username"]}, os.environ["GH_TOKEN"])
    weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(dt.date.fromisoformat(d["date"]), d["contributionCount"], LEVELS[d["contributionLevel"]])
            for w_ in weeks for d in w_["contributionDays"]]


def streaks(cal):
    counts = [n for _, n in [(d, n) for d, n, _ in cal]]
    longest = cur = 0
    for n in counts:
        cur = cur + 1 if n > 0 else 0
        longest = max(longest, cur)
    current = 0
    for i, n in enumerate(reversed(counts)):
        if n > 0:
            current += 1
        elif i == 0:
            continue  # today may still be empty
        else:
            break
    return current, longest


def load_avatar():
    for ext, mime in (("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png")):
        p = ROOT / "assets" / f"avatar.{ext}"
        if p.exists():
            return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    if DEMO:
        return None
    try:
        req = urllib.request.Request(f"https://github.com/{CFG['username']}.png?size=240",
                                     headers={"User-Agent": "bento-profile"})
        with urllib.request.urlopen(req, timeout=20) as r:
            mime = r.headers.get_content_type()
            return f"data:{mime};base64," + base64.b64encode(r.read()).decode()
    except Exception as e:  # keep the card rendering even if the avatar fails
        print("avatar fetch failed:", e, file=sys.stderr)
        return None



def asset_uri(name):
    p = ROOT / "assets" / name
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "svg": "image/svg+xml"}[p.suffix[1:]]
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "bento-profile", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read(), r.headers.get_content_type()


def load_spotify():
    """Track playing now, else the last one played. None when not configured or on any error."""
    keys = [os.environ.get(k) for k in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN")]
    if DEMO or not all(keys):
        return None
    cid, secret, refresh = keys
    try:
        basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
        _, body, _ = http("https://accounts.spotify.com/api/token",
                          urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": refresh}).encode(),
                          {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"})
        auth = {"Authorization": "Bearer " + json.loads(body)["access_token"]}
        status, body, _ = http("https://api.spotify.com/v1/me/player/currently-playing", headers=auth)
        cur = json.loads(body) if status == 200 and body else {}
        now = bool(cur.get("is_playing")) and (cur.get("item") or {}).get("type") == "track"
        if now:
            track = cur["item"]
        else:
            _, body, _ = http("https://api.spotify.com/v1/me/player/recently-played?limit=1", headers=auth)
            items = json.loads(body).get("items") or []
            if not items:
                return None
            track = items[0]["track"]
        imgs = sorted(track["album"]["images"], key=lambda i: i.get("width") or 0)
        pick = next((i for i in imgs if (i.get("width") or 0) >= 200), imgs[-1])
        _, raw, mime = http(pick["url"])
        return {"now": now, "title": track["name"], "artist": ", ".join(a["name"] for a in track["artists"]),
                "art": f"data:{mime};base64," + base64.b64encode(raw).decode()}
    except Exception as e:  # music is a nice-to-have; never break the card for it
        print("spotify failed:", e, file=sys.stderr)
        return None


def typing(x, y, phrases, size, t, slot=4.0, type_s=0.06, del_s=0.03):
    """Terminal-style line that types each phrase, holds it, deletes it, then moves to the next one."""
    cw = tw("a", "mono-400", size)
    dur = slot * len(phrases)
    out = ""
    for i, ph in enumerate(phrases):
        n = len(ph)
        hold = slot - n * (type_s + del_s) - 0.3
        assert hold > 0.4, f"phrase too long for its slot: {ph}"
        frames = [(k * type_s, k) for k in range(n + 1)]
        frames += [(n * type_s + hold + j * del_s, n - j) for j in range(1, n + 1)]
        kt = ";".join(f"{tm / dur:.4f}" for tm, _ in frames) + ";1"
        widths = ";".join(f"{k * cw:.1f}" for _, k in frames) + ";0"
        xs = ";".join(f"{x + k * cw + 1:.1f}" for _, k in frames) + f";{x + 1:.1f}"
        anim = f'calcMode="discrete" dur="{dur}s" begin="{i * slot}s" repeatCount="indefinite"'
        out += (f'<clipPath id="ty{i}"><rect x="{x}" y="{y - size}" height="{size * 1.4}" width="0">'
                f'<animate attributeName="width" values="{widths}" keyTimes="{kt}" {anim}/></rect></clipPath>'
                + T(x, y, ph, size, t["text"], "JB", 400, extra=f' clip-path="url(#ty{i})"')
                + f'<rect x="{x + 1}" y="{y - size * 0.82:.1f}" width="{cw * 0.55:.1f}" height="{size * 1.05:.1f}" '
                  f'fill="{t["a1"]}" opacity="0"><animate attributeName="x" values="{xs}" keyTimes="{kt}" {anim}/>'
                  f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.0001;{slot / dur:.4f}" {anim}/>'
                  f'</rect>')
    return out


def truncate(text, font, size, width):
    if tw(text, font, size) <= width:
        return text
    while text and tw(text + "…", font, size) > width:
        text = text[:-1]
    return text.rstrip() + "…"


# ------------------------------------------------------------------ building blocks
def tile(x, y, w, h, t, idx, inner=""):
    # each tile shows its own slice of the photo (same global position), so pieces line up when stacked
    return (f'<g class="tile" style="animation-delay:{0.06 * idx:.2f}s">'
            f'<clipPath id="tc{idx}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22"/></clipPath>'
            f'<g clip-path="url(#tc{idx})"><use href="#bgimg"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{t["veil"]}" fill-opacity="{t["veil_op"]}"/></g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{t["glass"]}" fill-opacity="{t["glass_op"]}"'
            f' stroke="{t["edge"]}" stroke-opacity="{t["edge_op"]}"/>{inner}</g>')


def head(x, y, w, t, title, tag, icon_uri=None):
    out, tx = "", x
    if icon_uri:
        out += f'<image href="{icon_uri}" x="{x}" y="{y - 26}" width="34" height="34"/>'
        tx = x + 46
    out += T(tx, y, title, 22, t["text"], "Inter", 800, ls=-0.4)
    out += T(x + w, y - 3, tag, 12, t["faint"], "Inter", 400, "end")
    return out


def shot(x, y, w, h, t, uri, cid):
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/></clipPath>'
            f'<image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h}" clip-path="url(#{cid})" '
            f'preserveAspectRatio="xMinYMin slice"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" stroke="{t["edge"]}" '
            f'stroke-opacity="{t["edge_op"] * 1.4:.2f}"/>')


def css(ncols):
    fonts = []
    for fam, items in FONT_FILES.items():
        for weight, fn in items:
            b64 = base64.b64encode((ROOT / "fonts" / fn).read_bytes()).decode()
            fonts.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:normal;"
                         f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    cols = "".join(f".c{i}{{animation-delay:{0.45 + i * 0.018:.3f}s}}" for i in range(ncols))
    return ("<style>" + "".join(fonts) +
            ".tile{animation:up .8s cubic-bezier(.2,.8,.2,1) both}"
            "@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}"
            ".cell{animation:pop .5s ease-out both}"
            "@keyframes pop{from{opacity:0}to{opacity:1}}" + cols +
            ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 1.8s ease-out infinite}"
            "@keyframes pulse{from{transform:scale(1);opacity:.8}to{transform:scale(3.2);opacity:0}}"
            ".vinyl{transform-box:fill-box;transform-origin:center;animation:spin 9s linear infinite}"
            "@keyframes spin{to{transform:rotate(360deg)}}"
            ".bg{animation:drift 40s ease-in-out infinite alternate}"
            "@keyframes drift{to{transform:scale(1.08) translate(-20px,10px)}}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            "</style>")


# ------------------------------------------------------------------ the card
def render(theme, cal, avatar, music, img):
    t = THEMES[theme]
    current, longest = streaks(cal)
    total = sum(n for _, n, _ in cal)
    best = max(cal, key=lambda r: r[1])
    weeks = []
    for d, n, lvl in cal:
        if not weeks or d.weekday() == 6:
            weeks.append([])
        weeks[-1].append((d, n, lvl))

    y_hero, h_hero = PAD, 214
    y_soc, h_soc = y_hero + h_hero + GAP, 64
    y_stats, h_stats = y_soc + h_soc + GAP, 116
    y_r3, h_r3 = y_stats + h_stats + GAP, 372
    y_r4, h_r4 = y_r3 + h_r3 + GAP, 372
    y_q, h_q = y_r4 + h_r4 + GAP, 60
    y_r5, h_r5 = y_q + len(CFG["questions"]) * (h_q + GAP), 106
    y_r6, h_r6 = y_r5 + h_r5 + GAP, 246
    H = y_r6 + h_r6 + PAD
    wl, wr = 548, INNER - 548 - GAP

    cx, cy = PAD + 100, y_hero + 107
    qkeys = [f"q{i}" for i in range(len(CFG["questions"]))]
    pieces = {k: [] for k in ["hero", "linkedin", "email", "stats", "pingo", "candidato", "soin", "creators",
                              *qkeys, "bottom"]}
    add = lambda k, svg: pieces[k].append(svg)

    # ---- hero
    if avatar:
        av = (f'<image href="{avatar}" x="{cx - 60}" y="{cy - 60}" width="120" height="120" clip-path="url(#av)" '
              f'preserveAspectRatio="xMidYMid slice"/>')
    else:
        initials = "".join(p[0] for p in CFG["name"].split()[:2]).upper()
        av = (f'<circle cx="{cx}" cy="{cy}" r="60" fill="{t["a1"]}"/>'
              + T(cx, cy + 14, initials, 38, "#ffffff", "Inter", 800, "middle"))
    av += (f'<circle cx="{cx}" cy="{cy}" r="60.5" fill="none" stroke="{t["edge"]}" '
           f'stroke-opacity="{min(1, t["edge_op"] * 3):.2f}" stroke-width="1.5"/>')
    hx = PAD + 194
    mw = W - PAD - 24 - 330 - hx - 20  # text column ends before the music card
    mono = "'JB', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    hero = (f'<text x="{hx}" y="{y_hero + 46}" font-family="{mono}" font-size="13" fill="{t["faint"]}">'
            f'<tspan fill="{t["good"]}">sammy@fortaleza</tspan>:<tspan fill="{t["a2"]}">~</tspan>$ whoami</text>')
    hero += T(hx - 2, y_hero + 94, CFG["name"], 44, t["text"], "Inter", 800, ls=-1.3)
    hero += T(hx, y_hero + 128, ">", 17, t["a1"], "JB", 500) + typing(hx + 18, y_hero + 128, CFG["typing"], 17, t)
    tag_svg, n_lines = paragraph(hx, y_hero + 162, CFG["tagline"], 15, t["muted"], mw, lh=1.4)
    hero += tag_svg

    mx_, my_, mw_, mh_ = W - PAD - 24 - 330, y_hero + 31, 330, 152
    card = (f'<rect x="{mx_}" y="{my_}" width="{mw_}" height="{mh_}" rx="18" fill="{t["node"]}" '
            f'fill-opacity="{t["node_op"]}" stroke="{t["edge"]}" stroke-opacity="{t["edge_op"]}"/>')
    tx = mx_ + 146
    tw_ = mw_ - 146 - 18
    if music:
        vx, vy, r = mx_ + 20 + 56, my_ + mh_ / 2, 56
        disc = (f'<clipPath id="art"><circle cx="{vx}" cy="{vy}" r="{r}"/></clipPath>'
                f'<g class="{"vinyl" if music["now"] else ""}">'
                f'<image href="{music["art"]}" x="{vx - r}" y="{vy - r}" width="{2 * r}" height="{2 * r}" '
                f'clip-path="url(#art)" preserveAspectRatio="xMidYMid slice"/>'
                f'<circle cx="{vx}" cy="{vy}" r="{r - 14}" fill="none" stroke="#000" stroke-opacity=".18"/>'
                f'<circle cx="{vx}" cy="{vy}" r="{r - 26}" fill="none" stroke="#000" stroke-opacity=".18"/></g>'
                f'<circle cx="{vx}" cy="{vy}" r="{r}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="2"/>'
                f'<circle cx="{vx}" cy="{vy}" r="7" fill="{t["glass"]}" stroke="#000" stroke-opacity=".3"/>')
        label = "listening now" if music["now"] else "last played"
        card += disc + icon("Spotify", tx, my_ + 30, 15, "#1DB954")
        card += T(tx + 22, my_ + 42, label, 12, t["muted"], "Inter", 400)
        lines = wrap(music["title"], "inter-800", 16, tw_)
        if len(lines) > 2:
            lines = [lines[0], truncate(" ".join(lines[1:]), "inter-800", 16, tw_)]
        for i, ln in enumerate(lines):
            card += T(tx, my_ + 74 + i * 21, truncate(ln, "inter-800", 16, tw_), 16, t["text"], "Inter", 800)
        card += T(tx, my_ + 74 + len(lines) * 21 + 4, truncate(music["artist"], "inter-400", 13, tw_), 13,
                  t["muted"], "Inter", 400)
    else:
        st = CFG["status"]
        card += (f'<circle class="pulse" cx="{mx_ + 26}" cy="{my_ + 32}" r="4.5" fill="{t["good"]}"/>'
                 f'<circle cx="{mx_ + 26}" cy="{my_ + 32}" r="4.5" fill="{t["good"]}"/>'
                 + T(mx_ + 40, my_ + 36, "right now", 12, t["muted"], "Inter", 400)
                 + T(mx_ + 22, my_ + 80, st["title"], 22, t["text"], "Inter", 800)
                 + T(mx_ + 22, my_ + 104, st["subtitle"], 13, t["muted"], "Inter", 400))
    add("hero", f'<clipPath id="av"><circle cx="{cx}" cy="{cy}" r="60"/></clipPath>')
    add("hero", tile(PAD, y_hero, INNER, h_hero, t, 0, av + hero + card))

    # ---- social links, each its own clickable piece
    hw = (INNER - GAP) / 2
    for j, (key, ic) in enumerate((("linkedin", "LinkedIn"), ("email", "Gmail"))):
        c = CFG["social"][key]
        x = PAD + j * (hw + GAP)
        inner = icon(ic, x + 24, y_soc + h_soc / 2 - 12, 24, brand(ic, t))
        inner += T(x + 62, y_soc + 39, c["label"], 17, t["text"], "Inter", 800)
        inner += T(x + 62 + tw(c["label"], "inter-800", 17) + 12, y_soc + 38, c["handle"], 14, t["muted"], "Inter", 400)
        inner += T(x + hw - 24, y_soc + 39, "↗", 16, t["a1"], "Inter", 600, "end")
        add(key, tile(round(x, 1), y_soc, round(hw, 1), h_soc, t, 11 + j, inner))

    # ---- stats
    sw_ = (INNER - GAP * 3) / 4
    for i, s in enumerate(CFG["stats"]):
        x = PAD + i * (sw_ + GAP)
        inner = T(x + 20, y_stats + 52, s["value"], 36, t["text"], "Inter", 800, ls=-1)
        para, _ = paragraph(x + 22, y_stats + 78, s["label"], 12.5, t["muted"], sw_ - 40, lh=1.4)
        add("stats", tile(round(x, 1), y_stats, round(sw_, 1), h_stats, t, 1 + i, inner + para))

    # ---- products with real screenshots
    for j, (key, x, w, yy) in enumerate((("pingo", PAD, wl, y_r3), ("candidato", PAD + wl + GAP, wr, y_r3),
                                          ("soin", PAD, wl, y_r4))):
        c = CFG[key]
        inner = head(x + 24, yy + 46, w - 48, t, c["title"], c["tag"], img.get(key + "_icon"))
        para, _ = paragraph(x + 24, yy + 82, c["text"], 13.5, t["muted"], w - 48, lh=1.45)
        sh_h = 196
        inner += para + shot(x + 24, yy + h_r3 - sh_h - 46, w - 48, sh_h, t, img[key + "_shot"], f"s{key}")
        link = c.get("url")
        inner += T(x + 24, yy + h_r3 - 20, c["footer"] + (" ↗" if link else ""), 12, t["a1"], "JB", 500)
        add(key, tile(x, yy, w, h_r3, t, 5 + j, inner))

    # ---- creator platform (client work, no public screenshot)
    c = CFG["creators"]
    x = PAD + wl + GAP
    inner = head(x + 24, y_r4 + 46, wr - 48, t, c["title"], c["tag"])
    para, _ = paragraph(x + 24, y_r4 + 82, c["text"], 13.5, t["muted"], wr - 48, lh=1.45)
    inner += para
    for i, (big, small) in enumerate(c["facts"]):
        fy = y_r4 + 186 + i * 58
        inner += T(x + 24, fy, big, 28, t["text"], "Inter", 800, ls=-0.6)
        inner += T(x + 26 + tw(big, "inter-800", 28) + 10, fy - 2, small, 13, t["muted"], "Inter", 400)
    inner += T(x + 24, y_r4 + h_r4 - 20, c["footer"], 12, t["a1"], "JB", 500)
    add("creators", tile(x, y_r4, wr, h_r4, t, 8, inner))

    # ---- question headers: the README wraps each one in <summary>, the answer is plain markdown below it
    for i, q in enumerate(CFG["questions"]):
        yy = y_q + i * (h_q + GAP)
        inner = T(PAD + 26, yy + 37, q, 17, t["text"], "Inter", 800, ls=-0.2)
        inner += T(W - PAD - 26, yy + 36, "click to open  +", 12, t["faint"], "Inter", 400, "end")
        add(f"q{i}", tile(PAD, yy, INNER, h_q, t, 13 + i, inner))

    # ---- stack, one row of real logos
    x, y = PAD, y_r5
    names = CFG["stack"]
    cw = (INNER - 40) / len(names)
    inner = ""
    for i, name in enumerate(names):
        ix = x + 20 + i * cw + cw / 2
        inner += (f'<rect x="{ix - 21:.1f}" y="{y + 20}" width="42" height="42" rx="12" fill="{t["node"]}" '
                  f'fill-opacity="{t["node_op"]}" stroke="{t["edge"]}" stroke-opacity="{t["edge_op"]}"/>')
        inner += icon(name, ix - 11, y + 30, 22, brand(name, t))
        label = name if tw(name, "inter-400", 10.5) < cw - 2 else name.split()[0]
        inner += T(ix, y + 84, label, 10.5, t["muted"], "Inter", 400, "middle")
    add("bottom", tile(x, y, INNER, h_r5, t, 9, inner))

    # ---- contributions
    x, y = PAD, y_r6
    inner = T(x + 26, y + 46, f"{total:,}", 30, t["text"], "Inter", 800, ls=-0.8)
    inner += T(x + 26 + tw(f"{total:,}", "inter-800", 30) + 10, y + 46, "contributions in the last year", 14,
               t["muted"], "Inter", 400)
    days = lambda n: f"{n} day" if n == 1 else f"{n} days"
    mini = [("current streak", days(current)), ("longest streak", days(longest)),
            ("best day", f"{best[1]} on {best[0].strftime('%b %-d')}")]
    mx = x + INNER - 26
    for label, val in reversed(mini):
        wv = max(tw(val, "inter-600", 14), tw(label, "inter-400", 11))
        inner += T(mx, y + 28, label, 11, t["faint"], "Inter", 400, "end")
        inner += T(mx, y + 48, val, 14, t["text"], "Inter", 600, "end")
        mx -= wv + 28
    cell, cg = 13.4, 3.6
    snake_dur = len(weeks) * 7 * SNAKE_STEP + SNAKE_HOLD
    gx =x + (INNER - (len(weeks) * (cell + cg) - cg)) / 2
    gy = y + 90
    month_seen = set()
    for wi, wk in enumerate(weeks):
        for d, n, lvl in wk:
            dy = (d.weekday() + 1) % 7
            if d.day <= 7 and d.month not in month_seen and dy == 0 and wi < len(weeks) - 1:
                month_seen.add(d.month)
                inner += T(gx + wi * (cell + cg), gy - 10, d.strftime("%b"), 10, t["faint"], "Inter", 400)
            # the snake walks the grid column by column (down, then up); a cell is eaten when the head reaches it
            k = wi * 7 + (dy if wi % 2 == 0 else 6 - dy)
            eat = (f'<animate attributeName="fill" values="{t["heat"][lvl]};{t["heat"][0]}" '
                   f'keyTimes="0;{k * SNAKE_STEP / snake_dur:.4f}" calcMode="discrete" dur="{snake_dur:.2f}s" '
                   f'begin="{SNAKE_START}s" repeatCount="indefinite"/>') if lvl else ""
            inner += (f'<rect class="cell c{wi}" x="{gx + wi * (cell + cg):.1f}" y="{gy + dy * (cell + cg):.1f}" '
                      f'width="{cell}" height="{cell}" rx="3.2" fill="{t["heat"][lvl]}">{eat}</rect>')
    step = cell + cg
    pts = [(gx + wi * step + cell / 2, gy + (r if wi % 2 == 0 else 6 - r) * step + cell / 2)
           for wi in range(len(weeks)) for r in range(7)]
    path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    fr = (len(pts) - 1) * SNAKE_STEP / snake_dur
    for i in range(SNAKE_LEN):
        sz = cell - 1.5 - i * 0.6
        color = t["a1"] if i == 0 else t["a2"]
        begin = f"{SNAKE_START + i * SNAKE_STEP:.3f}s"
        inner += (f'<rect x="{-sz / 2:.1f}" y="{-sz / 2:.1f}" width="{sz:.1f}" height="{sz:.1f}" rx="4" '
                  f'fill="{color}" opacity="0" fill-opacity="{1 - i * 0.12:.2f}">'
                  f'<animateMotion path="{path}" dur="{snake_dur:.2f}s" begin="{begin}" repeatCount="indefinite" '
                  f'keyPoints="0;1;1" keyTimes="0;{fr:.4f};1" calcMode="linear"/>'
                  f'<animate attributeName="opacity" values="1;0" keyTimes="0;{fr:.4f}" calcMode="discrete" '
                  f'dur="{snake_dur:.2f}s" begin="{begin}" repeatCount="indefinite"/></rect>')
    upd =dt.datetime.now(dt.timezone.utc).strftime("%b %-d, %Y") if not DEMO else "Nov 22, 2026"
    inner += T(x + 26, y + h_r6 - 16, f"updated {upd} · {CFG['background']['credit']}", 10.5, t["faint"],
               "Inter", 400)
    lx = x + INNER - 26
    for lvl in range(4, -1, -1):
        inner += f'<rect x="{lx - 11}" y="{y + h_r6 - 26}" width="11" height="11" rx="2.5" fill="{t["heat"][lvl]}"/>'
        lx -= 15
    inner += T(lx - 4, y + h_r6 - 16, "less", 10.5, t["faint"], "Inter", 400, "end")
    add("bottom", tile(x, y, INNER, h_r6, t, 10, inner))

    # viewBox regions in the shared canvas; side-by-side pieces each keep half the gutter on their inner edge
    mid = PAD + wl + GAP / 2
    boxes = {"hero": (PAD, y_hero, INNER, h_hero),
             "linkedin": (PAD, y_soc, W / 2 - PAD, h_soc), "email": (W / 2, y_soc, W / 2 - PAD, h_soc),
             "stats": (PAD, y_stats, INNER, h_stats),
             **{k: (PAD, y_q + i * (h_q + GAP), INNER, h_q) for i, k in enumerate(qkeys)},
             "pingo": (PAD, y_r3, mid - PAD, h_r3), "candidato": (mid, y_r3, W - PAD - mid, h_r3),
             "soin": (PAD, y_r4, mid - PAD, h_r4), "creators": (mid, y_r4, W - PAD - mid, h_r4),
             "bottom": (PAD, y_r5, INNER, y_r6 + h_r6 - y_r5)}
    style = css(len(weeks))
    bgdef = f'<defs><image id="bgimg" href="{img["bg"]}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/></defs>'
    out = {}
    for k, (bx, by, bw, bh) in boxes.items():
        label = f'{CFG["name"]}: {k}'
        out[k] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw:g}" height="{bh:g}" '
                  f'viewBox="{bx:g} {by:g} {bw:g} {bh:g}" role="img" aria-label="{escape(label)}">'
                  f'<title>{escape(label)}</title>' + style + bgdef + "".join(pieces[k]) + "</svg>\n")
    return out


if __name__ == "__main__":
    cal = load_calendar()
    avatar = load_avatar()
    music = load_spotify()
    img = {"bg": asset_uri(CFG["background"]["file"])}
    for key in ("pingo", "candidato", "soin"):
        if CFG[key].get("icon"):
            img[key + "_icon"] = asset_uri(CFG[key]["icon"])
        img[key + "_shot"] = asset_uri(CFG[key]["shot"])
    out = ROOT / "profile"
    out.mkdir(exist_ok=True)
    for th in THEMES:
        for name, svg in render(th, cal, avatar, music, img).items():
            (out / f"{name}-{th}.svg").write_text(svg, encoding="utf-8")
    print("wrote", sorted(p.name for p in out.glob("*.svg")), "music:", bool(music))
