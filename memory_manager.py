class MemoryManager:
    def __init__(self, enabled=True, limit=2500):
        self.enabled = bool(enabled)
        self.limit = int(limit)
        self.buf = []  # list of (user, assistant)

    def add_pair(self, user: str, assistant: str):
        if not self.enabled:
            return
        self.buf.append((user.strip(), assistant.strip()))
        while sum(len(u)+len(a) for u,a in self.buf) > self.limit and self.buf:
            self.buf.pop(0)

    def inject_memory(self, user_text: str) -> str:
        if not self.enabled or not self.buf:
            return ""
        tail = self.buf[-3:]
        return "\n".join([f"User: {u}\nAssistant: {a}" for u,a in tail])
