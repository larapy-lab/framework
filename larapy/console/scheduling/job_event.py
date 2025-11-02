from larapy.console.scheduling.event import Event


class JobEvent(Event):
    def __init__(self, container, job, queue: str = None):
        super().__init__(container)
        self.job = job
        self.queue_name = queue

    async def run(self):
        try:
            from larapy.queue import dispatch

            if self.queue_name:
                if hasattr(self.job, "on_queue"):
                    self.job.on_queue(self.queue_name)

            dispatch(self.job)
            return True
        except Exception:
            return False

    def _build_description(self) -> str:
        job_class = self.job.__class__.__name__
        if self.queue_name:
            return f"Job: {job_class} on queue '{self.queue_name}'"
        return f"Job: {job_class}"
