"""
Multiplayer Drawing App — Firebase REST API + Pygame
=====================================================
Compatible with Python 3.13+ (no pyrebase dependency)

Browser-compatible version:
    In browser: Python reads INITIAL_STROKES and INCOMING_STROKES from JS,
    and pushes to OUTGOING_STROKES which JS sends to Firebase.
    Falls back to the original desktop implementation otherwise.

Desktop requirements:
    pip install pygame requests sseclient-py
    pip install python-dotenv
"""

import sys
import json
import time

IS_WEB = sys.platform == "emscripten"

if not IS_WEB:
    import threading
    import os
    from dotenv import load_dotenv

    try:
        import requests
    except ImportError:
        requests = None

    try:
        import sseclient
        HAS_SSE = True
    except ImportError:
        HAS_SSE = False
        print("[Network] sseclient-py not installed. Live sync unavailable.")
        print("  pip install sseclient-py")

    load_dotenv()
    FIREBASE_CONFIG = {
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
    }
    print(FIREBASE_CONFIG["databaseURL"])
    print(os.getenv("FIREBASE_DATABASE_URL"))
    DB_URL = FIREBASE_CONFIG["databaseURL"]

else:
    try:
        import js
        DB_URL = str(js.window.FIREBASE_DB_URL)
    except Exception:
        DB_URL = "https://partygames-ee33c-default-rtdb.firebaseio.com"


