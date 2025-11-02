from typing import Optional, List, IO
from datetime import datetime


class Storage:
    _manager = None

    @classmethod
    def set_manager(cls, manager):
        cls._manager = manager

    @classmethod
    def _get_manager(cls):
        if cls._manager is None:
            raise RuntimeError("Storage manager not set. Call Storage.set_manager() first.")
        return cls._manager

    @classmethod
    def disk(cls, name: Optional[str] = None):
        return cls._get_manager().disk(name)

    @classmethod
    def get(cls, path: str) -> bytes:
        return cls.disk().get(path)

    @classmethod
    def put(cls, path: str, contents: bytes, options: Optional[dict] = None) -> bool:
        return cls.disk().put(path, contents, options)

    @classmethod
    def exists(cls, path: str) -> bool:
        return cls.disk().exists(path)

    @classmethod
    def missing(cls, path: str) -> bool:
        return cls.disk().missing(path)

    @classmethod
    def delete(cls, path: str) -> bool:
        return cls.disk().delete(path)

    @classmethod
    def copy(cls, from_path: str, to_path: str) -> bool:
        return cls.disk().copy(from_path, to_path)

    @classmethod
    def move(cls, from_path: str, to_path: str) -> bool:
        return cls.disk().move(from_path, to_path)

    @classmethod
    def size(cls, path: str) -> int:
        return cls.disk().size(path)

    @classmethod
    def last_modified(cls, path: str) -> int:
        return cls.disk().last_modified(path)

    @classmethod
    def files(cls, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        return cls.disk().files(directory, recursive)

    @classmethod
    def all_files(cls, directory: Optional[str] = None) -> List[str]:
        return cls.disk().all_files(directory)

    @classmethod
    def directories(cls, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        return cls.disk().directories(directory, recursive)

    @classmethod
    def all_directories(cls, directory: Optional[str] = None) -> List[str]:
        return cls.disk().all_directories(directory)

    @classmethod
    def make_directory(cls, path: str) -> bool:
        return cls.disk().make_directory(path)

    @classmethod
    def delete_directory(cls, directory: str) -> bool:
        return cls.disk().delete_directory(directory)

    @classmethod
    def url(cls, path: str) -> str:
        return cls.disk().url(path)

    @classmethod
    def temporary_url(cls, path: str, expiration: datetime) -> str:
        return cls.disk().temporary_url(path, expiration)

    @classmethod
    def read_stream(cls, path: str) -> IO:
        return cls.disk().read_stream(path)

    @classmethod
    def write_stream(cls, path: str, stream: IO, options: Optional[dict] = None) -> bool:
        return cls.disk().write_stream(path, stream, options)

    @classmethod
    def append(cls, path: str, contents: bytes) -> bool:
        return cls.disk().append(path, contents)

    @classmethod
    def prepend(cls, path: str, contents: bytes) -> bool:
        return cls.disk().prepend(path, contents)
