# Job Tracker (Python + Notion)

A command-line tool that logs and manages job applications in a Notion database using the Notion API.

## Features
- Add applications with company, position, source, and link
- List all applications or filter by status
- Update an application's status by company name or page ID

## Setup
1. Create a Notion database named "Job Applications" with these properties:
   Company (Title), Position (Text), Status (Select), Date Applied (Date),
   Source (Select), Link (URL), Follow-up Date (Date), Notes (Text)
2. Create an internal connection at notion.so/my-integrations and add it to the database.
3. Install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Create a `.env` file:
   ```
   NOTION_TOKEN=your_token
   DATABASE_ID=your_database_id
   ```

## Usage
```
python tracker.py add "Acme Corp" "IT Support" --source Jobstreet
python tracker.py list
python tracker.py list --status Interview
python tracker.py update "Acme Corp" Interview
```

## Tech
Python, Notion API, notion-client, python-dotenv, argparse