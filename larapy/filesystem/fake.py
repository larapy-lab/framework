from typing import Optional, List, IO, Dict
from datetime import datetime
from io import BytesIO
from larapy.filesystem.filesystem_adapter import FilesystemAdapter


class FakeStorage(FilesystemAdapter):

    def __init__(self):
        self._storage: Dict[str, bytes] = {}
        self.operations: List[Dict] = []

    def _record(self, operation: str, path: str, **kwargs):
        self.operations.append({"operation": operation, "path": path, **kwargs})

    def get(self, path: str) -> bytes:
        self._record("get", path)

        if path not in self._storage:
            raise FileNotFoundError(f"File not found: {path}")

        return self._storage[path]

    def put(self, path: str, contents: bytes, options: Optional[dict] = None) -> bool:
        self._record("put", path, options=options)
        self._storage[path] = contents
        return True

    def exists(self, path: str) -> bool:
        self._record("exists", path)
        return path in self._storage

    def missing(self, path: str) -> bool:
        self._record("missing", path)
        return path not in self._storage

    def delete(self, path: str) -> bool:
        self._record("delete", path)

        if path not in self._storage:
            return False

        del self._storage[path]
        return True

    def copy(self, from_path: str, to_path: str) -> bool:
        self._record("copy", from_path, to_path=to_path)

        if from_path not in self._storage:
            raise FileNotFoundError(f"Source file not found: {from_path}")

        self._storage[to_path] = self._storage[from_path]
        return True

    def move(self, from_path: str, to_path: str) -> bool:
        self._record("move", from_path, to_path=to_path)

        if from_path not in self._storage:
            raise FileNotFoundError(f"Source file not found: {from_path}")

        self._storage[to_path] = self._storage[from_path]
        del self._storage[from_path]
        return True

    def size(self, path: str) -> int:
        self._record("size", path)

        if path not in self._storage:
            raise FileNotFoundError(f"File not found: {path}")

        return len(self._storage[path])

    def last_modified(self, path: str) -> int:
        self._record("last_modified", path)

        if path not in self._storage:
            raise FileNotFoundError(f"File not found: {path}")

        return int(datetime.now().timestamp())

    def files(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        self._record("files", directory or "", recursive=recursive)

        prefix = (directory or "").rstrip("/") + "/" if directory else ""

        result = []
        for path in self._storage.keys():
            if path.startswith(prefix):
                relative_path = path[len(prefix) :]

                if recursive or "/" not in relative_path:
                    result.append(path)

        return sorted(result)

    def all_files(self, directory: Optional[str] = None) -> List[str]:
        return self.files(directory, recursive=True)

    def directories(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        self._record("directories", directory or "", recursive=recursive)

        prefix = (directory or "").rstrip("/") + "/" if directory else ""

        dirs = set()
        for path in self._storage.keys():
            if path.startswith(prefix):
                relative_path = path[len(prefix) :]
                parts = relative_path.split("/")

                if len(parts) > 1:
                    if recursive:
                        for i in range(len(parts) - 1):
                            dirs.add(prefix + "/".join(parts[: i + 1]))
                    else:
                        dirs.add(prefix + parts[0])

        return sorted(list(dirs))

    def all_directories(self, directory: Optional[str] = None) -> List[str]:
        return self.directories(directory, recursive=True)

    def make_directory(self, path: str) -> bool:
        self._record("make_directory", path)
        return True

    def delete_directory(self, directory: str) -> bool:
        self._record("delete_directory", directory)

        prefix = directory.rstrip("/") + "/"
        files_to_delete = [path for path in self._storage.keys() if path.startswith(prefix)]

        if not files_to_delete:
            return False

        for path in files_to_delete:
            del self._storage[path]

        return True

    def url(self, path: str) -> str:
        self._record("url", path)
        return f"https://fake-storage.local/{path}"

    def temporary_url(self, path: str, expiration: datetime) -> str:
        self._record("temporary_url", path, expiration=expiration)
        timestamp = int(expiration.timestamp())
        return f"https://fake-storage.local/{path}?expires={timestamp}"

    def read_stream(self, path: str) -> IO:
        self._record("read_stream", path)

        if path not in self._storage:
            raise FileNotFoundError(f"File not found: {path}")

        return BytesIO(self._storage[path])

    def write_stream(self, path: str, stream: IO, options: Optional[dict] = None) -> bool:
        self._record("write_stream", path, options=options)

        stream.seek(0)
        self._storage[path] = stream.read()
        return True

    def append(self, path: str, contents: bytes) -> bool:
        self._record("append", path)

        if path in self._storage:
            self._storage[path] += contents
        else:
            self._storage[path] = contents

        return True

    def prepend(self, path: str, contents: bytes) -> bool:
        self._record("prepend", path)

        if path in self._storage:
            self._storage[path] = contents + self._storage[path]
        else:
            self._storage[path] = contents

        return True

    def assert_exists(self, path: str):
        if path not in self._storage:
            raise AssertionError(f"File [{path}] does not exist")

    def assert_missing(self, path: str):
        if path in self._storage:
            raise AssertionError(f"File [{path}] exists")

    def assert_created(self, path: str):
        put_operations = [
            op for op in self.operations if op["operation"] == "put" and op["path"] == path
        ]
        if not put_operations:
            raise AssertionError(f"File [{path}] was not created")

    def assert_deleted(self, path: str):
        delete_operations = [
            op for op in self.operations if op["operation"] == "delete" and op["path"] == path
        ]
        if not delete_operations:
            raise AssertionError(f"File [{path}] was not deleted")

    def reset(self):
        self._storage = {}
        self.operations = []
