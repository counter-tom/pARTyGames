"""
network/stroke_deserializer.py

Converts incoming Firebase stroke dicts back into Stroke and PaintDot
objects so they can be applied to a PaintCanvas via DrawStrokeCommand.
"""

import pygame
from drawing.paint_dot import PaintDot
from drawing.stroke import Stroke


class _RawColor:
    def __init__(self, r, g, b):
        self.value = (r, g, b)


def deserialize_stroke(stroke_dict: dict) -> Stroke:
    if stroke_dict.get("is_fill"):
        s = Stroke([], remote=True)
        s.is_fill = True
        s.fill_x  = stroke_dict["fill_x"]
        s.fill_y  = stroke_dict["fill_y"]
        color = stroke_dict["color"]
        if isinstance(color, dict):
            color = [color[str(k)] for k in range(len(color))]
        r, g, b = color
        s.fill_color = (r, g, b)
        return s

    color = stroke_dict["color"]
    if isinstance(color, dict):
        color = [color[str(k)] for k in range(len(color))]
    r, g, b = color

    # ✅ Firebase returns arrays as numbered dicts — normalize dots
    raw_dots = stroke_dict.get("dots", [])
    if isinstance(raw_dots, dict):
        raw_dots = [raw_dots[str(k)] for k in range(len(raw_dots))]

    dots = []
    for dot_data in raw_dots:
        size     = int(dot_data["size"])
        centre_x = dot_data["x"] + size / 2
        centre_y = dot_data["y"] + size / 2
        dot      = PaintDot(size, (centre_x, centre_y), _RawColor(r, g, b))
        dots.append(dot)
    return Stroke(dots, remote=True)