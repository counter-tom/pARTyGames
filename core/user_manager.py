import uuid
import pygame
from core.user import User
from core.color import Color
from canvas.master_canvas import MasterCanvas
from network import FirebaseClient
from network.stroke_deserializer import deserialize_stroke
from commands import DrawStrokeCommand
from commands.clear_canvas_command import ClearCanvasCommand
import time
import random
import threading

class UserManager:
    def __init__(self, room_name, gamemode="freedraw"):
        self.users = {}
        self._next_id = 0
        self.master = MasterCanvas()
        self.active_user_id = 0 
        self.room_name = room_name
        self.firebase = FirebaseClient(room_id=self.room_name, user_id=str(uuid.uuid4())[:8])
        self.firebase.connect()
        self.firebase.start_listener()
        #Chat
        self._pending_initial_strokes = self.firebase.fetch_strokes()
        self._pending_initial_messages = self.firebase.fetch_chat_messages()
        #Heartbeat
        self.firebase.start_heartbeat()
        self.active_players = []
        self._presence_check_interval = 10
        self._last_presence_check = 0.0
        #Pictionary
        self.gamemode = gamemode
        self.my_order = self.firebase.register_player_order()  # ✅ Claim join slot
        self.game_state = {}
        self._game_state_check_interval = 3
        self._last_game_state_check = 0.0
        self.i_am_drawer = False
        self.current_word = None  # Only revealed to drawer
        self._game_state_lock = threading.Lock()
        self._ordered_players_cache = []
        self._fetching_game_state = False
        self._fetching_players = False
        self._last_player_count = 0
        

    def get_active_user(self):
        return self.users.get(self.active_user_id)

    def add_user(self, screen):
        user_id = self._next_id
        self._next_id += 1
        color = Color.BLACK

        self.users[user_id] = User(screen, user_id, color)
        self.master.register(user_id, self.users[user_id].canvas)
        self.users[user_id].cursor.firebase = self.firebase


    def draw(self):
        active_user = self.users.get(self.active_user_id)
        if active_user is not None:
            active_user.draw_canvas()

    def draw_cursor(self):
        active_user = self.users.get(self.active_user_id)
        if active_user is not None:
            active_user.draw_cursor()

    def get_clear_command(self):
        user = self.get_active_user()
        if user is not None:
            cmd = ClearCanvasCommand(user.canvas, self.firebase)
            user.commander.execute(cmd)        

    def update(self, is_cursor_on_ui, events):
        #Heartbeat 
        now = time.time()
        if now - self._last_presence_check > self._presence_check_interval:
            self._last_presence_check = now
            if not self._fetching_players:
                self._fetching_players = True
                threading.Thread(target=self._fetch_players_async, daemon=True).start()

        #Incoming chat messages
        if self._pending_initial_messages:
            for msg_dict in self._pending_initial_messages:
                self._on_incoming_message(msg_dict)
            self._pending_initial_messages = []

        for msg_dict in self.firebase.pop_incoming_messages():
            self._on_incoming_message(msg_dict)

        #Replay initial strokes on first update
        if self._pending_initial_strokes:
            active_user = self.users.get(self.active_user_id)
            if active_user is not None:
                for stroke_dict in self._pending_initial_strokes:
                    stroke = deserialize_stroke(stroke_dict)
                    cmd = DrawStrokeCommand(active_user.canvas, stroke)
                    cmd.do()
                if active_user.canvas.strokes:
                    active_user.canvas._last_pushed_stroke = active_user.canvas.strokes[-1]
            self._pending_initial_strokes = []

        #Active user update + stroke sync
        active_user = self.users.get(self.active_user_id)
        if active_user is not None:
            active_user.update(is_cursor_on_ui)
            canvas = active_user.canvas
            if not hasattr(canvas, '_last_pushed_stroke'):
                canvas._last_pushed_stroke = None
            if canvas.strokes and canvas.strokes[-1] is not canvas._last_pushed_stroke:
                latest = canvas.strokes[-1]
                canvas._last_pushed_stroke = latest
                if not latest.remote:
                    self.firebase.push_stroke(latest, active_user.color)
            for stroke_dict in self.firebase.pop_incoming_strokes():
                stroke = deserialize_stroke(stroke_dict)
                if active_user is not None:
                    if stroke.is_clear:
                        active_user.canvas.clear()
                        active_user.canvas._last_pushed_stroke = None
                    elif getattr(stroke, 'is_fill', False):  # ✅ Safe check, defaults to False
                        from commands.fill_command import FillCommand
                        cmd = FillCommand(active_user.canvas, (stroke.fill_x, stroke.fill_y), stroke.fill_color)
                        cmd.do()
                    else:
                        cmd = DrawStrokeCommand(active_user.canvas, stroke)
                        cmd.do()

        #Pictionary game state
        if self.gamemode == "pictionary":
            now = time.time()
            if now - self._last_game_state_check > self._game_state_check_interval:
                self._last_game_state_check = now
                if not self._fetching_game_state:
                    self._fetching_game_state = True
                    threading.Thread(
                        target=self._fetch_game_state_async,
                        daemon=True
                    ).start()

        #Pictionary game state update
    def _evaluate_game_state(self):
        players = self.firebase.fetch_ordered_players()
        enough_players = len(players) >= 2
        round_active = self.game_state.get("round_active", False)
        current_drawer = self.game_state.get("current_drawer")

        print(f"[Game] players={players}, enough={enough_players}, round_active={round_active}, drawer={current_drawer}, me={self.firebase.user_id}")  # ✅ Temp

        self.i_am_drawer = (current_drawer == self.firebase.user_id)

        if enough_players and not round_active and players and players[0] == self.firebase.user_id:
            self._start_new_round(players)       

    def get_player_count(self) -> int:
        return len(self.active_players)



    def on_exit(self):
        active = self.firebase.fetch_active_players()
        if len(active) <= 1:
            print("[Network] Last player leaving — clearing room.")
            self.firebase.clear_room()
        else:
            self.firebase.leave_room()
            if self.gamemode == "pictionary":
                self.reset_turn()  # ✅               

    def _on_incoming_message(self, msg_dict: dict):
        """Called for every incoming chat message — override or hook in main."""
        # Stores on self so main loop can read it
        if not hasattr(self, 'incoming_chat'):
            self.incoming_chat = []
        self.incoming_chat.append((msg_dict.get("uid", "?"), msg_dict.get("message", "")))

    ##Pictionary Methods
    def _evaluate_game_state(self):
        players = self.firebase.fetch_ordered_players()
        enough_players = len(players) >= 2
        round_active = self.game_state.get("round_active", False)
        current_drawer = self.game_state.get("current_drawer")

        self.i_am_drawer = (current_drawer == self.firebase.user_id)

        # Start a new round if no active round and enough players
        # Only the player with order=0 (or lowest order present) acts as host
        if enough_players and not round_active and players and players[0] == self.firebase.user_id:
            self._start_new_round(players)    
            
    def _start_new_round(self, players: list):
        turn_index = self.game_state.get("turn_index", 0)
        next_index = turn_index % len(players)
        drawer_uid = players[next_index]
        word = random.choice(self.firebase.FRUIT_POOL)
        print(f"[Game] New round — drawer: {drawer_uid}, word: {word}, i_am_drawer: {self.i_am_drawer}")
        self.firebase.push_game_state(next_index, drawer_uid, word)
        self.game_state = self.firebase.fetch_game_state()
        self.i_am_drawer = (drawer_uid == self.firebase.user_id)
        if self.i_am_drawer:
            self.current_word = word
            print(f"[Game] My word is: {self.current_word}")  # ✅
            self.firebase.push_clear()

    def check_guess(self, guess: str) -> bool:
        with self._game_state_lock:
            game_state = dict(self.game_state)
        word = game_state.get("current_word", "")
        print(f"[Game] Checking guess: '{guess}' against word: '{word}'")
        if word and guess.strip().lower() == word.lower():
            print(f"[Game] Correct guess by {self.firebase.user_id}!")
            turn_index = game_state.get("turn_index", 0)
            # ✅ Push in background — don't block main thread
            threading.Thread(
                target=self._end_round_async,
                args=(turn_index + 1,),
                daemon=True
            ).start()
            return True
        return False

    def _end_round_async(self, next_turn_index: int):
        self.firebase.push_game_state(next_turn_index, "", "")
        self.firebase.end_round()
        self.firebase.push_clear()
        self.get_clear_command()
        

    def is_input_locked(self) -> bool:
        """Uses cached players — no network call."""
        if self.gamemode != "pictionary":
            return False
        with self._game_state_lock:
            players = list(self._ordered_players_cache)
        return len(players) >= 2 and not self.i_am_drawer      
    
    # Add these new methods
    def _fetch_game_state_async(self):
        """Runs in background thread — no blocking on main loop."""
        try:
            game_state = self.firebase.fetch_game_state()
            players    = self.firebase.fetch_ordered_players()
            with self._game_state_lock:
                self.game_state = game_state
                self._ordered_players_cache = players
            self._evaluate_game_state_cached()
        finally:
            self._fetching_game_state = False

    def _fetch_players_async(self):
        try:
            players = self.firebase.fetch_active_players()
            with self._game_state_lock:
                current_count = len(players)
                last_count    = self._last_player_count

                self.active_players      = players
                self._last_player_count  = current_count

            #reset turn index
            if self.gamemode == "pictionary" and current_count != last_count and last_count != 0:
                print(f"[Game] Player count changed {last_count} → {current_count}, resetting turn index.")
                self.firebase.reset_turn()
        finally:
            self._fetching_players = False         

    def _evaluate_game_state_cached(self):
        with self._game_state_lock:
            players    = list(self._ordered_players_cache)
            game_state = dict(self.game_state)

        current_drawer = game_state.get("current_drawer")
        round_active   = game_state.get("round_active", False)

        with self._game_state_lock:
            self.i_am_drawer = (current_drawer == self.firebase.user_id)
            #sync current_word from Firebase for the new drawer
            if self.i_am_drawer and round_active:
                self.current_word = game_state.get("current_word", "")
            elif not self.i_am_drawer:
                self.current_word = None  #Guessers never see the word

        enough_players = len(players) >= 2
        print(f"[Game] players={players}, enough={enough_players}, round_active={round_active}, drawer={current_drawer}, me={self.firebase.user_id}")

        if enough_players and not round_active and players and players[0] == self.firebase.user_id:
            self._start_new_round(players)
