"""My Job Search Journal - Streamlit dashboard for the Notion job tracker.

Run from this folder:   streamlit run app.py
Try it with sample data: DASHBOARD_DEMO=1 streamlit run app.py
"""
import os
import re
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import find_dotenv, load_dotenv

import analytics
import local_store
import notion_store as ns
import ph_locations
import theme

st.set_page_config(page_title="My Job Search Journal", layout="wide")

load_dotenv(find_dotenv(usecwd=True))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

SORTS = ["Date applied (newest)", "Date applied (oldest)",
         "Deadline (soonest)", "Company (A-Z)"]
TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})$")
TASK_KINDS = ["Daily goal", "Reminder", "Interview prep", "Follow-up"]
PREP_ITEMS = [
    "Research the company and its products",
    "Re-read the job posting and match it to your experience",
    "Prepare answers for common interview questions",
    "Prepare questions to ask the interviewer",
    "Print or save copies of your resume",
    "Test the meeting link or plan the route",
]


def rerun():
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()


# ------------------------------------------------------------------ data

@st.cache_resource
def get_backend():
    if os.getenv("DASHBOARD_DEMO") == "1":
        return ns.DemoBackend()
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("DATABASE_ID")
    if not token or not database_id:
        return None
    return ns.NotionBackend(token, database_id)


@st.cache_data(ttl=60, show_spinner="Loading your applications...")
def load_records(_backend, key):
    return _backend.records()


@st.cache_data(ttl=300)
def load_schema(_backend, key):
    return _backend.schema()


def run_write(action, *args, success=""):
    try:
        action(*args)
    except Exception as exc:  # show Notion's message instead of a stack trace
        st.error("Notion rejected the change: %s" % exc)
        return False
    load_records.clear()
    st.session_state["flash"] = success
    return True


backend = get_backend()
if backend is None:
    st.error(
        "Missing NOTION_TOKEN or DATABASE_ID. Add them to the .env file in your "
        "job-tracker folder, or run with DASHBOARD_DEMO=1 to try sample data."
    )
    st.stop()

try:
    records = load_records(backend, backend.key)
    schema = load_schema(backend, backend.key)
except Exception as exc:
    st.error("Couldn't load your database: %s" % exc)
    st.caption("Check that the Job Tracker connection is added to the database "
               "and that the token and database ID in .env are correct.")
    st.stop()

today = date.today()
by_id = {r["id"]: r for r in records}
store = local_store.LocalStore(backend.demo)
local = store.load()


def build_alerts():
    alerts = []
    week = today + timedelta(days=7)
    for r in records:
        if r["status"] in ns.CLOSED_STATUSES:
            continue
        if r["follow_up"] and r["follow_up"] <= week:
            alerts.append(("Follow up", r, r["follow_up"]))
        if r["deadline"] and r["status"] in ("Interested", "To Apply") \
                and today <= r["deadline"] <= week:
            alerts.append(("Application deadline", r, r["deadline"]))
        day = theme.interview_day(r)
        if day and today <= day <= week:
            alerts.append(("Interview", r, day))
    for task in local["tasks"]:
        day = local_store.parse_day(task.get("due"))
        if task.get("done") or not day or day > week:
            continue
        alerts.append(("Task", {"company": task.get("text", ""),
                                "position": task.get("related") or task.get("kind", "Task")}, day))
    alerts.sort(key=lambda a: a[2])
    return alerts


alerts = build_alerts()
urgent = len([a for a in alerts if (a[2] - today).days <= 3])


# ------------------------------------------------------------------ forms

def parse_time(text):
    match = TIME_PATTERN.match(text.strip())
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    return (hour, minute) if hour < 24 and minute < 60 else None


def option_index(options, value):
    return options.index(value) if value in options else 0


def location_options(current):
    options = [""] + ph_locations.LOCATIONS
    if current and current not in options:
        options.append(current)
    return options


def salary_options(*current):
    extra = sorted({v for v in current if v and v not in ns.SALARY_STEPS})
    return [None] + sorted(ns.SALARY_STEPS + extra)


def peso(value):
    return "Not set" if value is None else "PHP {:,}".format(value)


def clean_link(text):
    text = (text or "").strip()
    if text and not text.lower().startswith(("http://", "https://")):
        text = "https://" + text
    return text


def company_options(current=""):
    names = sorted({r["company"] for r in records if r["company"]}, key=str.lower)
    if current and current not in names:
        names.append(current)
    return [""] + names


def duplicate_note(company, position):
    dup = analytics.find_duplicate(records, company, position)
    if not dup:
        return ""
    return "You already have %s at %s in your journal (status: %s)." % (
        dup["position"], dup["company"], dup["status"])


