import pickle
import sqlite3
from pathlib import Path
from typing import Literal

from .persistence import PersistenceMiddleware
from ...server.event import Event

from asyncio import Lock

lock = Lock()


class SQLitePersistenceMiddleware(PersistenceMiddleware):
    def __init__(self, db: str):
        self.database = Path(db)
        self.database.is_file() and self.database.parent.mkdir(exist_ok=True, parents=True)
        self.setup()

    def setup(self):
        conn = sqlite3.connect(self.database)
        conn.execute("CREATE TABLE IF NOT EXISTS events (" \
                            "id INTEGER PRIMARY KEY AUTOINCREMENT , " \
                            "identifier TEXT NOT NULL," \
                            "status TEXT NOT NULL,"
                            "data BLOB NOT NULL"
                            ")")
        conn.commit()
        conn.close()
    def register(self, ev: Event):
        conn = sqlite3.connect(self.database)
        query = "INSERT INTO events (identifier, status, data) VALUES (?, ?, ?)"
        conn.execute(query, [ev.identifier, ev.status, pickle.dumps(ev)])
        conn.commit()
        conn.close()

    def fetch(self, last = False) -> Event | None:
        conn = sqlite3.connect(self.database)
        query = "SELECT * FROM events WHERE status = ? ORDER BY id " + ("DESC" if last else "") + " LIMIT 1"
        cursor = conn.cursor()
        cursor.execute(query, ['waiting'])
        data = cursor.fetchone()
        cursor.close()
        event = None
        if data:
            event: Event = pickle.loads(data[3])
            event.status = 'delivered'
            self.update_event_status(event.identifier, 'delivered', event)
        conn.close()
        return event

    def get(self, identifier: str) -> Event | None:
        query = "SELECT * FROM events WHERE identifier = ? LIMIT 1"
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(query, [identifier])
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if data:
            return pickle.loads(data[3])
    
    def update_event_status(self, identifier: str, status: Literal['delivered', 'done', 'failed', 'waiting'], ev: Event):
        query = "UPDATE events SET status = ?, data = ? WHERE identifier = ?"
        conn = sqlite3.connect(self.database)
        conn.execute(query, [status, pickle.dumps(ev), identifier])
        conn.commit()
        conn.close()

    def prune_finished(self, remove_failed = False):
        query = "DELETE FROM events WHERE status = 'done'" + (" OR status = 'failed'" if remove_failed else '')
        conn = sqlite3.connect(self.database)
        conn.execute(query)
        conn.commit()
        conn.close()
    
    def remove(self, event_id: int):
        conn = sqlite3.connect(self.database)
        query = "DELETE FROM events WHERE id = ?"
        conn.execute(query, [event_id])
        conn.commit()
        conn.close()
