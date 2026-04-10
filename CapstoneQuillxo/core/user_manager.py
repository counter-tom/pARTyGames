import uuid
import pygame
from CapstoneQuillxo.core.user import User
from CapstoneQuillxo.core.color import Color
from CapstoneQuillxo.canvas.master_canvas import MasterCanvas
from CapstoneQuillxo.network import FirebaseClient
from CapstoneQuillxo.network.stroke_deserializer import deserialize_stroke
from CapstoneQuillxo.commands import DrawStrokeCommand
from CapstoneQuillxo.commands.clear_canvas_command import ClearCanvasCommand

class UserManager:
    def __init__(self):
        self.users = {}
        self._next_id = 0
        self.master = MasterCanvas()
        self.active_user_id = 0

        self.firebase = FirebaseClient(room_id="room1", user_id=str(uuid.uuid4())[:8])
        self.firebase.connect()
        self.firebase.start_listener()

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

        active_user = self.users.get(self.active_user_id)
        if active_user is not None:
            active_user.update(is_cursor_on_ui)

            canvas = active_user.canvas

            # Lazy-init tracking attribute (avoids touching PaintCanvas)
            if not hasattr(canvas, '_last_pushed_stroke'):
                canvas._last_pushed_stroke = None

            # Push the latest stroke to Firebase if it's new
            if canvas.strokes and canvas.strokes[-1] is not canvas._last_pushed_stroke:
                latest = canvas.strokes[-1]
                canvas._last_pushed_stroke = latest
                if not latest.remote:          # <-- only push local strokes
                    self.firebase.push_stroke(latest, active_user.color)

        # Apply incoming remote strokes onto the active canvas
        for stroke_dict in self.firebase.pop_incoming_strokes():
            stroke = deserialize_stroke(stroke_dict)
            if active_user is not None:
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