from abc import ABC, abstractmethod
from typing import Optional, List, IO
from datetime import datetime


class FilesystemAdapter(ABC):

    @abstractmethod
    def get(self, path: str) -> bytes:
        pass

    @abstractmethod
    def put(self, path: str, contents: bytes, options: Optional[dict] = None) -> bool:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def missing(self, path: str) -> bool:
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        pass

    @abstractmethod
    def copy(self, from_path: str, to_path: str) -> bool:
        pass

    @abstractmethod
    def move(self, from_path: str, to_path: str) -> bool:
        pass

    @abstractmethod
    def size(self, path: str) -> int:
        pass

    @abstractmethod
    def last_modified(self, path: str) -> int:
        pass

    @abstractmethod
    def files(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        pass

    @abstractmethod
    def all_files(self, directory: Optional[str] = None) -> List[str]:
        pass

    @abstractmethod
    def directories(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        pass

    @abstractmethod
    def all_directories(self, directory: Optional[str] = None) -> List[str]:
        pass

    @abstractmethod
    def make_directory(self, path: str) -> bool:
        pass

    @abstractmethod
    def delete_directory(self, directory: str) -> bool:
        pass

    @abstractmethod
    def url(self, path: str) -> str:
        pass

    @abstractmethod
    def temporary_url(self, path: str, expiration: datetime) -> str:
        pass

    @abstractmethod
    def read_stream(self, path: str) -> IO:
        pass

    @abstractmethod
    def write_stream(self, path: str, stream: IO, options: Optional[dict] = None) -> bool:
        pass

    @abstractmethod
    def append(self, path: str, contents: bytes) -> bool:
        pass

    @abstractmethod
    def prepend(self, path: str, contents: bytes) -> bool:
        pass