class FirebaseClient:
    SEND_INTERVAL = 0.2

    def __init__(self, room_id: str, user_id: str):
        self.room_id = room_id
        self.user_id = user_id
        self._last_send = 0.0
        self._seen_keys = set()

        if not IS_WEB:
            import threading
            self._lock = threading.Lock()
            self._incoming = []
            self._listener_thread = None

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        if IS_WEB:
            print(f"[Network] Web mode — room: {self.room_id}")
            return True
        else:
            import requests as req
            url = f"{DB_URL}/rooms/{self.room_id}.json"
            try:
                r = req.get(url, timeout=5)
                if r.status_code == 200:
                    print(f"[Network] Connected to room: {self.room_id}")
                    return True
                else:
                    print(f"[Network] Firebase returned status {r.status_code}")
                    return False
            except Exception as e:
                print(f"[Network] Could not reach Firebase: {e}")
                return False

    # ── Listener ──────────────────────────────────────────────────────────────

    def start_listener(self):
        if IS_WEB:
            print(f"[Network] JS listener active for room: {self.room_id}")
        else:
            if not HAS_SSE:
                return
            import threading
            self._listener_thread = threading.Thread(
                target=self._stream_loop, daemon=True
            )
            self._listener_thread.start()

    # ── Desktop-only stream loop ──────────────────────────────────────────────

    def _stream_loop(self):
        import requests as req
        import sseclient as sse
        path = f"rooms/{self.room_id}/strokes"
        url = f"{DB_URL}/{path}.json"
        headers = {"Accept": "text/event-stream"}
        while True:
            try:
                response = req.get(url, headers=headers, stream=True, timeout=None)
                client = sse.SSEClient(response)
                for event in client.events():
                    if event.event in ("put", "patch") and event.data:
                        self._handle_event(event.data)
            except Exception as e:
                import time as t
                print(f"[Network] Stream error: {e}. Reconnecting in 3s...")
                t.sleep(3)

    def _handle_event(self, raw: str):
        try:
            payload = json.loads(raw)
            data = payload.get("data")
            if not data:
                return
            if isinstance(data, dict):
                if "dots" in data:
                    self._queue_if_foreign(data)
                else:
                    for stroke in data.values():
                        if isinstance(stroke, dict):
                            self._queue_if_foreign(stroke)
        except Exception:
            pass

    def _queue_if_foreign(self, stroke: dict):
        if stroke.get("uid") != self.user_id:
            with self._lock:
                self._incoming.append(stroke)

    # ── Incoming strokes ──────────────────────────────────────────────────────

    def pop_incoming_strokes(self) -> list:
        if IS_WEB:
            try:
                import js
                raw = js.window.INCOMING_STROKES
                if raw is None:
                    return []
                data = json.loads(js.JSON.stringify(raw))
                if not isinstance(data, list) or len(data) == 0:
                    return []
                js.window.INCOMING_STROKES = js.eval("[]")
                return data
            except Exception as e:
                return []
        else:
            with self._lock:
                strokes = list(self._incoming)
                self._incoming.clear()
            return strokes

    def fetch_strokes(self) -> list:
        if IS_WEB:
            try:
                import js
                raw = js.window.INITIAL_STROKES
                if raw is None:
                    return []
                data = json.loads(js.JSON.stringify(raw))
                if isinstance(data, dict):
                    for key in data.keys():
                        self._seen_keys.add(key)
                    return list(data.values())
                return []
            except Exception as e:
                print(f"[Network] fetch_strokes error: {e}")
                return []
        else:
            import requests as req
            url = f"{DB_URL}/rooms/{self.room_id}/strokes.json"
            try:
                r = req.get(url, timeout=5)
                data = r.json()
                if not data or not isinstance(data, dict):
                    return []
                return list(data.values())
            except Exception as e:
                print(f"[Network] fetch_strokes error: {e}")
                return []

    # ── Outgoing strokes ──────────────────────────────────────────────────────

    def push_stroke(self, stroke, color):
        now = time.time()
        if now - self._last_send < self.SEND_INTERVAL:
            return
        self._last_send = now
        data = self._serialize_stroke(stroke, color)

        if IS_WEB:
            try:
                import js
                js.window.OUTGOING_STROKES.push(js.JSON.parse(json.dumps(data)))
            except Exception as e:
                print(f"[Network] push_stroke error: {e}")
        else:
            import threading
            threading.Thread(
                target=self._fb_push,
                args=(f"rooms/{self.room_id}/strokes", data),
                daemon=True
            ).start()

    def _serialize_stroke(self, stroke, color) -> dict:
        if hasattr(color, "value"):
            rgb = list(color.value)
        else:
            rgb = list(color)
        dots = [
            {"x": dot.x, "y": dot.y, "size": dot.surf.get_width()}
            for dot in stroke.dots
        ]
        return {
            "uid": self.user_id,
            "color": rgb,
            "dots": dots,
            "ts": time.time()
        }

    # ── Clear ─────────────────────────────────────────────────────────────────

    def push_clear(self):
        path = f"rooms/{self.room_id}/strokes"
        if IS_WEB:
            try:
                import js
                js.window.PUSH_CLEAR = True
            except Exception as e:
                print(f"[Network] push_clear error: {e}")
        else:
            import threading
            threading.Thread(target=self._fb_set, args=(path, {}), daemon=True).start()
            threading.Thread(target=self._fb_push, args=(path, self._white_stroke()), daemon=True).start()

    def _white_stroke(self) -> dict:
        return {
            "uid": self.user_id,
            "color": [225, 225, 225],
            "dots": [{"x": -500, "y": -500, "size": 2000}],
            "ts": time.time(),
            "is_clear": True
        }

    # ── Desktop REST calls ────────────────────────────────────────────────────

    def _fb_push(self, path: str, data: dict):
        import requests as req
        url = f"{DB_URL}/{path}.json"
        try:
            req.post(url, json=data, timeout=5)
        except Exception as e:
            print(f"[Network] Push error: {e}")

    def _fb_set(self, path: str, data):
        import requests as req
        url = f"{DB_URL}/{path}.json"
        try:
            req.put(url, json=data, timeout=5)
        except Exception as e:
            print(f"[Network] Set error: {e}")

    def _fb_delete(self, path: str):
        import requests as req
        url = f"{DB_URL}/{path}.json"
        try:
            req.delete(url, timeout=5)
        except Exception as e:
            print(f"[Network] Delete error: {e}")