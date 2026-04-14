class DrawingMemento:
    def __init__(self, strokes, surface):
        # IMPORTANT: Use list() to create a copy, otherwise the 
        # memento changes when the original list changes.
        self.strokes = list(strokes)
        self.surface = surface.copy()