def application_form(form_key, rec, extended):
    """Render the add/edit form. Returns the values when submitted and valid."""
    rec = rec or ns.blank_record()
    is_new = rec["id"] == ""

    def k(name):
        return "%s_%s" % (form_key, name)

    emp_options = [""] + ns.EMPLOYMENT_TYPES
    if rec["emp_type"] and rec["emp_type"] not in emp_options:
        emp_options.append(rec["emp_type"])
    iv_options = [""] + ns.INTERVIEW_TYPES
    if rec["interview_type"] and rec["interview_type"] not in iv_options:
        iv_options.append(rec["interview_type"])
    status_index = (ns.STATUSES.index(rec["status"]) if rec["status"] in ns.STATUSES
                    else ns.STATUSES.index("Applied"))

    with st.form(form_key, clear_on_submit=is_new):
        c1, c2 = st.columns(2)
        company = c1.text_input("Company name", value=rec["company"], key=k("company"))
        position = c2.text_input("Position applied for", value=rec["position"], key=k("position"))
        status = c1.selectbox("Status", ns.STATUSES, index=status_index, key=k("status"))
        date_applied = c2.date_input(
            "Date applied", value=rec["date_applied"] or (today if is_new else None),
            key=k("applied"))
        deadline = c1.date_input("Application deadline", value=rec["deadline"], key=k("deadline"))
        follow_up = c2.date_input("Follow-up date", value=rec["follow_up"], key=k("follow"))
        loc_opts = location_options(rec["location"])
        location = c1.selectbox(
            "Job location", loc_opts, index=option_index(loc_opts, rec["location"]),
            format_func=lambda v: v or "Not set", key=k("location"))
        location_other = c2.text_input("Other location (if not listed)", key=k("locother"))
        emp_type = c1.selectbox(
            "Employment type", emp_options, index=option_index(emp_options, rec["emp_type"]),
            format_func=lambda v: v or "Not set", key=k("emp"))
        source = c2.text_input("Source", value=rec["source"], key=k("source"),
                               placeholder="Jobstreet, LinkedIn, Referral")
        lo0, hi0 = ns.parse_salary(rec["salary"])
        sal_opts = salary_options(lo0, hi0)
        sal_min = c1.selectbox("Minimum salary (PHP per month)", sal_opts,
                               index=option_index(sal_opts, lo0), format_func=peso, key=k("smin"))
        sal_max = c2.selectbox("Maximum salary (PHP per month)", sal_opts,
                               index=option_index(sal_opts, hi0), format_func=peso, key=k("smax"))
        link = st.text_input("Job posting link (optional)", value=rec["link"], key=k("link"),
                             placeholder="https://")

        extra = {}
        if extended:
            d1, d2 = st.columns(2)
            extra["contact"] = d1.text_input("Contact person", value=rec["contact"], key=k("contact"))
            extra["email"] = d2.text_input("Contact email", value=rec["email"], key=k("email"))
            extra["resume"] = d1.text_input("Resume version submitted", value=rec["resume"], key=k("resume"))
            extra["cover"] = d2.text_input("Cover letter submitted", value=rec["cover"], key=k("cover"))
            iv_value = rec["interview"]
            iv_day = (iv_value.date() if hasattr(iv_value, "hour") else iv_value)
            iv_time = iv_value.strftime("%H:%M") if hasattr(iv_value, "hour") else ""
            iv_date = d1.date_input("Interview date", value=iv_day, key=k("ivdate"))
            iv_time_text = d2.text_input("Interview time (24-hour, like 14:30)", value=iv_time, key=k("ivtime"))
            extra["interview_type"] = d1.selectbox(
                "Interview type", iv_options, index=option_index(iv_options, rec["interview_type"]),
                format_func=lambda v: v or "Not set", key=k("ivtype"))
            extra["meeting"] = d2.text_input("Meeting link or location", value=rec["meeting"], key=k("meeting"))
            extra["prep"] = st.text_area("Preparation notes", value=rec["prep"], key=k("prep"))
            extra["interview_notes"] = st.text_area("Interview notes", value=rec["interview_notes"], key=k("ivnotes"))
            extra["assessment"] = st.text_area("Assessment results", value=rec["assessment"], key=k("assess"))
        notes = st.text_area("Personal remarks (optional)" if extended else "Notes (optional)",
                             value=rec["notes"], key=k("notes"))
        submitted = st.form_submit_button("Add application" if is_new else "Save changes")

    if not submitted:
        return None

    problems = []
    if not company.strip():
        problems.append("Enter a company name.")
    if not position.strip():
        problems.append("Enter the position you applied for.")
    if sal_min and sal_max and sal_max < sal_min:
        problems.append("The maximum salary can't be lower than the minimum.")
    interview = None
    if extended:
        if iv_time_text.strip() and not iv_date:
            problems.append("Pick an interview date to go with the time.")
        elif iv_date and iv_time_text.strip():
            parsed = parse_time(iv_time_text)
            if parsed is None:
                problems.append("Write the interview time as HH:MM, like 14:30.")
            else:
                interview = datetime(iv_date.year, iv_date.month, iv_date.day, parsed[0], parsed[1])
        elif iv_date:
            interview = iv_date
    if problems:
        for message in problems:
            st.error(message)
        return None

    values = {
        "company": company.strip(), "position": position.strip(), "status": status,
        "date_applied": date_applied, "deadline": deadline, "follow_up": follow_up,
        "location": (location_other.strip() or location),
        "emp_type": emp_type,
        "salary": (rec["salary"] if (sal_min, sal_max) == (lo0, hi0)
                   else ns.format_salary(sal_min, sal_max)),
        "source": source.strip(), "link": clean_link(link), "notes": notes.strip(),
    }
    if extended:
        values.update({k_: v.strip() if isinstance(v, str) else v for k_, v in extra.items()})
        values["interview"] = interview
    return values


