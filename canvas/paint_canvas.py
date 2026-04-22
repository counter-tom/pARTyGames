import pygame
from core.color import Color
from canvas.drawing_memento import DrawingMemento


class PaintCanvas:
    SYNC_INTERVAL = 200  # milliseconds

    def __init__(self, width=640, height=640, position=(0, 0)):
        self.strokes = []
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surface.fill(Color.WHITE.value)

        self.rect = pygame.Rect(position[0], position[1], width, height)

        self._last_sync = pygame.time.get_ticks()
        self._dirty = False

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
        return DrawingMemento(list(self.strokes), self.surface.copy())

    def restore(self, memento):
        self.strokes = list(memento.strokes)
        self.surface = memento.surface.copy()
        self.makeDirty()

    def clear(self):
        self.strokes.clear()
        self.surface.fill(Color.WHITE.value)
        self.makeDirty()

    def rebuild_canvas(self):
        self.surface.fill(Color.WHITE.value)
        for stroke in self.strokes:
            for dot in stroke.dots:
                self.surface.blit(dot.surf, (dot.x, dot.y))
        self.makeDirty()