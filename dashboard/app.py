"""My Job Search Journal - Streamlit dashboard for the Notion job tracker.

Run from this folder:   streamlit run app.py
Try it with sample data: DASHBOARD_DEMO=1 streamlit run app.py
"""
import os
import re
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import find_dotenv, load_dotenv

import notion_store as ns
import theme

st.set_page_config(page_title="Unemployment Journey", layout="wide")

load_dotenv(find_dotenv(usecwd=True))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

SORTS = ["Date applied (newest)", "Date applied (oldest)",
         "Deadline (soonest)", "Company (A-Z)"]
TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})$")


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
        location = c1.text_input("Job location", value=rec["location"], key=k("location"))
        emp_type = c2.selectbox(
            "Employment type", emp_options, index=option_index(emp_options, rec["emp_type"]),
            format_func=lambda v: v or "Not set", key=k("emp"))
        salary = c1.text_input("Salary range", value=rec["salary"], key=k("salary"))
        source = c2.text_input("Source", value=rec["source"], key=k("source"),
                               placeholder="Jobstreet, LinkedIn, Referral")
        link = st.text_input("Job posting link", value=rec["link"], key=k("link"))

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
        notes = st.text_area("Personal remarks" if extended else "Notes",
                             value=rec["notes"], key=k("notes"))
        submitted = st.form_submit_button("Add application" if is_new else "Save changes")

    if not submitted:
        return None

    problems = []
    if not company.strip():
        problems.append("Enter a company name.")
    if not position.strip():
        problems.append("Enter the position you applied for.")
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
        "location": location.strip(), "emp_type": emp_type, "salary": salary.strip(),
        "source": source.strip(), "link": link.strip(), "notes": notes.strip(),
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


# ---------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown("### Journal settings")
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
    st.caption("Banner and profile pictures: put banner.jpg and avatar.png in "
               "the assets folder.")

# ----------------------------------------------------------------- header

quote = theme.QUOTES[today.toordinal() % len(theme.QUOTES)]
initials = os.getenv("DASHBOARD_INITIALS", "ME")[:3]
st.markdown(theme.CSS, unsafe_allow_html=True)
st.markdown(theme.header_html("Unemployment Journey", quote, urgent, initials),
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

tab_tracker, tab_board, tab_interviews = st.tabs(
    ["Applications", "Board", "Interviews and reminders"])

# ---------------------------------------------------------- applications

with tab_tracker:
    with st.expander("Add new application"):
        new_values = application_form("add", None, False)
        if new_values:
            if not new_values["date_applied"]:
                new_values["date_applied"] = today
            if new_values["status"] == "Applied" and not new_values["follow_up"]:
                new_values["follow_up"] = new_values["date_applied"] + timedelta(days=7)
            new_values["history"] = ns.append_history(
                "", "Added as %s" % new_values["status"])
            if run_write(backend.create, new_values,
                         success="Added %s." % new_values["company"]):
                rerun()

    f1, f2, f3 = st.columns([2, 2, 1.4])
    query = f1.text_input("Search", placeholder="Company, position, or location", key="search")
    status_filter = f2.multiselect("Filter by status", ns.STATUSES, key="status_filter")
    sort_by = f3.selectbox("Sort by", SORTS, key="sort_by")
    rows = filter_sort(records, query, status_filter, sort_by)

    st.markdown(theme.table_html(rows, today), unsafe_allow_html=True)
    st.caption("Showing %d of %d applications." % (len(rows), len(records)))

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
               "haven't applied to yet, and interviews.")
