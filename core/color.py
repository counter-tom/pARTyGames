from enum import Enum

class Color(Enum):
    WHITE = (225, 225, 225)
    BLACK = (0, 0, 0)
    GREY = (128, 128, 128)
    BUTTON_INACTIVE_GREY = (212, 212, 212)
    BUTTON_ACTIVE_GREY = (73, 72, 72)
    PURPLE = (128, 0, 128)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    

class Tool(Enum):
    NEUTRAL = 0
    BRUSH = 1
    SPRAY = 2
    MARKER = 3
    BUCKET = 4
    LINE = 5
    EYEDROPPER = 6
    ERASER = 7