import pygame
from CapstoneQuillxo.core.user import User
from CapstoneQuillxo.core.color import Color
from CapstoneQuillxo.canvas.master_canvas import MasterCanvas

class UserManager():
    def __init__(self):
        self.users = {}
        self._next_id = 0
        self.master = MasterCanvas()
        
        #Artifcat of testing with single device
        self.active_user_id = 0

    def get_active_user(self):
        return self.users.get(self.active_user_id)
    
    def add_user(self, screen):
        user_id = self._next_id
        self._next_id += 1
        color = Color.BLACK
        
        if user_id > 1:
            color = Color.GREY

        self.users[user_id] = User(screen, user_id, color)
        self.master.register(user_id, self.users[user_id].canvas)
    
    def update(self, is_cursor_on_button, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_k and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self._cycle_active_user()

        active_user = self.users.get(self.active_user_id)
        active_user.update(is_cursor_on_button)
        self.master.composite()
        self.master.broadcast()

        

    def _cycle_active_user(self):
        user_ids = list(self.users.keys())
        current_index =  user_ids.index(self.active_user_id)
        next_index = (current_index + 1) % len(user_ids)
        self.active_user_id = user_ids[next_index]
        print("Active User: " + str(self.active_user_id))