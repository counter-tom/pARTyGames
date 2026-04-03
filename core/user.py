from CapstoneQuillxo.canvas import PaintCanvas
from CapstoneQuillxo.drawing import Cursor
from CapstoneQuillxo.commands import CommandManager


class User:
    def __init__(self, screen, user_id, color):
        self.color = color
        self.user_id = user_id
        self.screen = screen
        self.canvas = PaintCanvas()
        self.commander = CommandManager(self.canvas)
        self.current_stroke = []
        self.cursor = Cursor(screen, self.current_stroke, self.canvas, self.commander, self.color)

    def update(self, is_cursor_on_ui):
        self.cursor.color = self.color

        if not is_cursor_on_ui:
            self.cursor.update()
        else:
            self.cursor.update_position_only()

    def draw_canvas(self):
        self.screen.blit(self.canvas.surface, (0, 0))

        for dot in self.current_stroke:
            self.screen.blit(dot.surf, (dot.x, dot.y))

        for dot in self.cursor.line_preview:
            self.screen.blit(dot.surf, (dot.x, dot.y))

    def draw_cursor(self):
        self.screen.blit(self.cursor.surf, (self.cursor.x, self.cursor.y))

    def pass_command(self, command_class, *args):
        self.commander.execute(command_class(self.canvas, *args))

    def undo(self):
        self.commander.undo()

    def redo(self):
        self.commander.redo()

    def sync_canvas(self, master_canvas):
        self.canvas.sync(master_canvas)