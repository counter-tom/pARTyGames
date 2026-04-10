from CapstoneQuillxo.commands.command import Command


class CommandManager(Command):
    SNAPSHOT_INTERVAL = 20

    def __init__(self, canvas):
        self.canvas = canvas
        self.commands = []                                  # list of Command objects
        self.redo_stack = []
        self.snapshots = [(0, self.canvas.save())]          # list of Mementos

        print(f"CommandManager created: {id(self)} for canvas: {id(canvas)}")
    def execute(self, command):
        command.do()
        self.commands.append(command)
        self.redo_stack.clear()

        if len(self.commands) % self.SNAPSHOT_INTERVAL == 0:
            # Save the current command count (ID) along with the state
            self.snapshots.append((len(self.commands), self.canvas.save()))

    def undo(self):
        if not self.commands:
            return
        command = self.commands.pop()
        self.redo_stack.append(command)
        self.restore_to_current_state()

    def redo(self):
        if not self.redo_stack:
            return
        
        command = self.redo_stack.pop()
        self.commands.append(command)
        command.do()

    def restore_to_current_state(self):
        # Find the latest snapshot that doesn't exceed current command count
        latest_snap_id, memento = self.snapshots[0]
        for snap_id, snap_memento in self.snapshots:
            if snap_id <= len(self.commands):
                latest_snap_id = snap_id
                memento = snap_memento
            else:
                break
        
        # Restore that snapshot
        self.canvas.restore(memento)

        # Replay commands that happened AFTER restored snapshot
        for i in range(latest_snap_id, len(self.commands)):
            self.commands[i].do()