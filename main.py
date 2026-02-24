import pygame
from enum import Enum

class Color(Enum):
    WHITE = (225, 225, 225)
    BLACK = (0, 0, 0)
    GREY = (128, 128, 128)
    BUTTON_INACTIVE_GREY = (212, 212, 212)
    BUTTON_ACTIVE_GREY = (73, 72, 72)

class Paint:
    def __init__(self, size, coords, color):
        self.surf = pygame.Surface((size, size))
        self.coords = coords
        self.x = coords[0] - self.surf.get_width() / 2
        self.y = coords[1] - self.surf.get_height() / 2
        self.surf.fill(color.value)
    
    def draw(self):
        screen.blit(self.surf, (self.x, self.y))
        

class Cursor:
    def __init__(self):
        self.surf = pygame.Surface((10,10))
        self.x = 0
        self.y = 0
        self.surf.fill(Color.BLACK.value)
    
    def draw(self):
        mouse_x,mouse_y = pygame.mouse.get_pos()
        self.x = mouse_x - self.surf.get_width() / 2
        self.y = mouse_y - self.surf.get_height() / 2
        screen.blit(self.surf,(self.x, self.y) )
    
    def update(self):
        if pygame.mouse.get_pressed()[0]:
            current_stroke.append(Paint(16, (self.x, self.y), Color.BLACK))
        else:
            if len(current_stroke) > 0:
                for dot in current_stroke:
                    canvas.blit(dot.surf, (dot.x, dot.y))
                strokes.append(list(current_stroke))
                current_stroke.clear()
            
class Button:
    def __init__(self, text, coords, action):
        self.x, self.y = coords
        self.action = action
        self.text_surf = font.render(text, True, Color.BLACK.value)
        
        self.width = 150
        self.height = 25
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        color = Color.BUTTON_ACTIVE_GREY.value if self.check_hover() else Color.BUTTON_INACTIVE_GREY.value
        pygame.draw.rect(screen, color, self.rect, 0, 5)

        #Border
        pygame.draw.rect(screen, Color.BLACK.value, self.rect, 2, 5)
        surface.blit(self.text_surf, (self.x + 3, self.y + 3))

       
    def check_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) 
        
    def update(self):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0]:
                self.action() # Execute the passed function
                return True
        return False


class ButtonManager:
    def __init__(self):
        self.buttons = []
        self.is_hovering_ui = False

    def add_button(self, text, coords, action):
        self.buttons.append(Button(text, coords, action))

    def update(self):
        self.is_hovering_ui = False

        for button in self.buttons:
            button.update()
            
            # Check if the mouse is over any button to disable painting
            if button.check_hover():
                self.is_hovering_ui = True

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)


def rebuild_canvas():
    canvas.fill(Color.WHITE.value)
    for stroke in strokes:
        for dot in stroke:
            canvas.blit(dot.surf, (dot.x, dot.y))

def trigger_undo():
    global undo_flag
    undo_flag = True

def trigger_redo():
    global redo_flag
    redo_flag = True

#Initial Setup
pygame.init()

#Creates display window and the tuple controls the dimensions of said window
screen = pygame.display.set_mode((640,640))
running = True

canvas = pygame.Surface((640, 640))
canvas.fill(Color.WHITE.value)

font = pygame.font.Font('freesansbold.ttf', 18)
#Sets frame rate 
clock = pygame.time.Clock()

undo_flag = False
redo_flag = False

cursor = Cursor()
strokes = []
current_stroke = []
redo_stack = []
pygame.mouse.set_visible(False)


button_manager = ButtonManager()
button_manager.add_button("Clear", (10, 10), lambda: strokes.clear())
button_manager.add_button("Undo", (200, 10), lambda:  trigger_undo())
button_manager.add_button("Redo", (400, 10), lambda: trigger_redo())

while running:
    screen.fill(Color.WHITE.value)

    # 1. Button Stuff
    button_manager.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 

    if len(strokes) > 0 and undo_flag:
        if undo_flag and len(strokes) > 0:
            redo_stack.append(strokes.pop())
            rebuild_canvas()
            undo_flag = False

    if len(redo_stack) > 0 and redo_flag:
        strokes.append()



    # 2. Update Cursor (only paint if not clicking a button)
    if not button_manager.is_hovering_ui:
        cursor.update()

    # 3. Draw everything in layers
    screen.blit(canvas, (0,0))

    for dot in current_stroke:
        dot.draw()                    # Bottom
    button_manager.draw(screen)       # Middle
    cursor.draw()                     # Top

    pygame.display.flip()
    clock.tick(60) 

pygame.quit()