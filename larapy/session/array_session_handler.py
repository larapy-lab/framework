from typing import Optional, Dict


class ArraySessionHandler:
    def __init__(self):
        self._sessions: Dict[str, str] = {}
        self._minutes: int = 120

    def open(self, save_path: str, session_name: str) -> bool:
        return True

    def close(self) -> bool:
        return True

    def read(self, session_id: str) -> str:
        return self._sessions.get(session_id, "")

    def write(self, session_id: str, data: str) -> bool:
        self._sessions[session_id] = data
        return True

    def destroy(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
        return True

    def gc(self, max_lifetime: int) -> int:
        return 0
