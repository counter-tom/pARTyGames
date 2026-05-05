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
    HEARTBEAT_INTERVAL = 5
    PRESENCE_TIMEOUT = 15

    FRUIT_POOL = [
        "apple", "banana", "cherry", "grape", "mango",
        "orange", "peach", "pear", "pineapple", "strawberry",
        "watermelon", "lemon", "lime", "coconut", "kiwi",
        "baseball", "football", "basketball", "puck", "hockey stick",
        "baseball bat", "tennis ball", "bowling ball", "golf club",
        "skateboard", "surf board", "boxing glove", "pool cue",
        "sailboat", "popsicle", "brain",
        "birthday", "cake", "skirt", "knee",
        "pineapple", "tusk", "sprinkler",
        "money", "spool", "lighthouse",
        "doormat", "face", "flute",
        "rug", "snowball", "purse",
        "owl", "gate", "suitcase",
        "stomach", "doghouse", "pajamas",
        "bathroom", "scale", "peach", "newspaper",
        "watering", "can", "hook", "school",
        "beaver", "french", "fries", "beehive",
        "beach", "artist", "flagpole",
        "camera", "hair", "dryer", "mushroom",
        "toe", "pretzel", "TV",
        "quilt", "chalk", "dollar",
        "soda", "chin", "swing",
        "garden", "ticket", "boot",
        "cello", "rain", "clam",
        "pelican", "stingray", "fur",
        "blowfish", "rainbow", "happy",
        "fist", "base", "storm",
        "mitten", "easel", "nail",
        "sheep", "stoplight", "coconut",
        "crib", "hippopotamus", "ring",
        "seesaw", "plate", "fishing", "pole",
        "hopscotch", "bell", "pepper", "front", "porch",
        "cheek", "video", "camera", "washing", "machine",
        "telephone", "silverware", "barn",
        "snowflake", "bib", "flashlight",
        "popsicle", "muffin", "sunflower",
        "skirt", "top", "hat", "swimming", "pool",
        "tusk", "radish", "peanut",
        "spool", "poodle", "potato",
        "face", "shark", "fang",
        "snowball", "waist", "spoon",
        "gate", "bottle", "mail",
        "sheep", "lobster", "ice",
        "crib", "lawn", "mower", "bubble",
        "seesaw", "pencil", "cheeseburger",
        "hopscotch", "rocking", "chair", "corner",
        "cheek", "rolly", "polly", "popcorn",
        "telephone", "yo-yo", "seahorse",
        "snowflake", "spine", "desk",
    ]

    def __init__(self, room_id: str, user_id: str):
        self.room_id = room_id
        self.user_id = user_id
        self._last_send = 0.0
        self._seen_keys = set()

        if not IS_WEB:
            import threading
            self._lock = threading.Lock()
            self._incoming = []
            self._incoming_messages = []
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
        path = f"rooms/{self.room_id}"
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

            elif "strokes" in path or not path or path == "/":
                if isinstance(data, dict):
                    if "dots" in data or "is_fill" in data:
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

    def _queue_message_if_foreign(self, msg: dict):
        if msg.get("uid") != self.user_id:
            with self._lock:
                self._incoming_messages.append(msg)

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    def start_heartbeat(self):
        if IS_WEB:
            return  # Not supported in web mode
        import threading
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        while True:
            self._fb_set(
                f"rooms/{self.room_id}/presence/{self.user_id}",
                {"uid": self.user_id, "ts": time.time()}
            )
            time.sleep(self.HEARTBEAT_INTERVAL)

    def fetch_active_players(self) -> list:
        if IS_WEB:
            return []
        import requests as req
        url = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = req.get(url, timeout=5)
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
        if IS_WEB:
            return 0
        import requests as req
        purl = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = req.get(purl, timeout=5)
            data = response.json()
            order = len(data) if isinstance(data, dict) else 0
        except:
            order = 0
        url = f"{DB_URL}/rooms/{self.room_id}/presence/{self.user_id}.json"
        req.put(url, json={
            "uid": self.user_id,
            "ts": time.time(),
            "order": order
        }, timeout=5)
        return order

    def leave_room(self):
        if not IS_WEB:
            self._fb_delete(f"rooms/{self.room_id}/presence/{self.user_id}")

    def clear_room(self):
        if not IS_WEB:
            import threading
            threading.Thread(
                target=self._fb_set,
                args=(f"rooms/{self.room_id}", {}),
                daemon=False
            ).start()

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
        data = {
            "uid": self.user_id,
            "color": rgb,
            "dots": dots,
            "ts": time.time()
        }
        if getattr(stroke, "is_fill", False):
            data["is_fill"] = True
            data["fill_x"] = stroke.fill_pos[0] if stroke.fill_pos else 0
            data["fill_y"] = stroke.fill_pos[1] if stroke.fill_pos else 0
        return data

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

    # ── Chat ──────────────────────────────────────────────────────────────────

    def push_chat_message(self, message: str):
        data = {
            "uid": self.user_id,
            "message": message,
            "ts": time.time()
        }
        if IS_WEB:
            try:
                import js
                js.window.OUTGOING_CHAT.push(js.JSON.parse(json.dumps(data)))
            except Exception as e:
                print(f"[Network] push_chat_message error: {e}")
        else:
            import threading
            threading.Thread(
                target=self._fb_push,
                args=(f"rooms/{self.room_id}/chat", data),
                daemon=True
            ).start()

    def fetch_chat_messages(self) -> list:
        if IS_WEB:
            return []
        import requests as req
        url = f"{DB_URL}/rooms/{self.room_id}/chat.json"
        try:
            response = req.get(url, timeout=5)
            data = response.json()
            if not data or not isinstance(data, dict):
                return []
            return sorted(data.values(), key=lambda m: m.get("ts", 0))
        except Exception as e:
            print(f"[Network] fetch_chat_messages error: {e}")
            return []

    def pop_incoming_messages(self) -> list:
        if IS_WEB:
            try:
                import js
                raw = js.window.INCOMING_CHAT
                if raw is None:
                    return []
                data = json.loads(js.JSON.stringify(raw))
                if not isinstance(data, list) or len(data) == 0:
                    return []
                js.window.INCOMING_CHAT = js.eval("[]")
                return [m for m in data if m.get("uid") != self.user_id]
            except Exception as e:
                return []
        else:
            with self._lock:
                messages = list(self._incoming_messages)
                self._incoming_messages.clear()
            return messages

    # ── Gamemode ──────────────────────────────────────────────────────────────

    def push_gamemode(self, gamemode: str):
        if not IS_WEB:
            self._fb_set(f"rooms/{self.room_id}/gamemode", gamemode)

    def fetch_gamemode(self) -> str:
        if IS_WEB:
            return "freedraw"
        import requests as req
        url = f"{DB_URL}/rooms/{self.room_id}/gamemode.json"
        try:
            response = req.get(url, timeout=5)
            data = response.json()
            return data if isinstance(data, str) else "freedraw"
        except Exception as e:
            print(f"[Network] fetch_gamemode error: {e}")
            return "freedraw"

    # ── Game state (Pictionary) ───────────────────────────────────────────────

    def push_game_state(self, turn_index: int, drawer_uid: str, word: str):
        if not IS_WEB:
            self._fb_set(f"rooms/{self.room_id}/game_state", {
                "turn_index": turn_index,
                "current_drawer": drawer_uid,
                "current_word": word,
                "round_active": True
            })

    def fetch_game_state(self) -> dict:
        if IS_WEB:
            return {}
        import requests as req
        url = f"{DB_URL}/rooms/{self.room_id}/game_state.json"
        try:
            response = req.get(url, timeout=5)
            data = response.json()
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"[Network] fetch_game_state error: {e}")
            return {}

    def reset_turn(self):
        if not IS_WEB:
            self._fb_set(f"rooms/{self.room_id}/game_state/turn_index", 0)
            self.end_round()

    def end_round(self):
        if not IS_WEB:
            self._fb_set(f"rooms/{self.room_id}/game_state/current_word", None)
            self._fb_set(f"rooms/{self.room_id}/game_state/round_active", False)

    def fetch_ordered_players(self) -> list:
        if IS_WEB:
            return []
        import requests as req
        url = f"{DB_URL}/rooms/{self.room_id}/presence.json"
        try:
            response = req.get(url, timeout=5)
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