def filter_sort(rows, query, statuses, sort_by):
    q = query.strip().lower()
    out = [
        r for r in rows
        if (not statuses or r["status"] in statuses)
        and (not q or q in " ".join([r["company"], r["position"], r["location"]]).lower())
    ]
    if sort_by == SORTS[0]:
        out.sort(key=lambda r: (r["date_applied"] is None,
                                -r["date_applied"].toordinal() if r["date_applied"] else 0))
    elif sort_by == SORTS[1]:
        out.sort(key=lambda r: (r["date_applied"] is None, r["date_applied"] or date.max))
    elif sort_by == SORTS[2]:
        out.sort(key=lambda r: (r["deadline"] is None, r["deadline"] or date.max))
    else:
        out.sort(key=lambda r: r["company"].lower())
    return out


def label_for(rec):
    return "%s - %s (%s)" % (rec["company"], rec["position"], rec["status"])


def change_status(rec, new_status, success):
    values = {"status": new_status,
              "history": ns.append_history(rec["history"], "Status: %s" % new_status)}
    return run_write(backend.update, rec["id"], values, success=success)


# ------------------------------------------------------------- add wizard

HAS_DIALOG = hasattr(st, "dialog")

WIZ_STEPS = [
    ("Basics", [("company", "wz_company"), ("position", "wz_position"),
                ("status", "wz_status"), ("link", "wz_link")]),
    ("Job details", [("location", "wz_location"), ("location_other", "wz_locother"),
                     ("emp_type", "wz_emp"), ("source", "wz_source"),
                     ("salary_min", "wz_smin"), ("salary_max", "wz_smax")]),
    ("Dates and notes", [("date_applied", "wz_applied"), ("deadline", "wz_deadline"),
                         ("follow_up", "wz_follow"), ("notes", "wz_notes")]),
    ("Review", []),
]
WIZ_LABELS = [name for name, _fields in WIZ_STEPS]


def prepare_new(values):
    """Fill in the defaults for a new application."""
    values = dict(values)
    values["date_applied"] = values.get("date_applied") or today
    if values["status"] == "Applied" and not values.get("follow_up"):
        values["follow_up"] = values["date_applied"] + timedelta(days=7)
    values["history"] = ns.append_history("", "Added as %s" % values["status"])
    return values


def wizard_values(data):
    def text(key):
        return str(data.get(key) or "").strip()

    return {
        "company": text("company"), "position": text("position"),
        "status": data.get("status") or "Applied", "link": clean_link(data.get("link")),
        "location": text("location_other") or text("location"),
        "emp_type": data.get("emp_type") or "",
        "salary": ns.format_salary(data.get("salary_min"), data.get("salary_max")),
        "source": text("source"),
        "date_applied": data.get("date_applied"), "deadline": data.get("deadline"),
        "follow_up": data.get("follow_up"), "notes": text("notes"),
    }


def wiz_reset():
    st.session_state["wiz"] = {"step": 0, "data": {}, "error": ""}


def wiz_collect():
    wiz = st.session_state["wiz"]
    for data_key, widget_key in WIZ_STEPS[wiz["step"]][1]:
        if widget_key in st.session_state:
            wiz["data"][data_key] = st.session_state[widget_key]


def wiz_next():
    wiz_collect()
    wiz = st.session_state["wiz"]
    if wiz["step"] == 0:
        data = wiz["data"]
        if not (str(data.get("company") or "").strip()
                and str(data.get("position") or "").strip()):
            wiz["error"] = "Enter the company name and the position before continuing."
            return
    if wiz["step"] == 1:
        lo, hi = wiz["data"].get("salary_min"), wiz["data"].get("salary_max")
        if lo and hi and hi < lo:
            wiz["error"] = "The maximum salary can't be lower than the minimum."
            return
    wiz["error"] = ""
    wiz["step"] = min(wiz["step"] + 1, len(WIZ_STEPS) - 1)


def wiz_back():
    wiz_collect()
    wiz = st.session_state["wiz"]
    wiz["error"] = ""
    wiz["step"] = max(wiz["step"] - 1, 0)


def wiz_submit():
    wiz = st.session_state["wiz"]
    values = prepare_new(wizard_values(wiz["data"]))
    try:
        backend.create(values)
    except Exception as exc:
        wiz["error"] = "Notion rejected the change: %s" % exc
        return
    load_records.clear()
    wiz["done"] = values


