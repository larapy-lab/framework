from larapy.console.command import Command


class QueueForgetCommand(Command):
    name = "queue:forget"
    description = "Delete a failed queue job"

    def __init__(self, container):
        super().__init__()
        self.container = container

    def handle(self):
        job_id = self.argument("id")

        failed_job_provider = self.container.make("queue.failed")

        if failed_job_provider.forget(int(job_id)):
            self.info(f"Failed job {job_id} deleted")
        else:
            self.error(f"Failed job {job_id} not found")

    def configure(self):
        self.add_argument("id", "The ID of the failed job")
