# Notion Job Tracker Setup Guide (2-Minute Setup)

Your Notion API key (`ntn_...`) is already configured in `.env`. Follow these quick steps in Notion to connect your job applications database:

---

## Step 1: Create a Job Tracker Database in Notion

1. In your Notion workspace, create a new page and select **Table** or **Board** (Kanban).
2. Set up the following columns (properties):

| Property Name | Property Type | Options / Notes |
| :--- | :--- | :--- |
| **Company** | `Title` | Primary identifier (e.g. *Jobs for Humanity*, *Wynd Labs*) |
| **Role** | `Text` | Job title (e.g. *Full-Stack AI/ML Application Engineer*) |
| **Location** | `Text` or `Select` | City / Country (e.g. *Dammam, Saudi Arabia*, *Remote*) |
| **Status** | `Select` or `Status` | `To Apply`, `Applied`, `Screening`, `Interview`, `Offer`, `Rejected` |
| **Fit Score** | `Text` or `Select` | e.g. `95% (High)`, `90% (High)` |
| **URL** | `URL` | Direct apply link |
| **Date Added** | `Date` | Date discovered / applied |
| **Notes** | `Text` | Key requirements, match highlights, folder path |

---

## Step 2: Share the Database with Your Integration (Critical Step)

By default, Notion keeps new integrations completely private until you give them access to a page or database:

1. Open your Job Tracker database page in Notion.
2. In the top right corner, click the **`...`** (three dots) menu or the **Share** button.
3. Scroll down to **Connections** (or **Add connections**).
4. Search for your integration name (the one associated with your `ntn_...` token) and click **Confirm / Connect**.

---

## Step 3: Copy Your Database ID

1. In your browser or Notion app, click **Share ➔ Copy link** on the database.
2. The URL looks like this:
   ```text
   https://www.notion.so/myworkspace/32_CHARACTER_DATABASE_ID?v=...
   ```
3. Copy the 32-character string between the last slash and the question mark (`?v=`).
4. Paste it into your [`.env`](file:///c:/Users/lords/OneDrive/Documents/resume/.env) file:
   ```bash
   NOTION_DATABASE_ID=your_32_character_database_id_here
   ```

---

## Step 4: Run the Sync

Whenever you want to sync your tracker table into Notion, simply ask Antigravity:
> *"Sync my applications to Notion"*

Or run the script in your terminal:
```powershell
python scripts/sync_to_notion.py
```

All rows from [active_application_tracker.md](file:///c:/Users/lords/OneDrive/Documents/resume/job_research/active_application_tracker.md) will instantly populate into your Notion Kanban board!
