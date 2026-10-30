import argparse
import os
import re
import sys
from datetime import date

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

load_dotenv()
TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

if not TOKEN or not DATABASE_ID:
    sys.exit("Missing NOTION_TOKEN or DATABASE_ID in your .env file.")

notion = Client(auth=TOKEN, notion_version="2022-06-28")

STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected"]


def plain(prop, key):
    """Join the text pieces of a title or rich_text property."""
    return "".join(piece["plain_text"] for piece in prop.get(key, []))


def query_database(body=None):
    """Query the database and return the list of result pages."""
    result = notion.request(
        path=f"databases/{DATABASE_ID}/query", method="POST", body=body or {}
    )
    return result["results"]


def add_job(company, position, status, source, link):
    props = {
        "Company": {"title": [{"text": {"content": company}}]},
        "Position": {"rich_text": [{"text": {"content": position}}]},
        "Status": {"select": {"name": status}},
        "Date Applied": {"date": {"start": date.today().isoformat()}},
    }
    if source:
        props["Source"] = {"select": {"name": source}}
    if link:
        props["Link"] = {"url": link}

    page = notion.pages.create(parent={"database_id": DATABASE_ID}, properties=props)
    print(f"Added: {company} - {position}")
    print(f"Page ID: {page['id']}")


def list_jobs(status=None):
    body = {}
    if status:
        body["filter"] = {"property": "Status", "select": {"equals": status}}

    pages = query_database(body)

    if not pages:
        print("No matching applications.")
        return

    for page in pages:
        p = page["properties"]
        company = plain(p["Company"], "title") or "(no name)"
        position = plain(p["Position"], "rich_text")
        current = (p["Status"]["select"] or {}).get("name", "-")
        print(f"{company} | {position} | {current} | {page['id']}")


def looks_like_id(text):
    """True if the text looks like a Notion page ID (32 hex characters)."""
    return bool(re.fullmatch(r"[0-9a-fA-F]{32}", text.replace("-", "")))


def find_by_company(name):
    """Return all pages whose Company contains the given text."""
    body = {"filter": {"property": "Company", "title": {"contains": name}}}
    pages = query_database(body)

    # Prefer an exact (case-insensitive) match if there is exactly one
    exact = [
        p for p in pages
        if plain(p["properties"]["Company"], "title").lower() == name.lower()
    ]
    return exact if len(exact) == 1 else pages


def update_status(target, new_status):
    page_id = target

    if not looks_like_id(target):
        matches = find_by_company(target)

        if not matches:
            sys.exit(f"No application found for '{target}'.")

        if len(matches) > 1:
            print(f"Multiple matches for '{target}'. Re-run with a page ID:")
            for page in matches:
                p = page["properties"]
                print(f"  {plain(p['Company'], 'title')} | "
                      f"{plain(p['Position'], 'rich_text')} | {page['id']}")
            sys.exit(1)

        page_id = matches[0]["id"]

    notion.pages.update(
        page_id=page_id,
        properties={"Status": {"select": {"name": new_status}}},
    )
    print(f"Status updated to {new_status}.")


def main():
    parser = argparse.ArgumentParser(description="Job tracker for Notion")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a job application")
    add.add_argument("company")
    add.add_argument("position")
    add.add_argument("--status", default="Applied", choices=STATUSES)
    add.add_argument("--source")
    add.add_argument("--link")

    ls = sub.add_parser("list", help="List applications")
    ls.add_argument("--status", choices=STATUSES)

    upd = sub.add_parser("update", help="Update an application's status")
    upd.add_argument("target", help="Company name or page ID") 
    upd.add_argument("status", choices=STATUSES)

    args = parser.parse_args()

    try:
        if args.command == "add":
            add_job(args.company, args.position, args.status, args.source, args.link)
        elif args.command == "list":
            list_jobs(args.status)
        elif args.command == "update":
            update_status(args.target, args.status)
    except APIResponseError as err:
        sys.exit(f"Notion API error: {err}")


if __name__ == "__main__":
    main() 