def render_wizard():
    if "wiz" not in st.session_state:
        wiz_reset()
    wiz = st.session_state["wiz"]

    if wiz.get("done"):
        st.success("Added %s to your journal." % wiz["done"]["company"])
        st.markdown(theme.review_html(wiz["done"]), unsafe_allow_html=True)
        d1, d2, _gap = st.columns([1.4, 1.2, 2.4])
        d1.button("Add another", key="wz_another", on_click=wiz_reset)
        if d2.button("Done", key="wz_done", type="primary"):
            wiz_reset()
            rerun()
        return

    step, data = wiz["step"], wiz["data"]
    last = len(WIZ_STEPS) - 1

    st.markdown(theme.steps_html(WIZ_LABELS, step), unsafe_allow_html=True)
    if wiz["error"]:
        st.error(wiz["error"])

    if step == 0:
        c1, c2 = st.columns(2)
        c1.text_input("Company name", value=data.get("company", ""), key="wz_company")
        c2.text_input("Position applied for", value=data.get("position", ""), key="wz_position")
        c1.selectbox("Status", ns.STATUSES, key="wz_status",
                     index=ns.STATUSES.index(data.get("status") or "Applied"))
        c2.text_input("Job posting link (optional)", value=data.get("link", ""), key="wz_link",
                      placeholder="https://")
    elif step == 1:
        emp_options = [""] + ns.EMPLOYMENT_TYPES
        loc_opts = location_options(data.get("location", ""))
        sal_opts = salary_options(data.get("salary_min"), data.get("salary_max"))
        c1, c2 = st.columns(2)
        c1.selectbox("Job location", loc_opts, key="wz_location",
                     index=option_index(loc_opts, data.get("location", "")),
                     format_func=lambda v: v or "Not set")
        c2.text_input("Other location (if not listed)",
                      value=data.get("location_other", ""), key="wz_locother")
        c1.selectbox("Employment type", emp_options, key="wz_emp",
                     index=option_index(emp_options, data.get("emp_type", "")),
                     format_func=lambda v: v or "Not set")
        c2.text_input("Source", value=data.get("source", ""), key="wz_source",
                      placeholder="Jobstreet, LinkedIn, Referral")
        c1.selectbox("Minimum salary (PHP per month)", sal_opts, key="wz_smin",
                     index=option_index(sal_opts, data.get("salary_min")), format_func=peso)
        c2.selectbox("Maximum salary (PHP per month)", sal_opts, key="wz_smax",
                     index=option_index(sal_opts, data.get("salary_max")), format_func=peso)
    elif step == 2:
        c1, c2 = st.columns(2)
        c1.date_input("Date applied", value=data.get("date_applied") or today, key="wz_applied")
        c2.date_input("Application deadline", value=data.get("deadline"), key="wz_deadline")
        c1.date_input("Follow-up date", value=data.get("follow_up"), key="wz_follow")
        if (data.get("status") or "Applied") == "Applied":
            c2.caption("Leave the follow-up date empty and it will be set to 7 days after you apply.")
        st.text_area("Notes (optional)", value=data.get("notes", ""), key="wz_notes")
    else:
        preview = prepare_new(wizard_values(data))
        note = duplicate_note(preview["company"], preview["position"])
        if note:
            st.warning(note + " You can still add it.")
        st.markdown(theme.review_html(preview), unsafe_allow_html=True)
        st.caption("Check the details, then add the application. Use Back to change anything.")

    b_cancel, _gap, b_back, b_next = st.columns([1.3, 2.4, 1, 1.5])
    if b_cancel.button("Cancel", key="wz_cancel"):
        wiz_reset()
        rerun()
    b_back.button("Back", key="wz_back", on_click=wiz_back, disabled=step == 0)
    if step < last:
        b_next.button("Next", key="wz_next", on_click=wiz_next, type="primary")
    else:
        b_next.button("Add application", key="wz_add", type="primary", on_click=wiz_submit)


if HAS_DIALOG:
    add_wizard = st.dialog("Add application", width="large")(render_wizard)


# ------------------------------------------- tasks, contacts, calendar

def toggle_task(task_id):
    store.update("tasks", task_id, {"done": bool(st.session_state.get("tk_%s" % task_id))})


def task_sort_key(task):
    day = local_store.parse_day(task.get("due"))
    return (day is None, day or date.max, task.get("text", "").lower())


def task_meta(task):
    parts = []
    day = local_store.parse_day(task.get("due"))
    if day and not task.get("done"):
        label, _late = theme.relative(day, today)
        parts.append("Due %s (%s)" % (day.strftime("%b %d"), label))
    elif day:
        parts.append("Due %s" % day.strftime("%b %d"))
    parts.append(task.get("kind") or "Task")
    if task.get("related"):
        parts.append(task["related"])
    return " | ".join(parts)


def contacted_today(contact_id):
    store.update("contacts", contact_id, {"last_contacted": today.isoformat()})
    st.session_state["flash"] = "Updated the last contacted date."


def contact_problem(name, email):
    if not name.strip():
        return "Enter the contact's name."
    if email.strip() and "@" not in email:
        return "That email address doesn't look right."
    return ""


def contact_label(contact):
    company = " (%s)" % contact["company"] if contact.get("company") else ""
    return "%s%s" % (contact.get("name", ""), company)


def cal_shift(step):
    year, month = st.session_state.get("cal_ym", (today.year, today.month))
    if step == 0:
        year, month = today.year, today.month
    else:
        year, month0 = divmod(year * 12 + (month - 1) + step, 12)
        month = month0 + 1
    st.session_state["cal_ym"] = (year, month)


week_count = analytics.applications_in_week(records, today)

