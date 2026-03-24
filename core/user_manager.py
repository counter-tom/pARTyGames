import uuid
import pygame
from CapstoneQuillxo.core.user import User
from CapstoneQuillxo.core.color import Color
from CapstoneQuillxo.canvas.master_canvas import MasterCanvas
from CapstoneQuillxo.network import FirebaseClient
from CapstoneQuillxo.network.stroke_deserializer import deserialize_stroke
from CapstoneQuillxo.commands import DrawStrokeCommand

class UserManager():
    def __init__(self):
        self.users = {}
        self._next_id = 0
        self.master = MasterCanvas()
        
        # Artifact of testing with single device
        self.active_user_id = 0

        self.firebase = FirebaseClient(room_id="room1", user_id=str(uuid.uuid4())[:8])
        self.firebase.connect()
        self.firebase.start_listener()

    def get_active_user(self):
        return self.users.get(self.active_user_id)
        #return None  # No active user concept when artifact removed

    def add_user(self, screen):
        user_id = self._next_id
        self._next_id += 1
        color = Color.BLACK
        
        # Artifact of testing with single device
        # if user_id > 1:
        #     color = Color.GREY

        self.users[user_id] = User(screen, user_id, color)
        self.master.register(user_id, self.users[user_id].canvas)

    def update(self, is_cursor_on_button, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Artifact of single-user cycling
                # if event.key == pygame.K_k and pygame.key.get_mods() & pygame.KMOD_CTRL:
                #     self._cycle_active_user()
                pass

        # Artifact: active user update
        # active_user = self.users.get(self.active_user_id)
        # active_user.update(is_cursor_on_button)

        # Instead: update all users normally
        for user in self.users.values():
            user.update(is_cursor_on_button)

        self.master.composite()
        self.master.broadcast()

        for stroke_dict in self.firebase.pop_incoming_strokes():
            stroke = deserialize_stroke(stroke_dict)
            for canvas in self.master.canvases.values():
                cmd = DrawStrokeCommand(canvas, stroke)
                cmd.do()

    # Artifact of single-user testing
    # def _cycle_active_user(self):
    #     user_ids = list(self.users.keys())
    #     current_index = user_ids.index(self.active_user_id)
    #     next_index = (current_index + 1) % len(user_ids)
    #     self.active_user_id = user_ids[next_index]
    #     print("Active User: " + str(self.active_user_id))
