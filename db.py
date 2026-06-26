"""
Moduł bazy danych – obsługuje SQLite dla aplikacji Steam Support Dashboard.
Zawiera wszystkie operacje CRUD i inicjalizację schematu.
"""
import sqlite3
from contextlib import contextmanager

DB_NAME = "steam_monitor.db"


@contextmanager
def get_connection():
    """Context manager zapewniający bezpieczne połączenie z bazą."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Dostęp po nazwie kolumny
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Tworzy tabelę items jeśli nie istnieje i wykonuje migracje."""
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                author TEXT,
                title TEXT,
                content_orig TEXT,
                content_trans TEXT,
                url TEXT,
                sentiment TEXT DEFAULT 'neutral',
                is_archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timestamp_updated TIMESTAMP,
                developer_response TEXT,
                appid TEXT
            )
        ''')
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(items)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'sentiment' not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN sentiment TEXT DEFAULT 'neutral'")
            
        if 'created_at' not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN created_at TIMESTAMP")
            conn.execute("UPDATE items SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            
        if 'timestamp_updated' not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN timestamp_updated TIMESTAMP")
            
        if 'developer_response' not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN developer_response TEXT")
            
        if 'appid' not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN appid TEXT")

        # Zawsze zaktualizuj stare wpisy, które mają "neutral", a ich tytuł wskazuje na recenzję
        conn.execute("UPDATE items SET sentiment = 'positive' WHERE title LIKE '%Pozytywna%' AND sentiment = 'neutral'")
        conn.execute("UPDATE items SET sentiment = 'negative' WHERE title LIKE '%Negatywna%' AND sentiment = 'neutral'")
        
        conn.commit()


def get_items(is_archived: int, appid: str = None) -> list[dict]:
    """Pobiera elementy (aktywne lub zarchiwizowane) jako listę słowników."""
    with get_connection() as conn:
        query = "SELECT id, type, author, title, content_orig, content_trans, url, sentiment, created_at, timestamp_updated, developer_response, appid FROM items WHERE is_archived = ?"
        params = [is_archived]
        if appid:
            query += " AND appid = ?"
            params.append(appid)
        query += " ORDER BY created_at DESC"
        
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_stats(appid: str = None) -> dict:
    """Zwraca statystyki dashboardu."""
    with get_connection() as conn:
        base_query = "FROM items"
        params = []
        if appid:
            base_query += " WHERE appid = ?"
            params.append(appid)
            
        def _cnt(extra_cond=""):
            q = f"SELECT COUNT(*) {base_query}"
            if extra_cond:
                q += f" {'AND' if appid else 'WHERE'} {extra_cond}"
            return conn.execute(q, params).fetchone()[0]

        return {
            "total": _cnt(),
            "active": _cnt("is_archived = 0"),
            "archived": _cnt("is_archived = 1"),
            "reviews": _cnt("type = 'Recenzja'"),
            "forum": _cnt("type = 'Forum'"),
            "positive": _cnt("sentiment = 'positive'"),
            "negative": _cnt("sentiment = 'negative'"),
        }


def archive_item(item_id: str):
    """Przenosi element do archiwum."""
    with get_connection() as conn:
        conn.execute("UPDATE items SET is_archived = 1 WHERE id = ?", (item_id,))
        conn.commit()


def restore_item(item_id: str):
    """Przywraca element z archiwum."""
    with get_connection() as conn:
        conn.execute("UPDATE items SET is_archived = 0 WHERE id = ?", (item_id,))
        conn.commit()


def delete_item(item_id: str):
    """Trwale usuwa element z bazy."""
    with get_connection() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()


def insert_item(item: dict) -> bool:
    """Wstawia nowy element (recenzję/dyskusję) do bazy (upsert na ID)."""
    with get_connection() as conn:
        conn.execute('''
            INSERT INTO items (id, type, author, title, content_orig, url, created_at, timestamp_updated, developer_response, appid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                content_orig = excluded.content_orig,
                url = excluded.url,
                created_at = excluded.created_at,
                timestamp_updated = excluded.timestamp_updated,
                developer_response = excluded.developer_response,
                appid = excluded.appid
        ''', (
            item['id'], item['type'], item['author'], item['title'],
            item['content_orig'], item['url'], item.get('created_at'),
            item.get('timestamp_updated'), item.get('developer_response'),
            item.get('appid')
        ))
        conn.commit()
        return True
