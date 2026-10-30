"""Render hero.svg: one immersive scene for the profile README.

An isometric terrain of pillars rides a radial wave that never stops, the
camera drifts slowly and a volumetric light sweeps across. The middle band is
the last year of AI work (data/ai-usage.json): every day with Claude or OpenAI
tokens stands up as a pillar, amber for Claude, green for OpenAI, and the
heaviest days become beacons. A HUD rolls the totals in like an odometer;\nproviders without local logs come from data/manual-usage.json.
Pure SVG + CSS/SMIL, so it animates inside a GitHub README <img>.

Usage: python3 scripts/render_hero.py
"""
import json
import math
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "ai-usage.json").read_text())
# providers with no local logs, typed in by hand
for _key, _val in json.loads((ROOT / "data" / "manual-usage.json").read_text()).items():
    if not _key.startswith("_"):
        DATA[_key] = {"total_tokens": _val["total_tokens"], "last30": []}
# the ChatGPT total already includes Codex: borrow Codex's measured days for that column
if "chatgpt" in DATA:
    DATA["chatgpt"]["last30"] = DATA["openai"]["last30"]

W, H = 880, 630
FONT = "'SF Pro Display',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'SF Mono',ui-monospace,Menlo,Consolas,monospace"

THEMES = {
    "dark": {"BG": "#07080b", "EDGE": "#1a1e25", "TONE": ("#1d232c", "#141920", "#0d1015"),
             "SKY": "#151a22", "TEXT": "#f2f4f7", "TAG": "#7a838f", "META": "#3d444e",
             "SUB": "#5d6672", "FAINT": "#252b34", "BLEND": "screen"},
    "light": {"BG": "#f4f2ee", "EDGE": "#e3e0d9", "TONE": ("#e2ded6", "#cbc6bc", "#b7b2a8"),
              "SKY": "#ffffff", "TEXT": "#16191e", "TAG": "#6f7680", "META": "#9aa0a8",
              "SUB": "#7d838c", "FAINT": "#ddd9d1", "BLEND": "normal"},
}
# colours of the theme being drawn; main() switches them before each render
BG, EDGE, TONE, SKY, TEXT, TAG, META, SUB, FAINT, BLEND = THEMES["dark"].values()
AMBER = "#ff8f2e"
SHADES = {
    "claude": ("#ffbe6b", "#e0812e", "#9c4a16"),
    "openai": ("#8af0c4", "#2fb57e", "#176447"),   # Codex, shown as part of ChatGPT
    "kimi": ("#cfc6ff", "#8f7cf0", "#4d3f99"),
}
# Kimi has no daily logs: its total sits as one undated cluster behind the calendar band
KIMI_CLUSTER = [(c, r) for r in range(3, 8) for c in range(19, 25)
                if (c - 21.5) ** 2 / 9 + (r - 5) ** 2 / 3.2 <= 1]
ACCENT = {"claude": AMBER, "openai": "#2fd492", "chatgpt": "#2fd492", "kimi": "#a594ff"}
# HUD columns, left to right
PROVIDERS = (("claude", "CLAUDE"), ("chatgpt", "CHATGPT"), ("kimi", "KIMI"))

COLS, ROWS = 48, 30
U = (15.0, 5.4)    # one column step on screen
V = (-13.0, 8.5)   # one row step on screen
# terrain bleeds past the frame on three sides; only the far corner stays in view
ORIGIN = (W / 2 - (COLS * U[0] + ROWS * V[0]) / 2, 178.0)
BUCKETS = 40       # wave delays are quantised into shared classes to keep the file small
INSET = 0.08
DEPTH = 46         # sides run this far below ground so the wave never shows a gap
PERIOD = 5.2       # seconds per wave cycle
LIFT = 24          # wave amplitude in px
BEAMS = 5          # how many of the heaviest days get a light beam


def f(n: float) -> str:
    return f"{n:.1f}".rstrip("0").rstrip(".")


def pts(points) -> str:
    return " ".join(f"{f(x)},{f(y)}" for x, y in points)


def P(c: float, r: float) -> tuple[float, float]:
    return (ORIGIN[0] + c * U[0] + r * V[0], ORIGIN[1] + c * U[1] + r * V[1])


def noise(c: int, r: int) -> float:
    """Deterministic 0..1 grain."""
    v = math.sin(c * 12.9898 + r * 78.233) * 43758.5453
    return v - math.floor(v)


def relief(c: int, r: int) -> float:
    """Soft rolling hills plus a touch of grain, in px."""
    hills = 0.5 + 0.25 * math.sin(c * 0.29 + 1.3) * math.cos(r * 0.41 - 0.7) \
        + 0.25 * math.sin((c + r) * 0.17)
    return 4 + 16 * hills + 3 * noise(c, r) ** 3


