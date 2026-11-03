"""Monochrome manga-inspired look for the dashboard.

All artwork here is generated from simple shapes, halftone dots, and
hatching. To use your own original illustrations, put them in the assets
folder (see assets/README.txt).
"""
import base64
import html
import math
import os
import random
from functools import lru_cache

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
    "676767676767.",
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
@media (max-width:700px){div.mj-title{font-size:1.8rem;}.mj-banner-inner{flex-direction:column;}}
</style>
"""


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
            '<div class="mj-stat-value">%d</div><div class="mj-stat-label">%s</div>'
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