# ---------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown("### Journal settings")
    getattr(st, "toggle", st.checkbox)("Dark mode", key="dark_mode")
    goal_input = st.number_input(
        "Weekly goal (applications)", min_value=0, max_value=200, step=1,
        value=int(local["weekly_goal"]), key="weekly_goal_input")
    if int(goal_input) != int(local["weekly_goal"]):
        store.set("weekly_goal", int(goal_input))
        local["weekly_goal"] = int(goal_input)
    if st.button("Refresh data"):
        load_records.clear()
        load_schema.clear()
        rerun()
    if backend.demo:
        st.info("Demo mode: sample data only. Nothing is saved to Notion.")
    missing = ns.missing_properties(schema)
    if missing:
        st.warning(
            "Your Notion database is missing %d properties used by this "
            "dashboard: %s. Run `python setup_notion.py` to add them. Until then, "
            "those fields are left blank and not saved." % (len(missing), ", ".join(missing)))

    st.markdown("### Quick links")
    st.markdown(theme.links_html(local["links"]), unsafe_allow_html=True)
    with st.expander("Add or remove links"):
        with st.form("add_link", clear_on_submit=True):
            link_label = st.text_input("Label", key="ql_label",
                                       placeholder="Resume, Portfolio, LinkedIn")
            link_target = st.text_input("Link or file path", key="ql_url",
                                        placeholder="https://")
            add_link = st.form_submit_button("Add link")
        if add_link:
            target = link_target.strip()
            if not link_label.strip() or not target:
                st.error("Enter a label and a link or file path.")
            else:
                if target.lower().startswith("www."):
                    target = "https://" + target
                store.add("links", {"label": link_label.strip(), "url": target})
                rerun()
        if local["links"]:
            link_names = {i["id"]: i.get("label", "") for i in local["links"]}
            remove_id = st.selectbox(
                "Remove a link", [None] + list(link_names), key="ql_remove",
                format_func=lambda i: "Choose a link" if i is None else link_names[i])
            if st.button("Remove link", key="ql_remove_btn") and remove_id:
                store.delete("links", remove_id)
                rerun()
        st.caption("Web links open in a new tab. File paths on your computer "
                   "can't be opened from the browser, so they show as text you can "
                   "copy. A Google Drive or OneDrive link works as a clickable shortcut.")
    st.caption("Banner and profile pictures: put banner.jpg and avatar.png in "
               "the assets folder.")

# ----------------------------------------------------------------- header

quote = theme.QUOTES[today.toordinal() % len(theme.QUOTES)]
initials = os.getenv("DASHBOARD_INITIALS", "ME")[:3]
st.markdown(theme.css(st.session_state.get("dark_mode", False)), unsafe_allow_html=True)
st.markdown(theme.header_html("My Job Search Journal", quote, urgent, initials),
            unsafe_allow_html=True)

flash = st.session_state.pop("flash", "")
if flash:
    st.success(flash)

st.markdown(theme.stats_html([
    ("Total applications", len(records), "Everything in your journal", "list"),
    ("Pending applications", len([r for r in records if r["status"] in ns.PENDING_STATUSES]),
     "Waiting for a reply", "clock"),
    ("Interviews scheduled", len([r for r in records if r["status"] in ns.INTERVIEW_STATUSES]),
     "Interview rounds in progress", "calendar"),
    ("Job offers received", len([r for r in records if r["status"] == "Offered"]),
     "Offers on the table", "check"),
]), unsafe_allow_html=True)

goal_block = theme.goal_html(week_count, int(local["weekly_goal"]))
if goal_block:
    st.markdown(goal_block, unsafe_allow_html=True)

(tab_tracker, tab_board, tab_calendar, tab_interviews,
 tab_tasks, tab_contacts, tab_insights) = st.tabs(
    ["Applications", "Board", "Calendar", "Interviews and reminders",
     "Tasks and notes", "Contacts", "Insights"])

# ---------------------------------------------------------- applications

with tab_tracker:
    if HAS_DIALOG:
        if st.button("Add application", key="open_wizard", type="primary"):
            wiz_reset()
            add_wizard()
    else:
        with st.expander("Add new application"):
            new_values = application_form("add", None, False)
            if new_values:
                new_values = prepare_new(new_values)
                success = "Added %s." % new_values["company"]
                note = duplicate_note(new_values["company"], new_values["position"])
                if note:
                    success += " Note: " + note
                if run_write(backend.create, new_values, success=success):
                    rerun()

    f1, f2, f3 = st.columns([2, 2, 1.4])
    query = f1.text_input("Search", placeholder="Company, position, or location", key="search")
    status_filter = f2.multiselect("Filter by status", ns.STATUSES, key="status_filter")
    sort_by = f3.selectbox("Sort by", SORTS, key="sort_by")
    rows = filter_sort(records, query, status_filter, sort_by)

    st.markdown(theme.table_html(rows, today), unsafe_allow_html=True)
    st.caption("Showing %d of %d applications." % (len(rows), len(records)))
    st.download_button(
        "Download CSV (%d rows)" % len(rows),
        data=analytics.to_csv(rows).encode("utf-8-sig"),
        file_name="job-applications-%s.csv" % today.isoformat(),
        mime="text/csv", key="csv_download", disabled=not rows)

    options = [None] + [r["id"] for r in rows]
    if st.session_state.get("selected_id") not in options:
        st.session_state["selected_id"] = None
    selected_id = st.selectbox(
        "Open an application", options, key="selected_id",
        format_func=lambda i: "Choose an application" if i is None else label_for(by_id[i]))

    if selected_id:
        rec = by_id[selected_id]
        st.markdown(theme.detail_html(rec), unsafe_allow_html=True)

        s1, s2 = st.columns([3, 1])
        new_status = s1.selectbox(
            "Change status", ns.STATUSES, key="qs_%s" % rec["id"],
            index=option_index(ns.STATUSES, rec["status"]))
        s2.write("")
        s2.write("")
        if s2.button("Update status", key="qsb_%s" % rec["id"]):
            if new_status == rec["status"]:
                st.info("That's already the current status.")
            elif change_status(rec, new_status, "%s is now %s." % (rec["company"], new_status)):
                rerun()

        with st.expander("Edit application"):
            edited = application_form("edit_%s" % rec["id"], rec, True)
            if edited:
                if edited["status"] != rec["status"]:
                    edited["history"] = ns.append_history(
                        rec["history"], "Status: %s" % edited["status"])
                if run_write(backend.update, rec["id"], edited,
                             success="Saved changes to %s." % edited["company"]):
                    rerun()

        with st.expander("Delete application"):
            st.write("Deleting archives the page in Notion. You can restore it "
                     "from Notion's trash.")
            confirm = st.checkbox("Yes, delete this application", key="del_ck_%s" % rec["id"])
            if st.button("Delete application", key="del_%s" % rec["id"]):
                if not confirm:
                    st.warning("Tick the box to confirm the deletion.")
                elif run_write(backend.archive, rec["id"],
                               success="Deleted %s." % rec["company"]):
                    rerun()

