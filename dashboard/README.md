# Job search dashboard

A Streamlit dashboard for the Notion job tracker.

## Setup
1. Copy this `dashboard` folder into your `job-tracker` project.
2. Activate your virtual environment and install: `pip install streamlit`
3. Add the missing Notion properties: `python setup_notion.py`
4. Start the dashboard: `streamlit run app.py`

Try it with sample data first: `DASHBOARD_DEMO=1 streamlit run app.py`
(On Windows Command Prompt: `set DASHBOARD_DEMO=1` then `streamlit run app.py`.)

The dashboard reads NOTION_TOKEN and DATABASE_ID from the `.env` file in your
job-tracker folder. Run it on your own computer only: it shows your job search
data and uses your Notion token.
