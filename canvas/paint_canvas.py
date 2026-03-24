import pygame
from CapstoneQuillxo.core.color import Color
from CapstoneQuillxo.canvas.drawing_memento import DrawingMemento

class PaintCanvas:
    SYNC_INTERVAL = 200 #miliseconds

    def __init__(self):
        self.strokes = []  # List of strokes
        # Create the internal surface
        self.surface = pygame.Surface((640, 640))
        self.surface.fill(Color.WHITE.value)
        self._last_sync = pygame.time.get_ticks()
        self._dirty = False    #Flag to track if canvas has changed since last sync

        print(f"PaintCanvas created: {id(self)}")
    def makeDirty(self):
        self._dirty = True
    
    def sync(self, master_canvas):
        now = pygame.time.get_ticks()
        if self._dirty and (now - self._last_sync >= self.SYNC_INTERVAL):
            master_canvas.receive(self)
            self._last_sync = now
            self._dirty = False
    
    def save(self):
        return DrawingMemento(self.strokes)
    
    def restore(self, memento):
        self.strokes = list(memento.strokes)
        self.rebuild_canvas()

    def clear(self):
        self.strokes.clear()
        self.surface.fill(Color.WHITE.value)
    
    def rebuild_canvas(self):
        self.surface.fill(Color.WHITE.value)
        for stroke in self.strokes:
            for dot in stroke.dots: 
                self.surface.blit(dot.surf, (dot.x, dot.y))
