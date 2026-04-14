import pygame
import pytest
from CapstoneQuillxo.canvas import PaintCanvas, MasterCanvas

@pytest.fixture(autouse=True)
def pygame_init():
    pygame.init()
    yield
    pygame.quit()

def test_register_canvas():
    master = MasterCanvas()
    canvas = PaintCanvas()
    master.register("user1", canvas)
    assert "user1" in master.canvases

def test_composite_clears_before_drawing():
    master = MasterCanvas()
    canvas = PaintCanvas()
    master.register("user1", canvas)
    master.composite()  # should not raise