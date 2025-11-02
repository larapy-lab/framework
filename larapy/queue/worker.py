from typing import Optional, Dict, Any
import time
import signal
import sys
import traceback
import os

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class Worker:

    def __init__(self, manager, failed_job_provider=None, container=None):
        self.manager = manager
        self.failed_job_provider = failed_job_provider
        self.container = container
        self.should_quit = False
        self.paused = False

    def work(
        self,
        connection: Optional[str] = None,
        queue: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ):
        if options is None:
            options = {}

        connection = connection or self.manager.get_default_connection()

        self.listen_for_signals()

        last_restart = self.get_timestamp_of_last_queue_restart()

        while True:
            if self.should_quit:
                break

            if self.paused:
                time.sleep(options.get("sleep", 3))
                continue

            if self.memory_exceeded(options.get("memory", 128)):
                self.stop(12)

            if self.queue_should_restart(last_restart):
                self.stop()

            job = self.get_next_job(connection, queue)

            if job is None:
                time.sleep(options.get("sleep", 3))
                continue

            self.process(job, connection, options)

    def daemon(
        self,
        connection: Optional[str] = None,
        queue: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ):
        return self.work(connection, queue, options)

    def run_next_job(self, connection: str, queue: str, options: Optional[Dict[str, Any]] = None):
        if options is None:
            options = {}

        job = self.get_next_job(connection, queue)

        if job:
            self.process(job, connection, options)

    def get_next_job(self, connection: str, queue: str):
        try:
            queue_connection = self.manager.connection(connection)

            for queue_name in queue.split(","):
                queue_name = queue_name.strip()

                job = queue_connection.pop(queue_name)

                if job:
                    return job

            return None
        except Exception as e:
            print(f"Error getting next job: {e}")
            traceback.print_exc()
            return None

    def process(self, job, connection: str, options: Dict[str, Any]):
        try:
            self.raise_before_job_event(connection, job)

            self.mark_job_as_started(job)

            self.run_job(job, connection, options)

            self.raise_after_job_event(connection, job)
        except Exception as e:
            self.handle_job_exception(job, connection, e, options)

    def run_job(self, job, connection: str, options: Dict[str, Any]):
        try:
            timeout = self.get_timeout(job, options)

            if timeout:
                self.register_timeout_handler(job, timeout)

            job.fire()

            if not job.is_deleted_or_released():
                job.delete()

        except Exception as e:
            raise e

    def handle_job_exception(self, job, connection: str, e: Exception, options: Dict[str, Any]):
        try:
            if not job.is_deleted():
                max_tries = job.max_tries()

                if max_tries is None or job.attempts() < max_tries:
                    job.release(options.get("delay", 0))
                else:
                    self.fail_job(job, e)
        except Exception as fail_exception:
            print(f"Failed to handle job exception: {fail_exception}")
            traceback.print_exc()

    def fail_job(self, job, e: Exception):
        job.mark_as_failed()

        if job.is_deleted():
            return

        try:
            payload = job.payload()

            if "data" in payload["data"]:
                from larapy.queue.job import Job as JobClass

                job_instance = JobClass.unserialize(payload["data"])
                job_instance.failed(e)
        except Exception:
            pass

        job.delete()

        if self.failed_job_provider:
            self.failed_job_provider.log(
                job.get_connection_name(), job.get_queue(), job.get_raw_body(), e
            )

    def raise_before_job_event(self, connection: str, job):
        pass

    def raise_after_job_event(self, connection: str, job):
        pass

    def mark_job_as_started(self, job):
        pass

    def get_timeout(self, job, options: Dict[str, Any]) -> Optional[int]:
        return job.timeout() or options.get("timeout")

    def register_timeout_handler(self, job, timeout: int):
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Job exceeded maximum timeout of {timeout} seconds")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

    def memory_exceeded(self, memory_limit: int) -> bool:
        if not HAS_PSUTIL:
            return False

        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb > memory_limit
        except Exception:
            return False

    def stop(self, status: int = 0):
        self.should_quit = True
        sys.exit(status)

    def pause(self):
        self.paused = True

    def continue_work(self):
        self.paused = False

    def listen_for_signals(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGUSR2, self.pause_handler)
        signal.signal(signal.SIGCONT, self.continue_handler)

    def signal_handler(self, signum, frame):
        self.stop()

    def pause_handler(self, signum, frame):
        self.pause()

    def continue_handler(self, signum, frame):
        self.continue_work()

    def queue_should_restart(self, last_restart: Optional[int]) -> bool:
        return self.get_timestamp_of_last_queue_restart() != last_restart

    def get_timestamp_of_last_queue_restart(self) -> Optional[int]:
        try:
            if self.container and self.container.bound("cache"):
                cache = self.container.make("cache")
                return cache.get("illuminate:queue:restart")
        except Exception:
            pass

        return None

    def sleep(self, seconds: int):
        time.sleep(seconds)
