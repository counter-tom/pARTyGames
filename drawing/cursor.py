import math
import random
import pygame

from commands.draw_stroke_command import DrawStrokeCommand
from commands.fill_command import FillCommand
from core.color import Tool
from drawing.paint_dot import PaintDot
from drawing.stroke import Stroke


class Cursor:
    def __init__(self, screen, current_stroke, canvas, commander, color, firebase=None):
        self.screen = screen
        self.current_stroke = current_stroke
        self.canvas = canvas
        self.commander = commander
        self.color = color

        self.surf = pygame.Surface((10, 10))
        self.x = 0
        self.y = 0

        self.tool = Tool.BRUSH
        self.was_mouse_down = False
        self.line_start = None
        self.line_preview = []
        self.firebase = firebase  # ✅ Add this

    def execute_command(self, command_class, *args):
        self.commander.execute(command_class(self.canvas, *args))

    def _current_rgb(self):
        if hasattr(self.color, "value"):
            return self.color.value
        return self.color

    def update_position_only(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.x = mouse_x - self.surf.get_width() / 2
        self.y = mouse_y - self.surf.get_height() / 2
        self.surf.fill(self._current_rgb())

    def update(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_pos = (mouse_x, mouse_y)
        mouse_down = pygame.mouse.get_pressed()[0]

        self.x = mouse_x - self.surf.get_width() / 2
        self.y = mouse_y - self.surf.get_height() / 2
        self.surf.fill(self._current_rgb())

        if self.tool == Tool.BRUSH:
            self.handle_brush(mouse_down, mouse_pos)
        elif self.tool == Tool.SPRAY:
            self.handle_spray(mouse_down, mouse_pos)
        elif self.tool == Tool.MARKER:
            self.handle_marker(mouse_down, mouse_pos)
        elif self.tool == Tool.BUCKET:
            self.handle_bucket(mouse_down, mouse_pos)
        elif self.tool == Tool.LINE:
            self.handle_line(mouse_down, mouse_pos)

        self.was_mouse_down = mouse_down

    def finish_stroke(self):
        if len(self.current_stroke) > 0:
            new_stroke = Stroke(list(self.current_stroke), self.color)
            self.execute_command(DrawStrokeCommand, new_stroke)
            self.current_stroke.clear()

    def handle_brush(self, mouse_down, mouse_pos):
        if mouse_down:
            self.current_stroke.append(PaintDot(16, mouse_pos, self.color))
        else:
            self.finish_stroke()

    def handle_spray(self, mouse_down, mouse_pos):
        if mouse_down:
            spray_radius = 16
            dots_per_frame = 18

            for _ in range(dots_per_frame):
                angle = random.uniform(0, math.tau)
                distance = random.uniform(0, spray_radius)
                offset_x = math.cos(angle) * distance
                offset_y = math.sin(angle) * distance
                dot_pos = (mouse_pos[0] + offset_x, mouse_pos[1] + offset_y)

                self.current_stroke.append(
                    PaintDot(4, dot_pos, self.color, alpha=180, shape="circle")
                )
        else:
            self.finish_stroke()

    def handle_marker(self, mouse_down, mouse_pos):
        if mouse_down:
            self.current_stroke.append(
                PaintDot(24, mouse_pos, self.color, alpha=153, shape="circle")
            )
        else:
            self.finish_stroke()

    def handle_bucket(self, mouse_down, mouse_pos):
        if mouse_down and not self.was_mouse_down:
            cmd = FillCommand(self.canvas, mouse_pos, self._current_rgb(), firebase=self.firebase)
            self.commander.execute(cmd)

    def handle_line(self, mouse_down, mouse_pos):
        if mouse_down and not self.was_mouse_down:
            self.line_start = mouse_pos
            self.line_preview.clear()

        elif mouse_down and self.line_start is not None:
            self.line_preview = self.make_line_dots(self.line_start, mouse_pos, 16, self.color)

        elif not mouse_down and self.was_mouse_down and self.line_start is not None:
            final_dots = self.make_line_dots(self.line_start, mouse_pos, 16, self.color)

            if final_dots:
                new_stroke = Stroke(final_dots, self.color)
                self.execute_command(DrawStrokeCommand, new_stroke)

            self.line_start = None
            self.line_preview.clear()

    def make_line_dots(self, start, end, size, color):
        x1, y1 = start
        x2, y2 = end

        distance = math.dist((x1, y1), (x2, y2))
        steps = max(1, int(distance / 4))

        dots = []
        for i in range(steps + 1):
            t = i / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            dots.append(PaintDot(size, (x, y), color))
        return dots