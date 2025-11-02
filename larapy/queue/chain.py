from typing import List, Optional


class Chain:

    def __init__(self, jobs: List):
        self.jobs = jobs
        self.connection_name = None
        self.queue_name = None

    def on_connection(self, connection: str) -> "Chain":
        self.connection_name = connection
        return self

    def on_queue(self, queue: str) -> "Chain":
        self.queue_name = queue
        return self

    def dispatch(self):
        if not self.jobs:
            return None

        first_job = self.jobs[0]
        remaining_jobs = self.jobs[1:] if len(self.jobs) > 1 else []

        first_job.chain_connection = self.connection_name
        first_job.chain_queue = self.queue_name
        first_job.chain_jobs = remaining_jobs

        if self.connection_name:
            first_job.onConnection(self.connection_name)

        if self.queue_name:
            first_job.onQueue(self.queue_name)

        from larapy.queue.dispatcher import dispatch

        return dispatch(first_job)


def chain(jobs: List) -> Chain:
    return Chain(jobs)
