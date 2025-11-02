from typing import Optional
import json

from larapy.queue.job import Job


_queue_manager = None


def set_queue_manager(manager):
    global _queue_manager
    _queue_manager = manager


def dispatch(job: Job, connection: Optional[str] = None):
    if _queue_manager is None:
        raise RuntimeError("Queue manager not set. Call set_queue_manager() first")

    connection_name = connection or job.connection or _queue_manager.get_default_connection()
    queue_connection = _queue_manager.connection(connection_name)

    payload = job.serialize()
    payload_json = json.dumps(payload)

    if job.delay_time:
        return queue_connection.later(job.delay_time, job.__class__.__name__, payload, job.queue)

    return queue_connection.push(job.__class__.__name__, payload, job.queue)


def dispatch_sync(job: Job):
    return job.fire()


class Dispatcher:

    def __init__(self, manager):
        self.manager = manager

    def dispatch(self, job: Job, connection: Optional[str] = None):
        connection_name = connection or job.connection or self.manager.get_default_connection()
        queue_connection = self.manager.connection(connection_name)

        payload = job.serialize()
        payload_json = json.dumps(payload)

        if job.delay_time:
            return queue_connection.later(
                job.delay_time, job.__class__.__name__, payload, job.queue
            )

        return queue_connection.push(job.__class__.__name__, payload, job.queue)

    def dispatch_sync(self, job: Job):
        return job.fire()

    def dispatch_now(self, job: Job):
        return job.fire()
