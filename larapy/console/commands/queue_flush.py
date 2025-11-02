from larapy.console.command import Command


class QueueFlushCommand(Command):
    name = "queue:flush"
    description = "Flush all of the failed queue jobs"

    def __init__(self, container):
        super().__init__()
        self.container = container

    def handle(self):
        failed_job_provider = self.container.make("queue.failed")

        count = failed_job_provider.flush()

        self.info(f"Deleted {count} failed jobs")
