from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import json
import time

from larapy.queue.queue_interface import QueueInterface


class DatabaseQueue(QueueInterface):

    def __init__(
        self, database, table: str = "jobs", default_queue: str = "default", retry_after: int = 90
    ):
        self.database = database
        self.table = table
        self.default = default_queue
        self.retry_after = retry_after
        self.connection_name = "database"

    def push(
        self, job: str, data: Optional[Dict[str, Any]] = None, queue: Optional[str] = None
    ) -> Any:
        return self.push_to_database(queue, self.create_payload(job, data))

    def push_raw(
        self, payload: str, queue: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        return self.push_to_database(queue, payload, options)

    def later(
        self,
        delay: timedelta,
        job: str,
        data: Optional[Dict[str, Any]] = None,
        queue: Optional[str] = None,
    ) -> Any:
        return self.push_to_database(queue, self.create_payload(job, data), {"delay": delay})

    def pop(self, queue: Optional[str] = None) -> Optional[Any]:
        queue = self.get_queue(queue)

        job_record = self.get_next_available_job(queue)

        if job_record is None:
            return None

        self.mark_job_as_reserved(job_record["id"])

        from larapy.queue.jobs.database_job import DatabaseJob

        return DatabaseJob(self, job_record, self.connection_name, queue)

    def size(self, queue: Optional[str] = None) -> int:
        queue = self.get_queue(queue)

        return self.database.table(self.table).where("queue", queue).count()

    def clear(self, queue: str) -> int:
        queue = self.get_queue(queue)

        return self.database.table(self.table).where("queue", queue).delete()

    def release(self, job_id: int, delay: int = 0) -> None:
        available_at = int(time.time()) + delay

        self.database.table(self.table).where("id", job_id).update(
            {
                "reserved_at": None,
                "available_at": available_at,
                "attempts": self.database.raw("attempts + 1"),
            }
        )

    def delete_reserved(self, job_id: int) -> None:
        self.database.table(self.table).where("id", job_id).delete()

    def push_to_database(
        self, queue: Optional[str], payload: str, options: Optional[Dict[str, Any]] = None
    ) -> int:
        if options is None:
            options = {}

        queue = self.get_queue(queue)

        delay = options.get("delay")
        available_at = int(time.time())

        if delay:
            available_at += int(delay.total_seconds())

        return self.database.table(self.table).insert_get_id(
            {
                "queue": queue,
                "attempts": 0,
                "reserved_at": None,
                "available_at": available_at,
                "created_at": int(time.time()),
                "payload": payload,
            }
        )

    def get_next_available_job(self, queue: str) -> Optional[Dict[str, Any]]:
        current_time = int(time.time())
        retry_time = current_time - self.retry_after

        job = (
            self.database.table(self.table)
            .where("queue", queue)
            .where(
                lambda q: (q.where("reserved_at", None).or_where("reserved_at", "<=", retry_time))
            )
            .where("available_at", "<=", current_time)
            .order_by("id", "asc")
            .first()
        )

        return job

    def mark_job_as_reserved(self, job_id: int) -> None:
        self.database.table(self.table).where("id", job_id).update(
            {"reserved_at": int(time.time()), "attempts": self.database.raw("attempts + 1")}
        )

    def get_queue(self, queue: Optional[str]) -> str:
        return queue or self.default

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
