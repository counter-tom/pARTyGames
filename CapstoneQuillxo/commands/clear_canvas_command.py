from CapstoneQuillxo.commands.command import Command


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