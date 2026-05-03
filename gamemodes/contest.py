"""
gamemodes/contest.py

Contest gamemode — each player draws the same word on their own canvas,
then canvases are shown one at a time for rating.

Phases:
  drawing  → 30 seconds, everyone draws
  rating   → 10 seconds per player, canvases shown one at a time
  results  → 10 seconds, winner displayed
  (repeat)
"""

import time
import threading
import pygame



DRAWING_DURATION = 30   # seconds
RATING_DURATION  = 10   # seconds per player
RESULTS_DURATION = 10   # seconds

PHASE_DRAWING = "drawing"
PHASE_RATING  = "rating"
PHASE_RESULTS = "results"


class ContestGame:
    """
    Owns all contest-specific state and rendering.
    Communicates with Firebase via umanager.firebase.
    """

    def __init__(self, umanager, screen, font):
        self.umanager  = umanager
        self.firebase  = umanager.firebase
        self.screen    = screen
        self.font      = font
        self.small_font = pygame.font.Font(None, 28)

        # Phase state (read from Firebase, polled every 2s)
        self.phase               = PHASE_DRAWING
        self.current_word        = ""
        self.phase_start_ts      = time.time()
        self.player_order        = []
        self.current_rating_idx  = 0

        # Rating UI
        self.my_rating           = 0   # 0 = not rated yet this interval
        self.ratings_submitted   = {}  # rated_uid -> my score I gave
        self._rating_buttons     = []  # list of pygame.Rect
        self._build_rating_buttons()

        # Canvas cache — uid -> pygame.Surface fetched from Firebase
        self._canvas_cache       = {}
        self._fetching_canvas    = False

        # Results
        self.winner_uid          = ""
        self.final_scores        = {}  # uid -> average score

        # Polling
        self._last_state_poll    = 0.0
        self._state_poll_interval = 2.0
        self._fetching_state     = False

        # Phase transition lock — only lowest-order player drives transitions
        self._transition_lock       = threading.Lock()
        # ✅ Track phase_start_ts so we detect new rounds for ALL clients
        self._last_seen_phase_start = 0.0
        self._contest_initialised = False
        self._my_contest_strokes = []

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_rating_buttons(self):
        """Build 5 rating buttons centered at the bottom of the canvas area."""
        self._rating_buttons = []
        btn_w, btn_h = 80, 50
        gap          = 15
        total_w      = 5 * btn_w + 4 * gap
        start_x      = (640 - total_w) // 2  # canvas is 640px wide
        y            = 640 - btn_h - 20
        for i in range(5):
            x = start_x + i * (btn_w + gap)
            self._rating_buttons.append(pygame.Rect(x, y, btn_w, btn_h))

    # ── Update (called every frame from main loop) ────────────────────────────

    def update(self):
        """Poll Firebase for phase changes and drive timer-based transitions."""
        
        now = time.time()
        if now - self._last_state_poll > self._state_poll_interval:
            self._last_state_poll = now
            if not self._fetching_state:
                self._fetching_state = True
                threading.Thread(target=self._poll_state_async, daemon=True).start()

    def _poll_state_async(self):
        try:
            state = self.firebase.fetch_contest_state()
            if not state:
                players = self.firebase.fetch_ordered_players()
                if players and players[0] == self.firebase.user_id and not self._contest_initialised:
                    self._contest_initialised = True  # ✅ Only init once
                    self._init_contest(players)
                return

            self.phase              = state.get("phase", PHASE_DRAWING)
            self.current_word       = state.get("current_word", "")
            self.phase_start_ts     = state.get("phase_start_ts", time.time())
            self.current_rating_idx = state.get("current_rating_index", 0)

            # ✅ Firebase returns JSON arrays as {"0": v, "1": v} dicts via REST
            player_order_raw = state.get("player_order", [])
            if isinstance(player_order_raw, dict):
                self.player_order = [player_order_raw[str(i)] for i in range(len(player_order_raw))]
            else:
                self.player_order = list(player_order_raw)

            # ✅ Detect new drawing phase (new round) for ALL clients — clear local canvas
            if (self.phase == PHASE_DRAWING
                    and self.phase_start_ts != self._last_seen_phase_start
                    and self._last_seen_phase_start != 0.0):
                print("[Contest] New round detected — clearing local canvas.")
                active_user = self.umanager.get_active_user()
                if active_user is not None:
                    active_user.canvas.clear()
                    print('_poll_state_async() -> canvas.clear() called')
                    active_user.canvas._last_pushed_stroke = None
            self._last_seen_phase_start = self.phase_start_ts

            # Drive phase transitions — only lowest-order active player acts
            players = self.firebase.fetch_ordered_players()
            i_am_coordinator = players and players[0] == self.firebase.user_id
            elapsed = time.time() - self.phase_start_ts

            if i_am_coordinator:
                if self.phase == PHASE_DRAWING and elapsed >= DRAWING_DURATION:
                    self._transition_to_rating(players)
                elif self.phase == PHASE_RATING and elapsed >= RATING_DURATION:
                    next_idx = self.current_rating_idx + 1
                    if next_idx >= len(self.player_order):
                        self._transition_to_results()
                    else:
                        self._advance_rating(next_idx)
                elif self.phase == PHASE_RESULTS and elapsed >= RESULTS_DURATION:
                    self._restart_contest(players)

            # Fetch canvas to display during rating phase
            if self.phase == PHASE_RATING and 0 <= self.current_rating_idx < len(self.player_order):
                uid_to_show = self.player_order[self.current_rating_idx]
                if uid_to_show not in self._canvas_cache and not self._fetching_canvas:
                    self._fetching_canvas = True
                    threading.Thread(
                        target=self._fetch_canvas_async,
                        args=(uid_to_show,),
                        daemon=True
                    ).start()

            # Compute results if in results phase
            if self.phase == PHASE_RESULTS and not self.final_scores:
                self._compute_results_async()

        finally:
            self._fetching_state = False

    # ── Phase transitions ─────────────────────────────────────────────────────

    def _init_contest(self, players):
        import random
        word = random.choice(self.firebase.FRUIT_POOL)
        # ✅ Clear each player's contest strokes before starting
        for uid in players:
            self.firebase.clear_contest_strokes(uid)
            print('clear_contest_strokes() called')
        self.firebase.push_contest_state({
            "phase":                PHASE_DRAWING,
            "current_word":         word,
            "phase_start_ts":       time.time(),
            "player_order":         players,
            "current_rating_index": 0
        })
        self.firebase.clear_contest_ratings(uid)
        print(f"[Contest] Game initialised. Word: {word}, Players: {players}")

    def _transition_to_rating(self, players):
        print("[Contest] Drawing phase ended. Moving to rating.")
        now = time.time()
 
        # ✅ Save own strokes locally before anything is cleared
        self._my_contest_strokes = self.firebase.fetch_contest_strokes(self.firebase.user_id)
        print(f"[Contest] Cached {len(self._my_contest_strokes)} own strokes locally.")
 
        # ✅ Clear local canvas immediately
        active_user = self.umanager.get_active_user()
        if active_user is not None:
            active_user.canvas.clear()
            active_user.canvas._last_pushed_stroke = None
 
        # ✅ Promote first player's strokes using the unified method
        uid_to_show = players[0] if players else None
        if uid_to_show:
            self._promote_strokes_for(uid_to_show)
 
        self.firebase.push_contest_state({
            "phase":                PHASE_RATING,
            "current_word":         self.current_word,
            "phase_start_ts":       now,
            "player_order":         players,
            "current_rating_index": 0
        })
        # ✅ Update local state immediately
        self.phase              = PHASE_RATING
        self.phase_start_ts     = now
        self.current_rating_idx = 0
        self.player_order       = players
        self._canvas_cache      = {}
        self.my_rating          = 0
        print(f"[Contest] _transition_to_rating() -> current_rating_idx: {self.current_rating_idx}")

    def _advance_rating(self, next_idx):
        now = time.time()
        # ✅ Update immediately so next poll sees fresh elapsed time
        self.phase_start_ts     = now
        self.current_rating_idx = next_idx
        self.my_rating          = 0

        active_user = self.umanager.get_active_user()
        if active_user is not None:
            active_user.canvas.clear()
            active_user.canvas._last_pushed_stroke = None

        uid_to_show = self.player_order[next_idx] if next_idx < len(self.player_order) else None
        if uid_to_show:
            self._promote_strokes_for(uid_to_show)  # sleep happens inside here

        self.firebase.push_contest_state({
            "phase":                PHASE_RATING,
            "current_word":         self.current_word,
            "phase_start_ts":       now,
            "player_order":         self.player_order,
            "current_rating_index": next_idx
        })
        print(f"[Contest] Advancing to player index {next_idx}.")

    def _transition_to_results(self):
        print("[Contest] All canvases rated. Moving to results.")
        now = time.time()
        self.firebase.clear_shared_strokes()
        self.firebase.push_contest_state({
            "phase":                PHASE_RESULTS,
            "current_word":         self.current_word,
            "phase_start_ts":       now,
            "player_order":         self.player_order,
            "current_rating_index": 0
        })
        # ✅ Update local state immediately so poll doesn't re-trigger
        self.phase          = PHASE_RESULTS
        self.phase_start_ts = now
        self.final_scores   = {}

    def _restart_contest(self, players):
        self._contest_initialised = True
        print(f"[Contest] _restart_contest called for players: {players}")  # ✅
        self.firebase.clear_shared_strokes()
        import random
        word = random.choice(self.firebase.FRUIT_POOL)
        print(f"[Contest] Restarting. New word: {word}")
        # ✅ Clear each player's strokes
        for uid in players:
            self.firebase.clear_contest_strokes(uid)
            print('clear_contest_strokes() call')
        self.firebase.clear_contest_ratings(uid)
        self._canvas_cache  = {}
        self.final_scores   = {}
        self.my_rating      = 0
        self.ratings_submitted = {}
        self.firebase.push_contest_state({
            "phase":                PHASE_DRAWING,
            "current_word":         word,
            "phase_start_ts":       time.time(),
            "player_order":         players,
            "current_rating_index": 0
        })

    # ── Canvas fetch ──────────────────────────────────────────────────────────

    def _fetch_canvas_async(self, uid):
        try:
            strokes = self.firebase.fetch_contest_strokes(uid)
            if strokes:
                surface = self._render_strokes_to_surface(strokes)
                self._canvas_cache[uid] = surface
            else:
                # Blank canvas placeholder
                surf = pygame.Surface((640, 640))
                surf.fill((255, 255, 255))
                self._canvas_cache[uid] = surf
        finally:
            self._fetching_canvas = False

    def _render_strokes_to_surface(self, stroke_dicts) -> pygame.Surface:
        """Reconstruct a canvas surface from serialised stroke dicts."""
        from network.stroke_deserializer import deserialize_stroke
        surf = pygame.Surface((640, 640))
        surf.fill((255, 255, 255))
        for sd in stroke_dicts:
            try:
                stroke = deserialize_stroke(sd)
                for dot in stroke.dots:
                    surf.blit(dot.surf, (dot.x, dot.y))
            except Exception as e:
                print(f"[Contest] Stroke render error: {e}")
        return surf

    # ── Results ───────────────────────────────────────────────────────────────

    def _compute_results_async(self):
        try:
            all_ratings = self.firebase.fetch_all_contest_ratings()
            # all_ratings: { rated_uid: { rater_uid: score, ... }, ... }
            scores = {}
            for rated_uid, rater_dict in all_ratings.items():
                if isinstance(rater_dict, dict) and rater_dict:
                    avg = sum(rater_dict.values()) / len(rater_dict)
                    scores[rated_uid] = round(avg, 2)
                else:
                    scores[rated_uid] = 0.0
            self.final_scores = scores
            if scores:
                self.winner_uid = max(scores, key=scores.get)
                print(f"[Contest] Winner: {self.winner_uid} with {scores[self.winner_uid]:.2f}/5")
        except Exception as e:
            print(f"[Contest] compute_results error: {e}")

    # ── Input handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        """Call from main event loop. Handles rating button clicks."""
        if self.phase != PHASE_RATING:
            return
        if 0 <= self.current_rating_idx < len(self.player_order):
            uid_being_rated = self.player_order[self.current_rating_idx]
            # Don't rate yourself
            if uid_being_rated == self.firebase.user_id:
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self._rating_buttons):
                if btn.collidepoint(event.pos):
                    score = i + 1  # 1-5
                    self.my_rating = score
                    uid_being_rated = self.player_order[self.current_rating_idx]
                    self.ratings_submitted[uid_being_rated] = score
                    # Push to Firebase in background
                    threading.Thread(
                        target=self.firebase.push_contest_rating,
                        args=(uid_being_rated, self.firebase.user_id, score),
                        daemon=True
                    ).start()
                    print(f"[Contest] Rated {uid_being_rated}: {score}/5")
                    break

    def is_input_locked(self) -> bool:
        """Lock drawing during rating and results phases."""
        return self.phase in (PHASE_RATING, PHASE_RESULTS)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def draw(self):
        """Call after umanager.draw_cursor() in the main render section."""
        if self.phase == PHASE_DRAWING:
            self._draw_drawing_hud()
        elif self.phase == PHASE_RATING:
            self._draw_rating_phase()
        elif self.phase == PHASE_RESULTS:
            self._draw_results()

    def _time_remaining(self) -> int:
        elapsed = time.time() - self.phase_start_ts
        if self.phase == PHASE_DRAWING:
            return max(0, int(DRAWING_DURATION - elapsed))
        elif self.phase == PHASE_RATING:
            return max(0, int(RATING_DURATION - elapsed))
        elif self.phase == PHASE_RESULTS:
            return max(0, int(RESULTS_DURATION - elapsed))
        return 0

    def _draw_drawing_hud(self):
        # Word prompt top-left
        word_surf = self.font.render(
            f"Draw: {self.current_word}", True, (255, 255, 0)
        )
        self.screen.blit(word_surf, (10, 10))

        # Countdown top-right of canvas
        timer_surf = self.font.render(
            f"Time: {self._time_remaining()}s", True, (255, 255, 255)
        )
        self.screen.blit(timer_surf, (640 - timer_surf.get_width() - 10, 10))

    def _draw_rating_phase(self):
        if not self.player_order:
            return
        uid_shown    = self.player_order[self.current_rating_idx] if self.current_rating_idx < len(self.player_order) else ""
        is_my_canvas = (uid_shown == self.firebase.user_id)

        # ✅ No canvas blit needed — umanager.draw() renders shared strokes automatically

        header = f"Rating: {uid_shown}" if not is_my_canvas else "Your drawing!"
        header_surf = self.font.render(header, True, (255, 255, 0))
        self.screen.blit(header_surf, (10, 10))

        # Blit the fetched canvas over the drawing area
        # if uid_shown in self._canvas_cache:
        #     self.screen.blit(self._canvas_cache[uid_shown], (0, 0))
        # else:
            # Loading indicator
        loading = self.font.render("Loading canvas...", True, (200, 200, 200))
        self.screen.blit(loading, (280, 300))

        # Header
        header = f"Rating: {uid_shown}" if not is_my_canvas else "Your drawing!"
        header_surf = self.font.render(header, True, (255, 255, 0))
        self.screen.blit(header_surf, (10, 10))

        # Timer
        timer_surf = self.font.render(f"{self._time_remaining()}s", True, (255, 255, 255))
        self.screen.blit(timer_surf, (640 - timer_surf.get_width() - 10, 10))

        # Progress indicator  e.g. "1 / 3"
        progress = self.small_font.render(
            f"{self.current_rating_idx + 1} / {len(self.player_order)}",
            True, (200, 200, 200)
        )
        self.screen.blit(progress, (10, 35))

        # Rating buttons (hidden if it's your own canvas)
        if not is_my_canvas:
            mouse_pos = pygame.mouse.get_pos()
            for i, btn in enumerate(self._rating_buttons):
                score    = i + 1
                selected = (score == self.my_rating)
                hovered  = btn.collidepoint(mouse_pos)

                if selected:
                    color = (255, 200, 0)   # gold
                elif hovered:
                    color = (150, 210, 255) # light blue
                else:
                    color = (255, 255, 255) # white

                pygame.draw.rect(self.screen, color, btn, border_radius=8)
                pygame.draw.rect(self.screen, (0, 0, 0), btn, 2, border_radius=8)

                label = self.font.render(str(score), True, (0, 0, 0))
                self.screen.blit(label, (
                    btn.centerx - label.get_width() // 2,
                    btn.centery - label.get_height() // 2
                ))
        else:
            msg = self.font.render("Waiting for others to rate...", True, (200, 200, 200))
            self.screen.blit(msg, (640 // 2 - msg.get_width() // 2, 560))

    def _draw_results(self):
        # Semi-transparent overlay over canvas
        overlay = pygame.Surface((640, 640), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        y = 80
        title = self.font.render("Results!", True, (255, 215, 0))
        self.screen.blit(title, (640 // 2 - title.get_width() // 2, y))
        y += 50

        # Scores sorted highest first
        sorted_scores = sorted(self.final_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (uid, score) in enumerate(sorted_scores):
            prefix = "🏆 " if uid == self.winner_uid else f"{rank + 1}. "
            line   = self.font.render(f"{prefix}{uid}: {score:.1f}/5", True, (255, 255, 255))
            self.screen.blit(line, (640 // 2 - line.get_width() // 2, y))
            y += 35

        # Next round countdown
        timer_surf = self.small_font.render(
            f"Next round in {self._time_remaining()}s", True, (180, 180, 180)
        )
        self.screen.blit(timer_surf, (640 // 2 - timer_surf.get_width() // 2, y + 20))

    # ── Stroke push (contest-specific) ───────────────────────────────────────

    def push_stroke(self, stroke, color):
        """
        During drawing phase, push strokes under the player's presence entry
        instead of the shared strokes node.
        """
        if self.phase != PHASE_DRAWING:
            return
        self.firebase.push_contest_stroke(stroke, color)

    def _promote_strokes_for(self, uid: str):
        self.firebase.clear_shared_strokes()
        if uid == self.firebase.user_id:
            print(f"[Contest] Promoting own strokes from local cache ({len(self._my_contest_strokes)})")
            for stroke_dict in self._my_contest_strokes:
                self.firebase._fb_push(
                    f"rooms/{self.firebase.room_id}/strokes",
                    stroke_dict
                )
        else:
            print(f"[Contest] Fetching and promoting strokes for {uid}")
            self.firebase.promote_contest_strokes_to_shared(uid)
        
        time.sleep(1.0)  # ✅ Give SSE time to deliver strokes to all clients