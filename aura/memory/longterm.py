import sqlite3
import time
from aura import config


class LongTermMemory:
    def __init__(self):
        self.db_path = config.MEMORY_DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS longterm (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at REAL NOT NULL,
                    expires_at REAL,
                    importance REAL DEFAULT 1.0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON longterm(key)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_category ON longterm(category)"
            )
            conn.commit()

    def store(
        self,
        key: str,
        value: str,
        category: str = "general",
        ttl_days: float = config.LONG_TERM_TTL_DAYS,
        importance: float = 1.0,
    ):
        now = time.time()
        expires_at = None if ttl_days == -1 else now + (ttl_days * 86400)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO longterm 
                (key, value, category, created_at, expires_at, importance)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (key, value, category, now, expires_at, importance),
            )
            conn.commit()

    def get(self, key: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value FROM longterm
                WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
            """,
                (key, time.time()),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def prune_expired(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM longterm 
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """,
                (time.time(),),
            )
            conn.commit()
            return cursor.rowcount

    def get_by_category(self, category: str) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT key, value, importance
                FROM longterm
                WHERE category = ? AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY importance DESC
            """,
                (category, time.time()),
            )
            return cursor.fetchall()