# ------------------------------------------------------------------ board

with tab_board:
    st.markdown(theme.board_html(records), unsafe_allow_html=True)
    st.write("")
    if records:
        m1, m2, m3 = st.columns([3, 2, 1])
        move_id = m1.selectbox("Move an application", [r["id"] for r in records],
                               format_func=lambda i: label_for(by_id[i]), key="move_id")
        column_names = [name for name, _s in ns.KANBAN]
        target = m2.selectbox("To column", column_names, key="move_to")
        m3.write("")
        m3.write("")
        if m3.button("Move", key="move_btn"):
            rec = by_id[move_id]
            column_statuses = dict(ns.KANBAN)[target]
            if rec["status"] in column_statuses:
                st.info("%s is already in %s." % (rec["company"], target))
            elif change_status(rec, column_statuses[0],
                               "Moved %s to %s." % (rec["company"], target)):
                rerun()
        st.caption("Each column sets a default status when you move a card. "
                   "Use the Applications tab for finer statuses like Under Review.")
    else:
        st.info("Add your first application to see it on the board.")

# --------------------------------------------------------------- calendar

with tab_calendar:
    if "cal_ym" not in st.session_state:
        st.session_state["cal_ym"] = (today.year, today.month)
    cal_year, cal_month = st.session_state["cal_ym"]
    n1, n2, n3, n4 = st.columns([1, 1, 1, 4])
    n1.button("Previous", key="cal_prev", on_click=cal_shift, args=(-1,))
    n2.button("Today", key="cal_today", on_click=cal_shift, args=(0,))
    n3.button("Next", key="cal_next", on_click=cal_shift, args=(1,))
    n4.markdown("#### %s" % date(cal_year, cal_month, 1).strftime("%B %Y"))

    cal_events = analytics.calendar_events(records, local["tasks"])
    st.markdown(theme.legend_html(), unsafe_allow_html=True)
    st.markdown(theme.calendar_html(cal_year, cal_month, cal_events, today),
                unsafe_allow_html=True)
    st.markdown("#### Scheduled this month")
    st.markdown(theme.events_list_html(cal_events, cal_year, cal_month, today),
                unsafe_allow_html=True)
    st.caption("Shows deadlines, follow-ups, interviews and open tasks with a due date. "
               "An application with the Assessment status uses its Interview Date "
               "as the assessment date.")

# ------------------------------------------------------------- interviews

with tab_interviews:
    upcoming = sorted(
        [r for r in records if theme.interview_day(r) and theme.interview_day(r) >= today
         and r["status"] not in ("Rejected", "Withdrawn")],
        key=lambda r: (theme.interview_day(r), str(r["interview"])))
    st.markdown("#### Upcoming interviews")
    st.markdown(theme.interviews_html(upcoming, today), unsafe_allow_html=True)
    st.markdown("#### Reminders for the next 7 days")
    st.markdown(theme.reminders_html(alerts, today), unsafe_allow_html=True)
    st.caption("Reminders cover follow-ups, application deadlines for jobs you "
               "haven't applied to yet, interviews, and tasks that are due or overdue.")

# ------------------------------------------------------------------ tasks

