import pygame
import sys
import requests
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("FIREBASE_DATABASE_URL")

# In the browser, os.listdir on the virtual filesystem is unreliable.
# We explicitly list every asset instead.
ASSET_FILES = [
    "arrow",
    "Buster1",
    "Buster2",
    "chudoid1",
    "chudoid2",
    "host",
    "ibtc1",
    "ibtc2",
    "join",
    "pARTy_Logo",
    "quit",
    "settings",
    "speechbutton1",
    "speechbutton2",
    "start",
    "confuzo1",
    "confuzo2",
]

def load_all_images():
    images = {}
    for name in ASSET_FILES:
        path = f"assets/{name}.png"
        try:
            images[name] = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"[Assets] Could not load {path}: {e}")
    return images


def fetch_rooms() -> list:  # returns list of (room_id, gamemode) tuples
    """Fetch all rooms from Firebase. Returns sorted list of (room_id, gamemode) tuples."""
    if not DB_URL:
        print("[Menu] No DB_URL set — cannot fetch rooms.")
        return []
    try:
        url = f"{DB_URL}/rooms.json?shallow=true"  # shallow=true returns only keys, not all data
        response = requests.get(url, timeout=5)
        data = response.json()
        if not data or not isinstance(data, dict):
            return []
        room_ids = sorted(data.keys())
        rooms = []
        for room_id in room_ids:
            try:
                gm_url = f"{DB_URL}/rooms/{room_id}/gamemode.json"
                gm_resp = requests.get(gm_url, timeout=3)
                gamemode = gm_resp.json()
                if not isinstance(gamemode, str):
                    gamemode = "freedraw"
            except Exception:
                gamemode = "freedraw"
            rooms.append((room_id, gamemode))
        return rooms
    except Exception as e:
        print(f"[Menu] fetch_rooms error: {e}")
        return []


def check_room_exists(room_id: str) -> bool:
    """Returns True if the room already exists in Firebase."""
    if not DB_URL:
        return False
    try:
        url = f"{DB_URL}/rooms/{room_id}.json?shallow=true"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data is not None and data != {}
    except Exception as e:
        print(f"[Menu] check_room_exists error: {e}")
        return False


#Gamemode options
GAMEMODES = ["freedraw", "pictionary"]

#Scrollable room list constants 
ROOM_BTN_HEIGHT = 50
ROOM_BTN_GAP    = 10
ROOM_BTN_WIDTH  = 400
SCROLL_SPEED    = 30


