from typing import Dict, List, Any, Optional


class MessageBag:
    def __init__(self, messages: Optional[Dict[str, List[str]]] = None):
        self._messages: Dict[str, List[str]] = messages or {}

    def add(self, key: str, message: str) -> "MessageBag":
        if key not in self._messages:
            self._messages[key] = []
        self._messages[key].append(message)
        return self

    def get(self, key: str, format: Optional[str] = None) -> List[str]:
        messages = self._messages.get(key, [])
        if format:
            return [format.replace(":message", msg) for msg in messages]
        return messages

    def first(self, key: str, format: Optional[str] = None) -> Optional[str]:
        messages = self.get(key, format)
        return messages[0] if messages else None

    def all(self) -> List[str]:
        messages = []
        for key_messages in self._messages.values():
            messages.extend(key_messages)
        return messages

    def has(self, key: str) -> bool:
        return key in self._messages and len(self._messages[key]) > 0

    def any(self) -> bool:
        return len(self._messages) > 0

    def isEmpty(self) -> bool:
        return not self.any()

    def count(self) -> int:
        return sum(len(messages) for messages in self._messages.values())

    def keys(self) -> List[str]:
        return list(self._messages.keys())

    def messages(self) -> Dict[str, List[str]]:
        return self._messages.copy()

    def toDict(self) -> Dict[str, Any]:
        return {
            "messages": self._messages,
            "count": self.count(),
        }

    def __iter__(self):
        return iter(self._messages.items())

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __len__(self) -> int:
        return self.count()
