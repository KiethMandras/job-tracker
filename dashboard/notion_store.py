"""Data layer for the job search dashboard.

Two backends share one interface:
  NotionBackend  talks to your Notion database
  DemoBackend    keeps sample data in memory (set DASHBOARD_DEMO=1)
"""
from datetime import date, datetime, timedelta

TIMEZONE = "Asia/Manila"

STATUSES = [
    "Interested",
    "To Apply",
    "Applied",
    "Under Review",
    "Interview Scheduled",
    "Assessment",
    "Final Interview",
    "Offered",
    "Rejected",
    "Withdrawn",
]

# Statuses from the first version of the tracker, shown under their new names.
LEGACY_STATUS = {
    "Screening": "Under Review",
    "Interview": "Interview Scheduled",
    "Offer": "Offered",
}

# Kanban column name -> statuses shown in it. The first status is the one a
# card gets when it is moved into the column.
KANBAN = [
    ("Wishlist", ["Interested"]),
    ("To Apply", ["To Apply"]),
    ("Applied", ["Applied", "Under Review"]),
    ("Interview", ["Interview Scheduled", "Final Interview"]),
    ("Assessment", ["Assessment"]),
    ("Offer", ["Offered"]),
    ("Rejected", ["Rejected", "Withdrawn"]),
]

CLOSED_STATUSES = ("Offered", "Rejected", "Withdrawn")
PENDING_STATUSES = ("Applied", "Under Review")
INTERVIEW_STATUSES = ("Interview Scheduled", "Final Interview")

EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Temporary"]
INTERVIEW_TYPES = ["Online", "In-person"]

# (Notion property name, record key, kind)
FIELDS = [
    ("Company", "company", "title"),
    ("Position", "position", "rich_text"),
    ("Status", "status", "select"),
    ("Date Applied", "date_applied", "date"),
    ("Source", "source", "select"),
    ("Link", "link", "url"),
    ("Follow-up Date", "follow_up", "date"),
    ("Notes", "notes", "rich_text"),
    ("Deadline", "deadline", "date"),
    ("Location", "location", "rich_text"),
    ("Employment Type", "emp_type", "select"),
    ("Salary Range", "salary", "rich_text"),
    ("Contact Person", "contact", "rich_text"),
    ("Contact Email", "email", "email"),
    ("Resume Version", "resume", "rich_text"),
    ("Cover Letter", "cover", "rich_text"),
    ("Interview Date", "interview", "datetime"),
    ("Interview Type", "interview_type", "select"),
    ("Meeting Link", "meeting", "rich_text"),
    ("Prep Notes", "prep", "rich_text"),
    ("Interview Notes", "interview_notes", "rich_text"),
    ("Assessment Results", "assessment", "rich_text"),
    ("History", "history", "rich_text"),
]


def notion_type(kind):
    """The Notion property type that a field kind is stored in."""
    return "date" if kind == "datetime" else kind


def normalize_status(status):
    status = LEGACY_STATUS.get(status, status)
    return status or "Interested"


def blank_record():
    rec = {"id": "", "url": ""}
    for _name, key, kind in FIELDS:
        rec[key] = None if kind in ("date", "datetime") else ""
    rec["status"] = ""
    return rec


def append_history(history, text):
    lines = [ln for ln in (history or "").splitlines() if ln.strip()]
    lines.append("%s | %s" % (date.today().isoformat(), text))
    return "\n".join(lines[-30:])


# ---------------------------------------------------------------- reading

def _text(prop, key):
    return "".join(p.get("plain_text", "") for p in (prop.get(key) or []))


def _parse_datetime(value):
    if not value:
        return None
    if len(value) <= 10:
        return date.fromisoformat(value)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return date.fromisoformat(value[:10])


def _read(prop, kind):
    if kind in ("title", "rich_text"):
        return _text(prop, kind)
    if kind == "select":
        return (prop.get("select") or {}).get("name", "")
    if kind == "date":
        start = (prop.get("date") or {}).get("start")
        return date.fromisoformat(start[:10]) if start else None
    if kind == "datetime":
        return _parse_datetime((prop.get("date") or {}).get("start"))
    if kind == "url":
        return prop.get("url") or ""
    if kind == "email":
        return prop.get("email") or ""
    return ""


