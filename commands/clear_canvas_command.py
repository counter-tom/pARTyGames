from CapstoneQuillxo.commands.command import Command


class ClearCanvasCommand:
    def __init__(self, canvas, firebase=None):
        self.canvas = canvas
        self.firebase = firebase
        self.memento = None

    def do(self):
        self.memento = self.canvas.save()
        self.canvas.clear()
        if self.firebase is not None:
            self.firebase.push_clear()

    def undo(self):
        if self.memento is not None:
            self.canvas.restore(self.memento)