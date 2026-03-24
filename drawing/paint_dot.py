import pygame

class PaintDot:
    def __init__(self, size, coords, color):
        self.surf = pygame.Surface((size, size))
        self.x = coords[0] - self.surf.get_width() / 2
        self.y = coords[1] - self.surf.get_height() / 2
        self.surf.fill(color.value)

    def color_change(self, color):
        self.surf.fill(color.value)