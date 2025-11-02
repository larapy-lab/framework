from typing import List, Callable, Optional, Dict, Any
from datetime import datetime
import uuid
import json


class Batch:

    def __init__(
        self,
        batch_id: str,
        name: str,
        total_jobs: int,
        pending_jobs: int,
        failed_jobs: int,
        failed_job_ids: List[str],
        options: Optional[Dict[str, Any]] = None,
        cancelled_at: Optional[int] = None,
        created_at: Optional[int] = None,
        finished_at: Optional[int] = None,
    ):
        self.id = batch_id
        self.name = name
        self.total_jobs = total_jobs
        self.pending_jobs = pending_jobs
        self.failed_jobs = failed_jobs
        self.failed_job_ids = failed_job_ids
        self.options = options or {}
        self.cancelled_at = cancelled_at
        self.created_at = created_at or int(datetime.now().timestamp())
        self.finished_at = finished_at

        self.then_callbacks: List[Callable] = []
        self.catch_callbacks: List[Callable] = []
        self.finally_callbacks: List[Callable] = []

    def increment_total_jobs(self, count: int = 1) -> "Batch":
        self.total_jobs += count
        return self

    def decrement_pending_jobs(self, count: int = 1) -> "Batch":
        self.pending_jobs = max(0, self.pending_jobs - count)
        return self

    def increment_failed_jobs(self, job_id: str) -> "Batch":
        self.failed_jobs += 1
        self.failed_job_ids.append(job_id)
        return self

    def finished(self) -> bool:
        return self.pending_jobs == 0

    def has_failures(self) -> bool:
        return self.failed_jobs > 0

    def cancelled(self) -> bool:
        return self.cancelled_at is not None

    def cancel(self) -> None:
        self.cancelled_at = int(datetime.now().timestamp())

    def then(self, callback: Callable) -> "Batch":
        self.then_callbacks.append(callback)
        return self

    def catch(self, callback: Callable) -> "Batch":
        self.catch_callbacks.append(callback)
        return self

    def finally_callback(self, callback: Callable) -> "Batch":
        self.finally_callbacks.append(callback)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "total_jobs": self.total_jobs,
            "pending_jobs": self.pending_jobs,
            "failed_jobs": self.failed_jobs,
            "failed_job_ids": json.dumps(self.failed_job_ids),
            "options": json.dumps(self.options),
            "cancelled_at": self.cancelled_at,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }


class PendingBatch:

    def __init__(self, bus, jobs: List):
        self.bus = bus
        self.jobs = jobs
        self.batch_name = ""
        self.connection_name = None
        self.queue_name = None
        self.then_callbacks: List[Callable] = []
        self.catch_callbacks: List[Callable] = []
        self.finally_callbacks: List[Callable] = []
        self.options = {}

    def then(self, callback: Callable) -> "PendingBatch":
        self.then_callbacks.append(callback)
        return self

    def catch(self, callback: Callable) -> "PendingBatch":
        self.catch_callbacks.append(callback)
        return self

    def finally_callback(self, callback: Callable) -> "PendingBatch":
        self.finally_callbacks.append(callback)
        return self

    def name(self, name: str) -> "PendingBatch":
        self.batch_name = name
        return self

    def on_connection(self, connection: str) -> "PendingBatch":
        self.connection_name = connection
        return self

    def on_queue(self, queue: str) -> "PendingBatch":
        self.queue_name = queue
        return self

    def dispatch(self) -> Batch:
        batch_id = str(uuid.uuid4())

        batch = Batch(
            batch_id=batch_id,
            name=self.batch_name,
            total_jobs=len(self.jobs),
            pending_jobs=len(self.jobs),
            failed_jobs=0,
            failed_job_ids=[],
            options=self.options,
        )

        batch.then_callbacks = self.then_callbacks
        batch.catch_callbacks = self.catch_callbacks
        batch.finally_callbacks = self.finally_callbacks

        self.bus.store_batch(batch)

        for job in self.jobs:
            job.batch_id = batch_id

            if self.connection_name:
                job.onConnection(self.connection_name)

            if self.queue_name:
                job.onQueue(self.queue_name)

            from larapy.queue.dispatcher import dispatch

            dispatch(job)

        return batch


class Bus:

    _batch_repository = None

    @classmethod
    def set_batch_repository(cls, repository):
        cls._batch_repository = repository

    @classmethod
    def batch(cls, jobs: List) -> PendingBatch:
        return PendingBatch(cls, jobs)

    @classmethod
    def store_batch(cls, batch: Batch) -> None:
        if cls._batch_repository:
            cls._batch_repository.store(batch)

    @classmethod
    def find_batch(cls, batch_id: str) -> Optional[Batch]:
        if cls._batch_repository:
            return cls._batch_repository.find(batch_id)
        return None


class DatabaseBatchRepository:

    def __init__(self, database, table: str = "job_batches"):
        self.database = database
        self.table = table

    def store(self, batch: Batch) -> Batch:
        self.database.table(self.table).insert(batch.to_dict())
        return batch

    def find(self, batch_id: str) -> Optional[Batch]:
        record = self.database.table(self.table).where("id", batch_id).first()

        if not record:
            return None

        return Batch(
            batch_id=record["id"],
            name=record["name"],
            total_jobs=record["total_jobs"],
            pending_jobs=record["pending_jobs"],
            failed_jobs=record["failed_jobs"],
            failed_job_ids=json.loads(record["failed_job_ids"]),
            options=json.loads(record["options"]) if record["options"] else None,
            cancelled_at=record["cancelled_at"],
            created_at=record["created_at"],
            finished_at=record["finished_at"],
        )

    def update(self, batch: Batch) -> Batch:
        self.database.table(self.table).where("id", batch.id).update(batch.to_dict())
        return batch

    def delete(self, batch_id: str) -> bool:
        return self.database.table(self.table).where("id", batch_id).delete() > 0