with tab_tasks:
    tasks = local["tasks"]
    tasks_by_id = {t["id"]: t for t in tasks}
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### Tasks")
        with st.form("add_task", clear_on_submit=True):
            t1, t2 = st.columns([3, 1.4])
            task_text = t1.text_input("New task", key="nt_text",
                                      placeholder="Prepare answers for the interview")
            task_kind = t2.selectbox("Type", TASK_KINDS, key="nt_kind")
            t3, t4 = st.columns(2)
            task_due = t3.date_input("Due date (optional)", value=None, key="nt_due")
            task_related = t4.selectbox("Related application (optional)", company_options(""),
                                        format_func=lambda v: v or "None", key="nt_related")
            add_task = st.form_submit_button("Add task")
        if add_task:
            if not task_text.strip():
                st.error("Write the task first.")
            else:
                due = task_due or (today if task_kind == "Daily goal" else None)
                store.add("tasks", {
                    "text": task_text.strip(), "kind": task_kind,
                    "due": due.isoformat() if due else "",
                    "related": task_related, "done": False})
                st.session_state["flash"] = "Task added."
                rerun()
        st.caption("A daily goal with no due date is set for today.")

        open_tasks = sorted([t for t in tasks if not t.get("done")], key=task_sort_key)
        done_tasks = sorted([t for t in tasks if t.get("done")], key=task_sort_key)
        if not open_tasks:
            st.info("No open tasks. Add one above.")
        for t in open_tasks:
            st.checkbox(t.get("text", ""), value=False, key="tk_%s" % t["id"],
                        on_change=toggle_task, args=(t["id"],))
            st.caption(task_meta(t))
        if done_tasks:
            with st.expander("Completed (%d)" % len(done_tasks)):
                for t in done_tasks:
                    st.checkbox(t.get("text", ""), value=True, key="tk_%s" % t["id"],
                                on_change=toggle_task, args=(t["id"],))
                    st.caption(task_meta(t))

        task_ids = [None] + [t["id"] for t in sorted(tasks, key=task_sort_key)]
        if st.session_state.get("edit_task_id") not in task_ids:
            st.session_state["edit_task_id"] = None
        edit_id = st.selectbox(
            "Edit a task", task_ids, key="edit_task_id",
            format_func=lambda i: "Choose a task" if i is None else tasks_by_id[i].get("text", ""))
        if edit_id:
            task = tasks_by_id[edit_id]
            kind_opts = list(TASK_KINDS)
            if task.get("kind") and task["kind"] not in kind_opts:
                kind_opts.append(task["kind"])
            rel_opts = company_options(task.get("related", ""))
            with st.form("edit_task_%s" % edit_id):
                e1, e2 = st.columns([3, 1.4])
                new_text = e1.text_input("Task", value=task.get("text", ""), key="et_text_%s" % edit_id)
                new_kind = e2.selectbox("Type", kind_opts, key="et_kind_%s" % edit_id,
                                        index=option_index(kind_opts, task.get("kind")))
                e3, e4 = st.columns(2)
                new_due = e3.date_input("Due date", value=local_store.parse_day(task.get("due")),
                                        key="et_due_%s" % edit_id)
                new_related = e4.selectbox(
                    "Related application", rel_opts, key="et_rel_%s" % edit_id,
                    index=option_index(rel_opts, task.get("related", "")),
                    format_func=lambda v: v or "None")
                b1, b2 = st.columns(2)
                save_task = b1.form_submit_button("Save task")
                delete_task = b2.form_submit_button("Delete task")
            if save_task:
                if not new_text.strip():
                    st.error("The task can't be empty.")
                else:
                    store.update("tasks", edit_id, {
                        "text": new_text.strip(), "kind": new_kind,
                        "due": new_due.isoformat() if new_due else "",
                        "related": new_related})
                    st.session_state["flash"] = "Saved the task."
                    rerun()
            if delete_task:
                store.delete("tasks", edit_id)
                st.session_state["flash"] = "Deleted the task."
                rerun()

    with right:
        st.markdown("#### Quick notes")
        note_text = st.text_area("Notes", value=local["notes"], height=170,
                                 key="quick_notes", label_visibility="collapsed")
        if st.button("Save notes", key="save_notes"):
            store.set("notes", note_text)
            st.session_state["flash"] = "Notes saved."
            rerun()

        st.markdown("#### Interview prep checklist")
        prep_apps = sorted(
            [r for r in records if r["status"] not in ns.CLOSED_STATUSES],
            key=lambda r: (r["status"] not in ns.INTERVIEW_STATUSES, r["company"].lower()))
        if prep_apps:
            prep_id = st.selectbox("Application", [r["id"] for r in prep_apps], key="prep_app",
                                   format_func=lambda i: label_for(by_id[i]))
            if st.button("Add prep checklist", key="prep_btn"):
                rec = by_id[prep_id]
                have = {(t.get("text"), t.get("related", "")) for t in tasks}
                day = theme.interview_day(rec)
                new_items = [
                    {"text": item, "kind": "Interview prep",
                     "due": day.isoformat() if day else "",
                     "related": rec["company"], "done": False}
                    for item in PREP_ITEMS if (item, rec["company"]) not in have]
                if new_items:
                    store.add_many("tasks", new_items)
                    st.session_state["flash"] = "Added %d prep tasks for %s." % (
                        len(new_items), rec["company"])
                else:
                    st.session_state["flash"] = "%s already has the prep checklist." % rec["company"]
                rerun()
            st.caption("The tasks are due on the interview date when one is set.")
        else:
            st.caption("Add an open application to build a prep checklist for it.")

# --------------------------------------------------------------- contacts

