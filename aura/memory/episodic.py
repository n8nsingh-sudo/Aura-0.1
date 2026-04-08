import sqlite3
import time
import json
from aura import config


class EpisodicMemory:
    def __init__(self):
        self.db_path = config.MEMORY_DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    task TEXT NOT NULL,
                    result TEXT,
                    success INTEGER DEFAULT 1,
                    duration_seconds REAL,
                    metadata TEXT
                )
            """)
            conn.commit()

    def record(
        self,
        task: str,
        result: str,
        success: bool = True,
        duration: float = 0.0,
        metadata: dict = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO episodes (timestamp, task, result, success, duration_seconds, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    time.time(),
                    task,
                    result,
                    1 if success else 0,
                    duration,
                    json.dumps(metadata or {}),
                ),
            )
            conn.commit()

    def get_recent(self, n: int = 20) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, task, result, success, duration_seconds
                FROM episodes
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (n,),
            )
            return cursor.fetchall()

    def search(self, query: str, limit: int = 5) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, task, result, success
                FROM episodes
                WHERE task LIKE ? OR result LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )
            return cursor.fetchall()

    def get_success_rate(self) -> float:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT AVG(success) FROM episodes")
            result = cursor.fetchone()[0]
            return result if result else 0.0

    def get_task_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM episodes")
            return cursor.fetchone()[0]
