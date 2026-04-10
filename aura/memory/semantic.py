import sqlite3
import time
from aura import config


class SemanticMemory:
    def __init__(self):
        self.db_path = config.MEMORY_DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts 
                USING fts5(topic, content, content=knowledge, content_rowid=id)
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_ai 
                AFTER INSERT ON knowledge BEGIN
                    INSERT INTO knowledge_fts(rowid, topic, content) 
                    VALUES (new.id, new.topic, new.content);
                END
            """)
            conn.commit()

    def store(
        self, topic: str, content: str, source: str = "unknown", confidence: float = 1.0
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO knowledge (timestamp, topic, content, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """,
                (time.time(), topic, content, source, confidence),
            )
            conn.commit()

    def search(self, query: str, limit: int = 10) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT k.topic, k.content, k.source, k.confidence
                FROM knowledge_fts 
                JOIN knowledge k ON knowledge_fts.rowid = k.id
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """,
                (query, limit),
            )
            results = cursor.fetchall()
            return results

    def get_by_topic(self, topic: str) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT topic, content, source, confidence
                FROM knowledge
                WHERE topic LIKE ?
                ORDER BY confidence DESC
            """,
                (f"%{topic}%",),
            )
            return cursor.fetchall()

    def get_total_knowledge_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge")
            return cursor.fetchone()[0]

    def get_recent(self, limit: int = 50) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT topic, content, source, confidence, timestamp
                FROM knowledge
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )
            return cursor.fetchall()