async def menu_start_async() -> list:
    """
    Async version of menu_start for pygbag/browser.
    Returns [room_name, gamemode].
      - Host sets gamemode via dropdown.
      - Join returns gamemode="fetch" so main.py reads it from Firebase.
    """
    import asyncio
    pygame.init()

    menu_session_info = ["room1", "freedraw"]

    screen_width  = 900
    screen_height = 640
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("pARTy")

    #Main menu button rects 
    host_button     = pygame.Rect(220, 200, 450, 50)
    join_button     = pygame.Rect(220, 300, 450, 50)
    settings_button = pygame.Rect(220, 400, 450, 50)
    quit_button     = pygame.Rect(220, 500, 450, 50)

    #Shared sub-menu rects 
    arrow_button = pygame.Rect(10, 10, 125, 125)
    start_button = pygame.Rect(screen_width // 2 - 250, screen_height // 2 + 100, 500, 150)
    input_box    = pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 150, 200, 40)

    # Input / color state
    color_inactive = pygame.Color('gray')
    color_active   = pygame.Color('dodgerblue')
    input_color    = color_inactive
    font           = pygame.font.Font(None, 36)
    small_font     = pygame.font.Font(None, 28)
    text           = ""
    active         = False
    room_name      = "room1"

    host_error_msg = ""  # ✅ Shown when room already exists

    #Gamemode dropdown (HOST only) 
    selected_gamemode_index = 0
    dropdown_open  = False
    dropdown_rect  = pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 50, 200, 40)
    dropdown_options = [
        pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 50 + 40 * (i + 1), 200, 40)
        for i in range(len(GAMEMODES))
    ]

    # Join menu - scrollable room list 
    room_list     = []
    selected_room = None
    scroll_offset = 0

    scroll_box_x   = screen_width // 2 - ROOM_BTN_WIDTH // 2
    scroll_box_y   = 140
    scroll_box_w   = ROOM_BTN_WIDTH
    scroll_box_h   = 380
    scroll_box_rect = pygame.Rect(scroll_box_x, scroll_box_y, scroll_box_w, scroll_box_h)

    refresh_rect = pygame.Rect(scroll_box_x, scroll_box_y + scroll_box_h + 10, ROOM_BTN_WIDTH, 35)

    #State machine 
    STATE_MAIN = "main"
    STATE_HOST = "host"
    STATE_JOIN = "join"
    state = STATE_MAIN
    done  = False

    clock       = pygame.time.Clock()
    all_sprites = load_all_images()

    #Main loop 
    while not done:
        events    = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:
                raise SystemExit

            #Main menu 
            if state == STATE_MAIN:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if host_button.collidepoint(event.pos):
                        state         = STATE_HOST
                        text          = ""
                        active        = False
                        input_color   = color_inactive
                        dropdown_open = False
                    elif join_button.collidepoint(event.pos):
                        state         = STATE_JOIN
                        scroll_offset = 0
                        selected_room = None
                        room_list     = fetch_rooms()  
                    elif settings_button.collidepoint(event.pos):
                        print("Settings clicked!")
                    elif quit_button.collidepoint(event.pos):
                        raise SystemExit

            # Host menu 
            elif state == STATE_HOST:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state         = STATE_MAIN
                        text          = ""
                        active        = False
                        input_color   = color_inactive
                        dropdown_open = False
                    elif active:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            room_name = text or "room1"
                            print("Room name set:", room_name)
                            text = ""
                            menu_session_info[0] = room_name
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                            room_name = text or "room1"
                        else:
                            text += event.unicode
                            room_name = text
                            host_error_msg = ""  # ✅ Clear error on new input

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if dropdown_rect.collidepoint(event.pos):
                        dropdown_open = not dropdown_open
                    elif dropdown_open:
                        closed = False
                        for i, opt_rect in enumerate(dropdown_options):
                            if opt_rect.collidepoint(event.pos):
                                selected_gamemode_index = i
                                dropdown_open = False
                                closed = True
                                break
                        if not closed:
                            dropdown_open = False
                    elif input_box.collidepoint(event.pos):
                        active = not active
                        input_color = color_active if active else color_inactive
                    else:
                        active = False
                        input_color = color_inactive

                    if arrow_button.collidepoint(event.pos):
                        state         = STATE_MAIN
                        text          = ""
                        active        = False
                        input_color   = color_inactive
                        dropdown_open = False

                    if start_button.collidepoint(event.pos):
                        if check_room_exists(room_name):
                            host_error_msg = "Error — Room already exists!"  # ✅ Show error
                        else:
                            menu_session_info[0] = room_name
                            menu_session_info[1] = GAMEMODES[selected_gamemode_index]
                            done = True

            #Join menu 
            elif state == STATE_JOIN:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MAIN

                elif event.type == pygame.MOUSEWHEEL:
                    scroll_offset -= event.y * SCROLL_SPEED
                    total_h    = len(room_list) * (ROOM_BTN_HEIGHT + ROOM_BTN_GAP)
                    max_scroll = max(0, total_h - scroll_box_h)
                    scroll_offset = max(0, min(scroll_offset, max_scroll))

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if arrow_button.collidepoint(event.pos):
                        state         = STATE_MAIN
                        selected_room = None

                    elif refresh_rect.collidepoint(event.pos):
                        room_list     = fetch_rooms()
                        scroll_offset = 0
                        selected_room = None

                    elif scroll_box_rect.collidepoint(event.pos):
                        # Map click position to room index accounting for scroll
                        rel_y = event.pos[1] - scroll_box_y + scroll_offset
                        idx   = rel_y // (ROOM_BTN_HEIGHT + ROOM_BTN_GAP)
                        if 0 <= idx < len(room_list):
                            selected_room, _     = room_list[idx]  # unpack (room_id, gamemode)
                            menu_session_info[0] = selected_room
                            menu_session_info[1] = "fetch"
                            print(f"[Menu] Joining room: {selected_room}")
                            done = True  # ✅ Single click selects and joins

        #Rendering 

        if state == STATE_MAIN:
            screen.fill("purple")

            if 'pARTy_Logo' in all_sprites:
                logo = pygame.transform.scale(all_sprites['pARTy_Logo'], (400, 300))
                screen.blit(logo, (screen_width // 2 - 200, -50))

            for key, x, y in [
                ('host',     200, 175),
                ('join',     200, 275),
                ('settings', 200, 375),
                ('quit',     200, 475),
            ]:
                if key in all_sprites:
                    screen.blit(all_sprites[key], (x, y))

            if 'ibtc1' in all_sprites and 'ibtc2' in all_sprites:
                sprite = all_sprites['ibtc2'] if host_button.collidepoint(mouse_pos) else all_sprites['ibtc1']
                screen.blit(sprite, (80, 160))

            if 'chudoid1' in all_sprites and 'chudoid2' in all_sprites:
                sprite = all_sprites['chudoid2'] if join_button.collidepoint(mouse_pos) else all_sprites['chudoid1']
                screen.blit(sprite, (680, 280))

            if 'Buster1' in all_sprites and 'Buster2' in all_sprites:
                sprite = all_sprites['Buster2'] if settings_button.collidepoint(mouse_pos) else all_sprites['Buster1']
                screen.blit(sprite, (80, 380))

            if 'confuzo1' in all_sprites and 'confuzo2' in all_sprites:
                sprite = all_sprites['confuzo2'] if quit_button.collidepoint(mouse_pos) else all_sprites['confuzo1']
                screen.blit(sprite, (680, 500))

        elif state == STATE_HOST:
            screen.fill((232, 105, 186))

            if 'arrow' in all_sprites:
                if arrow_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['arrow'], (120, 120)), (10, 10))
                else:
                    screen.blit(all_sprites['arrow'], (20, 20))

            if 'start' in all_sprites:
                if start_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['start'], (600, 150)), (screen_width // 2 - 300, 425))
                else:
                    screen.blit(all_sprites['start'], (screen_width // 2 - 250, 450))

            screen.blit(font.render("Enter room name.", True, (255, 255, 255)),
                        (screen_width // 2 - 120, screen_height // 2 - 100))

            txt_surface = font.render(text, True, (255, 255, 255))
            input_box.w = max(200, txt_surface.get_width() + 10)
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(screen, input_color, input_box, 2)

            if room_name:
                screen.blit(font.render(f"Room: {room_name}", True, (255, 255, 255)),
                            (screen_width // 2 - 100, screen_height // 2 - 200))

            if host_error_msg:
                err_surface = small_font.render(host_error_msg, True, (255, 80, 80))
                screen.blit(err_surface, (screen_width // 2 - err_surface.get_width() // 2,
                                          screen_height // 2 + 70))

            pygame.draw.rect(screen, (255, 255, 255), dropdown_rect)
            pygame.draw.rect(screen, (0, 0, 0),       dropdown_rect, 2)
            screen.blit(
                font.render(f"Mode: {GAMEMODES[selected_gamemode_index]}", True, (0, 0, 0)),
                (dropdown_rect.x + 5, dropdown_rect.y + 8)
            )

            if dropdown_open:
                for i, opt_rect in enumerate(dropdown_options):
                    bg = (200, 230, 255) if i == selected_gamemode_index else (255, 255, 255)
                    pygame.draw.rect(screen, bg,        opt_rect)
                    pygame.draw.rect(screen, (0, 0, 0), opt_rect, 1)
                    screen.blit(
                        font.render(GAMEMODES[i], True, (0, 0, 0)),
                        (opt_rect.x + 5, opt_rect.y + 8)
                    )

        elif state == STATE_JOIN:
            screen.fill((100, 180, 232))

            # Arrow
            if 'arrow' in all_sprites:
                if arrow_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['arrow'], (120, 120)), (10, 10))
                else:
                    screen.blit(all_sprites['arrow'], (20, 20))

            # Title
            screen.blit(font.render("Select a Room", True, (255, 255, 255)),
                        (screen_width // 2 - 90, 100))

            # Scrollable box background
            pygame.draw.rect(screen, (70, 130, 180), scroll_box_rect)
            pygame.draw.rect(screen, (255, 255, 255), scroll_box_rect, 2)

            #Room buttons rendered onto a clipped surface 
            clip_surface = pygame.Surface((scroll_box_w, scroll_box_h), pygame.SRCALPHA)

            if not room_list:
                msg = small_font.render("No rooms found. Press Refresh.", True, (255, 255, 255))
                clip_surface.blit(msg, (scroll_box_w // 2 - msg.get_width() // 2, 20))
            else:
                for i, (rid, gm) in enumerate(room_list):
                    btn_y    = i * (ROOM_BTN_HEIGHT + ROOM_BTN_GAP) - scroll_offset
                    btn_rect = pygame.Rect(10, btn_y, scroll_box_w - 20, ROOM_BTN_HEIGHT)

                    # Skip if fully outside visible area
                    if btn_y + ROOM_BTN_HEIGHT < 0 or btn_y > scroll_box_h:
                        continue

                    # Compute absolute rect for hover detection
                    abs_rect   = pygame.Rect(scroll_box_x + 10, scroll_box_y + btn_y,
                                             scroll_box_w - 20, ROOM_BTN_HEIGHT)
                    is_hovered  = abs_rect.collidepoint(mouse_pos) and scroll_box_rect.collidepoint(mouse_pos)
                    is_selected = (rid == selected_room)

                    if is_selected:
                        btn_color = (255, 220, 50)   # yellow
                    elif is_hovered:
                        btn_color = (150, 210, 255)  # light blue
                    else:
                        btn_color = (255, 255, 255)  # white

                    pygame.draw.rect(clip_surface, btn_color, btn_rect, border_radius=6)
                    pygame.draw.rect(clip_surface, (0, 0, 0), btn_rect, 2, border_radius=6)

                    label = small_font.render(f"{rid} - {gm}", True, (0, 0, 0))
                    clip_surface.blit(label, (
                        btn_rect.x + 12,
                        btn_rect.y + ROOM_BTN_HEIGHT // 2 - label.get_height() // 2
                    ))

            screen.blit(clip_surface, (scroll_box_x, scroll_box_y))

            #Scrollbar 
            total_h = len(room_list) * (ROOM_BTN_HEIGHT + ROOM_BTN_GAP)
            if total_h > scroll_box_h:
                bar_h = max(30, scroll_box_h * scroll_box_h // total_h)
                bar_y = scroll_box_y + int(scroll_offset / total_h * scroll_box_h)
                bar_x = scroll_box_x + scroll_box_w + 5
                pygame.draw.rect(screen, (200, 200, 200), (bar_x, scroll_box_y, 8, scroll_box_h), border_radius=4)
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, 8, bar_h), border_radius=4)

            # Refresh button 
            refresh_color = (150, 210, 255) if refresh_rect.collidepoint(mouse_pos) else (255, 255, 255)
            pygame.draw.rect(screen, refresh_color, refresh_rect, border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0),     refresh_rect, 2,  border_radius=6)
            refresh_label = small_font.render("Refresh Rooms", True, (0, 0, 0))
            screen.blit(refresh_label, (
                refresh_rect.x + refresh_rect.w // 2 - refresh_label.get_width() // 2,
                refresh_rect.y + refresh_rect.h // 2 - refresh_label.get_height() // 2
            ))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)

    return menu_session_info


def menu_start() -> list:
    """
    Synchronous wrapper kept for desktop compatibility.
    In the browser, main.py calls menu_start_async() directly.
    """
    import asyncio

    if sys.platform == "emscripten":
        return ["room1", "freedraw"]

    return asyncio.run(menu_start_async())