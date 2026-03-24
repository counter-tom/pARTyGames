import pygame
from CapstoneQuillxo.commands import ClearCanvasCommand
from CapstoneQuillxo.core import Color, UserManager
from CapstoneQuillxo.ui import ButtonManager


    
# Initial Setup
pygame.init()

# Creates display window and the tuple controls the dimensions of said window
screen = pygame.display.set_mode((640, 640))
umanager = UserManager()
umanager.add_user(screen)
umanager.add_user(screen)
running = True

# Sets frame rate
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

button_manager = ButtonManager(screen)
button_manager.add_button("Clear", (10, 10), lambda: umanager.get_active_user().pass_command(ClearCanvasCommand))
button_manager.add_button("Undo", (200, 10), lambda: umanager.get_active_user().commander.undo())
button_manager.add_button("Redo", (400, 10), lambda: umanager.get_active_user().commander.redo())

while running:
    screen.fill(Color.WHITE.value)
    events = pygame.event.get()
    # 1. Logic
    button_manager.update()
    for event in events:
        if event.type == pygame.QUIT:
            running = False 
        button_manager.handle_events(event)

    umanager.update(button_manager.is_hovering_ui, events)

    # UI and Cursor
    button_manager.draw(screen)

    pygame.display.flip()
    clock.tick(60) 

pygame.quit()