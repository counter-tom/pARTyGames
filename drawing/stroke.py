class Stroke:
    def __init__(self, dots, color=None, remote=False, is_clear=False):
        self.dots = dots
        self.color = color
        self.remote = remote
        self.is_clear = is_clear