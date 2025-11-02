from typing import Optional, Any, Dict
from datetime import timedelta
import json
import time

from larapy.queue.queue_interface import QueueInterface


class RedisQueue(QueueInterface):

    def __init__(
        self,
        redis,
        default_queue: str = "default",
        retry_after: int = 90,
        block_for: Optional[int] = None,
    ):
        self.redis = redis
        self.default = default_queue
        self.retry_after = retry_after
        self.block_for = block_for
        self.connection_name = "redis"

    def push(
        self, job: str, data: Optional[Dict[str, Any]] = None, queue: Optional[str] = None
    ) -> Any:
        return self.push_raw(self.create_payload(job, data), queue)

    def push_raw(
        self, payload: str, queue: Optional[str] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        queue = self.get_queue(queue)

        self.redis.rpush(self.get_queue_key(queue), payload)

        return json.loads(payload).get("id")

    def later(
        self,
        delay: timedelta,
        job: str,
        data: Optional[Dict[str, Any]] = None,
        queue: Optional[str] = None,
    ) -> Any:
        queue = self.get_queue(queue)

        payload = self.create_payload(job, data)

        available_at = int(time.time()) + int(delay.total_seconds())

        self.redis.zadd(self.get_queue_key(queue) + ":delayed", {payload: available_at})

        return json.loads(payload).get("id")

    def pop(self, queue: Optional[str] = None) -> Optional[Any]:
        self.migrate_expired_jobs(queue)

        queue = self.get_queue(queue)

        if self.block_for:
            job = self.redis.blpop(self.get_queue_key(queue), self.block_for)
            if job:
                job = job[1]
        else:
            job = self.redis.lpop(self.get_queue_key(queue))

        if job:
            from larapy.queue.jobs.redis_job import RedisJob

            return RedisJob(
                self,
                job.decode("utf-8") if isinstance(job, bytes) else job,
                self.connection_name,
                queue,
            )

        return None

    def size(self, queue: Optional[str] = None) -> int:
        queue = self.get_queue(queue)

        return self.redis.llen(self.get_queue_key(queue))

    def clear(self, queue: str) -> int:
        queue = self.get_queue(queue)

        count = self.size(queue)
        self.redis.delete(self.get_queue_key(queue))

        return count

    def migrate_expired_jobs(self, queue: Optional[str]) -> None:
        queue = self.get_queue(queue)

        current_time = int(time.time())

        delayed_jobs = self.redis.zrangebyscore(
            self.get_queue_key(queue) + ":delayed", "-inf", current_time
        )

        if delayed_jobs:
            for job in delayed_jobs:
                self.redis.rpush(self.get_queue_key(queue), job)
                self.redis.zrem(self.get_queue_key(queue) + ":delayed", job)

    def delete_reserved(self, queue: str, job_payload: str) -> None:
        pass

    def get_queue(self, queue: Optional[str]) -> str:
        return queue or self.default

    def get_queue_key(self, queue: str) -> str:
        return f"queues:{queue}"

    def create_payload(self, job: str, data: Optional[Dict[str, Any]] = None) -> str:
        if data is None:
            data = {}

        import uuid

        payload = {
            "id": str(uuid.uuid4()),
            "displayName": job,
            "job": job,
            "maxTries": data.get("maxTries"),
            "timeout": data.get("timeout"),
            "data": data,
        }

        return json.dumps(payload)
