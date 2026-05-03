import asyncio  # Required for web
import pygame
from commands import ClearCanvasCommand
from core import UserManager
from core.color import Color, Tool
from ui import ButtonManager
from ui.rgb_picker import RGBPicker
from menu.menu_system import menu_start_async
from ui.tool_grid import ToolGrid

#TODO add guessing game mode
##TODO add sidebar that displays joined users.
####Then add a score counter on certain gamemodes. Wire it to firebase

#TODO fix chat messages. Chat messages need to wrap around to the next line.

def wrap_text(text, font, max_width):
    """Break `text` into a list of lines that each fit within `max_width` pixels."""
    words = text.split(' ')
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word  # start a new line with this word
    if current:
        lines.append(current)
    return lines


async def main():
    #Begin Menu
    menu_session_info = await menu_start_async()
    room_name = menu_session_info[0]
    gamemode  = menu_session_info[1] if len(menu_session_info) > 1 else "freedraw"
    print("Room name: " + room_name)
    #Fetch gamemode BEFORE creating umanager if joiner
    if gamemode == "fetch":
        from network import FirebaseClient
        import uuid
        temp_client = FirebaseClient(room_id=room_name, user_id=str(uuid.uuid4())[:8])
        gamemode = temp_client.fetch_gamemode()
        print(f"[Game] Fetched gamemode from Firebase: {gamemode}")

    in_lobby = True

    #Prevent the canvas from being marked when starting it
    while pygame.mouse.get_pressed()[0]:
        pygame.event.pump()
        await asyncio.sleep(0)

    pygame.event.clear()

    #Begin Game
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((1160, 640))
    pygame.display.set_caption("pARTyGames")
    font = pygame.font.Font("freesansbold.ttf", 18)

    umanager = UserManager(room_name, gamemode=gamemode)
    umanager.firebase.push_gamemode(gamemode)
    umanager.add_user(screen)

    running = True
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    menu_open = False

    top_buttons = ButtonManager(screen)
    tool_grid = ToolGrid(screen, 665, 140, font, columns=3)

    top_buttons.add_button("Clear", (665, 10), lambda: umanager.get_clear_command())
    top_buttons.add_button("Undo",  (665, 45),  lambda: umanager.get_active_user().commander.undo())
    top_buttons.add_button("Redo",  (665, 80),  lambda: umanager.get_active_user().commander.redo())

    tool_grid.add_tool(Tool.NEUTRAL, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.BUCKET), image_path="assets/neutral.png",
    selected_image_path="assets/neutral_selected.png", label="NEU")
    tool_grid.add_tool(Tool.BRUSH, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.BRUSH), image_path="assets/brush.png",
    selected_image_path="assets/brush_selected.png", label="PEN")
    tool_grid.add_tool(Tool.SPRAY, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.SPRAY), image_path="assets/spray.png",
    selected_image_path="assets/spray_selected.png", label="SPR")
    tool_grid.add_tool(Tool.MARKER, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.MARKER), image_path="assets/marker.png",
    selected_image_path="assets/marker_selected.png", label="MAR")
    tool_grid.add_tool(Tool.BUCKET, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.BUCKET), image_path="assets/bucket.png",
    selected_image_path="assets/bucket_selected.png", label="BUC")
    tool_grid.add_tool(Tool.LINE, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.LINE), image_path="assets/line.png",
    selected_image_path="assets/line_selected.png", label="LIN")
    tool_grid.add_tool(Tool.EYEDROPPER, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.EYEDROPPER), image_path="assets/eyedropper.png",
    selected_image_path="assets/eyedropper_selected.png", label="EYE")
    tool_grid.add_tool(Tool.ERASER, lambda: setattr(umanager.get_active_user().cursor, "tool", Tool.ERASER), image_path="assets/eraser.png",
    selected_image_path="assets/eraser_selected.png", label="ERA")

    rgb_picker = RGBPicker(screen, 700, 370, font)
    all_button_rect  = pygame.Rect(640, 0,   260, 900)
    menu_button_rect = pygame.Rect(665, 115, 150,  25)

    active_user = umanager.get_active_user()
    if active_user is not None:
        active_user.cursor.rgb_picker = rgb_picker

    # Chatroom variables
    chat_messages = []
    chat_text = ""
    chat_active = False
    chat_color_inactive = pygame.Color('gray')
    chat_color_active   = pygame.Color('dodgerblue')
    chat_color = chat_color_inactive

    chat_input_box    = pygame.Rect(905, 600, 250, 35)   # Input bar at the bottom
    chat_display_rect = pygame.Rect(905,   5, 250, 585)  # Message area above it
    chatroom_rect     = pygame.Rect(900,   0, 260, 640)

    def draw_outlined_text(surface, text, font, pos, text_color, outline_color):
        x, y = pos

        # Render outline (offset in 8 directions)
        outline_surface = font.render(text, True, outline_color)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    surface.blit(outline_surface, (x + dx, y + dy))

        # Render main text
        text_surface = font.render(text, True, text_color)
        surface.blit(text_surface, (x, y))

    try:
        while running:
            screen.fill(Color.PURPLE.value)
            events = pygame.event.get()

            top_buttons.update()
            if menu_open:
                tool_grid.update()
            input_locked = umanager.is_input_locked()    
            for event in events:
                if event.type == pygame.QUIT:
                    running = False  # Use flag instead of SystemExit for cleaner web exit

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if menu_button_rect.collidepoint(event.pos):
                        menu_open = not menu_open
                        continue

                if not input_locked:
                    top_buttons.handle_events(event)
                if menu_open:
                    if not input_locked:
                        tool_grid.handle_events(event)
                    rgb_picker.handle_event(event)

                # Chat event handler
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if chat_input_box.collidepoint(event.pos):
                        chat_active = True
                        chat_color = chat_color_active
                    else:
                        chat_active = False
                        chat_color = chat_color_inactive

                if event.type == pygame.KEYDOWN and chat_active:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if chat_text.strip():
                            if umanager.gamemode == "pictionary" and not umanager.i_am_drawer:
                                umanager.check_guess(chat_text)
                            chat_messages.append((umanager.firebase.user_id, chat_text))  
                            
                            umanager.firebase.push_chat_message(chat_text)                
                            chat_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        chat_text = chat_text[:-1]
                    else:
                        chat_text += event.unicode

            active_user = umanager.get_active_user()
            if active_user is not None:
                active_user.color = rgb_picker.get_color()
                active_user.cursor.color = active_user.color
                active_user.cursor.rgb_picker = rgb_picker
            #TODO fix
            

            hovering_ui = (top_buttons.is_hovering_ui
                        or menu_button_rect.collidepoint(pygame.mouse.get_pos())
                        or all_button_rect.collidepoint(pygame.mouse.get_pos())
                        or chatroom_rect.collidepoint(pygame.mouse.get_pos())
                        or input_locked) 
            
            if menu_open:
                hovering_ui = hovering_ui or tool_grid.is_hovering_ui or rgb_picker.is_hovering()

            # Render
            umanager.draw()
            pygame.draw.rect(screen, Color.PURPLE.value, all_button_rect)
            top_buttons.draw(screen)

            # Chat sidebar
            pygame.draw.rect(screen, Color.WHITE.value, chatroom_rect)

            # Draw messages with word-wrap, most recent at the bottom
            line_height = 22
            max_chat_width = chat_display_rect.width - 8  # small side padding

            # Pre-compute wrapped lines for every message
            all_wrapped = []
            for uid, msg in chat_messages:
                first_line = True
                for wrapped_line in wrap_text(f"{uid}: {msg}", font, max_chat_width):
                    all_wrapped.append((wrapped_line, first_line))
                    first_line = False

            # Only show as many lines as fit in the display area
            visible_lines = chat_display_rect.height // line_height
            visible = all_wrapped[-visible_lines:]

            for i, (line, _) in enumerate(visible):
                msg_surface = font.render(line, True, (0, 0, 0))
                screen.blit(msg_surface, (chat_display_rect.x + 4, chat_display_rect.y + i * line_height))

            # Divider line between messages and input
            pygame.draw.line(screen, pygame.Color('gray'), (900, 595), (1160, 595), 2)

            # Input box
            chat_txt_surface = font.render(chat_text, True, (0, 0, 0))
            screen.blit(chat_txt_surface, (chat_input_box.x + 5, chat_input_box.y + 5))
            pygame.draw.rect(screen, chat_color, chat_input_box, 2)

            # Menu toggle button
            btn_color = (Color.BUTTON_ACTIVE_GREY.value
                         if menu_button_rect.collidepoint(pygame.mouse.get_pos())
                         else Color.BUTTON_INACTIVE_GREY.value)
            pygame.draw.rect(screen, btn_color,          menu_button_rect, 0, 5)
            pygame.draw.rect(screen, Color.BLACK.value,  menu_button_rect, 2, 5)
            menu_text = font.render("Hide Menu" if menu_open else "Show Menu", True, Color.BLACK.value)
            screen.blit(menu_text, (menu_button_rect.x + 8, menu_button_rect.y + 3))

            if menu_open:
                pygame.draw.rect(screen, (201, 138, 44),   (650, 135, 240, 495))
                pygame.draw.rect(screen, Color.BLACK.value, (650, 135, 240, 495), 2)

                active_user = umanager.get_active_user()
                if active_user is not None:
                    tool_grid.draw(active_user.cursor.tool)

                rgb_picker.draw()

            umanager.draw_cursor()


            if umanager.i_am_drawer and umanager.current_word:
                draw_outlined_text(
                    screen,
                    f"Draw: {umanager.current_word}",
                    font,
                    (10, 10),
                    (255, 255, 255),
                    (0, 0, 0)
                )

            elif umanager.gamemode == "pictionary" and not umanager.i_am_drawer:
                draw_outlined_text(
                    screen,
                    "Guess the drawing!",
                    font,
                    (10, 10),
                    (255, 255, 255),
                    (0, 0, 0)
                )

            # Update (includes Firebase push/pull)
            umanager.update(hovering_ui, events)

            # Receive incoming chat messages from Firebase
            for uid, msg in getattr(umanager, 'incoming_chat', []):
                chat_messages.append((uid, msg))
            umanager.incoming_chat = []

            pygame.display.flip()

            # WEB ESSENTIALS
            await asyncio.sleep(0)  # Mandatory: yields control back to the browser
            clock.tick(60)

    finally:
        if in_lobby:
            umanager.on_exit()

    pygame.quit()

# Entry point
if __name__ == "__main__":
    asyncio.run(main())