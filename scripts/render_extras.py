"""Render the smaller profile pieces that sit under hero.svg.

  clock.svg    24-hour dial of when AI work happens (data/ai-usage.json "hours")
  project.svg  codename that decrypts and re-encrypts, with progress (data/project.json)
  bench.svg    isometric workbench, one object per tool
  repo-N.svg   one card per public repo (data/repos.json, from scripts/fetch_repos.py)

Every piece is drawn for a theme; dark is the default.
Pure SVG + CSS, so it animates inside a GitHub README <img>.

Usage: python3 scripts/render_extras.py
"""
import json
import math
import random
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USAGE = json.loads((ROOT / "data" / "ai-usage.json").read_text())
PROJECT = json.loads((ROOT / "data" / "project.json").read_text())
REPOS_FILE = ROOT / "data" / "repos.json"
REPOS = json.loads(REPOS_FILE.read_text()) if REPOS_FILE.exists() else []
LANG = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#663399",
        "Python": "#3572a5", "Swift": "#f05138"}

FONT = "'SF Pro Display',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'SF Mono',ui-monospace,Menlo,Consolas,monospace"
AMBER = "#ff8f2e"

THEMES = {
    "dark": {"bg": "#07080b", "edge": "#1a1e25", "text": "#f2f4f7", "muted": "#5d6672",
             "faint": "#1d232c", "glow": "screen"},
    "light": {"bg": "#f7f6f3", "edge": "#e3e0d9", "text": "#16191e", "muted": "#8a8f98",
              "faint": "#e7e4dd", "glow": "multiply"},
}


def f(n: float) -> str:
    return f"{n:.1f}".rstrip("0").rstrip(".")


def card(w: int, h: int, t: dict, style: str, inner: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f"<style>{style}\n.cap{{font:500 10px {MONO};letter-spacing:3px;fill:{t['muted']}}}\n"
        "@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>\n"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="{t["bg"]}" stroke="{t["edge"]}"/>\n'
        f"{inner}\n</svg>\n"
    )


def clock(t: dict) -> str:
    W = H = 430
    cx, cy = W / 2, H / 2 + 10
    hours = USAGE["hours"]
    peak = max(hours) or 1
    top = hours.index(peak)
    night = sum(hours[h] for h in (22, 23, 0, 1, 2, 3, 4, 5)) / (sum(hours) or 1)
    spin = 12.0  # seconds per sweep turn
    r0 = 72

    bars = []
    for h, v in enumerate(hours):
        a = math.radians(h * 15 - 90)
        length = 6 + 96 * math.sqrt(v / peak)
        x1, y1 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x2, y2 = cx + (r0 + length) * math.cos(a), cy + (r0 + length) * math.sin(a)
        colour = AMBER if v else t["faint"]
        bars.append(
            f'<line class="bar" pathLength="1" x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" '
            f'stroke="{colour}" style="animation-delay:{0.4 + h * 0.04:.2f}s,{h / 24 * spin - spin:.2f}s"/>'
        )

    ticks = []
    for h in range(24):
        a = math.radians(h * 15 - 90)
        r1, r2 = (r0 - 12, r0 - 4) if h % 6 == 0 else (r0 - 8, r0 - 4)
        ticks.append(
            f'<line x1="{f(cx + r1 * math.cos(a))}" y1="{f(cy + r1 * math.sin(a))}" '
            f'x2="{f(cx + r2 * math.cos(a))}" y2="{f(cy + r2 * math.sin(a))}" stroke="{t["muted"]}"/>'
        )
    labels = "".join(
        f'<text class="cap" x="{f(cx + 186 * math.cos(math.radians(h * 15 - 90)))}" '
        f'y="{f(cy + 186 * math.sin(math.radians(h * 15 - 90)) + 4)}" text-anchor="middle">{h:02d}</text>'
        for h in (0, 6, 12, 18)
    )
    # sweep: a soft 40 degree wedge trailing a bright edge, turning once per `spin`
    edge = 178
    wedge = (f"M{f(cx)},{f(cy)} L{f(cx)},{f(cy - edge)} "
             f"A{edge},{edge} 0 0 0 {f(cx - edge * math.sin(math.radians(40)))},"
             f"{f(cy - edge * math.cos(math.radians(40)))} Z")

    style = f"""
.bar{{stroke-width:8;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;
  animation:draw 1.2s cubic-bezier(.16,1,.3,1) both,lit {spin}s linear infinite both}}
.sweep{{transform-origin:{f(cx)}px {f(cy)}px;animation:spin {spin}s linear infinite;mix-blend-mode:{t['glow']}}}
.peak{{font:600 32px {MONO};fill:{t['text']};animation:fade 1s ease-out 1.2s both}}
.lbl{{font:500 10px {MONO};letter-spacing:3px;fill:{t['muted']};animation:fade 1s ease-out 1.4s both}}
.amber{{fill:{AMBER}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes lit{{0%{{opacity:1}}3%{{opacity:1}}25%,100%{{opacity:.45}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}"""

    inner = f"""<defs>
  <linearGradient id="trail" x1="1" y1="0" x2="0" y2=".4">
    <stop offset="0" stop-color="{AMBER}" stop-opacity=".28"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
  </linearGradient>
</defs>
<text class="cap" x="28" y="38">AI CLOCK · 24H</text>
<circle cx="{f(cx)}" cy="{f(cy)}" r="{r0 - 16}" fill="none" stroke="{t['edge']}"/>
{"".join(ticks)}
<g class="sweep"><path d="{wedge}" fill="url(#trail)"/>
  <line x1="{f(cx)}" y1="{f(cy)}" x2="{f(cx)}" y2="{f(cy - edge)}" stroke="{AMBER}" stroke-opacity=".7"/></g>
{"".join(bars)}
{labels}
<text class="peak" x="{f(cx)}" y="{f(cy + 8)}" text-anchor="middle">{top:02d}<tspan class="amber">:</tspan>00</text>
<text class="lbl" x="{f(cx)}" y="{f(cy + 30)}" text-anchor="middle">PEAK HOUR</text>
<text class="cap" x="{W - 28}" y="38" text-anchor="end">AFTER DARK {round(night * 100)}%</text>"""
    return card(W, H, t, style, inner)


