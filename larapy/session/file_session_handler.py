import os
import time
from typing import Optional


class FileSessionHandler:
    def __init__(self, path: str, minutes: int = 120):
        self._path = path
        self._minutes = minutes

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def open(self, save_path: str, session_name: str) -> bool:
        return True

    def close(self) -> bool:
        return True

    def read(self, session_id: str) -> str:
        file_path = self._get_path(session_id)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, "r") as f:
                return f.read()

        return ""

    def write(self, session_id: str, data: str) -> bool:
        file_path = self._get_path(session_id)

        with open(file_path, "w") as f:
            f.write(data)

        return True

    def destroy(self, session_id: str) -> bool:
        file_path = self._get_path(session_id)

        if os.path.exists(file_path):
            os.unlink(file_path)

        return True

    def gc(self, max_lifetime: int) -> int:
        files_deleted = 0
        now = time.time()

        for filename in os.listdir(self._path):
            file_path = os.path.join(self._path, filename)

            if os.path.isfile(file_path):
                if now - os.path.getmtime(file_path) > max_lifetime:
                    os.unlink(file_path)
                    files_deleted += 1

        return files_deleted

    def _get_path(self, session_id: str) -> str:
        return os.path.join(self._path, session_id)
