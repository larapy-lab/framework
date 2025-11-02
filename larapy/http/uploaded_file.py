"""
Uploaded File

Represents an uploaded file with validation and storage.
"""

import os
import hashlib
from typing import Optional


class UploadedFile:
    """
    Uploaded File matching Laravel's UploadedFile class.

    Handles file validation, storage, and metadata.
    """

    def __init__(
        self,
        path: str,
        original_name: str,
        mime_type: Optional[str] = None,
        size: Optional[int] = None,
        error: Optional[int] = None,
    ) -> None:
        """
        Initialize uploaded file.

        Args:
            path: Temporary file path
            original_name: Original filename
            mime_type: MIME type
            size: File size in bytes
            error: Upload error code
        """
        self._path = path
        self._original_name = original_name
        self._mime_type = mime_type
        self._size = size or (os.path.getsize(path) if os.path.exists(path) else 0)
        self._error = error or 0

    def path(self) -> str:
        """Get file path."""
        return self._path

    def extension(self) -> str:
        """Get file extension."""
        name, ext = os.path.splitext(self._original_name)
        return ext[1:] if ext else ""

    def getClientOriginalName(self) -> str:
        """Get original filename."""
        return self._original_name

    def getClientOriginalExtension(self) -> str:
        """Get original file extension."""
        return self.extension()

    def getClientMimeType(self) -> Optional[str]:
        """Get MIME type."""
        return self._mime_type

    def getSize(self) -> int:
        """Get file size in bytes."""
        return self._size

    def getError(self) -> int:
        """Get upload error code."""
        return self._error

    def isValid(self) -> bool:
        """Check if upload was successful."""
        return self._error == 0 and os.path.exists(self._path)

    def move(self, directory: str, name: Optional[str] = None) -> str:
        """
        Move file to directory.

        Args:
            directory: Target directory
            name: Target filename

        Returns:
            New file path
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if name is None:
            name = self._generate_unique_name()

        target = os.path.join(directory, name)

        if os.path.exists(self._path):
            os.rename(self._path, target)
            self._path = target

        return target

    def store(self, path: str, disk: str = "local") -> str:
        """
        Store file on disk.

        Args:
            path: Storage path
            disk: Disk name

        Returns:
            Stored file path
        """
        filename = self._generate_unique_name()
        full_path = os.path.join(path, filename)

        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if os.path.exists(self._path):
            import shutil

            shutil.copy2(self._path, full_path)

        return full_path

    def storeAs(self, path: str, name: str, disk: str = "local") -> str:
        """
        Store file with specific name.

        Args:
            path: Storage path
            name: Filename
            disk: Disk name

        Returns:
            Stored file path
        """
        full_path = os.path.join(path, name)

        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if os.path.exists(self._path):
            import shutil

            shutil.copy2(self._path, full_path)

        return full_path

    def _generate_unique_name(self) -> str:
        """Generate unique filename."""
        if os.path.exists(self._path):
            with open(self._path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        else:
            import time

            file_hash = hashlib.md5(str(time.time()).encode()).hexdigest()

        ext = self.extension()
        return f"{file_hash}.{ext}" if ext else file_hash

    def hashName(self, path: Optional[str] = None) -> str:
        """Get hash-based filename."""
        name = self._generate_unique_name()
        return os.path.join(path, name) if path else name

    def __str__(self) -> str:
        """String representation."""
        return f"<UploadedFile {self._original_name}>"
