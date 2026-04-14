"""
network/stroke_deserializer.py

Converts incoming Firebase stroke dicts back into Stroke and PaintDot
objects so they can be applied to a PaintCanvas via DrawStrokeCommand.
"""

import pygame
from CapstoneQuillxo.drawing.paint_dot import PaintDot
from CapstoneQuillxo.drawing.stroke import Stroke


class _RawColor:
    """
    Minimal stand-in for a Color enum value when deserializing
    incoming strokes. PaintDot expects an object with a .value
    tuple of (r, g, b).
    """
    def __init__(self, r, g, b):
        self.value = (r, g, b)


def deserialize_stroke(stroke_dict: dict) -> Stroke:
    r, g, b = stroke_dict["color"]
    color = _RawColor(r, g, b)
    dots = []
    for dot_data in stroke_dict.get("dots", []):
        size = int(dot_data["size"])
        centre_x = dot_data["x"] + size / 2
        centre_y = dot_data["y"] + size / 2
        dot = PaintDot(size, (centre_x, centre_y), color)
        dots.append(dot)
    return Stroke(dots, remote=True)  # <-- flag it
