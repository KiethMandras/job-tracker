"""Monochrome manga-inspired look for the dashboard.

All artwork here is generated from simple shapes, halftone dots, and
hatching. To use your own original illustrations, put them in the assets
folder (see assets/README.txt).
"""
import base64
import calendar
import html
import math
import os
import random
from datetime import date
from functools import lru_cache

import local_store
import notion_store as ns

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}

QUOTES = [
    "Every closed door is just the turn of a page, not the end of the story.",
    "Quiet persistence fills the empty panels.",
    "The next chapter starts with one more application.",
    "Even the longest night leaves room for a bright panel.",
    "Small steps, drawn carefully, make the whole story.",
]

STATUS_TONE = {
    "Interested": "grey",
    "To Apply": "grey",
    "Applied": "amber",
    "Under Review": "amber",
    "Interview Scheduled": "green",
    "Assessment": "green",
    "Final Interview": "green",
    "Offered": "green",
    "Rejected": "red",
    "Withdrawn": "red",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;800&family=Libre+Baskerville:ital@1&display=swap');
:root{--mj-ink:#171717;--mj-accent:#292929;--mj-muted:#777777;--mj-line:#E5E5E5;--mj-soft:#F5F5F5;}
html,body,.stApp,[class*="css"]{font-family:'Archivo','Segoe UI',Helvetica,Arial,sans-serif;color:var(--mj-ink);}
.stApp{background-color:#FFFFFF;}
.block-container{padding-top:1.4rem;max-width:1240px;}
footer{visibility:hidden;}
h1,h2,h3{font-family:'Archivo','Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:-0.01em;}
.mj-icon{display:block;}
.mj-banner{position:relative;border:1px solid var(--mj-ink);border-radius:2px;overflow:hidden;min-height:230px;margin-bottom:1.1rem;background:#0d0d0d;}
.mj-banner-bg{position:absolute;inset:0;background-size:cover;background-position:center;filter:grayscale(1) contrast(1.08);}
.mj-banner-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.78) 0%,rgba(0,0,0,.25) 62%,rgba(0,0,0,0) 100%);}
.mj-banner-inner{position:relative;display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;padding:1.5rem 1.6rem;min-height:230px;}
div.mj-title{font-size:2.5rem;font-weight:800;line-height:1.05;color:#fff;margin:0 0 .6rem 0;padding:0;max-width:640px;}
div.mj-quote{font-family:'Libre Baskerville',Georgia,serif;font-style:italic;font-size:1rem;line-height:1.6;color:#e6e6e6;margin:0;max-width:520px;}
.mj-tools{display:flex;align-items:center;gap:.7rem;}
.mj-tool{position:relative;display:flex;align-items:center;justify-content:center;width:38px;height:38px;border:1px solid rgba(255,255,255,.55);border-radius:50%;background:rgba(0,0,0,.35);}
.mj-badge{position:absolute;top:-6px;right:-6px;min-width:18px;height:18px;padding:0 4px;border-radius:9px;background:#fff;color:#171717;font-size:11px;font-weight:700;line-height:18px;text-align:center;}
.mj-avatar{width:46px;height:46px;border-radius:50%;border:2px solid #fff;object-fit:cover;background:#fff;}
.mj-initials{display:flex;align-items:center;justify-content:center;color:#171717;font-weight:800;font-size:15px;}
.mj-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.9rem;margin-bottom:1.2rem;}
.mj-stat{position:relative;overflow:hidden;background:#fff;border:1px solid var(--mj-ink);border-radius:2px;padding:1rem 1.1rem;}
.mj-stat::after{content:"";position:absolute;right:0;top:0;width:110px;height:110px;background-image:radial-gradient(rgba(23,23,23,.28) 1.2px,transparent 1.7px);background-size:7px 7px;-webkit-mask-image:linear-gradient(225deg,#000,transparent 70%);mask-image:linear-gradient(225deg,#000,transparent 70%);pointer-events:none;}
.mj-stat-top{display:flex;align-items:center;justify-content:space-between;}
div.mj-stat-value{font-size:2.6rem;font-weight:800;line-height:1;margin:.6rem 0 .3rem 0;}
div.mj-stat-label{font-size:.95rem;font-weight:700;margin:0;}
div.mj-stat-note{font-size:.82rem;color:var(--mj-muted);margin:.1rem 0 0 0;}
.mj-scroll{overflow-x:auto;border:1px solid var(--mj-ink);border-radius:2px;background:#fff;}
table.mj-table{width:100%;border-collapse:collapse;font-size:.88rem;min-width:860px;}
.mj-table th{text-align:left;font-weight:700;font-size:.8rem;color:var(--mj-ink);background:var(--mj-soft);border-bottom:1px solid var(--mj-ink);padding:.6rem .7rem;white-space:nowrap;}
.mj-table td{padding:.6rem .7rem;border-bottom:1px solid var(--mj-line);vertical-align:top;}
.mj-table tr:last-child td{border-bottom:none;}
.mj-table td.mj-company{font-weight:700;}
.mj-soon{font-weight:700;text-decoration:underline;text-decoration-thickness:2px;}
.mj-muted{color:var(--mj-muted);}
.mj-nw{white-space:nowrap;}
.mj-empty{padding:1.4rem;color:var(--mj-muted);text-align:center;}
.mj-pill{display:inline-block;padding:.12rem .55rem;border-radius:2px;font-size:.78rem;font-weight:700;white-space:nowrap;border:1px solid transparent;}
.mj-pill-grey{background:#efefef;color:#555;border-color:#d9d9d9;}
.mj-pill-amber{background:#f6ecd2;color:#7d5a12;border-color:#e3d1a0;}
.mj-pill-green{background:#e1ece4;color:#365f45;border-color:#bfd5c5;}
.mj-pill-red{background:#f3dede;color:#8a3737;border-color:#e0b9b9;}
.mj-board{display:flex;gap:.8rem;overflow-x:auto;padding-bottom:.6rem;align-items:flex-start;}
.mj-col{flex:0 0 205px;background:var(--mj-soft);border:1px solid var(--mj-ink);border-radius:2px;}
.mj-col-head{display:flex;justify-content:space-between;align-items:center;padding:.55rem .7rem;border-bottom:1px solid var(--mj-ink);font-weight:800;font-size:.9rem;background-image:radial-gradient(rgba(23,23,23,.16) 1px,transparent 1.5px);background-size:6px 6px;}
.mj-count{font-size:.78rem;font-weight:700;background:#fff;border:1px solid var(--mj-ink);border-radius:10px;padding:0 .45rem;}
.mj-col-body{padding:.55rem;display:flex;flex-direction:column;gap:.5rem;min-height:70px;}
.mj-card{background:#fff;border:1px solid var(--mj-line);border-left:3px solid var(--mj-ink);padding:.5rem .6rem;}
.mj-card b{display:block;font-size:.88rem;}
.mj-card > span{display:block;font-size:.8rem;color:var(--mj-muted);margin-top:.1rem;}
.mj-card .mj-pill{margin-top:.35rem;display:inline-block;}
.mj-panel{border:1px solid var(--mj-ink);border-radius:2px;background:#fff;padding:1.1rem 1.2rem;margin:.8rem 0;}
div.mj-h2{font-size:1.5rem;font-weight:800;margin:0;padding:0;}
div.mj-h3{font-size:1rem;font-weight:800;margin:1rem 0 .4rem 0;padding:0;}
div.mj-sub{color:var(--mj-muted);margin:.2rem 0 .6rem 0;}
.mj-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.55rem 1.4rem;margin:.4rem 0;}
.mj-grid div{font-size:.88rem;border-bottom:1px solid var(--mj-line);padding-bottom:.35rem;}
.mj-grid small{display:block;font-size:.75rem;color:var(--mj-muted);margin-bottom:.1rem;}
.mj-grid a,.mj-panel a{color:var(--mj-ink);text-decoration:underline;}
div.mj-text{white-space:pre-wrap;font-size:.9rem;line-height:1.55;margin:.2rem 0;}
ol.mj-timeline{list-style:none;margin:.4rem 0 0 .35rem;padding:0 0 0 1.1rem;border-left:2px solid var(--mj-ink);}
ol.mj-timeline li{position:relative;padding:0 0 .8rem 0;font-size:.88rem;}
ol.mj-timeline li::before{content:"";position:absolute;left:-1.6rem;top:.25rem;width:.7rem;height:.7rem;background:#fff;border:2px solid var(--mj-ink);border-radius:50%;}
ol.mj-timeline li:last-child::before{background:var(--mj-ink);}
ol.mj-timeline small{display:block;color:var(--mj-muted);font-size:.75rem;}
.mj-cards{margin-bottom:1.2rem;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.9rem;}
.mj-iv{border:1px solid var(--mj-ink);background:#fff;padding:.9rem 1rem;border-radius:2px;}
div.mj-h4{margin:0;font-size:1rem;font-weight:800;}
.mj-iv div.mj-line{margin:.25rem 0;font-size:.86rem;}
.mj-iv div.mj-when{font-weight:700;}
.mj-remind{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.6rem .8rem;border:1px solid var(--mj-line);border-left:3px solid var(--mj-ink);background:#fff;margin-bottom:.45rem;font-size:.88rem;}
.mj-remind b{font-weight:700;}
.mj-remind .mj-kind{font-size:.78rem;color:var(--mj-muted);}
.mj-late{color:#8a3737;font-weight:700;white-space:nowrap;}
.mj-ontime{font-weight:700;white-space:nowrap;}
[data-testid="stTabs"] button[role="tab"]{font-weight:700;}
.mj-wiz{margin:.1rem 0 1.1rem 0;}
.mj-steps{display:flex;align-items:center;}
.mj-step{display:flex;align-items:center;gap:.45rem;flex:0 0 auto;}
.mj-dot{width:26px;height:26px;border-radius:50%;border:1.5px solid var(--mj-ink);display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700;background:#fff;color:var(--mj-ink);}
.mj-dot .mj-icon{margin:0;}
.mj-step-done .mj-dot{background:var(--mj-ink);}
.mj-step-current .mj-dot{background:var(--mj-ink);color:#fff;box-shadow:0 0 0 3px rgba(23,23,23,.18);}
.mj-step-todo .mj-dot{border-color:#bdbdbd;color:#9a9a9a;}
.mj-step-label{font-size:.85rem;font-weight:700;}
.mj-step-todo .mj-step-label{color:#9a9a9a;font-weight:500;}
.mj-conn{flex:1 1 auto;height:2px;background:#d9d9d9;margin:0 .6rem;min-width:12px;}
.mj-conn-done{background:var(--mj-ink);}
.mj-wiz-track{height:4px;background:var(--mj-line);margin-top:.8rem;}
.mj-wiz-fill{height:4px;background:var(--mj-ink);transition:width .25s ease;}
.mj-wiz-cap{font-size:.8rem;color:var(--mj-muted);margin-top:.4rem;}
.mj-review{border:1px solid var(--mj-line);background:var(--mj-soft);padding:.8rem 1rem;margin-bottom:.6rem;}
.mj-cal{border:1px solid var(--mj-ink);border-radius:2px;background:#fff;overflow-x:auto;margin-bottom:1rem;}
.mj-cal-grid{display:grid;grid-template-columns:repeat(7,minmax(108px,1fr));min-width:780px;}
.mj-cal-dow{padding:.45rem .6rem;font-size:.78rem;font-weight:800;background:var(--mj-soft);border-bottom:1px solid var(--mj-ink);}
.mj-cal-day{min-height:98px;padding:.3rem .35rem;border-right:1px solid var(--mj-line);border-bottom:1px solid var(--mj-line);overflow:hidden;}
.mj-cal-day:nth-child(7n){border-right:none;}
.mj-cal-out{background:var(--mj-soft);opacity:.6;}
.mj-cal-num{font-size:.78rem;font-weight:700;margin-bottom:.15rem;}
.mj-cal-today .mj-cal-num{display:inline-block;background:var(--mj-ink);color:#fff;border-radius:10px;padding:0 .45rem;}
.mj-ev{display:block;font-size:.72rem;line-height:1.3;padding:.08rem .3rem;margin-top:.15rem;border-left:3px solid;border-radius:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.mj-ev-interview{background:#171717;color:#fff;border-color:#171717;}
.mj-ev-assessment{background:#e1ece4;color:#365f45;border-color:#365f45;}
.mj-ev-deadline{background:#f3dede;color:#8a3737;border-color:#8a3737;}
.mj-ev-followup{background:#f6ecd2;color:#7d5a12;border-color:#7d5a12;}
.mj-ev-task{background:#efefef;color:#555;border-color:#999;}
.mj-more{font-size:.72rem;color:var(--mj-muted);margin-top:.15rem;}
.mj-legend{display:flex;flex-wrap:wrap;gap:.5rem;margin:.3rem 0 .8rem 0;}
.mj-legend .mj-ev{margin:0;padding:.15rem .5rem;}
.mj-bars{border:1px solid var(--mj-ink);border-radius:2px;background:#fff;padding:.8rem 1rem;margin-bottom:1rem;}
.mj-bars-title{font-weight:800;margin-bottom:.5rem;}
.mj-bar-row{display:flex;align-items:center;gap:.7rem;margin:.35rem 0;font-size:.85rem;}
.mj-bar-label{flex:0 0 130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.mj-bar-track{flex:1 1 auto;height:12px;background:var(--mj-soft);border:1px solid var(--mj-line);}
.mj-bar-fill{height:100%;background:var(--mj-ink);}
.mj-bar-val{flex:0 0 auto;min-width:5.5rem;text-align:right;font-weight:700;}
.mj-goal{border:1px solid var(--mj-ink);border-radius:2px;background:#fff;padding:.7rem 1rem;margin-bottom:1.1rem;}
.mj-goal-top{display:flex;justify-content:space-between;gap:1rem;font-size:.9rem;font-weight:700;margin-bottom:.45rem;}
.mj-links{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.6rem;margin-bottom:.8rem;}
.mj-link{border:1px solid var(--mj-ink);border-radius:2px;background:#fff;padding:.55rem .7rem;}
.mj-link b{display:block;font-size:.88rem;}
.mj-link span{display:block;font-size:.76rem;color:var(--mj-muted);margin-top:.2rem;word-break:break-all;}
.mj-link a{display:block;font-size:.8rem;color:var(--mj-ink);text-decoration:underline;margin-top:.2rem;}
@media (max-width:700px){.mj-step-label{display:none;}.mj-step-current .mj-step-label{display:inline;}div.mj-title{font-size:1.8rem;}.mj-banner-inner{flex-direction:column;}}
</style>
"""

DARK_CSS = """
<style>
:root{--mj-ink:#ECECEC;--mj-accent:#D4D4D4;--mj-muted:#A3A3A3;--mj-line:#363636;--mj-soft:#222222;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background-color:#121212;color:#ECECEC;}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background-color:#1A1A1A;}
.stApp p,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp li,[data-testid="stWidgetLabel"] p{color:#ECECEC;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:#A3A3A3;}
[data-baseweb="input"],[data-baseweb="input"] input,[data-baseweb="textarea"],[data-baseweb="textarea"] textarea,
[data-baseweb="select"]>div,[data-baseweb="base-input"]{background-color:#1E1E1E;color:#ECECEC;}
[data-baseweb="popover"],[data-baseweb="popover"]>div,[data-baseweb="menu"],ul[role="listbox"],
[data-baseweb="calendar"]{background-color:#1E1E1E;color:#ECECEC;}
li[role="option"]{color:#ECECEC;}
.stButton>button,.stFormSubmitButton>button{background-color:#1E1E1E;color:#ECECEC;border:1px solid #555;}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background-color:#ECECEC;color:#121212;}
div[role="dialog"]{background-color:#161616;}
[data-testid="stExpander"] details{border-color:#363636;}
.mj-stat,.mj-scroll,.mj-card,.mj-panel,.mj-iv,.mj-remind,.mj-count,.mj-dot,.mj-cal,.mj-bars,.mj-goal,.mj-link{background:#181818;}
.mj-cal-today .mj-cal-num{background:#ECECEC;color:#121212;}
.mj-ev-interview{background:#ECECEC;color:#121212;border-color:#ECECEC;}
.mj-ev-assessment{background:#1d3326;color:#8fd0a4;border-color:#8fd0a4;}
.mj-ev-deadline{background:#3d2222;color:#e59a9a;border-color:#e59a9a;}
.mj-ev-followup{background:#3a3117;color:#e6c670;border-color:#e6c670;}
.mj-ev-task{background:#2b2b2b;color:#cfcfcf;border-color:#777;}
.mj-col,.mj-review{background:#1E1E1E;}
.mj-stat .mj-icon,.mj-step-done .mj-icon{filter:invert(1);}
.mj-stat::after{background-image:radial-gradient(rgba(255,255,255,.16) 1.2px,transparent 1.7px);}
.mj-col-head{background-image:radial-gradient(rgba(255,255,255,.1) 1px,transparent 1.5px);}
.mj-step-done .mj-dot{background:#ECECEC;}
.mj-step-current .mj-dot{background:#ECECEC;color:#121212;}
.mj-step-todo .mj-dot{border-color:#555;color:#888;}
.mj-conn{background:#444;}
ol.mj-timeline li::before{background:#181818;}
.mj-late{color:#e59a9a;}
.mj-pill-grey{background:#2b2b2b;color:#cfcfcf;border-color:#444;}
.mj-pill-amber{background:#3a3117;color:#e6c670;border-color:#5c4d22;}
.mj-pill-green{background:#1d3326;color:#8fd0a4;border-color:#2f5640;}
.mj-pill-red{background:#3d2222;color:#e59a9a;border-color:#5e3434;}
</style>
"""


def css(dark=False):
    return CSS + (DARK_CSS if dark else "")


def e(text):
    return html.escape(str(text if text is not None else ""), quote=True)


# ------------------------------------------------------------------ assets

def find_asset(stem):
    for ext in MIME:
        path = os.path.join(ASSETS, "%s.%s" % (stem, ext))
        if os.path.isfile(path):
            return path
    return None


@lru_cache(maxsize=16)
def _file_uri(path, mtime):
    ext = path.rsplit(".", 1)[-1].lower()
    with open(path, "rb") as handle:
        data = base64.b64encode(handle.read()).decode("ascii")
    return "data:%s;base64,%s" % (MIME[ext], data)


def asset_uri(stem):
    path = find_asset(stem)
    return _file_uri(path, os.path.getmtime(path)) if path else None


def _svg_uri(svg):
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return "data:image/svg+xml;base64," + data


ICONS = {
    "list": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "calendar": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
    "tick": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "bell": '<path d="M6 9a6 6 0 0 1 12 0c0 6 2 7 2 7H4s2-1 2-7"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "sliders": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
}


def icon(name, color="#292929", size=22):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="%d" '
        'height="%d" fill="none" stroke="%s" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round">%s</svg>'
    ) % (size, size, color, ICONS[name])
    return '<img class="mj-icon" alt="" width="%d" height="%d" src="%s">' % (
        size, size, _svg_uri(svg))


@lru_cache(maxsize=1)
def banner_svg():
    """An original ink-and-screentone night skyline under a halftone moon."""
    rng = random.Random(11)
    cx, cy = 1010, 118
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 360" '
        'preserveAspectRatio="xMidYMid slice">',
        '<defs>'
        '<pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse">'
        '<circle cx="4.5" cy="4.5" r="1.7" fill="#fff"/></pattern>'
        '<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(35)"><line x1="0" y1="0" x2="0" y2="7" '
        'stroke="#fff" stroke-width="1"/></pattern>'
        '<radialGradient id="halo"><stop offset="0.45" stop-color="#fff"/>'
        '<stop offset="1" stop-color="#000"/></radialGradient>'
        '<mask id="haloMask"><circle cx="%d" cy="%d" r="210" fill="url(#halo)"/></mask>'
        '<linearGradient id="fadeV" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0.35" stop-color="#000"/><stop offset="1" stop-color="#fff"/>'
        '</linearGradient>'
        '<mask id="fogMask"><rect width="1600" height="360" fill="url(#fadeV)"/></mask>'
        '<linearGradient id="fadeH" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff"/><stop offset="0.6" stop-color="#000"/>'
        '</linearGradient>'
        '<mask id="hatchMask"><rect width="1600" height="360" fill="url(#fadeH)"/></mask>'
        '</defs>' % (cx, cy),
        '<rect width="1600" height="360" fill="#0d0d0d"/>',
        '<rect width="1600" height="360" fill="url(#hatch)" opacity="0.22" mask="url(#hatchMask)"/>',
    ]
    # radiating speed lines around the moon
    parts.append('<g stroke="#fff" stroke-width="1.2" opacity="0.32">')
    for deg in range(0, 360, 9):
        a = math.radians(deg + rng.uniform(-2, 2))
        r1 = 118 + rng.uniform(0, 30)
        r2 = r1 + rng.uniform(90, 330)
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            cx + math.cos(a) * r1, cy + math.sin(a) * r1,
            cx + math.cos(a) * r2, cy + math.sin(a) * r2))
    parts.append('</g>')
    parts.append('<circle cx="%d" cy="%d" r="210" fill="url(#dots)" mask="url(#haloMask)"/>' % (cx, cy))
    parts.append('<circle cx="%d" cy="%d" r="96" fill="#fff"/>' % (cx, cy))
    for dx, dy, r in ((-28, -20, 15), (24, 18, 22), (-6, 42, 9), (36, -34, 8)):
        parts.append('<circle cx="%d" cy="%d" r="%d" fill="#0d0d0d" opacity="0.85"/>' % (
            cx + dx, cy + dy, r))
    # skyline with ink outlines and lit windows
    x = -20
    while x < 1620:
        w = rng.randint(46, 118)
        h = rng.randint(70, 215)
        top = 360 - h
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#000" '
                     'stroke="#e8e8e8" stroke-width="1.5"/>' % (x, top, w, h))
        if rng.random() < 0.35:
            parts.append('<path d="M%d %d l%d -22 l%d 22z" fill="#000" '
                         'stroke="#e8e8e8" stroke-width="1.5"/>' % (x, top, w // 2, w // 2))
        for wy in range(top + 14, 350, 22):
            for wx in range(x + 10, x + w - 10, 16):
                if rng.random() < 0.22:
                    parts.append('<rect x="%d" y="%d" width="7" height="10" fill="#fff"/>' % (wx, wy))
        x += w + rng.randint(-6, 10)
    parts.append('<rect width="1600" height="360" fill="url(#dots)" opacity="0.5" mask="url(#fogMask)"/>')
    parts.append('</svg>')
    return "".join(parts)


# -------------------------------------------------------------- formatting

def fmt_date(value):
    return value.strftime("%b %d, %Y") if value else "-"


def interview_day(rec):
    value = rec["interview"]
    if not value:
        return None
    return value.date() if hasattr(value, "hour") else value


def fmt_interview(rec):
    value = rec["interview"]
    if not value:
        return "-"
    if hasattr(value, "hour"):
        return value.strftime("%b %d, %Y, %I:%M %p")
    return fmt_date(value)


def relative(day, today):
    delta = (day - today).days
    if delta == 0:
        return "Today", False
    if delta == 1:
        return "Tomorrow", False
    if delta > 1:
        return "In %d days" % delta, False
    if delta == -1:
        return "1 day overdue", True
    return "%d days overdue" % -delta, True


def pill(status):
    tone = STATUS_TONE.get(status, "grey")
    return '<span class="mj-pill mj-pill-%s">%s</span>' % (tone, e(status))


def safe_url(url):
    return url if url and url.lower().startswith(("http://", "https://")) else ""


def link_html(url, label=None):
    url = safe_url(url)
    if not url:
        return e(url) or "-"
    return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (
        e(url), e(label or url))


# ---------------------------------------------------------------- builders

def header_html(title, quote, badge, initials):
    banner = asset_uri("banner") or _svg_uri(banner_svg())
    avatar = asset_uri("avatar")
    badge_html = '<span class="mj-badge">%d</span>' % badge if badge else ""
    if avatar:
        avatar_html = '<img class="mj-avatar" alt="Profile" src="%s">' % avatar
    else:
        avatar_html = '<div class="mj-avatar mj-initials">%s</div>' % e(initials)
    return (
        '<div class="mj-banner">'
        '<div class="mj-banner-bg" style="background-image:url(%s)"></div>'
        '<div class="mj-banner-shade"></div>'
        '<div class="mj-banner-inner">'
        '<div><div class="mj-title" role="heading" aria-level="1">%s</div><div class="mj-quote">%s</div></div>'
        '<div class="mj-tools">'
        '<span class="mj-tool" title="Reminders">%s%s</span>'
        '<span class="mj-tool" title="Settings are in the sidebar">%s</span>'
        '%s</div></div></div>'
    ) % (banner, e(title), e(quote), icon("bell", "#ffffff", 20), badge_html,
         icon("sliders", "#ffffff", 20), avatar_html)


def stats_html(cards):
    out = ['<div class="mj-stats">']
    for label, value, note, icon_name in cards:
        out.append(
            '<div class="mj-stat"><div class="mj-stat-top">%s</div>'
            '<div class="mj-stat-value">%s</div><div class="mj-stat-label">%s</div>'
            '<div class="mj-stat-note">%s</div></div>' % (
                icon(icon_name, "#292929", 24), value, e(label), e(note)))
    out.append('</div>')
    return "".join(out)


def table_html(rows, today):
    if not rows:
        return '<div class="mj-scroll"><div class="mj-empty">No applications match. Add one above or clear the filters.</div></div>'
    head = ["Company", "Position", "Applied", "Deadline", "Location",
            "Type", "Salary", "Status"]
    out = ['<div class="mj-scroll"><table class="mj-table"><tr>']
    out.extend("<th>%s</th>" % h for h in head)
    out.append("</tr>")
    for r in rows:
        deadline = fmt_date(r["deadline"])
        soon = (r["deadline"] and r["status"] not in ns.CLOSED_STATUSES
                and 0 <= (r["deadline"] - today).days <= 3)
        if soon:
            deadline = '<span class="mj-soon">%s</span>' % deadline
        out.append(
            "<tr><td class=\"mj-company\">%s</td><td>%s</td><td class=\"mj-nw\">%s</td><td class=\"mj-nw\">%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                e(r["company"]), e(r["position"]), fmt_date(r["date_applied"]),
                deadline, e(r["location"] or "-"), e(r["emp_type"] or "-"),
                e(r["salary"] or "-"), pill(r["status"])))
    out.append("</table></div>")
    return "".join(out)


def board_html(records):
    out = ['<div class="mj-board">']
    for name, statuses in ns.KANBAN:
        cards = [r for r in records if r["status"] in statuses]
        out.append('<div class="mj-col"><div class="mj-col-head"><span>%s</span>'
                   '<span class="mj-count">%d</span></div><div class="mj-col-body">' % (
                       e(name), len(cards)))
        if not cards:
            out.append('<span class="mj-muted" style="font-size:.8rem">Nothing here yet.</span>')
        for r in cards:
            extra = pill(r["status"]) if len(statuses) > 1 else ""
            out.append('<div class="mj-card"><b>%s</b><span>%s</span>%s</div>' % (
                e(r["company"]), e(r["position"]), extra))
        out.append("</div></div>")
    out.append("</div>")
    return "".join(out)


def _timeline_items(rec):
    items = []
    for line in rec["history"].splitlines():
        if not line.strip():
            continue
        when, sep, text = line.partition(" | ")
        items.append((when.strip(), text.strip()) if sep else ("", line.strip()))
    if not items:
        if rec["date_applied"]:
            items.append((rec["date_applied"].isoformat(), "Application date"))
        items.append(("", "Current status: %s" % rec["status"]))
    return items


def detail_html(rec):
    def cell(label, value_html):
        return "<div><small>%s</small>%s</div>" % (e(label), value_html or "-")

    contact = e(rec["contact"])
    if rec["email"]:
        contact = (contact + " " if contact else "") + (
            '<a href="mailto:%s">%s</a>' % (e(rec["email"]), e(rec["email"])))
    out = [
        '<div class="mj-panel"><div class="mj-h2" role="heading" aria-level="2">%s</div>' % e(rec["company"]),
        '<div class="mj-sub">%s &nbsp; %s</div>' % (e(rec["position"]), pill(rec["status"])),
        '<div class="mj-grid">',
        cell("Location", e(rec["location"])),
        cell("Employment type", e(rec["emp_type"])),
        cell("Salary", e(rec["salary"])),
        cell("Date applied", fmt_date(rec["date_applied"])),
        cell("Deadline", fmt_date(rec["deadline"])),
        cell("Follow-up", fmt_date(rec["follow_up"])),
        cell("Source", e(rec["source"])),
        cell("Job posting", link_html(rec["link"], "Open posting")),
        cell("Contact", contact),
        cell("Resume version", e(rec["resume"])),
        cell("Cover letter", e(rec["cover"])),
        "</div>",
    ]
    if rec["interview"] or rec["meeting"] or rec["prep"]:
        out.append('<div class="mj-h3" role="heading" aria-level="3">Interview</div><div class="mj-grid">')
        out.append(cell("When", fmt_interview(rec)))
        out.append(cell("Type", e(rec["interview_type"])))
        meet = link_html(rec["meeting"]) if safe_url(rec["meeting"]) else e(rec["meeting"])
        out.append(cell("Link or place", meet))
        out.append("</div>")
        if rec["prep"]:
            out.append('<div class="mj-h3" role="heading" aria-level="3">Preparation notes</div><div class="mj-text">%s</div>' % e(rec["prep"]))
    if rec["interview_notes"]:
        out.append('<div class="mj-h3" role="heading" aria-level="3">Interview notes</div><div class="mj-text">%s</div>' % e(rec["interview_notes"]))
    if rec["assessment"]:
        out.append('<div class="mj-h3" role="heading" aria-level="3">Assessment results</div><div class="mj-text">%s</div>' % e(rec["assessment"]))
    if rec["notes"]:
        out.append('<div class="mj-h3" role="heading" aria-level="3">Personal remarks</div><div class="mj-text">%s</div>' % e(rec["notes"]))
    out.append('<div class="mj-h3" role="heading" aria-level="3">Progress</div><ol class="mj-timeline">')
    for when, text in _timeline_items(rec):
        out.append("<li>%s%s</li>" % (
            "<small>%s</small>" % e(when) if when else "", e(text)))
    out.append("</ol></div>")
    return "".join(out)


def interviews_html(rows, today):
    if not rows:
        return '<div class="mj-scroll"><div class="mj-empty">No interviews scheduled. Add an interview date to an application and it will show up here.</div></div>'
    out = ['<div class="mj-cards">']
    for r in rows:
        label, late = relative(interview_day(r), today)
        place = r["meeting"]
        place_html = link_html(place) if safe_url(place) else e(place or "-")
        out.append(
            '<div class="mj-iv"><div class="mj-h4" role="heading" aria-level="4">%s</div><div class="mj-line">%s</div>'
            '<div class="mj-line mj-when">%s (%s)</div><div class="mj-line">%s: %s</div>%s</div>' % (
                e(r["company"]), e(r["position"]), e(fmt_interview(r)), e(label),
                e(r["interview_type"] or "Type not set"), place_html,
                ('<div class="mj-line mj-muted">%s</div>' % e(r["prep"])) if r["prep"] else ""))
    out.append("</div>")
    return "".join(out)


def reminders_html(alerts, today):
    if not alerts:
        return '<div class="mj-scroll"><div class="mj-empty">Nothing needs attention this week.</div></div>'
    out = []
    for kind, rec, day in alerts:
        label, late = relative(day, today)
        out.append(
            '<div class="mj-remind"><div><b>%s</b> - %s<div class="mj-kind">%s</div></div>'
            '<span class="%s">%s</span></div>' % (
                e(rec["company"]), e(rec["position"]), e(kind),
                "mj-late" if late else "mj-ontime", e(label)))
    return "".join(out)


def steps_html(labels, current):
    """Wizard progress: numbered steps, a filled bar, and a 'Step n of N' line."""
    out = ['<div class="mj-wiz"><div class="mj-steps">']
    for i, label in enumerate(labels):
        state = "done" if i < current else ("current" if i == current else "todo")
        mark = icon("tick", "#ffffff", 14) if state == "done" else str(i + 1)
        out.append('<div class="mj-step mj-step-%s"><span class="mj-dot">%s</span>'
                   '<span class="mj-step-label">%s</span></div>' % (state, mark, e(label)))
        if i < len(labels) - 1:
            out.append('<span class="mj-conn%s"></span>' % (" mj-conn-done" if i < current else ""))
    percent = int(round((current + 1) * 100.0 / len(labels)))
    out.append('</div><div class="mj-wiz-track"><div class="mj-wiz-fill" style="width:%d%%"></div></div>'
               '<div class="mj-wiz-cap">Step %d of %d: %s</div></div>' % (
                   percent, current + 1, len(labels), e(labels[current])))
    return "".join(out)


def review_html(v):
    def cell(label, value_html):
        return "<div><small>%s</small>%s</div>" % (e(label), value_html or "-")

    out = ['<div class="mj-review"><div class="mj-grid">',
           cell("Company", e(v["company"])),
           cell("Position", e(v["position"])),
           cell("Status", pill(v["status"])),
           cell("Source", e(v["source"])),
           cell("Location", e(v["location"])),
           cell("Employment type", e(v["emp_type"])),
           cell("Salary", e(v["salary"])),
           cell("Job posting", e(v["link"])),
           cell("Date applied", fmt_date(v["date_applied"])),
           cell("Deadline", fmt_date(v["deadline"])),
           cell("Follow-up", fmt_date(v["follow_up"])),
           "</div>"]
    if v["notes"]:
        out.append('<div class="mj-h3" role="heading" aria-level="3">Notes</div>'
                   '<div class="mj-text">%s</div>' % e(v["notes"]))
    out.append("</div>")
    return "".join(out)


# ------------------------------------------------- calendar, charts, lists

KIND_CLASS = {"Interview": "interview", "Assessment": "assessment",
              "Deadline": "deadline", "Follow-up": "followup", "Task": "task"}
KIND_SHORT = {"Interview": "Int", "Assessment": "Test", "Deadline": "Due",
              "Follow-up": "F/U", "Task": "Task"}


def legend_html():
    out = ['<div class="mj-legend">']
    for kind in ("Interview", "Assessment", "Deadline", "Follow-up", "Task"):
        out.append('<span class="mj-ev mj-ev-%s">%s = %s</span>' % (
            KIND_CLASS[kind], KIND_SHORT[kind], kind))
    out.append("</div>")
    return "".join(out)


def calendar_html(year, month, events, today):
    by_day = {}
    for ev in events:
        by_day.setdefault(ev["day"], []).append(ev)
    out = ['<div class="mj-cal"><div class="mj-cal-grid">']
    for name in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
        out.append('<div class="mj-cal-dow">%s</div>' % name)
    for week in calendar.Calendar(0).monthdatescalendar(year, month):
        for day in week:
            classes = "mj-cal-day"
            if day.month != month:
                classes += " mj-cal-out"
            if day == today:
                classes += " mj-cal-today"
            out.append('<div class="%s"><div class="mj-cal-num">%d</div>' % (classes, day.day))
            items = by_day.get(day, [])
            for ev in items[:3]:
                tip = "%s: %s%s" % (ev["kind"], ev["title"],
                                    (" - " + ev["detail"]) if ev["detail"] else "")
                out.append('<span class="mj-ev mj-ev-%s" title="%s">%s | %s</span>' % (
                    KIND_CLASS[ev["kind"]], e(tip), KIND_SHORT[ev["kind"]], e(ev["title"])))
            if len(items) > 3:
                out.append('<div class="mj-more">+%d more</div>' % (len(items) - 3))
            out.append("</div>")
    out.append("</div></div>")
    return "".join(out)


def events_list_html(events, year, month, today):
    rows = [ev for ev in events if ev["day"].year == year and ev["day"].month == month]
    if not rows:
        return '<div class="mj-scroll"><div class="mj-empty">Nothing is scheduled this month.</div></div>'
    out = []
    for ev in rows:
        label, _late = relative(ev["day"], today)
        when = ev["day"].strftime("%a, %b %d")
        when += " (%s)" % label if ev["day"] >= today else " (past)"
        detail = ev["detail"]
        out.append(
            '<div class="mj-remind"><div><b>%s</b>%s<div class="mj-kind">%s</div></div>'
            '<span class="mj-ontime">%s</span></div>' % (
                e(ev["title"]), (" - " + e(detail)) if detail else "", e(ev["kind"]), e(when)))
    return "".join(out)


def bars_html(title, rows, max_value=None, empty="Nothing to show yet."):
    """Horizontal bars. rows = [(label, value, text)]."""
    out = ['<div class="mj-bars"><div class="mj-bars-title">%s</div>' % e(title)]
    if not rows:
        out.append('<div class="mj-muted">%s</div>' % e(empty))
    else:
        top = max_value or max(value for _label, value, _text in rows) or 1
        for label, value, text in rows:
            width = max(0, min(100, int(round(100.0 * value / top))))
            out.append(
                '<div class="mj-bar-row"><span class="mj-bar-label" title="%s">%s</span>'
                '<div class="mj-bar-track"><div class="mj-bar-fill" style="width:%d%%"></div></div>'
                '<span class="mj-bar-val">%s</span></div>' % (e(label), e(label), width, e(text)))
    out.append("</div>")
    return "".join(out)


def goal_html(done, target):
    if target <= 0:
        return ""
    percent = min(100, int(round(100.0 * done / target)))
    note = " - goal reached" if done >= target else ""
    return (
        '<div class="mj-goal"><div class="mj-goal-top"><span>Weekly goal</span>'
        '<span>%d of %d applications this week%s</span></div>'
        '<div class="mj-bar-track"><div class="mj-bar-fill" style="width:%d%%"></div></div></div>'
    ) % (done, target, note, percent)


def _ago(day, today):
    delta = (today - day).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "yesterday"
    if delta > 1:
        return "%d days ago" % delta
    return "in %d days" % -delta


def contacts_html(contacts, today):
    if not contacts:
        return '<div class="mj-scroll"><div class="mj-empty">No contacts yet. Add a recruiter or someone you have spoken to.</div></div>'

    def sort_key(c):
        day = local_store.parse_day(c.get("last_contacted"))
        return (day is not None, day or date.min, c.get("name", "").lower())

    head = ["Name", "Role", "Company", "Email", "Phone", "Last contacted", "Notes"]
    out = ['<div class="mj-scroll"><table class="mj-table"><tr>']
    out.extend("<th>%s</th>" % h for h in head)
    out.append("</tr>")
    for c in sorted(contacts, key=sort_key):
        day = local_store.parse_day(c.get("last_contacted"))
        last = "%s (%s)" % (fmt_date(day), _ago(day, today)) if day else "Never"
        email = c.get("email", "")
        email_html = '<a href="mailto:%s">%s</a>' % (e(email), e(email)) if email else "-"
        out.append(
            '<tr><td class="mj-company">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
            '<td class="mj-nw">%s</td><td class="mj-muted">%s</td></tr>' % (
                e(c.get("name", "")), e(c.get("role") or "-"), e(c.get("company") or "-"),
                email_html, e(c.get("phone") or "-"), e(last), e(c.get("notes") or "")))
    out.append("</table></div>")
    return "".join(out)


def links_html(links):
    if not links:
        return '<div class="mj-muted" style="font-size:.85rem">No shortcuts yet.</div>'
    out = ['<div class="mj-links">']
    for item in links:
        target = item.get("url", "")
        body = link_html(target, "Open") if safe_url(target) else "<span>%s</span>" % e(target)
        out.append('<div class="mj-link"><b>%s</b>%s</div>' % (e(item.get("label", "")), body))
    out.append("</div>")
    return "".join(out)