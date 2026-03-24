
from CapstoneQuillxo.commands import *
from CapstoneQuillxo.commands.draw_stroke_command import DrawStrokeCommand
from CapstoneQuillxo.core.color import Color
from CapstoneQuillxo.drawing.paint_dot import PaintDot
from CapstoneQuillxo.drawing.stroke import Stroke
import pygame

class Cursor:
    def __init__(self, screen, current_stroke, canvas, commander, color):
        self.screen = screen
        self.current_stroke = current_stroke
        self.canvas = canvas
        self.commander = commander
        self.color = color
        self.surf = pygame.Surface((10, 10))
        self.surf.fill(Color.BLACK.value)
        self.x = 0
        self.y = 0
    
    def execute_command(self, command_class, *args):
        self.commander.execute(command_class(self.canvas, *args))

    def update(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.x = mouse_x - self.surf.get_width() / 2
        self.y = mouse_y - self.surf.get_height() / 2
    
        if pygame.mouse.get_pressed()[0]:
            # Just add to current stroke while mouse is down
            self.current_stroke.append(PaintDot(16, (self.x + 5, self.y + 5), self.color))
        else:
            # When mouse is released, finish the stroke
            if len(self.current_stroke) > 0:
                new_stroke = Stroke(list(self.current_stroke))

                # Create the Command and Hand command to Command Manager to execute
                self.execute_command(DrawStrokeCommand, new_stroke)

                # Clear the current stroke
                self.current_stroke.clear()
    