class Stroke:
    def __init__(self, dots, color=None, remote=False, is_clear=False, is_fill=False):
        self.dots = dots
        self.color = color
        self.remote = remote
        self.is_clear = is_clear
        self.is_fill = is_fill
        self.fill_pos = None
        self.fill_color = None