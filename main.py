import pygame
from enum import Enum
 

class Color(Enum):
    WHITE = (225, 225, 225)
    BLACK = (0, 0, 0)
    GREY = (128, 128, 128)
    BUTTON_INACTIVE_GREY = (212, 212, 212)
    BUTTON_ACTIVE_GREY = (73, 72, 72)

class PaintDot:
    def __init__(self, size, coords, color):
        self.surf = pygame.Surface((size, size))
        self.x = coords[0] - self.surf.get_width() / 2
        self.y = coords[1] - self.surf.get_height() / 2
        self.surf.fill(color.value)
        
class Stroke:
    def __init__(self, dots, color):
        self.dots = dots  # List of PaintDot objects
        self.color = color
        
class Cursor:
    def __init__(self, screen, current_stroke, canvas, commander):
        self.screen = screen
        self.current_stroke = current_stroke
        self.canvas = canvas
        self.commander = commander
        self.surf = pygame.Surface((10, 10))
        self.surf.fill(Color.BLACK.value)
        self.x = 0
        self.y = 0
    
    def update(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.x = mouse_x - self.surf.get_width() / 2
        self.y = mouse_y - self.surf.get_height() / 2
        self.screen.blit(self.surf, (self.x, self.y))
    
        if pygame.mouse.get_pressed()[0]:
            # Just add to current stroke while mouse is down
            self.current_stroke.append(PaintDot(16, (self.x + 5, self.y + 5), Color.BLACK))
        else:
            # When mouse is released, finish the stroke
            if len(self.current_stroke) > 0:
                new_stroke = Stroke(list(self.current_stroke), Color.BLACK)

                # Create the Command
                cmd = DrawStrokeCommand(self.canvas, new_stroke)

                # Hand command to Command Manager to execute
                self.commander.execute(cmd)

                # Clear the current stroke
                self.current_stroke.clear()

class Button:
    def __init__(self, text, coords, action, screen):
        self.screen = screen
        self.x, self.y = coords
        self.action = action
        self.text = text
        self.text_surf = font.render(text, True, Color.BLACK.value)
        
        self.width = 150
        self.height = 25
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        color = Color.BUTTON_ACTIVE_GREY.value if self.check_hover() else Color.BUTTON_INACTIVE_GREY.value
        pygame.draw.rect(self.screen, color, self.rect, 0, 5)

        # Border
        pygame.draw.rect(self.screen, Color.BLACK.value, self.rect, 2, 5)
        surface.blit(self.text_surf, (self.x + 3, self.y + 3))

    def check_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) 
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.check_hover():
                self.action()
                print(f"{self.text} button triggered.")
                return True
        return False


class ButtonManager:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []
        self.is_hovering_ui = False

    def add_button(self, text, coords, action):
        self.buttons.append(Button(text, coords, action, self.screen))

    def handle_events(self, event):
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        self.is_hovering_ui = any(button.check_hover() for button in self.buttons)

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)

class Command:
    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError
    
class DrawStrokeCommand(Command):
    def __init__(self, canvas, stroke):
        self.canvas = canvas
        self.stroke = stroke

    def do(self):
        # Only add to the list if it's not already there (prevents replay duplicates)
        if self.stroke not in self.canvas.strokes:
            self.canvas.strokes.append(self.stroke)
        
        # Always bake the pixels to the surface
        for dot in self.stroke.dots:
            self.canvas.surface.blit(dot.surf, (dot.x, dot.y))
    
    def undo(self):
        if self.stroke in self.canvas.strokes:
            self.canvas.strokes.remove(self.stroke)
            self.canvas.rebuild_canvas()

class ClearCanvasCommand(Command):
    def __init__(self, canvas):
        self.canvas = canvas
        self.old_strokes = []

    def do(self):
        self.old_strokes = list(self.canvas.strokes)    # Backup strokes
        self.canvas.clear()                             # Clear the canvas

    def undo(self):
        self.canvas.strokes = list(self.old_strokes)    # Restore backup strokes
        self.canvas.rebuild_canvas()                    # Redraw strokes to canvas

