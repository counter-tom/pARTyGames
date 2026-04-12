import pygame
import os
#Begin Menu
# 1. Initialize Pygame
def menu_start() -> list:
    menu_session_info = []
    menu_session_info.insert(0, "room1")

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
    start_button = pygame.Rect(500, 500, 700, 450)

    ### Host Menu Element Initialization ###
    input_box = pygame.Rect(screen_width // 2 - 120, screen_height // 2 - 150, 200, 40)
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
    join_menu = False
    room_name = "room1"
    # --- Main Menu Loop ---
    while main_menu:
        while running:
            screen.fill("purple")  # Clear screen with a background color
            # A. Check for events (Input)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if host_button.collidepoint(event.pos):
                        host_menu = True
                        running = False
                    if join_button.collidepoint(event.pos):
                        join_menu = True
                        running = False 
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


        ###join MENU

        while join_menu:
            screen.fill((232, 105, 186))

            arrow_button = pygame.Rect(10, 10, 125, 125)  
            start_button = pygame.Rect(screen_width // 2 - 250, screen_height // 2 , 500, 150)
            #pygame.draw.rect(screen, (0, 128, 255), start_button)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        host_menu = False
                    elif active:
                        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                            room_name = text   
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
                    color = color_active if active else color_inactive
                    if arrow_button.collidepoint(event.pos):  
                        join_menu = False
                        host_menu = False
                        running = True
                    if start_button.collidepoint(event.pos):
                        main_menu = False
                        running = False
                        host_menu = False
                        join_menu = False        

            ##Drawings
            mouse_pos = pygame.mouse.get_pos()

            # Arrow button
            if arrow_button.collidepoint(mouse_pos):
                big_arrow = pygame.transform.scale(all_sprites['arrow'], (120, 120))
                screen.blit(big_arrow, (10, 10))
            else:
                screen.blit(all_sprites['arrow'], (20, 20))
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
            pygame.draw.rect(screen, color, input_box, 2)

            
            if room_name:
                confirmed_surface = font.render(f"Room: {room_name}", True, (255, 255, 255))
                screen.blit(confirmed_surface, (screen_width // 2 - 100, screen_height // 2 - 200))

            pygame.display.flip()
            clock.tick(60)

        while host_menu:
            screen.fill((232, 105, 186))

            arrow_button = pygame.Rect(10, 10, 125, 125)  
            start_button = pygame.Rect(screen_width // 2 - 250, screen_height // 2 , 500, 150)
            #pygame.draw.rect(screen, (0, 128, 255), start_button)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        join_menu = False
                        running = True
                        host_menu = False
                    elif active:
                        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                            room_name = text   
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
                    color = color_active if active else color_inactive
                    if arrow_button.collidepoint(event.pos):  
                        host_menu = False
                        running = True
                    if start_button.collidepoint(event.pos):
                        main_menu = False
                        running = False
                        host_menu = False
                        join_menu = False    


            ##Drawings
            mouse_pos = pygame.mouse.get_pos()

            # Arrow button
            if arrow_button.collidepoint(mouse_pos):
                big_arrow = pygame.transform.scale(all_sprites['arrow'], (120, 120))
                screen.blit(big_arrow, (10, 10))
            else:
                screen.blit(all_sprites['arrow'], (20, 20))
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
            pygame.draw.rect(screen, color, input_box, 2)

            
            if room_name:
                confirmed_surface = font.render(f"Room: {room_name}", True, (255, 255, 255))
                screen.blit(confirmed_surface, (screen_width // 2 - 100, screen_height // 2 - 200))

            pygame.display.flip()
            clock.tick(60)    

    pygame.quit()
    return menu_session_info