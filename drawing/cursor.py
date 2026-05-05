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
        self.firebase = firebase
        self.rgb_picker = None

        self.surf = pygame.Surface((10, 10))
        self.x = 0
        self.y = 0

        self.tool = Tool.BRUSH
        self.was_mouse_down = False
        self.line_start = None
        self.line_preview = []

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
            if self.tool == Tool.ERASER:
                self.surf.fill((225, 225, 225))
            else:
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
            elif self.tool == Tool.EYEDROPPER:
                self.handle_eyedropper(mouse_down, mouse_pos)
            elif self.tool == Tool.ERASER:
                self.handle_eraser(mouse_down, mouse_pos)
            elif self.tool == Tool.NEUTRAL:
                pass

            self.was_mouse_down = mouse_down

    def finish_stroke(self):
        if len(self.current_stroke) > 0:
            new_stroke = Stroke(list(self.current_stroke), self.color)
            self.execute_command(DrawStrokeCommand, new_stroke)
            self.current_stroke.clear()

    def handle_brush(self, mouse_down, mouse_pos):
        if mouse_down:
            if self.current_stroke:
                last_dot = self.current_stroke[-1]
                last_pos = (last_dot.x + 8, last_dot.y + 8)
                dots = self.make_line_dots(last_pos, mouse_pos, 16, self.color)
                self.current_stroke.extend(dots)
            else:
                self.current_stroke.append(PaintDot(16, mouse_pos, self.color))
        else:
            self.finish_stroke()

    def handle_spray(self, mouse_down, mouse_pos):
        if mouse_down:
            spray_radius = 16
            dots_per_frame = 18
            if self.current_stroke:
                last_dot = self.current_stroke[-1]
                last_pos = (last_dot.x + 2, last_dot.y + 2)
                distance = math.dist(last_pos, mouse_pos)
                steps = max(1, int(distance / 8))
                for i in range(steps):
                    t = i / steps
                    x = last_pos[0] + (mouse_pos[0] - last_pos[0]) * t
                    y = last_pos[1] + (mouse_pos[1] - last_pos[1]) * t
                    for _ in range(dots_per_frame // steps):
                        angle = random.uniform(0, math.tau)
                        distance_r = random.uniform(0, spray_radius)
                        dot_pos = (x + math.cos(angle) * distance_r,
                                   y + math.sin(angle) * distance_r)
                        self.current_stroke.append(
                            PaintDot(4, dot_pos, self.color, alpha=180, shape="circle")
                        )
            else:
                for _ in range(dots_per_frame):
                    angle = random.uniform(0, math.tau)
                    distance_r = random.uniform(0, spray_radius)
                    dot_pos = (mouse_pos[0] + math.cos(angle) * distance_r,
                               mouse_pos[1] + math.sin(angle) * distance_r)
                    self.current_stroke.append(
                        PaintDot(4, dot_pos, self.color, alpha=180, shape="circle")
                    )
        else:
            self.finish_stroke()

    def handle_marker(self, mouse_down, mouse_pos):
        if mouse_down:
            if self.current_stroke:
                last_dot = self.current_stroke[-1]
                last_pos = (last_dot.x + 12, last_dot.y + 12)
                dots = self.make_line_dots(last_pos, mouse_pos, 24, self.color)
                for dot in dots:
                    self.current_stroke.append(
                        PaintDot(24, (dot.x + 12, dot.y + 12), self.color, alpha=153, shape="circle")
                    )
            else:
                self.current_stroke.append(
                    PaintDot(24, mouse_pos, self.color, alpha=153, shape="circle")
                )
        else:
            self.finish_stroke()

    def handle_bucket(self, mouse_down, mouse_pos):
        if mouse_down and not self.was_mouse_down:
            self.execute_command(FillCommand, mouse_pos, self._current_rgb())
            fill_dot = PaintDot(1, mouse_pos, self.color)
            new_stroke = Stroke([fill_dot], self.color, is_fill=True)
            new_stroke.fill_pos = mouse_pos
            new_stroke.fill_color = self._current_rgb()
            self.commander.execute(DrawStrokeCommand(self.canvas, new_stroke))

    def handle_eraser(self, mouse_down, mouse_pos):
        white = (225, 225, 225)
        if mouse_down:
            if self.current_stroke:
                last_dot = self.current_stroke[-1]
                last_pos = (last_dot.x + 12, last_dot.y + 12)
                dots = self.make_line_dots(last_pos, mouse_pos, 24, white)
                for dot in dots:
                    self.current_stroke.append(
                        PaintDot(24, (dot.x + 12, dot.y + 12), white)
                    )
            else:
                self.current_stroke.append(PaintDot(24, mouse_pos, white))
        else:
            if len(self.current_stroke) > 0:
                new_stroke = Stroke(list(self.current_stroke), white)
                self.commander.execute(DrawStrokeCommand(self.canvas, new_stroke))
                self.current_stroke.clear()

    def handle_eyedropper(self, mouse_down, mouse_pos):
        if mouse_down and not self.was_mouse_down:
            try:
                x, y = int(mouse_pos[0]), int(mouse_pos[1])
                w, h = self.canvas.surface.get_size()
                if 0 <= x < w and 0 <= y < h:
                    picked = self.canvas.surface.get_at((x, y))[:3]
                    if self.rgb_picker is not None:
                        self.rgb_picker.set_color(picked)
            except Exception as e:
                print(f"[Eyedropper] Error: {e}")

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