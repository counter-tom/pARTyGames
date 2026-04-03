from enum import Enum

class Color(Enum):
    WHITE = (225, 225, 225)
    BLACK = (0, 0, 0)
    GREY = (128, 128, 128)
    BUTTON_INACTIVE_GREY = (212, 212, 212)
    BUTTON_ACTIVE_GREY = (73, 72, 72)

class Tool(Enum):
    BRUSH = 1
    SPRAY = 2
    MARKER = 3
    BUCKET = 4
    LINE = 5