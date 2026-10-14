class SimpleCommandHistory:
    def __init__(self):
        self._history = []
        self._redo_stack = []

    def execute(self, do_action, undo_action):
        """Execute a command defined by two functions."""
        do_action()
        self._history.append((do_action, undo_action))
        self._redo_stack.clear()

    def undo(self):
        if not self._history:
            return
        do_action, undo_action = self._history.pop()
        undo_action()
        self._redo_stack.append((do_action, undo_action))

    def redo(self):
        if not self._redo_stack:
            return
        do_action, undo_action = self._redo_stack.pop()
        do_action()
        self._history.append((do_action, undo_action))


# Usage with lambdas
text = ""


def insert(t):
    global text
    text += t
    print(f"Inserted '{t}', text is now: '{text}'")


def delete_last():
    global text
    removed = text[-1]
    text = text[:-1]
    print(f"Deleted '{removed}', text is now: '{text}'")


history = SimpleCommandHistory()

if __name__ == '__main__':
    # Execute commands
    history.execute(
        do_action=lambda: insert("A"),
        undo_action=delete_last
    )
    history.execute(
        do_action=lambda: insert("B"),
        undo_action=delete_last
    )
    history.execute(
        do_action=lambda: insert("C"),
        undo_action=delete_last
    )

    # Undo/redo
    history.undo()  # Remove C
    history.undo()  # Remove B
    history.redo()  # Re-add B
