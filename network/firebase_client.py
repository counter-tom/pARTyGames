
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
        self._incoming_messages = []  

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
        path = f"rooms/{self.room_id}"
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
        try:
            payload = json.loads(raw)
            path = payload.get("path", "")
            data = payload.get("data")
            if not data:
                return

            if "chat" in path:
                if isinstance(data, dict):
                    if "message" in data:
                        self._queue_message_if_foreign(data)
                    else:
                        for msg in data.values():
                            if isinstance(msg, dict):
                                self._queue_message_if_foreign(msg)

            elif "strokes" in path:
                if isinstance(data, dict):
                    if "dots" in data or "is_fill" in data:
                        # ✅ Single stroke or single fill — queue directly
                        self._queue_if_foreign(data)
                    else:
                        # Bulk dict of strokes/fills
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

    ##Heartbeat implementation to check active players.
    HEARTBEAT_INTERVAL = 5   # seconds
    PRESENCE_TIMEOUT   = 15  # seconds

    def start_heartbeat(self):
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        while True:
            self._fb_set(
                f"rooms/{self.room_id}/presence/{self.user_id}",
                {"uid": self.user_id, "ts": time.time()}
            )
            time.sleep(self.HEARTBEAT_INTERVAL)

    def fetch_active_players(self) -> list:
        url = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if not data or not isinstance(data, dict):
                return []
            now = time.time()
            return [
                entry["uid"] for entry in data.values()
                if now - entry.get("ts", 0) < self.PRESENCE_TIMEOUT
            ]
        except Exception as e:
            print(f"[Network] fetch_active_players error: {e}")
            return []
        
    def register_player_order(self) -> int:
        """
        Claims the next join order slot for this player.
        Returns the integer slot claimed (0, 1, 2...).
        """
        purl = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = requests.get(purl, timeout=5)
            data = response.json()
            order = len(data) if isinstance(data, dict) else 0
        except:
            order = 0

        url = f"{DB_URL}/rooms/{self.room_id}/presence/{self.user_id}.json"
        requests.put(url, json={
            "uid":   self.user_id,
            "ts":    time.time(),
            "order": order
        }, timeout=5)
        return order    

    def leave_room(self):
        self._fb_delete(f"rooms/{self.room_id}/presence/{self.user_id}")

    def clear_room(self):
        threading.Thread(
            target=self._fb_set,
            args=(f"rooms/{self.room_id}", {}),
            daemon=False  # ✅ Must complete before process dies
        ).start()


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
    
    def fetch_strokes(self) -> list:
        """
        Fetch all existing strokes in the room on startup.
        Returns a list of stroke dicts.
        """
        url = f"{DB_URL}/rooms/{self.room_id}/strokes.json"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
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

    # Chat functions
    def push_chat_message(self, message: str):
        """Push a chat message to Firebase."""
        data = {
            "uid": self.user_id,
            "message": message,
            "ts": time.time()
        }
        threading.Thread(
            target=self._fb_push,
            args=(f"rooms/{self.room_id}/chat", data),
            daemon=True
        ).start()

    def fetch_chat_messages(self) -> list:
        """Fetch all existing chat messages on startup."""
        url = f"{DB_URL}/rooms/{self.room_id}/chat.json"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if not data or not isinstance(data, dict):
                return []
            return sorted(data.values(), key=lambda m: m.get("ts", 0))  
        except Exception as e:
            print(f"[Network] fetch_chat_messages error: {e}")
            return []

    def pop_incoming_messages(self) -> list:
        """Return and clear all queued incoming chat messages."""
        with self._lock:
            messages = list(self._incoming_messages)
            self._incoming_messages.clear()
        return messages
    
    #TODO Topic draw pool
    FRUIT_POOL = [
        "apple", "banana", "cherry", "grape", "mango",
        "orange", "peach", "pear", "pineapple", "strawberry",
        "watermelon", "lemon", "lime", "coconut", "kiwi"
    ]

    # ── Room setup ────────────────────────────────────────────────────────────────

    def push_gamemode(self, gamemode: str):
        """Host writes gamemode when creating the room."""
        self._fb_set(f"rooms/{self.room_id}/gamemode", gamemode)

    def fetch_gamemode(self) -> str:
        """Joiners read the gamemode on connect."""
        url = f"{DB_URL}/rooms/{self.room_id}/gamemode.json"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            return data if isinstance(data, str) else "freedraw"
        except Exception as e:
            print(f"[Network] fetch_gamemode error: {e}")
            return "freedraw"

    # ── Presence order ────────────────────────────────────────────────────────────

    def register_player_order(self):
        """
        Claim the next join order slot.
        Returns the integer slot claimed (0, 1, 2...).
        """
        url = f"{DB_URL}/rooms/{self.room_id}/presence/{self.user_id}.json"
        # Read current presence count to assign order
        purl = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = requests.get(purl, timeout=5)
            data = response.json()
            order = len(data) if isinstance(data, dict) else 0
        except:
            order = 0
        requests.put(url, json={"uid": self.user_id, "ts": time.time(), "order": order}, timeout=5)
        return order

    # ── Game state ────────────────────────────────────────────────────────────────

    def push_game_state(self, turn_index: int, drawer_uid: str, word: str):
        self._fb_set(f"rooms/{self.room_id}/game_state", {
            "turn_index": turn_index,
            "current_drawer": drawer_uid,
            "current_word": word,
            "round_active": True
        })

    def fetch_game_state(self) -> dict:
        url = f"{DB_URL}/rooms/{self.room_id}/game_state.json"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"[Network] fetch_game_state error: {e}")
            return {}
        
    def reset_turn(self):
        """Reset turn index to 0 and end the current round."""
        self._fb_set(f"rooms/{self.room_id}/game_state/turn_index", 0)
        self.end_round()        

    def end_round(self):
        """Clear word, mark round inactive. turn_index increment handled by new round start."""
        self._fb_set(f"rooms/{self.room_id}/game_state/current_word", None)
        self._fb_set(f"rooms/{self.room_id}/game_state/round_active", False)

    def fetch_ordered_players(self) -> list:
        """Returns uids sorted by their join order."""
        url = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if not data or not isinstance(data, dict):
                return []
            now = time.time()
            active = [
                v for v in data.values()
                if now - v.get("ts", 0) < self.PRESENCE_TIMEOUT
            ]
            return [p["uid"] for p in sorted(active, key=lambda x: x.get("order", 0))]
        except Exception as e:
            print(f"[Network] fetch_ordered_players error: {e}")
            return []