def usage_cells() -> dict[tuple[int, int], tuple[int, str]]:
    """Map the year (53 weeks x 7 days, oldest first) onto the middle band of the terrain."""
    claude, openai = DATA["claude"]["year"], DATA["openai"]["year"]
    first = date.fromisoformat(DATA["updated"]) - timedelta(days=len(claude) - 1)
    lead = (first.weekday() + 1) % 7  # weeks start on Sunday, like GitHub
    weeks = (len(claude) + lead + 6) // 7
    out = {}
    if DATA.get("kimi", {}).get("total_tokens"):
        share = DATA["kimi"]["total_tokens"] // len(KIMI_CLUSTER)
        out.update({cell: (share, "kimi") for cell in KIMI_CLUSTER})
    for i, (a, b) in enumerate(zip(claude, openai)):
        if a + b:
            k = i + lead
            col = 6 + round((k // 7) * (COLS - 16) / max(weeks - 1, 1))
            out[(col, 9 + k % 7)] = (a + b, "claude" if a >= b else "openai")
    return out


def terrain() -> str:
    cells = usage_cells()
    peak = max((v for v, _ in cells.values()), default=1)
    beams = set(sorted(cells, key=lambda k: cells[k][0])[-BEAMS:])
    # the ripple starts from the most recent day of work (dict keeps calendar order)
    centre = list(cells)[-1] if cells else (COLS * 0.5, ROWS * 0.45)
    out = []
    for c, r in sorted(((c, r) for c in range(COLS) for r in range(ROWS)),
                       key=lambda t: (t[0] + t[1], t[0])):
        A = P(c + INSET, r + INSET)
        B = P(c + 1 - INSET, r + INSET)
        C = P(c + 1 - INSET, r + 1 - INSET)
        D = P(c + INSET, r + 1 - INSET)
        value, kind = cells.get((c, r), (0, ""))
        h = relief(c, r)
        if value:
            h += 14 + 74 * math.sqrt(value / peak)
        top = [(x, y - h) for x, y in (A, B, C, D)]
        down = lambda p: (p[0], p[1] + DEPTH)
        tones = SHADES[kind] if value else TONE
        dist = math.hypot(c - centre[0], (r - centre[1]) * 1.3)
        bucket = round((dist * 0.2 % PERIOD) / PERIOD * BUCKETS) % BUCKETS
        parts = [
            f'<polygon points="{pts([top[1], top[2], down(C), down(B)])}" fill="{tones[1]}"/>',
            f'<polygon points="{pts([top[3], top[2], down(C), down(D)])}" fill="{tones[2]}"/>',
            f'<polygon points="{pts(top)}" fill="{tones[0]}"/>',
        ]
        if (c, r) in beams:
            cx = sum(x for x, _ in top) / 4
            cy = sum(y for _, y in top) / 4
            parts.append(
                f'<rect class="halo" x="{f(cx - 22)}" y="{f(cy - 320)}" width="44" height="320" '
                f'fill="url(#beam-{kind})"/>'
                f'<rect class="beam" x="{f(cx - 3)}" y="{f(cy - 320)}" width="6" height="320" '
                f'fill="url(#beam-{kind})"/>'
                f'<ellipse class="halo" cx="{f(cx)}" cy="{f(cy)}" rx="34" ry="16" fill="{ACCENT[kind]}"/>'
            )
        elif not value:
            parts.append(f'<polygon class="g d{bucket}" points="{pts(top)}" fill="{AMBER}"/>')
        out.append(f'<g class="p d{bucket}">{"".join(parts)}</g>')
    return "\n".join(out)


def delay_classes() -> str:
    return "".join(f".d{i}{{animation-delay:-{i * PERIOD / BUCKETS:.3f}s}}" for i in range(BUCKETS))


def short(n: int) -> str:
    for size, unit, digits in ((1e9, "B", 2), (1e6, "M", 1), (1e3, "K", 1)):
        if n >= size:
            return f"{n / size:.{digits}f}".rstrip("0").rstrip(".") + unit
    return str(n)


def advance(ch: str, size: int) -> float:
    return size * (0.36 if ch == "." else 0.62)


def odometer(text: str, x: float, y: float, size: int, anchor: str, begin: float, uid: str) -> str:
    """Digits roll up through a full turn and settle; the unit letter takes the brand colour."""
    lh = size * 1.15
    width = sum(advance(ch, size) for ch in text)
    x0 = x - width if anchor == "end" else x
    parts = [f'<clipPath id="odo-{uid}"><rect x="{f(x0 - 2)}" y="{f(y - size * 0.92)}" '
             f'width="{f(width + 4)}" height="{f(size * 1.12)}"/></clipPath>',
             f'<g clip-path="url(#odo-{uid})" class="odo">']
    cx = x0 - advance(text[0], size)
    for i, ch in enumerate(text):
        cx += advance(text[i - 1], size) if i else advance(ch, size)
        if ch == ".":
            parts.append(f'<text x="{f(cx - size * 0.13)}" y="{f(y)}">.</text>')
            continue
        if not ch.isdigit():
            parts.append(f'<text x="{f(cx)}" y="{f(y)}" fill="{ACCENT[uid]}">{ch}</text>')
            continue
        d = int(ch)
        strip = "".join(f'<text x="{f(cx)}" y="{f(y + n * lh)}">{n % 10}</text>' for n in range(11 + d))
        start = begin + i * 0.09
        parts.append(
            f'<g>{strip}<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {f(-(10 + d) * lh)}" keyTimes="0;1" calcMode="spline" '
            f'keySplines=".16 1 .3 1" begin="{start:.2f}s" dur="2.2s" fill="freeze"/></g>'
        )
    parts.append("</g>")
    return "".join(parts)


def bars(series: list[int], x: float, base: float, kind: str, begin: float) -> str:
    """30-day bar strip; grows bar by bar."""
    bw, gap, tall = 4, 2.5, 18
    if not any(series):  # no daily data: leave the space clean
        return ""
    peak = max(series)
    out = []
    for i, v in enumerate(series):
        h = 2 + tall * math.sqrt(v / peak) if v else 2
        out.append(
            f'<rect class="bar" x="{f(x + i * (bw + gap))}" y="{f(base - h)}" width="{bw}" '
            f'height="{f(h)}" rx="1" fill="{ACCENT[kind] if v else FAINT}" '
            f'style="animation-delay:{begin + i * 0.03:.2f}s"/>'
        )
    return "".join(out)


def hud_column(i: int, kind: str, label: str, begin: float) -> str:
    d = DATA[kind]
    col = (W - 68) / len(PROVIDERS)
    x = 34 + i * col
    rule = f'<rect x="{f(x - 14)}" y="{H - 150}" width="1" height="104" fill="{EDGE}"/>' if i else ""
    return f"""<g class="hud" style="animation-delay:{begin:.2f}s">{rule}
  {bars(d["last30"], x, H - 138, kind, begin + 0.6)}
  <circle cx="{f(x + 4)}" cy="{H - 118}" r="3.5" fill="{ACCENT[kind]}" class="dot"/>
  <text class="hud-label" x="{f(x + 15)}" y="{H - 114}" fill="{ACCENT[kind]}">{label}</text>
  {odometer(short(d["total_tokens"]), x, H - 76, 30, "start", begin + 0.2, kind)}
  <text class="hud-sub" x="{f(x)}" y="{H - 52}">TOKENS</text>
</g>"""


def hero() -> str:
    # the terrain silhouette extruded upward: hides the sides that run below the front edges
    left, front, right = P(0, ROWS), P(COLS, ROWS), P(COLS, 0)
    clip = pts([left, front, right, (right[0], -400), (left[0], -400)])
    updated = date.fromisoformat(DATA["updated"]).strftime("%d.%m.%Y")

    style = f"""
.p{{animation:wave {PERIOD}s ease-in-out infinite both}}
.g{{opacity:0;animation:glint {PERIOD}s ease-in-out infinite both}}
.beam{{animation:beam 3.2s ease-in-out infinite both;mix-blend-mode:{BLEND}}}
.halo{{filter:url(#soft);opacity:.3;mix-blend-mode:{BLEND};animation:halo 3.2s ease-in-out infinite both}}
{delay_classes()}
.cam{{transform-box:view-box;transform-origin:50% 60%;animation:cam 22s ease-in-out infinite alternate both}}
.sweep{{mix-blend-mode:{BLEND};animation:sweep 16s cubic-bezier(.45,0,.25,1) infinite both}}
.name{{font:700 46px {FONT};fill:{TEXT};letter-spacing:15px;
  animation:name 2.2s cubic-bezier(.16,1,.3,1) .2s both}}
.tag{{font:400 12px {MONO};letter-spacing:4px;fill:{TAG};animation:fade 1.4s ease-out 1.4s both}}
.meta{{font:400 10px {MONO};letter-spacing:3px;fill:{META};animation:fade 1.4s ease-out 2.4s both}}
.dot{{animation:pulse 1.6s ease-in-out infinite both}}
.tag .dot{{fill:{AMBER}}}
.rule{{transform-box:fill-box;transform-origin:center;animation:rule 1.8s cubic-bezier(.16,1,.3,1) .9s both}}
.hud{{animation:fade 1.2s ease-out both}}
.hud-label{{font:600 10.5px {MONO};letter-spacing:2.5px}}
.hud-sub{{font:400 10px {MONO};letter-spacing:2.5px;fill:{SUB}}}
.odo text{{font:600 30px {MONO}}}
.odo{{fill:{TEXT}}}

.bar{{transform-box:fill-box;transform-origin:bottom;animation:grow .9s cubic-bezier(.16,1,.3,1) both}}
@keyframes wave{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-{LIFT}px)}}}}
@keyframes glint{{0%,32%,68%,100%{{opacity:0}}50%{{opacity:.3}}}}
@keyframes beam{{0%,100%{{opacity:.6}}50%{{opacity:1}}}}
@keyframes halo{{0%,100%{{opacity:.18}}50%{{opacity:.4}}}}
@keyframes cam{{from{{transform:translate(0,0) scale(1)}}to{{transform:translate(-26px,-10px) scale(1.07)}}}}
@keyframes sweep{{0%{{transform:translateX(-520px)}}60%,100%{{transform:translateX({W + 120}px)}}}}
@keyframes name{{from{{opacity:0;letter-spacing:42px;filter:blur(14px)}}to{{opacity:1;letter-spacing:15px;filter:blur(0)}}}}
@keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
@keyframes rule{{from{{transform:scaleX(0);opacity:0}}to{{transform:scaleX(1);opacity:1}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}"""

    beam_grads = "".join(
        f'<linearGradient id="beam-{k}" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{SHADES[k][0]}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{ACCENT[k]}" stop-opacity="0"/></linearGradient>'
        for k in SHADES
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>{style}</style>
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  <clipPath id="ground"><polygon points="{clip}"/></clipPath>
  <radialGradient id="sky" cx="50%" cy="38%" r="70%">
    <stop offset="0" stop-color="{SKY}"/><stop offset=".6" stop-color="{BG}"/>
  </radialGradient>
  <linearGradient id="fog" x1="0" y1="0" x2="0" y2="1">
    <stop offset=".26" stop-color="{BG}"/><stop offset=".45" stop-color="{BG}" stop-opacity="0"/>
    <stop offset=".66" stop-color="{BG}" stop-opacity="0"/><stop offset=".84" stop-color="{BG}" stop-opacity=".88"/>
    <stop offset="1" stop-color="{BG}"/>
  </linearGradient>
  <linearGradient id="sides" x1="0" x2="1">
    <stop offset="0" stop-color="{BG}"/><stop offset=".14" stop-color="{BG}" stop-opacity="0"/>
    <stop offset=".86" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/>
  </linearGradient>
  {beam_grads}
  <radialGradient id="light">
    <stop offset="0" stop-color="{AMBER}" stop-opacity=".16"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="9"/></filter>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  <g class="cam"><g clip-path="url(#ground)">
{terrain()}
  </g></g>
  <ellipse class="sweep" cx="0" cy="330" rx="260" ry="220" fill="url(#light)"/>
  <rect width="{W}" height="{H}" fill="url(#fog)"/>
  <rect width="{W}" height="{H}" fill="url(#sides)"/>
  <text class="name" x="{W / 2 + 7}" y="92" text-anchor="middle">ENRICO BUTACU</text>
  <rect class="rule" x="{W / 2 - 70}" y="112" width="140" height="1" fill="{AMBER}"/>
  <g class="tag"><circle class="dot" cx="{W / 2 - 146}" cy="139" r="3"/>
  <text x="{W / 2 + 8}" y="143" text-anchor="middle">SOMETHING IS BEING BUILT</text></g>
  {"".join(hud_column(i, k, label, 1.8 + i * 0.25) for i, (k, label) in enumerate(PROVIDERS))}
  <text class="meta" x="{W / 2}" y="{H - 18}" text-anchor="middle">UPDATED {updated}</text>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{EDGE}"/>
</svg>
"""


def main() -> None:
    global BG, EDGE, TONE, SKY, TEXT, TAG, META, SUB, FAINT, BLEND
    for theme, name in (("dark", "hero.svg"), ("light", "hero-light.svg")):
        BG, EDGE, TONE, SKY, TEXT, TAG, META, SUB, FAINT, BLEND = THEMES[theme].values()
        (ROOT / name).write_text(hero())
    print(f"wrote hero.svg ({(ROOT / 'hero.svg').stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