def project(t: dict) -> str:
    W, H = 880, 92
    name = PROJECT["codename"].upper()
    progress = max(0, min(100, int(PROJECT["progress"])))
    rng = random.Random(name)  # same scramble every render, so git only sees real changes
    glyphs = "#%@$*/?!01X=+▓▒░"  # no &, < or >: they would break the XML
    size, adv, lh = 26, 26 * 0.62 + 6, 34
    loop, frame = 9.0, 0.08
    frames = int(loop / frame)
    x0 = W / 2 - adv * len(name) / 2
    y = H / 2 + 9

    chars = []
    for i, ch in enumerate(name):
        strip = [rng.choice(glyphs) for _ in range(8)] + [ch]
        # scramble, then lock in left to right, hold, then break up again right to left
        lock = int((1.2 + i * 0.14) / frame)
        free = int((6.4 + (len(name) - i) * 0.1) / frame)
        rows = [8 if lock <= k < free else rng.randrange(8) for k in range(frames)]
        values = ";".join(f"0 {-r * lh}" for r in rows)
        times = ";".join(f"{k / frames:.4f}" for k in range(frames))
        texts = "".join(f'<text x="{f(x0 + i * adv)}" y="{f(y + r * lh)}">{g}</text>'
                        for r, g in enumerate(strip))
        chars.append(
            f'<g>{texts}<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
            f'values="{values}" keyTimes="{times}" dur="{loop}s" repeatCount="indefinite"/></g>'
        )

    bar_w = 150
    bx = W - 34 - bar_w
    style = f"""
.code text{{font:600 {size}px {MONO};fill:{t['text']}}}
.dot{{fill:{AMBER};animation:pulse 1.6s ease-in-out infinite}}
.fill{{transform-box:fill-box;transform-origin:left;animation:fill 2.4s cubic-bezier(.16,1,.3,1) .4s both}}
.shine{{animation:shine 3.2s ease-in-out 2.8s infinite both}}
.pct{{font:600 13px {MONO};fill:{t['text']}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
@keyframes fill{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes shine{{0%{{transform:translateX(-40px);opacity:0}}20%{{opacity:1}}60%,100%{{transform:translateX({bar_w * progress / 100}px);opacity:0}}}}"""
    inner = f"""<defs>
  <clipPath id="code"><rect x="{f(x0 - 4)}" y="{f(y - size)}" width="{f(adv * len(name) + 8)}" height="{size + 8}"/></clipPath>
  <clipPath id="bar"><rect x="{bx}" y="{H / 2 - 2}" width="{f(bar_w * progress / 100)}" height="4" rx="2"/></clipPath>
  <linearGradient id="shinegrad" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<circle class="dot" cx="38" cy="{H / 2}" r="3.5"/>
<text class="cap" x="52" y="{H / 2 + 4}">NOW BUILDING</text>
<g class="code" clip-path="url(#code)">{"".join(chars)}</g>
<rect x="{bx}" y="{H / 2 - 2}" width="{bar_w}" height="4" rx="2" fill="{t['faint']}"/>
<rect class="fill" x="{bx}" y="{H / 2 - 2}" width="{f(bar_w * progress / 100)}" height="4" rx="2" fill="{AMBER}"/>
<g clip-path="url(#bar)"><rect class="shine" x="{bx}" y="{H / 2 - 2}" width="40" height="4" fill="url(#shinegrad)"/></g>
<text class="pct" x="{bx - 14}" y="{H / 2 + 5}" text-anchor="end">{progress}%</text>"""
    return card(W, H, t, style, inner)


