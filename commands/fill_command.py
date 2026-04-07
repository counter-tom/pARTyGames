class FillCommand:
    def __init__(self, canvas, start_pos, fill_color):
        self.canvas = canvas
        self.start_pos = start_pos
        self.fill_color = fill_color
        self.old_strokes = []
        self.old_surface = None

    def do(self):
        self.old_strokes = list(self.canvas.strokes)
        self.old_surface = self.canvas.surface.copy()
        self.flood_fill(self.canvas.surface, self.start_pos, self.fill_color)
        self.canvas.makeDirty()

    def undo(self):
        self.canvas.strokes = list(self.old_strokes)
        self.canvas.surface = self.old_surface.copy()
        self.canvas.makeDirty()

    def flood_fill(self, surface, start_pos, fill_color):
        width, height = surface.get_size()
        x, y = start_pos

        if x < 0 or x >= width or y < 0 or y >= height:
            return

        target_color = surface.get_at((x, y))[:3]
        if target_color == fill_color:
            return

        stack = [(x, y)]

        while stack:
            px, py = stack.pop()

            if px < 0 or px >= width or py < 0 or py >= height:
                continue

            current_color = surface.get_at((px, py))[:3]
            if current_color != target_color:
                continue

            surface.set_at((px, py), fill_color)

            stack.append((px + 1, py))
            stack.append((px - 1, py))
            stack.append((px, py + 1))
            stack.append((px, py - 1))