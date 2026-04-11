import pygame
from CapstoneQuillxo.commands import ClearCanvasCommand
from CapstoneQuillxo.core import UserManager
from CapstoneQuillxo.core.color import Color, Tool
from CapstoneQuillxo.ui import ButtonManager
from CapstoneQuillxo.ui.rgb_picker import RGBPicker
import os


#Begin Menu
# 1. Initialize Pygame
pygame.init()

# 2. Setup the window
screen_width = 900
screen_height = 640
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("My Game Window") #



host_button = pygame.Rect(220, 200, 450, 50)  # x, y, width, height
join_button = pygame.Rect(220, 300, 450, 50)  # x, y, width, height
settings_button = pygame.Rect(220, 400, 450, 50)  # x, y, width, height
quit_button = pygame.Rect(220, 500, 450, 50)  # x, y, width, height

### Host Menu Element Initialization ###
input_box = pygame.Rect(200, 150, 200, 40)
color_inactive = pygame.Color('gray')
color_active = pygame.Color('dodgerblue')
color = color_inactive

font = pygame.font.Font(None, 36)
text = ""

###


# 3. Clock to control frame rate
clock = pygame.time.Clock()
running = True

# C. Render the frame (Drawing)


# Initialize Sprites
# image_path = os.path.join('assets', 'ibtc1.png')
# image_path2 = os.path.join('assets', 'ibtc2.png')
# character_image = pygame.image.load(image_path).convert_alpha()
# character_image2 = pygame.image.load(image_path2).convert_alpha()

def load_all_images(directory):
    images = {}
    for filename in os.listdir(directory):
        if filename.endswith((".png", ".jpg", ".bmp")):
            path = os.path.join(directory, filename)
            # 2. Load and 3. Convert (essential for performance)
            # Use .convert_alpha() for transparency
            img_name = os.path.splitext(filename)[0]
            images[img_name] = pygame.image.load(path).convert_alpha()
    return images

all_sprites = load_all_images("assets")
active = False
main_menu = True
host_menu = False
room_name = "room1"
# --- Main Menu Loop ---
while main_menu:
    while running:
        screen.fill("purple")  # Clear screen with a background color
        # A. Check for events (Input)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # B. Update game state (Logic)
        # [Insert movement, collisions, etc. here]
                # Check for mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if host_button.collidepoint(event.pos):
                host_menu = True
            if join_button.collidepoint(event.pos):
                print("Button Clicked!") 
            if settings_button.collidepoint(event.pos):
                print("Button Clicked!")     
            if quit_button.collidepoint(event.pos):
                raise SystemExit       

        ## [Draw your sprites/shapes here]
        #pygame.draw.rect(screen, (0, 128, 255), button_rect1)
        # pygame.draw.rect(screen, (0, 128, 255), join_button)
        # pygame.draw.rect(screen, (0, 128, 255), settings_button)
        # pygame.draw.rect(screen, (0, 128, 255), quit_button)

        #Logo
        logo = pygame.transform.scale(all_sprites['pARTy_Logo'], (400, 300)) #Resize to n x m
        screen.blit(logo, ((screen_width // 2) - 200, -50))

        screen.blit(all_sprites['host'], (200, 175)) # (x, y)
        screen.blit(all_sprites['join'], (200, 275))
        screen.blit(all_sprites['settings'], (200, 375))
        screen.blit(all_sprites['quit'], (200, 475))

        ##Images
        #screen.blit(character_image, (100, 100))

        mouse_pos = pygame.mouse.get_pos()
        
        if host_button.collidepoint(mouse_pos): #Host Button Monster
            screen.blit(all_sprites['ibtc2'], (80, 160)) # (x, y)
        else:
            screen.blit(all_sprites['ibtc1'], (80, 160))

        if join_button.collidepoint(mouse_pos): #Join Button Monster
            screen.blit(all_sprites['chudoid2'], (680, 280)) # (x, y)
        else:
            screen.blit(all_sprites['chudoid1'], (680, 280))    

        if settings_button.collidepoint(mouse_pos): #Settings Button Monster
            screen.blit(all_sprites['Buster2'], (80, 380)) # (x, y)
        else:
            screen.blit(all_sprites['Buster1'], (80, 380))

        # #TODO Quit Button Monster
        # if quit_button.collidepoint(mouse_pos): #Quit Button Monster
        #     screen.blit(all_sprites['ibtc2'], (80, 160)) # (x, y)
        # else:
        #     screen.blit(all_sprites['ibtc1'], (80, 160))           

        # D. Refresh the display
        pygame.display.flip()

        # E. Limit FPS to 60
        clock.tick(60) #

        if host_menu:
            break

    
    
    # 4. Clean up and close
    ###HOST MENU
    # --- Host Menu Loop --- (runs after main menu, not inside it)
    
    while host_menu:
        screen.fill((232, 105, 186))

        arrow_button = pygame.Rect(10, 10, 125, 125)  # ✅ Move outside loop eventually, but fine here

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                host_menu = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    host_menu = False
                elif active:
                    if event.key == pygame.K_RETURN:
                        room_name = text   # ✅ FIX: capture BEFORE clearing
                        print("Entered:", room_name)
                        text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive

                if arrow_button.collidepoint(event.pos):  # ✅ FIX: inside event loop
                    host_menu = False

        ##Drawings
        mouse_pos = pygame.mouse.get_pos()

        # Arrow button
        if arrow_button.collidepoint(mouse_pos):
            big_arrow = pygame.transform.scale(all_sprites['arrow'], (120, 120))
            screen.blit(big_arrow, (10, 10))
        else:
            screen.blit(all_sprites['arrow'], (20, 20))

        # ✅ "Room Name:" label above the input box
        label_surface = font.render("Room Name:", True, (255, 255, 255))
        screen.blit(label_surface, (input_box.x, input_box.y - 35))

        # Input box with live typing
        txt_surface = font.render(text, True, (255, 255, 255))
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        # ✅ Display confirmed room name below the box
        if room_name:
            confirmed_surface = font.render(f"Room: {room_name}", True, (255, 255, 0))
            screen.blit(confirmed_surface, (input_box.x, input_box.y + 55))

        pygame.display.flip()
        clock.tick(60)

pygame.quit()
#End Menu

###Host Menu






























#Begin Game
pygame.init()

screen = pygame.display.set_mode((900, 640))
pygame.display.set_caption("CapstoneQuillxo")
font = pygame.font.Font("freesansbold.ttf", 18)

umanager = UserManager()
umanager.add_user(screen)

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

    # ── Render ────────────────────────────────────────────────────────────────
    umanager.draw()                                          # canvas
    pygame.draw.rect(screen, Color.PURPLE.value, all_button_rect)  # sidebar bg
    top_buttons.draw(screen)

    # menu toggle button
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
        tool_buttons.draw(screen)
        rgb_picker.draw()

    umanager.draw_cursor()

    # ── Update (includes Firebase push/pull) ──────────────────────────────────
    umanager.update(hovering_ui, events)

    pygame.display.flip()
    clock.tick(120)

pygame.quit()