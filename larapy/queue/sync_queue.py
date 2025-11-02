from typing import Optional, Any, Dict
from datetime import timedelta
import json

from larapy.queue.queue_interface import QueueInterface
from larapy.queue.job import Job


class SyncQueue(QueueInterface):

    def __init__(self):
        self.connection_name = "sync"

    def push(
        self, job: str, data: Optional[Dict[str, Any]] = None, queue: Optional[str] = None
    ) -> Any:
        return self.resolve_job(self.create_payload(job, data), queue)

    def push_raw(
        self, payload: str, queue: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        pass

    def later(
        self,
        delay: timedelta,
        job: str,
        data: Optional[Dict[str, Any]] = None,
        queue: Optional[str] = None,
    ) -> Any:
        return self.push(job, data, queue)

    def pop(self, queue: Optional[str] = None) -> Optional[Any]:
        return None

    def size(self, queue: Optional[str] = None) -> int:
        return 0

    def create_payload(self, job: str, data: Optional[Dict[str, Any]] = None) -> str:
        if data is None:
            data = {}

        payload = {
            "displayName": job,
            "job": job,
            "maxTries": data.get("maxTries"),
            "timeout": data.get("timeout"),
            "data": data,
        }

        return json.dumps(payload)

    def resolve_job(self, payload: str, queue: Optional[str] = None) -> Any:
        payload_data = json.loads(payload)
        job_data = payload_data["data"]

        if "data" in job_data and (
            isinstance(job_data["data"], str) or isinstance(job_data["data"], bytes)
        ):
            job_instance = Job.unserialize(job_data)
            job_instance.fire()
            return 0

        return 0
