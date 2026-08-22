import json, os, sqlite3, threading
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        self._lock = threading.RLock()
        self._conn = None
    def start(self):
        with self._lock:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            try: self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            except Exception: self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            cursor = self._conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, val TEXT);")
            cursor.execute("CREATE TABLE IF NOT EXISTS event_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, payload TEXT);")
            self._conn.commit()
    def stop(self):
        with self._lock:
            if self._conn: self._conn.close()
    def set(self, key, val):
        with self._lock:
            if not self._conn: return False
            self._conn.execute("INSERT OR REPLACE INTO kv VALUES (?, ?);", (key, json.dumps(val)))
            self._conn.commit()
            return True
    def get(self, key, default=None):
        with self._lock:
            if not self._conn: return default
            cur = self._conn.cursor()
            cur.execute("SELECT val FROM kv WHERE key = ?;", (key,))
            r = cur.fetchone()
            return json.loads(r[0]) if r else default
    def log_event(self, event_type, payload=None):
        with self._lock:
            if not self._conn: return -1
            cur = self._conn.cursor()
            cur.execute("INSERT INTO event_logs (event_type, payload) VALUES (?, ?);", (event_type, json.dumps(payload or {})))
            self._conn.commit()
            return cur.lastrowid
