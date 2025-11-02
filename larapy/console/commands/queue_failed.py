from larapy.console.command import Command


class QueueFailedCommand(Command):
    name = "queue:failed"
    description = "List all of the failed queue jobs"

    def __init__(self, container):
        super().__init__()
        self.container = container

    def handle(self):
        failed_job_provider = self.container.make("queue.failed")

        failed_jobs = failed_job_provider.all()

        if not failed_jobs:
            self.info("No failed jobs found")
            return

        self.info(f"\nFound {len(failed_jobs)} failed jobs:\n")

        for job in failed_jobs:
            import json

            payload = json.loads(job["payload"])
            job_name = payload.get("displayName", payload.get("job", "Unknown"))

            self.info(f"  [{job['id']}] {job_name}")
            self.line(f"      Connection: {job['connection']}")
            self.line(f"      Queue: {job['queue']}")
            self.line(f"      Failed at: {job['failed_at']}")
            self.line(f"      Exception: {job['exception'][:100]}...")
            self.line("")
