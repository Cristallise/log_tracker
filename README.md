# Flow Logger

Flow Logger is a personal activity tracker that captures what you’re doing in the moment with minimal friction.  
Instead of relying on memory, you log quick entries as you work, switch tasks, or take breaks.  

The goal: see your flows over time — not just to-do lists, but the real paths of attention across tasks, apps, and contexts.

---

## Core Concepts

**Entry**  
Every log line is an entry written to a CSV file (`flow_log.csv`).  
Each entry records:  
- **log_id** – unique UUID for the entry  
- **timestamp** – when the entry was made (ISO-8601 with timezone)  
- **event** – one of:  
  - `start` = beginning a new task/session  
  - `stop` = ending a task/session  
  - `note` = a quick breadcrumb without starting/stopping  
- **session_id** – UUID linking related entries (blank if standalone note)  
- **action_note** – what you typed in the popup  
- **tags** – optional keywords (comma-separated, chosen from quick checkboxes or typed)  
- **app_name** – active app (e.g., Chrome, Obsidian)  
- **window_title** – active window/tab title  
- **url** – active page URL (blank if not available)  
- **schema_version** – current schema version (v1)  

**Session**  
A session = a block of focused activity, started by a `start` entry and ended by a `stop` entry.  
- All entries in a session share the same `session_id`.  
- Notes inside a session attach to it.  
- Sessions let you measure blocks of time.  

**Notes**  
Notes are lightweight log entries that do not start or stop sessions by default.  
- If a session is open: note attaches to it.  
- If no session is open: note is standalone.  
- Option: checkbox to “Make this note a new session start.”  

---

## Popup Behavior

- Opened with a global hotkey (`Ctrl+Alt+L` on Windows/Linux, `Cmd+Opt+L` on macOS).  
- Fields shown:  
  - Text field: “What are you doing?”  
  - Quick tag checkboxes (lookup, chat, planning, admin, family — customizable)  
  - Context (auto-captured app name, window title, URL if available)  
- If a previous session is open:  
  - Banner: “Previous session open (Started HH:MM • Elapsed XXm)”  
  - Checkbox (checked by default): “Stop that session when I save.”  

---

## Examples

- **Start a new session**  
  Event: `start`  
  Session ID: `abc123`  
  Action note: Grant outline  
  Tags: planning  

- **Note inside a session**  
  Event: `note`  
  Session ID: `abc123`  
  Action note: Looked up somatics  
  Tags: lookup  

- **Stop a session**  
  Event: `stop`  
  Session ID: `abc123`  
  Action note: Wrapping up  

- **Standalone note**  
  Event: `note`  
  Session ID: (blank)  
  Action note: Kid interruption  

---

## Why Flow Logger?

- **Self-awareness**: See where your attention actually goes.  
- **Pattern discovery**: Summaries show top tags, apps, and flows.  
- **Context memory**: Notes act like breadcrumbs to reconstruct your day.  
- **Portable**: CSV format → import into Obsidian, spreadsheets, dashboards.  

---

## Installation and Usage (v1)

1. Install dependencies: run `pip install -r requirements.txt`  
2. Run the logger: run `python flow_logger.py`  
3. Press hotkey (`Ctrl+Alt+L` or `Cmd+Opt+L`) to open popup.  
4. Fill in note/tags, adjust options, hit Save.  

Entries append to `flow_log.csv` in the project root.  

---

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for planned features.
