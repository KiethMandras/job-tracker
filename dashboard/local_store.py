"""A small JSON file for the things Notion does not hold: tasks, notes,
contacts, quick links and your weekly goal.

The real data lives in local_data.json next to app.py. Demo mode uses its own
file (local_data_demo.json) so sample data never mixes with yours.
"""
import json
import os
import uuid
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    "weekly_goal": 5,
    "notes": "",
    "tasks": [],
    "contacts": [],
    "links": [],
}


def new_id():
    return uuid.uuid4().hex[:8]


def parse_day(text):
    """'2026-11-05' -> date, anything else -> None."""
    try:
        return date.fromisoformat(str(text or "").strip()[:10])
    except ValueError:
        return None


def sample_data():
    today = date.today()

    def d(n):
        return (today + timedelta(days=n)).isoformat()

    def item(**values):
        values["id"] = new_id()
        return values

    return {
        "weekly_goal": 5,
        "notes": "Ask about team size and the on-call schedule.\nUpdate the resume with the new project.",
        "tasks": [
            item(text="Apply to two new jobs", kind="Daily goal", due=d(0), related="", done=False),
            item(text="Send a follow-up email", kind="Follow-up", due=d(0),
                 related="Harbor Logistics", done=False),
            item(text="Review ticketing basics", kind="Interview prep", due=d(1),
                 related="Northwind Systems", done=False),
            item(text="Prepare questions to ask the interviewer", kind="Interview prep",
                 due=d(1), related="Northwind Systems", done=False),
            item(text="Update the resume with the new project", kind="Reminder", due="",
                 related="", done=False),
            item(text="Create a LinkedIn post about job hunting", kind="Reminder", due=d(-2),
                 related="", done=True),
        ],
        "contacts": [
            item(name="Ana Reyes", role="HR officer", company="Northwind Systems",
                 email="hr@northwind.example", phone="0917 000 0000",
                 last_contacted=d(-3), notes="Scheduled the online interview."),
            item(name="Mark Santos", role="Recruiter", company="Pinecrest Bank",
                 email="mark@pinecrest.example", phone="", last_contacted=d(-9),
                 notes="Will send the exam link."),
            item(name="Lia Cruz", role="Engineering manager", company="Lumen Labs",
                 email="", phone="", last_contacted="", notes="Referral contact."),
        ],
        "links": [
            item(label="Resume", url="https://example.com/resume"),
            item(label="Portfolio", url="https://example.com/portfolio"),
            item(label="Jobstreet", url="https://www.jobstreet.com.ph"),
            item(label="Cover letters", url="C:\\Users\\me\\Documents\\cover-letters"),
        ],
    }


class LocalStore(object):
    def __init__(self, demo=False):
        name = "local_data_demo.json" if demo else "local_data.json"
        self.path = os.path.join(HERE, name)
        if demo and not os.path.exists(self.path):
            self.save(sample_data())

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        out = {}
        for key, default in DEFAULTS.items():
            value = data.get(key, default)
            if not isinstance(value, type(default)):
                value = default
            out[key] = list(value) if isinstance(value, list) else value
        return out

    def save(self, data):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    def set(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)

    def add(self, key, item):
        return self.add_many(key, [item])[0]

    def add_many(self, key, items):
        data = self.load()
        added = []
        for item in items:
            item = dict(item)
            item["id"] = new_id()
            data[key].append(item)
            added.append(item)
        self.save(data)
        return added

    def update(self, key, item_id, values):
        data = self.load()
        for item in data[key]:
            if item.get("id") == item_id:
                item.update(values)
        self.save(data)

    def delete(self, key, item_id):
        data = self.load()
        data[key] = [i for i in data[key] if i.get("id") != item_id]
        self.save(data)