with tab_contacts:
    contacts = local["contacts"]
    contacts_by_id = {c["id"]: c for c in contacts}
    st.markdown(theme.contacts_html(contacts, today), unsafe_allow_html=True)
    st.caption("People you have not contacted yet or longest ago are listed first.")

    with st.expander("Add a contact"):
        with st.form("add_contact", clear_on_submit=True):
            a1, a2 = st.columns(2)
            c_name = a1.text_input("Name", key="nc_name")
            c_role = a2.text_input("Role or title", key="nc_role",
                                   placeholder="Recruiter, HR, Hiring manager")
            c_company = a1.text_input("Company", key="nc_company")
            c_email = a2.text_input("Email", key="nc_email")
            c_phone = a1.text_input("Phone", key="nc_phone")
            c_last = a2.date_input("Last contacted", value=today, key="nc_last")
            c_notes = st.text_area("Notes", key="nc_notes")
            add_contact = st.form_submit_button("Add contact")
        if add_contact:
            problem = contact_problem(c_name, c_email)
            if problem:
                st.error(problem)
            else:
                store.add("contacts", {
                    "name": c_name.strip(), "role": c_role.strip(), "company": c_company.strip(),
                    "email": c_email.strip(), "phone": c_phone.strip(),
                    "last_contacted": c_last.isoformat() if c_last else "",
                    "notes": c_notes.strip()})
                st.session_state["flash"] = "Added %s to your contacts." % c_name.strip()
                rerun()

    contact_ids = [None] + [c["id"] for c in sorted(contacts, key=lambda c: c.get("name", "").lower())]
    if st.session_state.get("edit_contact_id") not in contact_ids:
        st.session_state["edit_contact_id"] = None
    edit_contact_id = st.selectbox(
        "Edit a contact", contact_ids, key="edit_contact_id",
        format_func=lambda i: "Choose a contact" if i is None else contact_label(contacts_by_id[i]))
    if edit_contact_id:
        contact = contacts_by_id[edit_contact_id]
        st.button("Contacted today", key="ct_today_%s" % edit_contact_id,
                  on_click=contacted_today, args=(edit_contact_id,))
        with st.form("edit_contact_%s" % edit_contact_id):
            x1, x2 = st.columns(2)
            n_name = x1.text_input("Name", value=contact.get("name", ""),
                                   key="ec_name_%s" % edit_contact_id)
            n_role = x2.text_input("Role or title", value=contact.get("role", ""),
                                   key="ec_role_%s" % edit_contact_id)
            n_company = x1.text_input("Company", value=contact.get("company", ""),
                                      key="ec_company_%s" % edit_contact_id)
            n_email = x2.text_input("Email", value=contact.get("email", ""),
                                    key="ec_email_%s" % edit_contact_id)
            n_phone = x1.text_input("Phone", value=contact.get("phone", ""),
                                    key="ec_phone_%s" % edit_contact_id)
            n_last = x2.date_input("Last contacted",
                                   value=local_store.parse_day(contact.get("last_contacted")),
                                   key="ec_last_%s" % edit_contact_id)
            n_notes = st.text_area("Notes", value=contact.get("notes", ""),
                                   key="ec_notes_%s" % edit_contact_id)
            y1, y2 = st.columns(2)
            save_contact = y1.form_submit_button("Save contact")
            delete_contact = y2.form_submit_button("Delete contact")
        if save_contact:
            problem = contact_problem(n_name, n_email)
            if problem:
                st.error(problem)
            else:
                store.update("contacts", edit_contact_id, {
                    "name": n_name.strip(), "role": n_role.strip(), "company": n_company.strip(),
                    "email": n_email.strip(), "phone": n_phone.strip(),
                    "last_contacted": n_last.isoformat() if n_last else "",
                    "notes": n_notes.strip()})
                st.session_state["flash"] = "Saved %s." % n_name.strip()
                rerun()
        if delete_contact:
            store.delete("contacts", edit_contact_id)
            st.session_state["flash"] = "Deleted %s." % contact.get("name", "the contact")
            rerun()

# --------------------------------------------------------------- insights

with tab_insights:
    sent, heard = analytics.response_totals(records)
    rate = int(round(100.0 * heard / sent)) if sent else 0
    avg_days, avg_n = analytics.average_days_to_response(records)
    goal = int(local["weekly_goal"])
    st.markdown(theme.stats_html([
        ("Applied this week", week_count,
         "Goal: %d" % goal if goal else "Set a goal in the sidebar", "list"),
        ("Response rate", "%d%%" % rate, "%d of %d applications heard back" % (heard, sent), "check"),
        ("Days to hear back", "%.1f" % avg_days if avg_days is not None else "-",
         "Average, from %d applications" % avg_n if avg_n else "Not enough history yet", "clock"),
    ]), unsafe_allow_html=True)

    weekly = analytics.weekly_counts(records, today)
    st.markdown(theme.bars_html(
        "Applications per week (last 8 weeks)",
        [(label, n, str(n)) for label, n in weekly] if any(n for _l, n in weekly) else [],
        empty="No applications with a date applied yet."), unsafe_allow_html=True)

    source_rows = analytics.response_by_source(records)
    st.markdown(theme.bars_html(
        "Response rate by source",
        [(name, pct, "%d%% (%d/%d)" % (pct, got, applied))
         for name, applied, got, pct in source_rows],
        max_value=100, empty="Applications you have sent will appear here."),
        unsafe_allow_html=True)
    st.caption("A reply means the status moved past Applied (for example Under Review, "
               "an interview, or a rejection). Days to hear back come from the status "
               "history, so older applications without history are left out.")