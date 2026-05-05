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
    if "color" not in stroke_dict:
        return Stroke([], remote=True)  # skip invalid strokes
    r, g, b = stroke_dict["color"]
    color = _RawColor(r, g, b)
    dots = []
    for dot_data in stroke_dict.get("dots", []):
        size = int(dot_data["size"])
        centre_x = dot_data["x"] + size / 2
        centre_y = dot_data["y"] + size / 2
        dot = PaintDot(size, (centre_x, centre_y), color)
        dots.append(dot)
    stroke = Stroke(dots, color, remote=True)
    if stroke_dict.get("is_fill"):
        stroke.is_fill = True
        stroke.fill_pos = (int(stroke_dict["dots"][0]["x"]), int(stroke_dict["dots"][0]["y"]))
        stroke.fill_color = (r, g, b)
    return stroke