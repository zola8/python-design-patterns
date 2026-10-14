from abc import ABC
from abc import abstractmethod


# ==========================================
# 1. THE COMMAND INTERFACE
# ==========================================
class Command(ABC):
    @abstractmethod
    def execute(self):
        """Perform the action."""
        pass

    @abstractmethod
    def undo(self):
        """Reverse the action."""
        pass


# ==========================================
# 2. THE RECEIVER (The object that does the work)
# ==========================================
class TextEditor:
    def __init__(self):
        self.text = ""

    def insert(self, text: str, position: int):
        self.text = self.text[:position] + text + self.text[position:]
        print(f"[Editor] Inserted '{text}' at position {position}")

    def delete(self, length: int, position: int) -> str:
        deleted = self.text[position:position + length]
        self.text = self.text[:position] + self.text[position + length:]
        print(f"[Editor] Deleted '{deleted}' from position {position}")
        return deleted

    def display(self):
        print(f"[Editor] Current text: '{self.text}'")


# ==========================================
# 3. CONCRETE COMMANDS
# ==========================================
class InsertCommand(Command):
    def __init__(self, editor: TextEditor, text: str, position: int):
        self.editor = editor
        self.text = text
        self.position = position

    def execute(self):
        self.editor.insert(self.text, self.position)

    def undo(self):
        # To undo insert, we delete what we inserted
        self.editor.delete(len(self.text), self.position)


class DeleteCommand(Command):
    def __init__(self, editor: TextEditor, length: int, position: int):
        self.editor = editor
        self.length = length
        self.position = position
        self.deleted_text = None  # Store for undo

    def execute(self):
        self.deleted_text = self.editor.delete(self.length, self.position)

    def undo(self):
        # To undo delete, we re-insert what we deleted
        if self.deleted_text:
            self.editor.insert(self.deleted_text, self.position)


# ==========================================
# 4. THE INVOKER (Manages command execution and history)
# ==========================================
class CommandHistory:
    def __init__(self):
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []

    def execute(self, command: Command):
        command.execute()
        self._history.append(command)
        self._redo_stack.clear()  # Clear redo stack on new action

    def undo(self):
        if not self._history:
            print("[History] Nothing to undo")
            return

        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self):
        if not self._redo_stack:
            print("[History] Nothing to redo")
            return

        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)


# ==========================================
# 5. USAGE
# ==========================================
if __name__ == "__main__":
    editor = TextEditor()
    history = CommandHistory()

    # Execute commands
    history.execute(InsertCommand(editor, "Hello", 0))
    editor.display()  # 'Hello'

    history.execute(InsertCommand(editor, " World", 5))
    editor.display()  # 'Hello World'

    history.execute(DeleteCommand(editor, 5, 5))  # Delete "World"
    editor.display()  # 'Hello'

    # Undo operations
    print("\n--- Undoing ---")
    history.undo()  # Undo delete → re-insert "World"
    editor.display()  # 'Hello World'

    history.undo()  # Undo second insert
    editor.display()  # 'Hello'

    # Redo operations
    print("\n--- Redoing ---")
    history.redo()  # Redo second insert
    editor.display()  # 'Hello World'
