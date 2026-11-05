"""Numbers, exports and calendar events built from your applications."""
import csv
import io
from datetime import timedelta

import local_store
import notion_store as ns

# Statuses that mean an employer has replied.
RESPONDED = ("Under Review", "Interview Scheduled", "Assessment",
             "Final Interview", "Offered", "Rejected")
# Statuses that mean you actually sent the application.
APPLIED_STATUSES = tuple(s for s in ns.STATUSES if s not in ("Interested", "To Apply"))

EVENT_ORDER = ["Interview", "Assessment", "Deadline", "Follow-up", "Task"]


# ------------------------------------------------------------------ stats

def week_start(day):
    return day - timedelta(days=day.weekday())


def applications_in_week(records, today):
    start = week_start(today)
    end = start + timedelta(days=7)
    return len([r for r in records if r["date_applied"] and start <= r["date_applied"] < end])


def weekly_counts(records, today, weeks=8):
    """[(label, count)] for the last `weeks` weeks, oldest first."""
    this_week = week_start(today)
    out = []
    for i in range(weeks - 1, -1, -1):
        first = this_week - timedelta(weeks=i)
        last = first + timedelta(days=7)
        count = len([r for r in records
                     if r["date_applied"] and first <= r["date_applied"] < last])
        label = first.strftime("%b %d") + (" (this week)" if i == 0 else "")
        out.append((label, count))
    return out


def response_totals(records):
    """(applications sent, applications that got a reply)."""
    sent = [r for r in records if r["status"] in APPLIED_STATUSES and r["date_applied"]]
    heard = [r for r in sent if r["status"] in RESPONDED]
    return len(sent), len(heard)


def response_by_source(records):
    """[(source, applied, heard back, percent)], busiest source first."""
    groups = {}
    for r in records:
        if r["status"] not in APPLIED_STATUSES or not r["date_applied"]:
            continue
        counts = groups.setdefault(r["source"] or "Unknown", [0, 0])
        counts[0] += 1
        if r["status"] in RESPONDED:
            counts[1] += 1
    rows = [(name, applied, heard, int(round(100.0 * heard / applied)))
            for name, (applied, heard) in groups.items()]
    rows.sort(key=lambda row: (-row[1], row[0].lower()))
    return rows


def days_to_first_response(rec):
    """Days from applying to the first status change that shows a reply."""
    if not rec["date_applied"]:
        return None
    for line in (rec["history"] or "").splitlines():
        when, sep, text = line.partition(" | ")
        text = text.strip()
        if not sep or not text.startswith("Status:"):
            continue
        status = ns.normalize_status(text[len("Status:"):].strip())
        if status in RESPONDED:
            day = local_store.parse_day(when)
            if day:
                return max((day - rec["date_applied"]).days, 0)
    return None


def average_days_to_response(records):
    """(average days or None, how many applications it is based on)."""
    days = [d for d in (days_to_first_response(r) for r in records) if d is not None]
    if not days:
        return None, 0
    return sum(days) / float(len(days)), len(days)


# ------------------------------------------------------------- duplicates

def _norm(text):
    return " ".join((text or "").lower().split())


def find_duplicate(records, company, position):
    company, position = _norm(company), _norm(position)
    if not company or not position:
        return None
    for r in records:
        if _norm(r["company"]) == company and _norm(r["position"]) == position:
            return r
    return None


# -------------------------------------------------------------------- csv

def _cell(value):
    if value is None:
        return ""
    if hasattr(value, "hour"):
        return value.strftime("%Y-%m-%d %H:%M")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value)
    # Stop spreadsheet apps from treating text as a formula.
    return "'" + text if text[:1] in ("=", "+", "@", "-") else text


def to_csv(records):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([name for name, _key, _kind in ns.FIELDS])
    for r in records:
        writer.writerow([_cell(r[key]) for _name, key, _kind in ns.FIELDS])
    return buffer.getvalue()


# --------------------------------------------------------------- calendar

def calendar_events(records, tasks):
    """Everything with a date: deadlines, interviews, assessments,
    follow-ups and open tasks."""
    events = []
    for r in records:
        company, position = r["company"], r["position"]
        if r["deadline"]:
            events.append({"day": r["deadline"], "kind": "Deadline",
                           "title": company, "detail": position})
        if r["follow_up"] and r["status"] not in ns.CLOSED_STATUSES:
            events.append({"day": r["follow_up"], "kind": "Follow-up",
                           "title": company, "detail": position})
        value = r["interview"]
        if value:
            day = value.date() if hasattr(value, "hour") else value
            kind = "Assessment" if r["status"] == "Assessment" else "Interview"
            detail = position
            if hasattr(value, "hour"):
                detail += " at " + value.strftime("%I:%M %p").lstrip("0")
            events.append({"day": day, "kind": kind, "title": company, "detail": detail})
    for task in tasks:
        day = local_store.parse_day(task.get("due"))
        if day and not task.get("done"):
            events.append({"day": day, "kind": "Task", "title": task.get("text", ""),
                           "detail": task.get("related", "")})
    events.sort(key=lambda ev: (ev["day"], EVENT_ORDER.index(ev["kind"]), ev["title"].lower()))
    return events