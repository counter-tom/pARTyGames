import asyncio  # Required for web
import sys
import pygame
from commands import ClearCanvasCommand
from core import UserManager
from core.color import Color, Tool
from ui import ButtonManager
from ui.rgb_picker import RGBPicker
from menu.menu_system import menu_start_async

# --- ASYNC MAIN WRAPPER ---
async def main():
    # Begin Menu — pygame.init() is called inside menu_start_async
    menu_session_info = await menu_start_async()
    room_name = menu_session_info[0]
    print(f"[Debug] Menu done, room: {room_name}")
    print(f"[Debug] IS_WEB = {sys.platform}")

    # Test js module availability
    try:
        import js
        print(f"[Debug] js module available: {js.window.firebaseDB}")
    except Exception as e:
        print(f"[Debug] js module error: {e}")

    # Begin Game — reuse existing pygame display, don't reinitialize
    screen = pygame.display.set_mode((900, 640))
    print(f"[Debug] Screen created: {screen}")
    pygame.display.set_caption("CapstoneQuillxo")
    font = pygame.font.Font("freesansbold.ttf", 18)
    print(f"[Debug] Font loaded")

    umanager = UserManager(room_name)
    print(f"[Debug] UserManager created")
    umanager.add_user(screen)
    print(f"[Debug] User added, starting game loop")

    running = True
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    menu_open = False

    top_buttons = ButtonManager(screen)
    tool_buttons = ButtonManager(screen)

    top_buttons.add_button("Clear", (665, 10), lambda: umanager.get_clear_command())
    top_buttons.add_button("Undo",  (665, 45),  lambda: umanager.get_active_user().commander.undo())
    top_buttons.add_button("Redo",  (665, 80),  lambda: umanager.get_active_user().commander.redo())

    tool_buttons.add_button("Brush",  (665, 140), lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.BRUSH))
    tool_buttons.add_button("Spray",  (665, 175), lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.SPRAY))
    tool_buttons.add_button("Marker", (665, 210), lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.MARKER))
    tool_buttons.add_button("Bucket", (665, 245), lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.BUCKET))
    tool_buttons.add_button("Line",   (665, 280), lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.LINE))

    rgb_picker = RGBPicker(screen, 700, 370, font)
    all_button_rect  = pygame.Rect(640, 0,   260, 900)
    menu_button_rect = pygame.Rect(665, 115, 150,  25)

    while running:
        screen.fill(Color.PURPLE.value)
        events = pygame.event.get()

        top_buttons.update()
        if menu_open:
            tool_buttons.update()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if menu_button_rect.collidepoint(event.pos):
                    menu_open = not menu_open
                    continue

            top_buttons.handle_events(event)
            if menu_open:
                tool_buttons.handle_events(event)
                rgb_picker.handle_event(event)

        active_user = umanager.get_active_user()
        if active_user is not None:
            active_user.color = rgb_picker.get_color()
            active_user.cursor.color = active_user.color

        hovering_ui = top_buttons.is_hovering_ui or menu_button_rect.collidepoint(pygame.mouse.get_pos())
        if menu_open:
            hovering_ui = hovering_ui or tool_buttons.is_hovering_ui or rgb_picker.is_hovering()

        # Update first, then render
        umanager.update(hovering_ui, events)

        # Render
        umanager.draw()
        pygame.draw.rect(screen, Color.PURPLE.value, all_button_rect)
        top_buttons.draw(screen)

        btn_color = (Color.BUTTON_ACTIVE_GREY.value
                     if menu_button_rect.collidepoint(pygame.mouse.get_pos())
                     else Color.BUTTON_INACTIVE_GREY.value)
        pygame.draw.rect(screen, btn_color, menu_button_rect, 0, 5)
        pygame.draw.rect(screen, Color.BLACK.value,  menu_button_rect, 2, 5)
        menu_text = font.render("Hide Menu" if menu_open else "Show Menu", True, Color.BLACK.value)
        screen.blit(menu_text, (menu_button_rect.x + 8, menu_button_rect.y + 3))

        if menu_open:
            pygame.draw.rect(screen, (201, 138, 44),   (650, 135, 240, 495))
            pygame.draw.rect(screen, Color.BLACK.value, (650, 135, 240, 495), 2)
            tool_buttons.draw(screen)
            rgb_picker.draw()

        umanager.draw_cursor()

        pygame.display.flip()

        # --- WEB ESSENTIALS ---
        await asyncio.sleep(0)
        clock.tick(60)

    pygame.quit()

# Entry point
if __name__ == "__main__":
    asyncio.run(main())