
"""
Multiplayer Drawing App — Firebase REST API + Pygame
=====================================================
Compatible with Python 3.13+ (no pyrebase dependency)

Requirements:
    pip install pygame requests sseclient-py
    pip install python-dotenv

Setup:
    1. Fill in FIREBASE_CONFIG below
    2. Run on multiple machines with the same ROOM_ID
"""

import pygame
import requests
import threading
import time
import uuid
import sys
import json

import os 
from dotenv import load_dotenv


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

print ( FIREBASE_CONFIG["databaseURL"] ) 
print ( os.getenv("FIREBASE_DATABASE_URL") )

DB_URL = FIREBASE_CONFIG["databaseURL"]


class FirebaseClient:
    """
    Wraps Firebase REST API calls for stroke push, stream, and clear.

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
    """

    SEND_INTERVAL = 0.2  # seconds — matches PaintCanvas.SYNC_INTERVAL

    def __init__(self, room_id: str, user_id: str):
        self.room_id = room_id
        self.user_id = user_id
        self._last_send = 0.0
        self._incoming = []
        self._lock = threading.Lock()
        self._listener_thread = None

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """
        Test connectivity to Firebase. Returns True if reachable.
        Should be called once before starting the listener.
        """
        url = f"{DB_URL}/rooms/{self.room_id}.json"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[Network] Connected to room: {self.room_id}")
                return True
            else:
                print(f"[Network] Firebase returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"[Network] Could not reach Firebase: {e}")
            return False

    # ── Listener ──────────────────────────────────────────────────────────────

    def start_listener(self):
        """
        Start a background daemon thread that listens for incoming strokes
        from other users via Firebase Server-Sent Events.
        Silently does nothing if sseclient-py is not installed.
        """
        if not HAS_SSE:
            return
        self._listener_thread = threading.Thread(
            target=self._stream_loop,
            daemon=True
        )
        self._listener_thread.start()

    def _stream_loop(self):
        """Internal — runs in daemon thread, reconnects on failure."""
        path = f"rooms/{self.room_id}/strokes"
        url = f"{DB_URL}/{path}.json"
        headers = {"Accept": "text/event-stream"}

        while True:
            try:
                response = requests.get(
                    url, headers=headers, stream=True, timeout=None
                )
                client = sseclient.SSEClient(response)
                for event in client.events():
                    if event.event in ("put", "patch") and event.data:
                        self._handle_event(event.data)
            except Exception as e:
                print(f"[Network] Stream error: {e}. Reconnecting in 3s...")
                time.sleep(3)

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
        with self._lock:
            strokes = list(self._incoming)
            self._incoming.clear()
        return strokes

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
        threading.Thread(
            target=self._fb_push,
            args=(f"rooms/{self.room_id}/strokes", data),
            daemon=True
        ).start()

    def _serialize_stroke(self, stroke, color) -> dict:
        """
        Convert a Stroke + Color into a Firebase-safe dict.
        Dots are stored as {x, y, size} — size is inferred from surf width.
        Color is stored as [r, g, b] from the Color enum value tuple.
        """
        dots = [
            {
                "x": dot.x,
                "y": dot.y,
                "size": dot.surf.get_width()
            }
            for dot in stroke.dots
        ]
        return {
            "uid": self.user_id,
            "color": list(color.value),
            "dots": dots,
            "ts": time.time()
        }

    # ── Clear ─────────────────────────────────────────────────────────────────

    def push_clear(self):
        """
        Delete all strokes in the room from Firebase.
        Called when ClearCanvasCommand is executed.
        """
        threading.Thread(
            target=self._fb_delete,
            args=(f"rooms/{self.room_id}/strokes",),
            daemon=True
        ).start()

    # ── Firebase REST ─────────────────────────────────────────────────────────

    def _fb_push(self, path: str, data: dict):
        url = f"{DB_URL}/{path}.json"
        try:
            requests.post(url, json=data, timeout=5)
        except Exception as e:
            print(f"[Network] Push error: {e}")

    def _fb_delete(self, path: str):
        url = f"{DB_URL}/{path}.json"
        try:
            requests.delete(url, timeout=5)
        except Exception as e:
            print(f"[Network] Delete error: {e}")