def parse_page(page):
    rec = blank_record()
    rec["id"] = page["id"]
    rec["url"] = page.get("url", "")
    props = page.get("properties", {})
    for name, key, kind in FIELDS:
        if name in props:
            rec[key] = _read(props[name], kind)
    rec["status"] = normalize_status(rec["status"])
    return rec


# ---------------------------------------------------------------- writing

def _rich_text(value):
    value = value or ""
    chunks = [value[i:i + 2000] for i in range(0, len(value), 2000)]
    return [{"text": {"content": c}} for c in chunks]


def _write(kind, value):
    if kind == "title":
        return {"title": _rich_text((value or "")[:2000])}
    if kind == "rich_text":
        return {"rich_text": _rich_text(value)}
    if kind == "select":
        name = (value or "").replace(",", " ").strip()
        return {"select": {"name": name} if name else None}
    if kind in ("date", "datetime"):
        if not value:
            return {"date": None}
        if isinstance(value, datetime):
            start = value.replace(microsecond=0, tzinfo=None).isoformat()
            return {"date": {"start": start, "time_zone": TIMEZONE}}
        return {"date": {"start": value.isoformat()}}
    if kind == "url":
        return {"url": value or None}
    if kind == "email":
        return {"email": value or None}
    raise ValueError("Unknown field kind: %s" % kind)


def to_properties(values, schema):
    """Convert record values to Notion properties, skipping any property
    that does not exist in the database (or has a different type)."""
    props = {}
    for name, key, kind in FIELDS:
        if key in values and schema.get(name) == notion_type(kind):
            props[name] = _write(kind, values[key])
    return props


def missing_properties(schema):
    """Names of properties the dashboard expects but the database lacks."""
    return [n for n, _k, kind in FIELDS if schema.get(n) != notion_type(kind)]


# --------------------------------------------------------------- backends

class NotionBackend(object):
    demo = False

    def __init__(self, token, database_id):
        from notion_client import Client

        self.key = database_id
        self.database_id = database_id
        self.client = Client(auth=token, notion_version="2022-06-28")

    def raw_database(self):
        return self.client.request(
            path="databases/%s" % self.database_id, method="GET"
        )

    def schema(self):
        data = self.raw_database()
        return {n: p.get("type") for n, p in data.get("properties", {}).items()}

    def records(self):
        pages = []
        body = {}
        while True:
            result = self.client.request(
                path="databases/%s/query" % self.database_id,
                method="POST",
                body=body,
            )
            pages.extend(result["results"])
            if not result.get("has_more"):
                break
            body["start_cursor"] = result["next_cursor"]
        return [parse_page(p) for p in pages if not p.get("archived")]

    def create(self, values):
        props = to_properties(values, self.schema())
        self.client.pages.create(
            parent={"database_id": self.database_id}, properties=props
        )

    def update(self, page_id, values):
        props = to_properties(values, self.schema())
        self.client.pages.update(page_id=page_id, properties=props)

    def archive(self, page_id):
        self.client.pages.update(page_id=page_id, archived=True)


