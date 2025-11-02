from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import pickle
import uuid
import base64


class ShouldQueue:
    pass


class Job(ABC):
    queue: Optional[str] = None
    connection: Optional[str] = None
    delay_time: Optional[timedelta] = None
    tries: int = 1
    timeout: int = 60
    max_exceptions: Optional[int] = None

    job_id: Optional[str] = None
    chain_connection: Optional[str] = None
    chain_queue: Optional[str] = None
    chain_jobs: list = []

    def __init__(self):
        self.job_id = str(uuid.uuid4())

    @abstractmethod
    def handle(self, *args, **kwargs) -> None:
        pass

    def failed(self, exception: Exception) -> None:
        pass

    def onQueue(self, queue: str) -> "Job":
        self.queue = queue
        return self

    def onConnection(self, connection: str) -> "Job":
        self.connection = connection
        return self

    def delay(self, delay: timedelta) -> "Job":
        self.delay_time = delay
        return self

    def serialize(self) -> Dict[str, Any]:
        pickled_data = pickle.dumps(self)
        encoded_data = base64.b64encode(pickled_data).decode("utf-8")

        return {
            "job_id": self.job_id,
            "class": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "data": encoded_data,
            "queue": self.queue,
            "connection": self.connection,
            "delay": self.delay_time.total_seconds() if self.delay_time else None,
            "tries": self.tries,
            "timeout": self.timeout,
            "max_exceptions": self.max_exceptions,
            "chain_connection": self.chain_connection,
            "chain_queue": self.chain_queue,
            "chain_jobs": [
                base64.b64encode(pickle.dumps(job)).decode("utf-8") for job in self.chain_jobs
            ],
        }

    @staticmethod
    def unserialize(payload: Dict[str, Any]) -> "Job":
        if isinstance(payload["data"], str):
            decoded_data = base64.b64decode(payload["data"])
            job = pickle.loads(decoded_data)
        else:
            job = pickle.loads(payload["data"])

        job.job_id = payload["job_id"]
        return job

    def fire(self) -> None:
        try:
            self.handle()
        except Exception as e:
            self.failed(e)
            raise

    def delete(self) -> None:
        pass

    def release(self, delay: int = 0) -> None:
        pass

    def attempts(self) -> int:
        return 0

    def maxTries(self) -> Optional[int]:
        return self.tries

    def maxExceptions(self) -> Optional[int]:
        return self.max_exceptions

    def retryUntil(self) -> Optional[datetime]:
        return None

    def timeout_at(self) -> Optional[datetime]:
        if self.timeout:
            return datetime.now() + timedelta(seconds=self.timeout)
        return None
