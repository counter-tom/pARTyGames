import uuid
import pygame
from core.user import User
from core.color import Color
from canvas.master_canvas import MasterCanvas
from network import FirebaseClient
from network.stroke_deserializer import deserialize_stroke
from commands import DrawStrokeCommand
from commands.clear_canvas_command import ClearCanvasCommand

class UserManager:
    def __init__(self, room_name):
        self.users = {}
        self._next_id = 0
        self.master = MasterCanvas()
        self.active_user_id = 0
        self.room_name = room_name
        self.firebase = FirebaseClient(room_id=self.room_name, user_id=str(uuid.uuid4())[:8])
        self.firebase.connect()
        self.firebase.start_listener()
        self._pending_initial_strokes = self.firebase.fetch_strokes()

    def get_active_user(self):
        return self.users.get(self.active_user_id)

    def add_user(self, screen):
        user_id = self._next_id
        self._next_id += 1
        color = Color.BLACK

        self.users[user_id] = User(screen, user_id, color)
        self.master.register(user_id, self.users[user_id].canvas)

    def update(self, is_cursor_on_ui, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                pass

        # Replay initial strokes on first update
        if self._pending_initial_strokes:
            active_user = self.users.get(self.active_user_id)
            if active_user is not None:
                for stroke_dict in self._pending_initial_strokes:
                    stroke = deserialize_stroke(stroke_dict)
                    cmd = DrawStrokeCommand(active_user.canvas, stroke)
                    cmd.do()
                # Mark last pushed so none of these get re-pushed
                if active_user.canvas.strokes:
                    active_user.canvas._last_pushed_stroke = active_user.canvas.strokes[-1]
            self._pending_initial_strokes = []

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
                    else:
                        cmd = DrawStrokeCommand(active_user.canvas, stroke)
                        cmd.do()

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