from typing import Optional, List, IO
from datetime import datetime, timedelta
from io import BytesIO
from larapy.filesystem.filesystem_adapter import FilesystemAdapter


class S3Adapter(FilesystemAdapter):

    def __init__(self, config: dict):
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("boto3 is required for S3 driver. Install with: pip install boto3")

        self.config = config
        self.bucket = config["bucket"]
        self.prefix = config.get("prefix", "").rstrip("/") + "/" if config.get("prefix") else ""
        self.region = config.get("region", "us-east-1")
        self.url_prefix = config.get("url")

        self.client = boto3.client(
            "s3",
            aws_access_key_id=config.get("key"),
            aws_secret_access_key=config.get("secret"),
            region_name=self.region,
        )

        self.ClientError = ClientError

    def _full_key(self, path: str) -> str:
        return self.prefix + path.lstrip("/")

    def get(self, path: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._full_key(path))
            return response["Body"].read()
        except self.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {path}")
            raise

    def put(self, path: str, contents: bytes, options: Optional[dict] = None) -> bool:
        extra_args = {}

        if options:
            if "visibility" in options:
                extra_args["ACL"] = (
                    "public-read" if options["visibility"] == "public" else "private"
                )
            if "content_type" in options:
                extra_args["ContentType"] = options["content_type"]
            if "cache_control" in options:
                extra_args["CacheControl"] = options["cache_control"]

        self.client.put_object(
            Bucket=self.bucket, Key=self._full_key(path), Body=contents, **extra_args
        )

        return True

    def exists(self, path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._full_key(path))
            return True
        except self.ClientError:
            return False

    def missing(self, path: str) -> bool:
        return not self.exists(path)

    def delete(self, path: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=self._full_key(path))
            return True
        except self.ClientError:
            return False

    def copy(self, from_path: str, to_path: str) -> bool:
        copy_source = {"Bucket": self.bucket, "Key": self._full_key(from_path)}

        try:
            self.client.copy_object(
                CopySource=copy_source, Bucket=self.bucket, Key=self._full_key(to_path)
            )
            return True
        except self.ClientError:
            return False

    def move(self, from_path: str, to_path: str) -> bool:
        if self.copy(from_path, to_path):
            return self.delete(from_path)
        return False

    def size(self, path: str) -> int:
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=self._full_key(path))
            return response["ContentLength"]
        except self.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File not found: {path}")
            raise

    def last_modified(self, path: str) -> int:
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=self._full_key(path))
            return int(response["LastModified"].timestamp())
        except self.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File not found: {path}")
            raise

    def files(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        prefix = self._full_key(directory or "")
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        delimiter = "" if recursive else "/"

        files = []
        continuation_token = None

        while True:
            params = {"Bucket": self.bucket, "Prefix": prefix, "Delimiter": delimiter}

            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = self.client.list_objects_v2(**params)

            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if key.startswith(self.prefix):
                        key = key[len(self.prefix) :]

                    if not key.endswith("/"):
                        files.append(key)

            if not response.get("IsTruncated"):
                break

            continuation_token = response.get("NextContinuationToken")

        return sorted(files)

    def all_files(self, directory: Optional[str] = None) -> List[str]:
        return self.files(directory, recursive=True)

    def directories(self, directory: Optional[str] = None, recursive: bool = False) -> List[str]:
        prefix = self._full_key(directory or "")
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        dirs = set()
        continuation_token = None

        while True:
            params = {"Bucket": self.bucket, "Prefix": prefix, "Delimiter": "/"}

            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = self.client.list_objects_v2(**params)

            if "CommonPrefixes" in response:
                for common_prefix in response["CommonPrefixes"]:
                    prefix_key = common_prefix["Prefix"]
                    if prefix_key.startswith(self.prefix):
                        prefix_key = prefix_key[len(self.prefix) :]

                    dirs.add(prefix_key.rstrip("/"))

            if not response.get("IsTruncated"):
                break

            continuation_token = response.get("NextContinuationToken")

        return sorted(list(dirs))

    def all_directories(self, directory: Optional[str] = None) -> List[str]:
        all_files = self.all_files(directory)
        dirs = set()

        for file_path in all_files:
            parts = file_path.split("/")
            for i in range(len(parts) - 1):
                dirs.add("/".join(parts[: i + 1]))

        return sorted(list(dirs))

    def make_directory(self, path: str) -> bool:
        key = self._full_key(path).rstrip("/") + "/"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=b"")
        return True

    def delete_directory(self, directory: str) -> bool:
        files = self.all_files(directory)

        if not files:
            return False

        objects = [{"Key": self._full_key(f)} for f in files]

        for i in range(0, len(objects), 1000):
            batch = objects[i : i + 1000]
            self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": batch})

        return True

    def url(self, path: str) -> str:
        if self.url_prefix:
            return f"{self.url_prefix.rstrip('/')}/{path.lstrip('/')}"

        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{self._full_key(path)}"

    def temporary_url(self, path: str, expiration: datetime) -> str:
        expires_in = int((expiration - datetime.now()).total_seconds())

        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": self._full_key(path)},
            ExpiresIn=expires_in,
        )

    def read_stream(self, path: str) -> IO:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._full_key(path))
            return response["Body"]
        except self.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {path}")
            raise

    def write_stream(self, path: str, stream: IO, options: Optional[dict] = None) -> bool:
        extra_args = {}

        if options:
            if "visibility" in options:
                extra_args["ACL"] = (
                    "public-read" if options["visibility"] == "public" else "private"
                )
            if "content_type" in options:
                extra_args["ContentType"] = options["content_type"]

        stream.seek(0)

        self.client.upload_fileobj(
            stream, self.bucket, self._full_key(path), ExtraArgs=extra_args if extra_args else None
        )

        return True

    def append(self, path: str, contents: bytes) -> bool:
        try:
            existing = self.get(path)
            return self.put(path, existing + contents)
        except FileNotFoundError:
            return self.put(path, contents)

    def prepend(self, path: str, contents: bytes) -> bool:
        try:
            existing = self.get(path)
            return self.put(path, contents + existing)
        except FileNotFoundError:
            return self.put(path, contents)
