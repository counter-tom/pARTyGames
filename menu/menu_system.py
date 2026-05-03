import pygame
import sys

# In the browser, os.listdir on the virtual filesystem is unreliable.
# We explicitly list every asset instead.
# To add a new asset: add its filename (without .png) to this list.
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

# Replaces os.listdir — loads each asset explicitly by name
def load_all_images():
    images = {}
    for name in ASSET_FILES:
        path = f"assets/{name}.png"
        try:
            images[name] = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"[Assets] Could not load {path}: {e}")
    return images


# ── Gamemode options ───────────────────────────────────────────────────────────
GAMEMODES = ["freedraw", "pictionary"]


async def menu_start_async() -> list:
    """
    Async version of menu_start for pygbag/browser.
    Returns [room_name, gamemode].
      - Host sets gamemode via dropdown.
      - Join returns gamemode="fetch" so main.py reads it from Firebase.
    """
    import asyncio
    pygame.init()

    # menu_session_info[0] = room_name, menu_session_info[1] = gamemode
    menu_session_info = ["room1", "freedraw"]

    # 2. Setup the window
    screen_width  = 900
    screen_height = 640
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("pARTy")

    # ── Shared button rects (main menu) ───────────────────────────────────────
    host_button     = pygame.Rect(220, 200, 450, 50)
    join_button     = pygame.Rect(220, 300, 450, 50)
    settings_button = pygame.Rect(220, 400, 450, 50)
    quit_button     = pygame.Rect(220, 500, 450, 50)

    # ── Shared sub-menu rects ─────────────────────────────────────────────────
    arrow_button = pygame.Rect(10, 10, 125, 125)
    start_button = pygame.Rect(screen_width // 2 - 250, screen_height // 2 + 100, 500, 150)
    input_box    = pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 150, 200, 40)

    # ── Input state ───────────────────────────────────────────────────────────
    color_inactive = pygame.Color('gray')
    color_active   = pygame.Color('dodgerblue')
    input_color    = color_inactive
    font           = pygame.font.Font(None, 36)
    text           = ""
    active         = False
    room_name      = "room1"

    # ── Gamemode dropdown (HOST only) ─────────────────────────────────────────
    selected_gamemode_index = 0
    dropdown_open  = False
    dropdown_rect  = pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 50, 200, 40)
    dropdown_options = [
        pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 50 + 40 * (i + 1), 200, 40)
        for i in range(len(GAMEMODES))
    ]

    # ── State machine ─────────────────────────────────────────────────────────
    STATE_MAIN = "main"
    STATE_HOST = "host"
    STATE_JOIN = "join"
    state = STATE_MAIN
    done  = False

    clock       = pygame.time.Clock()
    all_sprites = load_all_images()

    # ── Main loop ─────────────────────────────────────────────────────────────
    while not done:
        events    = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()

        # ── Event handling ────────────────────────────────────────────────────
        for event in events:
            if event.type == pygame.QUIT:
                raise SystemExit

            # ── Main menu ─────────────────────────────────────────────────────
            if state == STATE_MAIN:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if host_button.collidepoint(event.pos):
                        state = STATE_HOST
                        text  = ""
                        active = False
                        input_color = color_inactive
                        dropdown_open = False
                    elif join_button.collidepoint(event.pos):
                        state = STATE_JOIN
                        text  = ""
                        active = False
                        input_color = color_inactive
                    elif settings_button.collidepoint(event.pos):
                        print("Settings clicked!")
                    elif quit_button.collidepoint(event.pos):
                        raise SystemExit

            # ── Host menu ─────────────────────────────────────────────────────
            elif state == STATE_HOST:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MAIN
                        text  = ""
                        active = False
                        input_color  = color_inactive
                        dropdown_open = False
                    elif active:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            room_name = text or "room1"
                            print("Room name set:", room_name)
                            text = ""
                            menu_session_info[0] = room_name
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Dropdown toggle/select
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
                    # Input box
                    elif input_box.collidepoint(event.pos):
                        active = not active
                        input_color = color_active if active else color_inactive
                    else:
                        active = False
                        input_color = color_inactive

                    # Arrow — back to main
                    if arrow_button.collidepoint(event.pos):
                        state = STATE_MAIN
                        text  = ""
                        active = False
                        input_color   = color_inactive
                        dropdown_open = False

                    # Start — create room with chosen gamemode
                    if start_button.collidepoint(event.pos):
                        menu_session_info[0] = room_name
                        menu_session_info[1] = GAMEMODES[selected_gamemode_index]
                        done = True

            # ── Join menu ─────────────────────────────────────────────────────
            elif state == STATE_JOIN:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MAIN
                        text  = ""
                        active = False
                        input_color = color_inactive
                    elif active:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            room_name = text or "room1"
                            print("Joining room:", room_name)
                            text = ""
                            menu_session_info[0] = room_name
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint(event.pos):
                        active = not active
                        input_color = color_active if active else color_inactive
                    else:
                        active = False
                        input_color = color_inactive

                    # Arrow — back to main
                    if arrow_button.collidepoint(event.pos):
                        state = STATE_MAIN
                        text  = ""
                        active = False
                        input_color = color_inactive

                    # Start — join room, fetch gamemode from Firebase
                    if start_button.collidepoint(event.pos):
                        menu_session_info[0] = room_name
                        menu_session_info[1] = "fetch"  # main.py reads gamemode from Firebase
                        done = True

        # ── Rendering ─────────────────────────────────────────────────────────

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
            screen.fill((232, 105, 186))  # Pink

            # Arrow
            if 'arrow' in all_sprites:
                if arrow_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['arrow'], (120, 120)), (10, 10))
                else:
                    screen.blit(all_sprites['arrow'], (20, 20))

            # Start button
            if 'start' in all_sprites:
                if start_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['start'], (600, 150)), (screen_width // 2 - 300, 425))
                else:
                    screen.blit(all_sprites['start'], (screen_width // 2 - 250, 450))

            # Room name label + input
            screen.blit(font.render("Enter room name.", True, (255, 255, 255)),
                        (screen_width // 2 - 120, screen_height // 2 - 100))

            txt_surface  = font.render(text, True, (255, 255, 255))
            input_box.w  = max(200, txt_surface.get_width() + 10)
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(screen, input_color, input_box, 2)

            if room_name:
                screen.blit(font.render(f"Room: {room_name}", True, (255, 255, 255)),
                            (screen_width // 2 - 100, screen_height // 2 - 200))

            # ── Gamemode dropdown (HOST ONLY) ──────────────────────────────
            pygame.draw.rect(screen, (255, 255, 255), dropdown_rect)
            pygame.draw.rect(screen, (0, 0, 0),       dropdown_rect, 2)
            screen.blit(
                font.render(f"Mode: {GAMEMODES[selected_gamemode_index]}", True, (0, 0, 0)),
                (dropdown_rect.x + 5, dropdown_rect.y + 8)
            )

            if dropdown_open:
                for i, opt_rect in enumerate(dropdown_options):
                    bg = (200, 230, 255) if i == selected_gamemode_index else (255, 255, 255)
                    pygame.draw.rect(screen, bg,       opt_rect)
                    pygame.draw.rect(screen, (0, 0, 0), opt_rect, 1)
                    screen.blit(
                        font.render(GAMEMODES[i], True, (0, 0, 0)),
                        (opt_rect.x + 5, opt_rect.y + 8)
                    )

        elif state == STATE_JOIN:
            screen.fill((100, 180, 232))  # Blue — visually distinct from host

            # Arrow
            if 'arrow' in all_sprites:
                if arrow_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['arrow'], (120, 120)), (10, 10))
                else:
                    screen.blit(all_sprites['arrow'], (20, 20))

            # Start button
            if 'start' in all_sprites:
                if start_button.collidepoint(mouse_pos):
                    screen.blit(pygame.transform.scale(all_sprites['start'], (600, 150)), (screen_width // 2 - 300, 425))
                else:
                    screen.blit(all_sprites['start'], (screen_width // 2 - 250, 450))

            # Room name label + input
            screen.blit(font.render("Enter room name to join.", True, (255, 255, 255)),
                        (screen_width // 2 - 150, screen_height // 2 - 100))

            txt_surface  = font.render(text, True, (255, 255, 255))
            input_box.w  = max(200, txt_surface.get_width() + 10)
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(screen, input_color, input_box, 2)

            if room_name:
                screen.blit(font.render(f"Joining: {room_name}", True, (255, 255, 255)),
                            (screen_width // 2 - 100, screen_height // 2 - 200))

            # No dropdown — joiner fetches gamemode from Firebase

        pygame.display.flip()
        await asyncio.sleep(0)  # Mandatory for pygbag
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