class DemoBackend(object):
    """Sample data for trying the dashboard without Notion."""

    demo = True
    key = "demo"

    def __init__(self):
        self._next = 1
        self._rows = []
        for row in self._sample():
            self._add(row)

    def _add(self, values):
        rec = blank_record()
        rec.update(values)
        rec["id"] = "demo-%d" % self._next
        self._next += 1
        self._rows.append(rec)

    def _sample(self):
        t = date.today()

        def d(n):
            return t + timedelta(days=n)

        def at(n, hour, minute=0):
            return datetime(d(n).year, d(n).month, d(n).day, hour, minute)

        def hist(*items):
            return "\n".join("%s | %s" % (d(n).isoformat(), txt) for n, txt in items)

        return [
            dict(company="Northwind Systems", position="IT Support Specialist",
                 status="Interview Scheduled", date_applied=d(-12), deadline=d(-5),
                 location="Baguio City", emp_type="Full-time", salary="PHP 24,000 - 28,000",
                 source="Jobstreet", follow_up=d(4), interview=at(2, 14, 0),
                 interview_type="Online", meeting="https://meet.example.com/northwind",
                 prep="Review ticketing basics and network troubleshooting.",
                 contact="Ana Reyes", email="hr@northwind.example", resume="v3 (IT support)",
                 cover="Support cover letter", notes="Referred by a classmate.",
                 history=hist((-12, "Added as Applied"), (-6, "Status: Under Review"),
                              (-3, "Status: Interview Scheduled"))),
            dict(company="Harbor Logistics", position="Junior Systems Analyst",
                 status="Applied", date_applied=d(-9), deadline=d(-3), location="Remote",
                 emp_type="Full-time", salary="PHP 30,000", source="LinkedIn",
                 follow_up=d(-2), resume="v3 (IT support)",
                 history=hist((-9, "Added as Applied"))),
            dict(company="Pinecrest Bank", position="Security Operations Trainee",
                 status="Assessment", date_applied=d(-15), location="Makati",
                 emp_type="Full-time", salary="PHP 35,000 - 40,000", source="LinkedIn",
                 follow_up=d(1), assessment="Online exam on Thursday.",
                 history=hist((-15, "Added as Applied"), (-8, "Status: Under Review"),
                              (-2, "Status: Assessment"))),
            dict(company="Lumen Labs", position="Junior Python Developer",
                 status="Under Review", date_applied=d(-6), location="Remote",
                 emp_type="Contract", salary="USD 800 / month", source="Referral",
                 follow_up=d(0), history=hist((-6, "Added as Applied"), (-1, "Status: Under Review"))),
            dict(company="Blue Ridge Telecom", position="Network Technician",
                 status="Final Interview", date_applied=d(-25), location="La Union",
                 emp_type="Full-time", salary="PHP 27,000", source="Jobstreet",
                 interview=at(5, 10, 30), interview_type="In-person",
                 meeting="3rd floor, main office", prep="Bring printed resume and IDs.",
                 history=hist((-25, "Added as Applied"), (-14, "Status: Interview Scheduled"),
                              (-1, "Status: Final Interview"))),
            dict(company="Cordillera Municipal Office", position="Computer Programmer I",
                 status="To Apply", deadline=d(6), location="Benguet", emp_type="Full-time",
                 salary="Salary Grade 11", source="Gov't", notes="Check eligibility requirements.",
                 history=hist((-1, "Added as To Apply"))),
            dict(company="Summit Cloud", position="Cloud Support Associate",
                 status="Interested", location="Remote", emp_type="Full-time",
                 source="LinkedIn", history=hist((-2, "Added as Interested"))),
            dict(company="Granite Retail Group", position="IT Helpdesk Agent",
                 status="Offered", date_applied=d(-30), location="Baguio City",
                 emp_type="Full-time", salary="PHP 22,000", source="Referral",
                 notes="Offer expires next week.",
                 history=hist((-30, "Added as Applied"), (-20, "Status: Interview Scheduled"),
                              (-4, "Status: Offered"))),
            dict(company="Westfield Media", position="Web Support Intern",
                 status="Rejected", date_applied=d(-28), location="Manila",
                 emp_type="Internship", source="Jobstreet",
                 history=hist((-28, "Added as Applied"), (-10, "Status: Rejected"))),
            dict(company="Ironwood Security", position="SOC Analyst Trainee",
                 status="Withdrawn", date_applied=d(-20), location="Cebu",
                 emp_type="Full-time", source="LinkedIn", notes="Relocation was required.",
                 history=hist((-20, "Added as Applied"), (-7, "Status: Withdrawn"))),
            dict(company="Maple Health Tech", position="Application Support Engineer",
                 status="Applied", date_applied=d(-3), location="Remote",
                 emp_type="Full-time", salary="PHP 32,000", source="Jobstreet",
                 follow_up=d(4), history=hist((-3, "Added as Applied"))),
            dict(company="Silverline Bank", position="IT Audit Trainee",
                 status="Interested", location="Quezon City", emp_type="Full-time",
                 source="Gov't", history=hist((-1, "Added as Interested"))),
        ]

    def schema(self):
        return {n: notion_type(k) for n, _key, k in FIELDS}

    def records(self):
        return [dict(r) for r in self._rows]

    def create(self, values):
        self._add(values)

    def update(self, page_id, values):
        for rec in self._rows:
            if rec["id"] == page_id:
                rec.update(values)

    def archive(self, page_id):
        self._rows = [r for r in self._rows if r["id"] != page_id]
