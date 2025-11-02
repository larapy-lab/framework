import sys
from typing import Optional


class ProgressBar:

    def __init__(self, command, max_steps: int):
        self.command = command
        self.max_steps = max_steps
        self.current = 0
        self.message = ""
        self.bar_width = 50
        self.started = False

    def start(self):
        self.started = True
        self.current = 0
        self._render()

    def advance(self, step: int = 1):
        if not self.started:
            self.start()

        self.current = min(self.current + step, self.max_steps)
        self._render()

    def finish(self):
        self.current = self.max_steps
        self._render()
        sys.stdout.write("\n")
        sys.stdout.flush()

    def set_message(self, message: str):
        self.message = message
        if self.started:
            self._render()

    def _render(self):
        if self.max_steps == 0:
            percentage = 100
        else:
            percentage = int((self.current / self.max_steps) * 100)

        filled = (
            int((self.current / self.max_steps) * self.bar_width)
            if self.max_steps > 0
            else self.bar_width
        )
        bar = "=" * filled + "-" * (self.bar_width - filled)

        progress_text = f"\r[{bar}] {percentage}% ({self.current}/{self.max_steps})"

        if self.message:
            progress_text += f" {self.message}"

        sys.stdout.write(progress_text)
        sys.stdout.flush()
