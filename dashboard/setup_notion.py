"""Adds the properties and status options the dashboard needs to your Notion
database. Existing rows and properties are left alone.

Run from this folder:   python setup_notion.py
"""
import os
import sys

from dotenv import find_dotenv, load_dotenv
from notion_client import Client

import notion_store as ns

load_dotenv(find_dotenv(usecwd=True))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
if not TOKEN or not DATABASE_ID:
    sys.exit("Missing NOTION_TOKEN or DATABASE_ID in your .env file.")

client = Client(auth=TOKEN, notion_version="2022-06-28")
path = "databases/%s" % DATABASE_ID

SELECT_OPTIONS = {
    "Employment Type": ns.EMPLOYMENT_TYPES,
    "Interview Type": ns.INTERVIEW_TYPES,
}


def definition(name, kind):
    if kind == "select":
        options = [{"name": n} for n in SELECT_OPTIONS.get(name, [])]
        return {"select": {"options": options}}
    return {notion_type: {} for notion_type in [ns.notion_type(kind)]}


database = client.request(path=path, method="GET")
existing = database.get("properties", {})

to_add = {}
for name, _key, kind in ns.FIELDS:
    if name not in existing:
        to_add[name] = definition(name, kind)
    elif existing[name].get("type") != ns.notion_type(kind):
        print("Skipping %s: it exists as a %s property, but the dashboard "
              "expects %s. Rename or delete it in Notion, then run this again."
              % (name, existing[name].get("type"), ns.notion_type(kind)))

status = existing.get("Status")
new_statuses = []
if status and status.get("type") == "select":
    current = status["select"].get("options", [])
    names = {o["name"] for o in current}
    new_statuses = [s for s in ns.STATUSES if s not in names]
    if new_statuses:
        to_add["Status"] = {"select": {"options": current + [{"name": s} for s in new_statuses]}}

if not to_add:
    print("Your database already has everything the dashboard needs.")
    sys.exit(0)

print("This will change your Notion database:")
for name, spec in to_add.items():
    if name == "Status":
        print("  Status: add options %s" % ", ".join(new_statuses))
    else:
        print("  Add property %s (%s)" % (name, list(spec)[0]))

if input("Continue? (y/n) ").strip().lower() != "y":
    sys.exit("No changes made.")

client.request(path=path, method="PATCH", body={"properties": to_add})
print("Done. Refresh the dashboard to see the new fields.")
