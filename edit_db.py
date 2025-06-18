import sqlite3
import os
import json

DB_FILE = "user_edits.db"
JSON_BACKUP = "backup_edits.json"


def init_db():
    """Initialize the user edits database and table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS edits (
            filename TEXT,
            date TEXT,
            card_type TEXT,
            field TEXT,
            value TEXT,
            PRIMARY KEY (filename, date, card_type, field)
        )
    ''')
    conn.commit()
    conn.close()


def save_edit(filename, date, card_type, field, value):
    """Save or update a cell edit into the database and backup JSON."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO edits (filename, date, card_type, field, value)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, date, card_type, field, str(value)))
    conn.commit()
    conn.close()

    try:
        if os.path.exists(JSON_BACKUP):
            with open(JSON_BACKUP, "r") as f:
                backup_data = json.load(f)
        else:
            backup_data = {}

        key = f"{filename}::{date}::{card_type}::{field}"
        backup_data[key] = str(value)

        with open(JSON_BACKUP, "w") as f:
            json.dump(backup_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to write JSON backup: {e}")


def get_edits_for_file(filename):
    """Retrieve all edits for a specific file from DB, fallback to JSON if DB fails."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, card_type, field, value FROM edits WHERE filename = ?
        ''', (filename,))
        rows = cursor.fetchall()
        conn.close()

        return {
            (date, card_type, field): value
            for date, card_type, field, value in rows
        }

    except Exception as db_err:
        print(f"DB error: {db_err}. Trying JSON backup...")

        if not os.path.exists(JSON_BACKUP):
            return {}

        try:
            with open(JSON_BACKUP, "r") as f:
                raw_data = json.load(f)

            if isinstance(raw_data, dict):
                # Backup from save_edit()
                return {
                    tuple(key.split("::")[1:]): val
                    for key, val in raw_data.items()
                    if key.startswith(f"{filename}::")
                }
            else:
                # Imported full backup from export
                return {
                    (item["date"], item["card_type"], item["field"]): item["value"]
                    for item in raw_data
                    if item.get("filename") == filename
                }
        except Exception as json_err:
            print(f"JSON recovery failed: {json_err}")
            return {}


def delete_edit(filename, date, card_type, field):
    """Remove a specific edit from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM edits WHERE filename = ? AND date = ? AND card_type = ? AND field = ?
    ''', (filename, date, card_type, field))
    conn.commit()
    conn.close()


def export_edits_to_json(json_path="user_edits.json"):
    """Export all database edits into a structured JSON array."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, date, card_type, field, value FROM edits")
    edits = cursor.fetchall()
    conn.close()

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([
            {
                "filename": filename,
                "date": date,
                "card_type": card_type,
                "field": field,
                "value": value
            }
            for filename, date, card_type, field, value in edits
        ], f, indent=2)


def import_edits_from_json(json_path="user_edits.json"):
    """Import edits from JSON. Handles both dict and list format."""
    if not os.path.exists(json_path):
        raise FileNotFoundError("JSON file not found")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, dict):
            # Convert dict format (from backup_edits.json) to list
            edits = []
            for key, value in raw_data.items():
                parts = key.split("::")
                if len(parts) == 4:
                    filename, date, card_type, field = parts
                    edits.append({
                        "filename": filename,
                        "date": date,
                        "card_type": card_type,
                        "field": field,
                        "value": value
                    })
        else:
            edits = raw_data

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while loading JSON: {e}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for e in edits:
        cursor.execute('''
            INSERT OR REPLACE INTO edits (filename, date, card_type, field, value)
            VALUES (?, ?, ?, ?, ?)
        ''', (e["filename"], e["date"], e["card_type"], e["field"], str(e["value"])))
    conn.commit()
    conn.close()


def clear_json_backup():
    if os.path.exists(JSON_BACKUP):
        os.remove(JSON_BACKUP)
        print("JSON backup cleared.")
