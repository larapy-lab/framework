from typing import Optional, Dict, Any
import json

from larapy.queue.job import Job


class RedisJob:

    def __init__(self, queue, payload_str: str, connection_name: str, queue_name: str):
        self.queue = queue
        self.payload_str = payload_str
        self.connection_name = connection_name
        self.queue_name = queue_name
        self.deleted = False
        self.released = False
        self.has_failed = False

    def fire(self) -> None:
        payload = self.payload()

        job_data = payload["data"]

        if "data" in job_data and (
            isinstance(job_data["data"], str) or isinstance(job_data["data"], bytes)
        ):
            job_instance = Job.unserialize(job_data)
            job_instance.fire()
        else:
            raise Exception(f"Unable to resolve job: {payload['job']}")

    def release(self, delay: int = 0) -> None:
        self.released = True
        self.queue.release(self.queue_name, self.payload_str, delay)

    def delete(self) -> None:
        self.deleted = True
        self.queue.delete_reserved(self.queue_name, self.payload_str)

    def is_deleted(self) -> bool:
        return self.deleted

    def is_released(self) -> bool:
        return self.released

    def is_deleted_or_released(self) -> bool:
        return self.deleted or self.released

    def attempts(self) -> int:
        payload = self.payload()
        return payload.get("attempts", 0)

    def mark_as_failed(self) -> None:
        self.has_failed = True

    def failed(self) -> bool:
        return self.has_failed

    def payload(self) -> Dict[str, Any]:
        return json.loads(self.payload_str)

    def max_tries(self) -> Optional[int]:
        payload = self.payload()
        return payload.get("maxTries")

    def timeout(self) -> Optional[int]:
        payload = self.payload()
        return payload.get("timeout")

    def timeout_at(self) -> Optional[int]:
        return None

    def get_name(self) -> str:
        payload = self.payload()
        return payload.get("displayName", payload.get("job", ""))

    def get_connection_name(self) -> str:
        return self.connection_name

    def get_queue(self) -> str:
        return self.queue_name

    def get_raw_body(self) -> str:
        return self.payload_str
