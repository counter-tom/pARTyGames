"""
network/stroke_deserializer.py

Converts incoming Firebase stroke dicts back into Stroke and PaintDot
objects so they can be applied to a PaintCanvas via DrawStrokeCommand.
"""

import pygame
from drawing.paint_dot import PaintDot
from drawing.stroke import Stroke


class _RawColor:
    """
    Minimal stand-in for a Color enum value when deserializing
    incoming strokes. PaintDot expects an object with a .value
    tuple of (r, g, b).
    """
    def __init__(self, r, g, b):
        self.value = (r, g, b)


def deserialize_stroke(stroke_dict: dict) -> Stroke:
    if stroke_dict.get("is_fill"):
            s = Stroke([], remote=True)
            s.is_fill = True
            s.fill_x  = stroke_dict["fill_x"]
            s.fill_y  = stroke_dict["fill_y"]

            # ✅ Firebase may return color as {0: r, 1: g, 2: b} instead of [r, g, b]
            color = stroke_dict["color"]
            if isinstance(color, dict):
                color = [color[k] for k in sorted(color.keys())]
            r, g, b = color
            s.fill_color = (r, g, b)
            return s
    
    color = stroke_dict["color"]
    if isinstance(color, dict):
        color = [color[k] for k in sorted(color.keys())]
    r, g, b = color
    dots = []
    for dot_data in stroke_dict.get("dots", []):
        size = int(dot_data["size"])
        centre_x = dot_data["x"] + size / 2
        centre_y = dot_data["y"] + size / 2
        dot = PaintDot(size, (centre_x, centre_y), color)
        dots.append(dot)
    return Stroke(dots, remote=True)  # <-- flag it
