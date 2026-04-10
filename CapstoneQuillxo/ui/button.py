import pygame
from CapstoneQuillxo.core import Color
 
class Button:
    def __init__(self, text, coords, action, screen, font):
        self.screen = screen
        self.x, self.y = coords
        self.action = action
        self.text = text
        self.font = font
        self.text_surf = font.render(text, True, Color.BLACK.value)
        
        self.width = 150
        self.height = 25
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        if self.check_hover():
            color = (26, 122, 84)   # hover color
        else:
            color = (44, 201, 138)      # normal color
        pygame.draw.rect(self.screen, color, self.rect, 0, 5)

        # Border
        pygame.draw.rect(self.screen, Color.BLACK.value, self.rect, 2, 5)
        surface.blit(self.text_surf, (self.x + 3, self.y + 3))

    def check_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) 
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.check_hover():
                self.action()
                print(f"{self.text} button triggered.")
                return True
        return False