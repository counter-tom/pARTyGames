class DrawStrokeCommand:
    def __init__(self, canvas, stroke):
        self.canvas = canvas
        self.stroke = stroke

    def do(self):
        if self.stroke not in self.canvas.strokes:
            self.canvas.strokes.append(self.stroke)

        for dot in self.stroke.dots:
            self.canvas.surface.blit(dot.surf, (dot.x, dot.y))

        self.canvas.makeDirty()

    def undo(self):
        if self.stroke in self.canvas.strokes:
            self.canvas.strokes.remove(self.stroke)
            self.canvas.rebuild_canvas()
            self.canvas.makeDirty()