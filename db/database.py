import sqlite3
import os
from datetime import datetime
from utils.paths import database_path


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = database_path()
        self._db_path = db_path
        self._conn = None
        self._init_db()

    def _init_db(self):
        parent = os.path.dirname(os.path.abspath(self._db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration REAL,
                file_path TEXT,
                status TEXT DEFAULT 'recording'
            )
        """)
        self._conn.commit()

    def add_event(self, start_time: float, file_path: str) -> int:
        dt = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
        cursor = self._conn.execute(
            "INSERT INTO events (start_time, file_path, status) VALUES (?, ?, ?)",
            (dt, file_path, "recording")
        )
        self._conn.commit()
        return cursor.lastrowid

    def finish_event(self, event_id: int, duration: float):
        end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._conn.execute(
            "UPDATE events SET end_time=?, duration=?, status=? WHERE id=?",
            (end_dt, duration, "completed", event_id)
        )
        self._conn.commit()

    def get_all_events(self) -> list:
        cursor = self._conn.execute(
            "SELECT id, start_time, end_time, duration, file_path, status FROM events ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0], "start_time": r[1], "end_time": r[2],
                "duration": r[3], "file_path": r[4], "status": r[5]
            }
            for r in rows
        ]

    def get_events_by_date(self, date_str: str) -> list:
        cursor = self._conn.execute(
            "SELECT id, start_time, end_time, duration, file_path, status FROM events WHERE start_time LIKE ? ORDER BY id DESC",
            (f"{date_str}%",)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0], "start_time": r[1], "end_time": r[2],
                "duration": r[3], "file_path": r[4], "status": r[5]
            }
            for r in rows
        ]

    def _safe_remove(self, file_path: str):
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except (PermissionError, OSError):
            pass

    def delete_event(self, event_id: int) -> str:
        cursor = self._conn.execute("SELECT file_path FROM events WHERE id=?", (event_id,))
        row = cursor.fetchone()
        file_path = row[0] if row else None
        self._conn.execute("DELETE FROM events WHERE id=?", (event_id,))
        self._conn.commit()
        self._safe_remove(file_path)
        return file_path

    def delete_events_by_ids(self, event_ids: list) -> list:
        if not event_ids:
            return []
        removed = []
        for eid in event_ids:
            cursor = self._conn.execute("SELECT file_path FROM events WHERE id=?", (eid,))
            row = cursor.fetchone()
            if row and row[0]:
                removed.append(row[0])
        placeholders = ",".join("?" * len(event_ids))
        self._conn.execute(f"DELETE FROM events WHERE id IN ({placeholders})", event_ids)
        self._conn.commit()
        for fp in removed:
            self._safe_remove(fp)
        return removed

    def delete_events_by_date(self, date_str: str) -> list:
        cursor = self._conn.execute(
            "SELECT file_path FROM events WHERE start_time LIKE ?", (f"{date_str}%",)
        )
        removed = [r[0] for r in cursor.fetchall() if r[0]]
        self._conn.execute("DELETE FROM events WHERE start_time LIKE ?", (f"{date_str}%",))
        self._conn.commit()
        for fp in removed:
            self._safe_remove(fp)
        return removed

    def delete_all_events(self) -> list:
        cursor = self._conn.execute("SELECT file_path FROM events")
        removed = [r[0] for r in cursor.fetchall() if r[0]]
        self._conn.execute("DELETE FROM events")
        self._conn.commit()
        for fp in removed:
            self._safe_remove(fp)
        return removed

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
