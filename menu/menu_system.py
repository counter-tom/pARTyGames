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
]

# Replaces os.listdir — loads each asset explicitly by name
def load_all_images():
    images = {}
    for name in ASSET_FILES:
        path = f"assets/{name}.png"
        try:
            # Load and convert (essential for performance)
            # Use convert_alpha() for transparency
            images[name] = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"[Assets] Could not load {path}: {e}")
    return images


# Begin Menu
# 1. Initialize Pygame
async def menu_start_async() -> list:
    """
    Async version of menu_start for pygbag/browser.
    Returns [room_name].
    """
    import asyncio
    pygame.init()
    menu_session_info = []
    menu_session_info.insert(0, "room1")

    # 2. Setup the window
    screen_width = 900
    screen_height = 640
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("pARTy")

    host_button     = pygame.Rect(220, 200, 450, 50)  # x, y, width, height
    join_button     = pygame.Rect(220, 300, 450, 50)  # x, y, width, height
    settings_button = pygame.Rect(220, 400, 450, 50)  # x, y, width, height
    quit_button     = pygame.Rect(220, 500, 450, 50)  # x, y, width, height

    ### Host Menu Element Initialization ###
    input_box      = pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 150, 200, 40)
    color_inactive = pygame.Color('gray')
    color_active   = pygame.Color('dodgerblue')
    input_color    = color_inactive

    font      = pygame.font.Font(None, 36)
    text      = ""
    active    = False
    room_name = "room1"
    ###

    # 3. Clock to control frame rate
    clock = pygame.time.Clock()

    # Initialize Sprites
    all_sprites = load_all_images()

    # ── States ────────────────────────────────────────────────────────────────
    STATE_MAIN = "main"
    STATE_HOST = "host"
    STATE_JOIN = "join"
    state = STATE_MAIN
    done  = False

    # --- Main Menu Loop ---
    while not done:
        # A. Check for events (Input)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                raise SystemExit

            # ── Main menu ─────────────────────────────────────────────────────
            if state == STATE_MAIN:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if host_button.collidepoint(event.pos):
                        state = STATE_HOST
                    elif join_button.collidepoint(event.pos):
                        state = STATE_JOIN
                    elif settings_button.collidepoint(event.pos):
                        print("Button Clicked!")
                    elif quit_button.collidepoint(event.pos):
                        raise SystemExit

            # ── Host / Join menus ─────────────────────────────────────────────
            elif state in (STATE_HOST, STATE_JOIN):
                arrow_button = pygame.Rect(10, 10, 125, 125)
                start_button = pygame.Rect(
                    screen_width // 2 - 250, screen_height // 2, 500, 150
                )

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MAIN
                        text  = ""
                        active = False
                        input_color = color_inactive
                    elif active:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            room_name = text or "room1"
                            print("Entered:", room_name)
                            text = ""
                            menu_session_info[0] = room_name
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint(event.pos):
                        active = not active
                    else:
                        active = False
                    input_color = color_active if active else color_inactive

                    if arrow_button.collidepoint(event.pos):
                        state = STATE_MAIN
                        text  = ""
                        active = False
                        input_color = color_inactive

                    if start_button.collidepoint(event.pos):
                        menu_session_info[0] = room_name
                        done = True

        # C. Render the frame (Drawing)
        mouse_pos = pygame.mouse.get_pos()

        if state == STATE_MAIN:
            screen.fill("purple")  # Clear screen with a background color

            # Logo
            if 'pARTy_Logo' in all_sprites:
                logo = pygame.transform.scale(all_sprites['pARTy_Logo'], (400, 300))  # Resize to n x m
                screen.blit(logo, (screen_width // 2 - 200, -50))

            # [Draw your sprites/shapes here]
            for key, x, y in [
                ('host',     200, 175),
                ('join',     200, 275),
                ('settings', 200, 375),
                ('quit',     200, 475),
            ]:
                if key in all_sprites:
                    screen.blit(all_sprites[key], (x, y))  # (x, y)

            # Host Button Monster
            if 'ibtc1' in all_sprites and 'ibtc2' in all_sprites:
                sprite = all_sprites['ibtc2'] if host_button.collidepoint(mouse_pos) else all_sprites['ibtc1']
                screen.blit(sprite, (80, 160))  # (x, y)

            # Join Button Monster
            if 'chudoid1' in all_sprites and 'chudoid2' in all_sprites:
                sprite = all_sprites['chudoid2'] if join_button.collidepoint(mouse_pos) else all_sprites['chudoid1']
                screen.blit(sprite, (680, 280))

            # Settings Button Monster
            if 'Buster1' in all_sprites and 'Buster2' in all_sprites:
                sprite = all_sprites['Buster2'] if settings_button.collidepoint(mouse_pos) else all_sprites['Buster1']
                screen.blit(sprite, (80, 380))

            # #TODO Quit Button Monster

        elif state in (STATE_HOST, STATE_JOIN):
            screen.fill((232, 105, 186))

            arrow_button = pygame.Rect(10, 10, 125, 125)
            start_button = pygame.Rect(
                screen_width // 2 - 250, screen_height // 2, 500, 150
            )

            ##Drawings
            # Arrow button
            if 'arrow' in all_sprites:
                if arrow_button.collidepoint(mouse_pos):
                    big_arrow = pygame.transform.scale(all_sprites['arrow'], (120, 120))
                    screen.blit(big_arrow, (10, 10))
                else:
                    screen.blit(all_sprites['arrow'], (20, 20))

            # Start button
            if 'start' in all_sprites:
                if start_button.collidepoint(mouse_pos):
                    big_start = pygame.transform.scale(all_sprites['start'], (600, 150))
                    screen.blit(big_start, (screen_width // 2 - 300, 325))
                else:
                    screen.blit(all_sprites['start'], (screen_width // 2 - 250, 350))

            label_surface = font.render("Enter room name.", True, (255, 255, 255))
            screen.blit(label_surface, (screen_width // 2 - 120, screen_height // 2 - 100))

            # Input box with live typing
            txt_surface = font.render(text, True, (255, 255, 255))
            width = max(200, txt_surface.get_width() + 10)
            input_box.w = width
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(screen, input_color, input_box, 2)

            if room_name:
                confirmed_surface = font.render(f"Room: {room_name}", True, (255, 255, 255))
                screen.blit(confirmed_surface, (screen_width // 2 - 100, screen_height // 2 - 200))

        # D. Refresh the display
        pygame.display.flip()

        # MANDATORY for pygbag — yields control back to the browser
        await asyncio.sleep(0)

        # E. Limit FPS to 60
        clock.tick(60)

    return menu_session_info


def menu_start() -> list:
    """
    Synchronous wrapper kept for desktop compatibility.
    In the browser, main.py calls menu_start_async() directly.
    """
    import asyncio

    if sys.platform == "emscripten":
        # Should not be called directly in browser — use menu_start_async
        return ["room1"]

    # Desktop: run the async version synchronously
    return asyncio.run(menu_start_async())