#########################
    # def _handle_event(self, raw: str):
    #     """Parse an SSE payload and queue any foreign strokes or messages."""
    #     try:
    #         payload = json.loads(raw)
    #         path = payload.get("path", "")
    #         data = payload.get("data")
    #         if not data:
    #             return

    #         if "chat" in path:
    #             if isinstance(data, dict):
    #                 if "message" in data:
    #                     self._queue_message_if_foreign(data)
    #                 else:
    #                     for msg in data.values():
    #                         if isinstance(msg, dict):
    #                             self._queue_message_if_foreign(msg)
    #         else:
    #             if isinstance(data, dict):
    #                 if "dots" in data:
    #                     self._queue_if_foreign(data)
    #                 else:
    #                     for stroke in data.values():
    #                         if isinstance(stroke, dict):
    #                             self._queue_if_foreign(stroke)
    #     except Exception:
    #         pass

    def _queue_message_if_foreign(self, msg: dict):
        """Queue chat messages from other users."""
        if msg.get("uid") != self.user_id:
            with self._lock:
                self._incoming_messages.append(msg)    


#########################

    def push_clear(self):
    # Wipe all strokes from DB
        threading.Thread(
            target=self._fb_set,
            args=(f"rooms/{self.room_id}/strokes", {}),
            daemon=True
        ).start()
        # Push a single canvas-sized white stroke as the clear signal
        threading.Thread(
            target=self._fb_push,
            args=(f"rooms/{self.room_id}/strokes", self._white_stroke()),
            daemon=True
        ).start()

    def push_fill(self, x: int, y: int, color):
        if hasattr(color, "value"):
            rgb = list(color.value)
        else:
            rgb = list(color)

        data = {
            "uid":     self.user_id,
            "is_fill": True,
            "fill_x":  x,
            "fill_y":  y,
            "color":   rgb,  # ✅ Already a list, Firebase should store as array
            "ts":      time.time()
        }
        threading.Thread(
            target=self._fb_push,
            args=(f"rooms/{self.room_id}/strokes", data),
            daemon=True
        ).start()

    #This is an adhoc way to clear other users' canvasses.    
    def _white_stroke(self) -> dict:
        return {
            "uid": self.user_id,
            "color": [225, 225, 225],
            "dots": [{"x": -500, "y": -500, "size": 2000}],
            "ts": time.time(),
            "is_clear": True
        }
    
    def _fb_set(self, path: str, data):
        url = f"{DB_URL}/{path}.json"
        try:
            requests.put(url, json=data, timeout=5)
        except Exception as e:
            print(f"[Network] Set error: {e}")        

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