class DrawingMemento:
    def __init__(self, strokes):
        # IMPORTANT: Use list() to create a copy, otherwise the 
        # memento changes when the original list changes.
        self.strokes = list(strokes)

class PaintCanvas:
    def __init__(self):
        self.strokes = []  # List of strokes
        # Create the internal surface
        self.surface = pygame.Surface((640, 640))
        self.surface.fill(Color.WHITE.value)

    def save(self):
        return DrawingMemento(self.strokes)
    
    def restore(self, memento):
        self.strokes = memento.strokes
        self.rebuild_canvas()

    def clear(self):
        self.strokes.clear()
        self.surface.fill(Color.WHITE.value)
    
    def rebuild_canvas(self):
        self.surface.fill(Color.WHITE.value)
        for stroke in self.strokes:
            for dot in stroke.dots: 
                self.surface.blit(dot.surf, (dot.x, dot.y))

class CommandManager:
    SNAPSHOT_INTERVAL = 20

    def __init__(self, canvas):
        self.canvas = canvas
        self.commands = []                                  # list of Command objects
        self.redo_stack = []
        self.snapshots = [(0, self.canvas.save())]          # list of Mementos

    def execute(self, command):
        command.do()
        self.commands.append(command)
        self.redo_stack.clear()

        if len(self.commands) % self.SNAPSHOT_INTERVAL == 0:
            # Save the current command count (ID) along with the state
            self.snapshots.append((len(self.commands), self.canvas.save()))

    def undo(self):
        if not self.commands:
            return

        command = self.commands.pop()
        self.redo_stack.append(command)
        self.restore_to_current_state()

    def redo(self):
        if not self.redo_stack:
            return
        
        command = self.redo_stack.pop()
        self.commands.append(command)
        command.do()

    def restore_to_current_state(self):
        # Find the latest snapshot that doesn't exceed current command count
        latest_snap_id, memento = self.snapshots[0]
        for snap_id, snap_memento in self.snapshots:
            if snap_id <= len(self.commands):
                latest_snap_id = snap_id
                memento = snap_memento
            else:
                break
        
        # Restore that snapshot
        self.canvas.restore(memento)

        # Replay commands that happened AFTER restored snapshot
        for i in range(latest_snap_id, len(self.commands)):
            self.commands[i].do()

class User:
    def __init__(self, cursor, commander, color, brush):
        self.curosr = cursor
        self.commander = commander
        self.color = Color.BLACK
        self.brush = brush

    
# Initial Setup
pygame.init()

# Creates display window and the tuple controls the dimensions of said window
screen = pygame.display.set_mode((640, 640))
canvas_obj = PaintCanvas()
commander = CommandManager(canvas_obj)

running = True

font = pygame.font.Font('freesansbold.ttf', 18)
# Sets frame rate
clock = pygame.time.Clock()

current_stroke = []

cursor = Cursor(screen, current_stroke, canvas_obj, commander)
pygame.mouse.set_visible(False)

button_manager = ButtonManager(screen)
button_manager.add_button("Clear", (10, 10), lambda: commander.execute(ClearCanvasCommand(canvas_obj)))
button_manager.add_button("Undo", (200, 10), lambda: commander.undo())
button_manager.add_button("Redo", (400, 10), lambda: commander.redo())

while running:
    screen.fill(Color.WHITE.value)
    
    # 1. Logic
    button_manager.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 
        button_manager.handle_events(event)

    if not button_manager.is_hovering_ui:
        cursor.update()

    # 2. Drawing (Layered)
    # Background Canvas
    screen.blit(canvas_obj.surface, (0, 0))

    # Active line being drawn (the "preview")
    for dot in current_stroke:
        screen.blit(dot.surf, (dot.x, dot.y))

    # UI and Cursor
    button_manager.draw(screen)

    pygame.display.flip()
    clock.tick(60) 

pygame.quit()