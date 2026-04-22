"""
Multiplayer Drawing App — Firebase REST API + Pygame
=====================================================
Compatible with Python 3.13+ (no pyrebase dependency)

Browser-compatible version:
    Replaces requests/threading/sseclient with browser JS calls via
    the `js` module (pyodide) when running in the browser.
    Falls back to the original desktop implementation otherwise.
    The DB_URL is injected by index.html into window.FIREBASE_DB_URL
    before Pygbag starts, so no .env file is needed in the browser.

Desktop requirements:
    pip install pygame requests sseclient-py
    pip install python-dotenv

Setup:
    1. For desktop: FIREBASE_DATABASE_URL in your .env file
    2. For web: Firebase config in index.html
    3. Run on multiple machines with the same ROOM_ID
"""

import sys
import json
import time

# True when running inside the browser via pygbag/WebAssembly
IS_WEB = sys.platform == "emscripten"

if not IS_WEB:
    # ── Desktop fallback (original implementation) ────────────────────────────
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
    # ── Browser: grab the URL that index.html injected ────────────────────────
    import js
    DB_URL = str(js.window.FIREBASE_DB_URL)


class FirebaseClient:
    """
    Wraps Firebase calls for stroke push, stream, and clear.

    Strokes are sent as:
    {
        "uid":   "<user_id>",
        "color": [r, g, b],
        "dots":  [{"x": float, "y": float, "size": int}, ...],
        "ts":    float
    }

    The dot format maps directly to PaintDot — x/y are the top-left
    surface position and size is the surface dimension. Color is shared
    across all dots in a stroke since PaintDot owns its color.

    On desktop: uses requests + sseclient (original behavior).
    In browser: uses Firebase JS SDK via the js/pyodide bridge.
    """

    SEND_INTERVAL = 0.2  # seconds — matches PaintCanvas.SYNC_INTERVAL

    def __init__(self, room_id: str, user_id: str):
        self.room_id = room_id
        self.user_id = user_id
        self._last_send = 0.0
        self._incoming = []

        if not IS_WEB:
            import threading
            self._lock = threading.Lock()
            self._listener_thread = None

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """
        Test connectivity to Firebase. Returns True if reachable.
        Should be called once before starting the listener.
        """
        if IS_WEB:
            # Connection is handled by Firebase JS SDK in index.html
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
        """
        Start listening for incoming strokes from other users.
        On desktop: background daemon thread via SSE.
        In browser: Firebase JS realtime listener.
        Silently does nothing if sseclient-py is not installed on desktop.
        """
        if IS_WEB:
            # Set up Firebase JS realtime listener
            # index.html exposes window.firebaseDB
            try:
                path = f"rooms/{self.room_id}/strokes"
                uid = self.user_id
                incoming_ref = js.window.firebaseDB.ref(path)

                # Store reference so we can remove it later if needed
                self._js_listener = incoming_ref

                def on_value(snapshot):
                    try:
                        val = snapshot.val()
                        if val is None:
                            return
                        data = json.loads(js.JSON.stringify(val))
                        if isinstance(data, dict):
                            for stroke in data.values():
                                if isinstance(stroke, dict) and stroke.get("uid") != uid:
                                    self._incoming.append(stroke)
                    except Exception as e:
                        print(f"[Network] Listener error: {e}")

                incoming_ref.on("value", js.create_proxy(on_value))
            except Exception as e:
                print(f"[Network] Could not start JS listener: {e}")
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
        """Internal — runs in daemon thread, reconnects on failure."""
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
        """Parse an SSE payload and queue any foreign strokes."""
        try:
            payload = json.loads(raw)
            data = payload.get("data")
            if not data:
                return
            if isinstance(data, dict):
                # Single stroke or dict of strokes
                if "dots" in data:
                    self._queue_if_foreign(data)
                else:
                    for stroke in data.values():
                        if isinstance(stroke, dict):
                            self._queue_if_foreign(stroke)
        except Exception:
            pass

    def _queue_if_foreign(self, stroke: dict):
        """Only queue strokes from other users."""
        if stroke.get("uid") != self.user_id:
            if IS_WEB:
                self._incoming.append(stroke)
            else:
                with self._lock:
                    self._incoming.append(stroke)

    # ── Incoming strokes ──────────────────────────────────────────────────────

    def pop_incoming_strokes(self) -> list:
        """
        Return and clear all queued incoming strokes from other users.
        Call this each frame from UserManager.update().

        Returns a list of stroke dicts:
        [{"uid": str, "color": [r,g,b], "dots": [{"x","y","size"}], "ts": float}]
        """
        if IS_WEB:
            strokes = list(self._incoming)
            self._incoming.clear()
            return strokes
        else:
            with self._lock:
                strokes = list(self._incoming)
                self._incoming.clear()
            return strokes

    def fetch_strokes(self) -> list:
        """
        Fetch all existing strokes in the room on startup.
        Returns a list of stroke dicts.
        On desktop: REST GET request.
        In browser: reads window.INITIAL_STROKES set by index.html.
        """
        if IS_WEB:
            # Initial strokes are loaded via JS in index.html
            # window.INITIAL_STROKES is set before Pygbag starts
            try:
                raw = js.window.INITIAL_STROKES
                if raw is None:
                    return []
                data = json.loads(js.JSON.stringify(raw))
                if isinstance(data, dict):
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
        """
        Serialize a Stroke object and push it to Firebase if the send
        interval has elapsed. Call this from PaintCanvas.sync() or
        UserManager after a stroke is committed.

        Args:
            stroke: A Stroke instance (has .dots list of PaintDot)
            color:  A Color enum value — the user's drawing colour
        """
        now = time.time()
        if now - self._last_send < self.SEND_INTERVAL:
            return
        self._last_send = now
        data = self._serialize_stroke(stroke, color)

        if IS_WEB:
            self._js_push(f"rooms/{self.room_id}/strokes", data)
        else:
            import threading
            threading.Thread(
                target=self._fb_push,
                args=(f"rooms/{self.room_id}/strokes", data),
                daemon=True
            ).start()

    def _serialize_stroke(self, stroke, color) -> dict:
        # Normalize color to [r, g, b] regardless of type
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
        # Wipe all strokes from DB
        path = f"rooms/{self.room_id}/strokes"
        if IS_WEB:
            self._js_set(path, {})
            # Push a single canvas-sized white stroke as the clear signal
            self._js_push(path, self._white_stroke())
        else:
            import threading
            threading.Thread(target=self._fb_set, args=(path, {}), daemon=True).start()
            # Push a single canvas-sized white stroke as the clear signal
            threading.Thread(target=self._fb_push, args=(path, self._white_stroke()), daemon=True).start()

    # This is an adhoc way to clear other users' canvases.
    def _white_stroke(self) -> dict:
        return {
            "uid": self.user_id,
            "color": [225, 225, 225],
            "dots": [{"x": -500, "y": -500, "size": 2000}],
            "ts": time.time(),
            "is_clear": True
        }

    # ── JS Firebase calls (web only) ──────────────────────────────────────────

    def _js_push(self, path: str, data: dict):
        try:
            ref = js.window.firebaseDB.ref(path)
            ref.push(js.JSON.parse(json.dumps(data)))
        except Exception as e:
            print(f"[Network] JS push error: {e}")

    def _js_set(self, path: str, data: dict):
        try:
            ref = js.window.firebaseDB.ref(path)
            ref.set(js.JSON.parse(json.dumps(data)))
        except Exception as e:
            print(f"[Network] JS set error: {e}")

    # ── Firebase REST (desktop only) ──────────────────────────────────────────

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