import pygame

class PaintDot:
    def __init__(self, size, coords, color, alpha=255, shape="circle"):
        self.surf = pygame.Surface((size, size), pygame.SRCALPHA)
        self.x = coords[0] - self.surf.get_width() / 2
        self.y = coords[1] - self.surf.get_height() / 2

        if hasattr(color, "value"):
            rgb_color = color.value
        else:
            rgb_color = color

        rgba = (rgb_color[0], rgb_color[1], rgb_color[2], alpha)

        if shape == "circle":
            pygame.draw.circle(self.surf, rgba, (size // 2, size // 2), size // 2)
        elif shape == "square":
            self.surf.fill(rgba)

    def color_change(self, color):
        if hasattr(color, "value"):
            rgb_color = color.value
        else:
            rgb_color = color
        self.surf.fill(rgb_color)