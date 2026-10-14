class Document:
    def __init__(self, content: str, owner: str):
        self.content = content
        self.owner = owner

    def read(self) -> str:
        return self.content


class ProtectedDocumentProxy:
    def __init__(self, document: Document, allowed_users: list[str]):
        self._document = document
        self._allowed = set(allowed_users)

    def read(self, user: str) -> str:
        if user not in self._allowed:
            raise PermissionError(f"User '{user}' is not allowed to read this document.")
        print(f"[Proxy] Access granted to '{user}'")
        return self._document.read()


if __name__ == '__main__':
    doc = Document("Secret business plan", owner="alice")
    proxy = ProtectedDocumentProxy(doc, allowed_users=["alice", "bob"])

    print(proxy.read("alice"))
    print(proxy.read("bob"))
    print(proxy.read("eve"))
