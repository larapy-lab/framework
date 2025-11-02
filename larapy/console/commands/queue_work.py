from larapy.console.command import Command
from larapy.queue.worker import Worker


class QueueWorkCommand(Command):
    name = "queue:work"
    description = "Start processing jobs on the queue as a daemon"

    def __init__(self, container):
        super().__init__()
        self.container = container

    def handle(self):
        connection = self.option("connection")
        queue = self.option("queue", "default")

        manager = self.container.make("queue")
        failed_job_provider = self.container.make("queue.failed")

        worker = Worker(manager, failed_job_provider, self.container)

        self.info(
            f"Processing jobs from '{queue}' queue on '{connection or 'default'}' connection..."
        )

        worker.work(
            connection,
            queue,
            {
                "sleep": int(self.option("sleep", 3)),
                "timeout": int(self.option("timeout", 60)),
                "memory": int(self.option("memory", 128)),
                "tries": int(self.option("tries", 1)),
                "delay": int(self.option("delay", 0)),
            },
        )

    def configure(self):
        self.add_option(
            "connection", None, "The name of the queue connection to work", default=None
        )
        self.add_option("queue", None, "The queue to work", default="default")
        self.add_option(
            "sleep", None, "Number of seconds to sleep when no job is available", default=3
        )
        self.add_option("timeout", None, "The number of seconds a job may run", default=60)
        self.add_option("memory", None, "The memory limit in megabytes", default=128)
        self.add_option("tries", None, "Number of times to attempt a job", default=1)
        self.add_option("delay", None, "The number of seconds to delay failed jobs", default=0)
