from pathlib import Path
from typing import Optional, List, IO
from datetime import datetime
import shutil
import os
from larapy.filesystem.filesystem_adapter import FilesystemAdapter


class LocalFilesystemAdapter(FilesystemAdapter):

    def __init__(self, root: str, url: Optional[str] = None, visibility: str = "public"):
        self.root = Path(root).resolve()
        self.url_prefix = url or ""
        self.visibility = visibility

        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        full_path = self.root / path.lstrip("/")

        if not str(full_path.resolve()).startswith(str(self.root)):
            raise ValueError(f"Path '{path}' is outside root directory")

        return full_path

    def get(self, path: str) -> bytes:
        file_path = self._full_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return file_path.read_bytes()

    def put(self, path: str, contents: bytes, options: Optional[dict] = None) -> bool:
        file_path = self._full_path(path)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(contents)

        if options and "visibility" in options:
            self._set_visibility(file_path, options["visibility"])
        elif self.visibility == "public":
            self._set_visibility(file_path, "public")

        return True

    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    def missing(self, path: str) -> bool:
        return not self.exists(path)

    def delete(self, path: str) -> bool:
        file_path = self._full_path(path)

        if not file_path.exists():
            return False

        if file_path.is_file():
            file_path.unlink()
        else:
            shutil.rmtree(file_path)

        return True

    def copy(self, from_path: str, to_path: str) -> bool:
        source = self._full_path(from_path)
        destination = self._full_path(to_path)

        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {from_path}")

        destination.parent.mkdir(parents=True, exist_ok=True)

        if source.is_file():
            shutil.copy2(source, destination)
        else:
            shutil.copytree(source, destination, dirs_exist_ok=True)

        return True

    def move(self, from_path: str, to_path: str) -> bool:
        source = self._full_path(from_path)
        destination = self._full_path(to_path)

        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {from_path}")

        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source), str(destination))

        return True

    def size(self, path: str) -> int:
        file_path = self._full_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return file_path.stat().st_size

    def last_modified(self, path: str) -> int:
        file_path = self._full_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return int(file_path.stat().st_mtime)

    def files(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        dir_path = self._full_path(directory or "")

        if not dir_path.exists():
            return []

        if recursive:
            files = [str(p.relative_to(self.root)) for p in dir_path.rglob("*") if p.is_file()]
        else:
            files = [str(p.relative_to(self.root)) for p in dir_path.iterdir() if p.is_file()]

        return sorted(files)

    def all_files(self, directory: Optional[str] = None) -> List[str]:
        return self.files(directory, recursive=True)

    def directories(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        dir_path = self._full_path(directory or "")

        if not dir_path.exists():
            return []

        if recursive:
            dirs = [str(p.relative_to(self.root)) for p in dir_path.rglob("*") if p.is_dir()]
        else:
            dirs = [str(p.relative_to(self.root)) for p in dir_path.iterdir() if p.is_dir()]

        return sorted(dirs)

    def all_directories(self, directory: Optional[str] = None) -> List[str]:
        return self.directories(directory, recursive=True)

    def make_directory(self, path: str) -> bool:
        dir_path = self._full_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return True

    def delete_directory(self, directory: str) -> bool:
        dir_path = self._full_path(directory)

        if not dir_path.exists():
            return False

        shutil.rmtree(dir_path)
        return True

    def url(self, path: str) -> str:
        if not self.url_prefix:
            return f"file://{self._full_path(path)}"

        return f"{self.url_prefix.rstrip('/')}/{path.lstrip('/')}"

    def temporary_url(self, path: str, expiration: datetime) -> str:
        raise NotImplementedError("Local driver does not support temporary URLs")

    def read_stream(self, path: str) -> IO:
        file_path = self._full_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return open(file_path, "rb")

    def write_stream(self, path: str, stream: IO, options: Optional[dict] = None) -> bool:
        file_path = self._full_path(path)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(stream, f)

        if options and "visibility" in options:
            self._set_visibility(file_path, options["visibility"])

        return True

    def append(self, path: str, contents: bytes) -> bool:
        file_path = self._full_path(path)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "ab") as f:
            f.write(contents)

        return True

    def prepend(self, path: str, contents: bytes) -> bool:
        file_path = self._full_path(path)

        existing_contents = b""
        if file_path.exists():
            existing_contents = file_path.read_bytes()

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(contents + existing_contents)

        return True

    def _set_visibility(self, path: Path, visibility: str):
        if visibility == "public":
            os.chmod(path, 0o644 if path.is_file() else 0o755)
        elif visibility == "private":
            os.chmod(path, 0o600 if path.is_file() else 0o700)
