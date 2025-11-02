from larapy.console.command import Command


class QueueRetryCommand(Command):
    name = "queue:retry"
    description = "Retry a failed queue job"

    def __init__(self, container):
        super().__init__()
        self.container = container

    def handle(self):
        job_id = self.argument("id")

        failed_job_provider = self.container.make("queue.failed")

        if job_id == "all":
            failed_jobs = failed_job_provider.all()

            for failed_job in failed_jobs:
                self.retry_job(failed_job)
                failed_job_provider.forget(failed_job["id"])

            self.info(f"Retried {len(failed_jobs)} failed jobs")
        else:
            failed_job = failed_job_provider.find(int(job_id))

            if not failed_job:
                self.error(f"Failed job {job_id} not found")
                return

            self.retry_job(failed_job)
            failed_job_provider.forget(int(job_id))

            self.info(f"Retried failed job {job_id}")

    def retry_job(self, failed_job):
        import json

        manager = self.container.make("queue")
        connection = manager.connection(failed_job["connection"])

        payload = json.loads(failed_job["payload"])

        connection.push_raw(failed_job["payload"], failed_job["queue"])

    def configure(self):
        self.add_argument("id", 'The ID of the failed job or "all"')