def shade(hex_colour: str, k: float) -> str:
    """Lighten (k > 0) or darken (k < 0) a #rrggbb colour."""
    c = [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    c = [round(v + (255 - v) * k) if k > 0 else round(v * (1 + k)) for v in c]
    return "#" + "".join(f"{v:02x}" for v in c)


def bench(t: dict) -> str:
    W = H = 430
    S = 38                      # px per bench unit
    # centre the 5.6 x 4.2 bench: corner (0, 0, 0) sits up and left of the card centre
    OX, OY = W / 2 - (5.6 - 4.2) / 2 * math.cos(math.radians(30)) * S, 118
    c30, s30 = math.cos(math.radians(30)), 0.5

    def iso(x, y, z=0.0):
        return (OX + (x - y) * c30 * S, OY + (x + y) * s30 * S - z * S)

    def poly(points, fill, extra=""):
        return f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in points)}" fill="{fill}"{extra}/>'

    def box(x, y, z, w, d, h, base):
        top = [iso(x, y, z + h), iso(x + w, y, z + h), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
        right = [iso(x + w, y, z), iso(x + w, y + d, z), iso(x + w, y + d, z + h), iso(x + w, y, z + h)]
        left = [iso(x, y + d, z), iso(x + w, y + d, z), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
        return poly(right, shade(base, -0.35)) + poly(left, shade(base, -0.15)) + poly(top, shade(base, 0.12))

    dark = t["bg"] == THEMES["dark"]["bg"]
    desk = "#1a1f27" if dark else "#d9d5cc"
    body = "#262c36" if dark else "#c9c4b9"
    ink = t["text"]

    def blender(x, y, z):
        cx, cy = iso(x + 0.5, y + 0.5, z + 0.75)
        return (box(x + 0.15, y + 0.15, z, 0.7, 0.7, 0.25, body)
                + f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(0.42 * S)}" fill="url(#sphere)"/>'
                + f'<ellipse class="orbit" cx="{f(cx)}" cy="{f(cy)}" rx="{f(0.78 * S)}" ry="{f(0.26 * S)}" '
                  f'fill="none" stroke="{AMBER}" stroke-width="1.5" pathLength="100" '
                  f'transform="rotate(-18 {f(cx)} {f(cy)})"/>')

    def affinity(x, y, z):
        apex = iso(x + 0.5, y + 0.5, z + 1.15)
        a, b, c = iso(x + 1, y, z), iso(x + 1, y + 1, z), iso(x, y + 1, z)
        return (poly([a, b, apex], shade("#b48cff", -0.45)) + poly([c, b, apex], shade("#b48cff", -0.1))
                + f'<circle class="spark" cx="{f(apex[0])}" cy="{f(apex[1])}" r="2.5" fill="#d9c7ff"/>')

    def after_effects(x, y, z):
        out = box(x, y + 0.2, z, 1.1, 0.6, 0.14, body)
        for i in range(4):
            px, py = iso(x + 0.15 + i * 0.27, y + 0.5, z + 0.3)
            out += (f'<rect class="key" x="{f(px - 4)}" y="{f(py - 4)}" width="8" height="8" fill="#9d9dff" '
                    f'transform="rotate(45 {f(px)} {f(py)})" style="animation-delay:{i * 0.35:.2f}s"/>')
        return out

    def premiere(x, y, z):
        out = box(x + 0.1, y + 0.1, z, 0.8, 0.8, 0.8, body)
        # play triangle laid on the top face
        tri = [iso(x + 0.35, y + 0.32, z + 0.8), iso(x + 0.72, y + 0.5, z + 0.8), iso(x + 0.35, y + 0.68, z + 0.8)]
        return out + poly(tri, "#8f8fff", ' class="play"')

    def figma(x, y, z):
        out = ""
        for i, colour in enumerate(("#2fd492", "#ff7262", "#a259ff")):
            out += f'<g class="layer" style="animation-delay:{i * 0.25:.2f}s">' + box(
                x + 0.1, y + 0.1, z + i * 0.32, 0.8, 0.8, 0.06, colour) + "</g>"
        return out

    def claude_code(x, y, z):
        out = box(x + 0.05, y + 0.15, z, 0.95, 0.75, 0.5, "#1a1d22" if dark else "#2a2e35")
        # text on the top face: map unit square onto the face
        ox, oy = iso(x + 0.05, y + 0.15, z + 0.5)
        m = f"matrix({f(c30 * S / 100)},{f(s30 * S / 100)},{f(-c30 * S / 100)},{f(s30 * S / 100)},{f(ox)},{f(oy)})"
        return out + (f'<g transform="{m}"><text x="12" y="58" class="term">&gt;</text>'
                      f'<rect class="cursor" x="44" y="40" width="22" height="18" fill="{AMBER}"/></g>')

    tools = [("BLENDER", blender), ("AFFINITY", affinity), ("AFTER EFFECTS", after_effects),
             ("PREMIERE", premiere), ("FIGMA", figma), ("CLAUDE CODE", claude_code)]
    slots = [(0.3, 0.3), (2.3, 0.3), (4.3, 0.3), (0.3, 2.5), (2.3, 2.5), (4.3, 2.5)]
    desk_h = 0.35
    parts = [box(0, 0, -desk_h, 5.6, 4.2, desk_h, desk)]
    tags, legend = [], []
    order = sorted(range(len(tools)), key=lambda k: slots[k][0] + slots[k][1])  # back to front
    for i in order:
        (name, draw), (x, y) = tools[i], slots[i]
        sx, sy = iso(x + 0.5, y + 0.5, 0)
        parts.append(f'<ellipse class="shadow" cx="{f(sx)}" cy="{f(sy)}" rx="{f(0.62 * S)}" ry="{f(0.3 * S)}" '
                     f'fill="#000" style="animation-delay:{i * 0.4:.2f}s"/>')
        parts.append(f'<g class="float" style="animation-delay:{i * 0.4:.2f}s">{draw(x, y, 0.08)}</g>')
        tx, ty = iso(x + 0.5, y + 0.5, 1.55)
        tags.append(f'<text class="tag" x="{f(tx)}" y="{f(ty)}" text-anchor="middle">{i + 1:02d}</text>')
    for i, (name, _) in enumerate(tools):
        lx = 28 + (i % 3) * 120
        ly = H - 52 + (i // 3) * 18
        legend.append(f'<text class="cap tool" x="{lx}" y="{ly}"><tspan fill="{AMBER}">{i + 1:02d}</tspan> {name}</text>')

    style = f"""
.float{{animation:float 4.2s ease-in-out infinite alternate both}}
.shadow{{opacity:.28;filter:url(#blur);animation:shadow 4.2s ease-in-out infinite alternate both}}
.orbit{{stroke-dasharray:62 38;animation:orbit 3s linear infinite}}
.key{{opacity:.25;animation:key 1.4s ease-in-out infinite}}
.layer{{animation:layer 3.6s ease-in-out infinite alternate both}}
.spark,.play{{animation:glow 2.4s ease-in-out infinite}}
.term{{font:700 50px {MONO};fill:#e8ecf2}}
.cursor{{animation:blink 1.1s steps(1) infinite}}
.tool{{font-size:9px;letter-spacing:2px}}
.tag{{font:600 9px {MONO};letter-spacing:1px;fill:{ink};opacity:.55}}
@keyframes float{{from{{transform:translateY(0)}}to{{transform:translateY(-6px)}}}}
@keyframes shadow{{from{{opacity:.3}}to{{opacity:.14}}}}
@keyframes orbit{{to{{stroke-dashoffset:-100}}}}
@keyframes key{{0%,100%{{opacity:.25}}30%{{opacity:1}}}}
@keyframes layer{{from{{transform:translateY(0)}}to{{transform:translateY(-4px)}}}}
@keyframes glow{{0%,100%{{opacity:1}}50%{{opacity:.45}}}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}"""
    inner = f"""<defs>
  <radialGradient id="sphere" cx=".35" cy=".3" r=".75">
    <stop offset="0" stop-color="#ffd2a1"/><stop offset=".45" stop-color="{AMBER}"/><stop offset="1" stop-color="#5a2a0a"/>
  </radialGradient>
  <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>
<text class="cap" x="28" y="38">WORKBENCH</text>
<text class="cap" x="{W - 28}" y="38" text-anchor="end">{len(tools)} TOOLS</text>
{"".join(parts)}
{"".join(tags)}
{"".join(legend)}"""
    return card(W, H, t, style, inner)


def repo_card(repo: dict, t: dict) -> str:
    W, H = 430, 150
    weeks = repo["weeks"]
    peak = max(weeks) or 1
    lang = repo.get("language") or ""
    when = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).strftime("%b %Y").upper()
    c30 = math.cos(math.radians(30))
    pillars = []
    for i, v in enumerate(weeks):
        x, base = 32 + i * (W - 64) / (len(weeks) - 1), H - 26
        h = 3 + 22 * math.sqrt(v / peak) if v else 3
        top = AMBER if v else t["faint"]
        side = shade(AMBER, -0.35) if v else shade(t["faint"], -0.3)
        front = shade(AMBER, -0.15) if v else shade(t["faint"], -0.15)
        w = 4.2
        # a tiny iso column: top diamond plus two side faces
        pts_top = f"{f(x)},{f(base - h)} {f(x + w * c30)},{f(base - h + w / 2)} {f(x)},{f(base - h + w)} {f(x - w * c30)},{f(base - h + w / 2)}"
        pts_r = f"{f(x)},{f(base - h + w)} {f(x + w * c30)},{f(base - h + w / 2)} {f(x + w * c30)},{f(base + w / 2)} {f(x)},{f(base + w)}"
        pts_l = f"{f(x)},{f(base - h + w)} {f(x - w * c30)},{f(base - h + w / 2)} {f(x - w * c30)},{f(base + w / 2)} {f(x)},{f(base + w)}"
        pillars.append(f'<g class="pil" style="animation-delay:{0.3 + i * 0.03:.2f}s">'
                       f'<polygon points="{pts_r}" fill="{side}"/><polygon points="{pts_l}" fill="{front}"/>'
                       f'<polygon points="{pts_top}" fill="{top}"/></g>')
    style = f"""
.name{{font:600 26px {FONT};fill:{t['text']};animation:rise .9s cubic-bezier(.16,1,.3,1) .1s both}}
.lang{{font:500 10px {MONO};letter-spacing:2px;fill:{t['muted']}}}
.arrow{{font:400 18px {FONT};fill:{AMBER};animation:nudge 2.4s ease-in-out infinite}}
.pil{{transform-box:fill-box;transform-origin:bottom;animation:grow .8s cubic-bezier(.16,1,.3,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes nudge{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(3px,-3px)}}}}"""
    dot = (f'<circle cx="{W - 28 - len(lang) * 8.4 - 10}" cy="34" r="4" fill="{LANG.get(lang, t["muted"])}"/>'
           f'<text class="lang" x="{W - 28}" y="38" text-anchor="end">{lang.upper()}</text>') if lang else ""
    inner = f"""<text class="cap" x="28" y="38">REPOSITORY</text>
{dot}
<text class="name" x="28" y="76">{repo['name']}</text>
<text class="arrow" x="{W - 30}" y="78" text-anchor="end">↗</text>
{"".join(pillars)}
<text class="cap" x="28" y="102">{repo['commits']} COMMITS · {when}</text>"""
    return card(W, H, t, style, inner)


PIECES = {"clock": clock, "project": project, "bench": bench}


def main() -> None:
    names = []
    for theme, suffix in (("dark", ""), ("light", "-light")):
        for name, draw in PIECES.items():
            (ROOT / f"{name}{suffix}.svg").write_text(draw(THEMES[theme]))
            names.append(f"{name}{suffix}.svg")
        for i, repo in enumerate(REPOS, 1):
            (ROOT / f"repo-{i}{suffix}.svg").write_text(repo_card(repo, THEMES[theme]))
            names.append(f"repo-{i}{suffix}.svg")
    link_repos()
    print("wrote " + ", ".join(names))


def link_repos() -> None:
    """Point the README's repo cards at the repos they show, in the current order."""
    readme = ROOT / "README.md"
    text = readme.read_text()
    start, end = "<!-- repos:start -->", "<!-- repos:end -->"
    if start not in text:
        return
    cards = "\n".join(
        f'<a href="{r["html_url"]}"><picture>'
        f'<source media="(prefers-color-scheme: light)" srcset="./repo-{i}-light.svg" />'
        f'<img src="./repo-{i}.svg" width="49%" alt="{r["name"]}" /></picture></a>'
        for i, r in enumerate(REPOS, 1))
    head, rest = text.split(start, 1)
    readme.write_text(f"{head}{start}\n{cards}\n{end}{rest.split(end, 1)[1]}")


if __name__ == "__main__":
    main()
