from typing import Dict, Optional, Callable
from larapy.filesystem.filesystem_adapter import FilesystemAdapter


class StorageManager:

    def __init__(self, app):
        self.app = app
        self.disks: Dict[str, FilesystemAdapter] = {}
        self.custom_creators: Dict[str, Callable] = {}

    def disk(self, name: Optional[str] = None) -> FilesystemAdapter:
        name = name or self.get_default_driver()

        if name not in self.disks:
            self.disks[name] = self.resolve(name)

        return self.disks[name]

    def resolve(self, name: str) -> FilesystemAdapter:
        config = self.get_config(name)

        if not config:
            raise ValueError(f"Disk [{name}] is not defined.")

        driver_method = f'_create_{config["driver"]}_driver'

        if hasattr(self, driver_method):
            return getattr(self, driver_method)(config)

        if config["driver"] in self.custom_creators:
            return self.custom_creators[config["driver"]](config)

        raise ValueError(f"Driver [{config['driver']}] is not supported.")

    def _create_local_driver(self, config: dict) -> FilesystemAdapter:
        from larapy.filesystem.drivers.local import LocalFilesystemAdapter

        return LocalFilesystemAdapter(
            root=config["root"],
            url=config.get("url"),
            visibility=config.get("visibility", "public"),
        )

    def _create_s3_driver(self, config: dict) -> FilesystemAdapter:
        from larapy.filesystem.drivers.s3 import S3Adapter

        return S3Adapter(config)

    def _create_gcs_driver(self, config: dict) -> FilesystemAdapter:
        from larapy.filesystem.drivers.gcs import GCSAdapter

        return GCSAdapter(config)

    def _create_azure_driver(self, config: dict) -> FilesystemAdapter:
        from larapy.filesystem.drivers.azure import AzureBlobAdapter

        return AzureBlobAdapter(config)

    def extend(self, driver: str, creator: Callable):
        self.custom_creators[driver] = creator
        return self

    def get_config(self, name: str) -> Optional[dict]:
        config = self.app.config.get("filesystems", {})
        disks = config.get("disks", {})
        return disks.get(name)

    def get_default_driver(self) -> str:
        config = self.app.config.get("filesystems", {})
        return config.get("default", "local")

    def purge(self, name: Optional[str] = None):
        if name:
            if name in self.disks:
                del self.disks[name]
        else:
            self.disks = {}
