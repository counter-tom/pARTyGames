import pygame
from CapstoneQuillxo.ui.button import Button

class ButtonManager:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []
        self.is_hovering_ui = False
        self.font = pygame.font.Font('freesansbold.ttf', 18)


    def add_button(self, text, coords, action):
        self.buttons.append(Button(text, coords, action, self.screen, self.font))

    def handle_events(self, event):
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        self.is_hovering_ui = any(button.check_hover() for button in self.buttons)

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)