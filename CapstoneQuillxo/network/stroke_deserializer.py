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
    """
    Convert a Firebase stroke dict back into a Stroke object.

    Args:
        stroke_dict: Dict with keys uid, color ([r,g,b]), dots ([{x,y,size}])

    Returns:
        A Stroke instance with PaintDot objects ready to be blitted.
    """
    r, g, b = stroke_dict["color"]
    color = _RawColor(r, g, b)

    dots = []
    for dot_data in stroke_dict.get("dots", []):
        size = int(dot_data["size"])
        # x and y in Firebase are already the top-left surface position.
        # PaintDot.__init__ offsets from centre, so we pass the centre back.
        centre_x = dot_data["x"] + size / 2
        centre_y = dot_data["y"] + size / 2
        dot = PaintDot(size, (centre_x, centre_y), color)
        dots.append(dot)

    return Stroke(dots)
