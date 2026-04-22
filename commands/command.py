class Command:
    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError
    