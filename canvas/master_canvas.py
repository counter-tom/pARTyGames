import pygame
from core.color import Color

class MasterCanvas:
    def __init__(self):
        self.surface = pygame.Surface((640, 640))
        self.canvases = {}  # user_id -> PaintCanvas

    def register(self, user_id, canvas):
        self.canvases[user_id] = canvas

    def receive(self, canvas, position=(0, 0)):
        self.surface.blit(canvas.surface, position)

    def composite(self):
        self.surface.fill(Color.WHITE.value)
        for canvas in self.canvases.values():
            self.surface.blit(canvas.surface, (0, 0))
    
    def broadcast(self): 
        for canvas in self.canvases.values():
            canvas.surface.blit(self.surface, (0, 0))
        

       

