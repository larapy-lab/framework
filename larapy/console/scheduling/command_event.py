from larapy.console.scheduling.event import Event
import subprocess
import sys
import os


class CommandEvent(Event):
    def __init__(self, container, command: str, parameters: list):
        super().__init__(container)
        self.command = command
        self.parameters = parameters

    async def run(self):
        python_path = sys.executable
        artisan_path = os.path.join(os.getcwd(), "artisan")

        cmd = [python_path, artisan_path, self.command] + self.parameters

        try:
            if self.output_path:
                mode = "a" if self.output_append else "w"
                with open(self.output_path, mode) as f:
                    result = subprocess.run(
                        cmd, stdout=f, stderr=subprocess.STDOUT, cwd=os.getcwd()
                    )
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            return result.returncode == 0
        except Exception:
            return False

    def _build_description(self) -> str:
        params = " ".join(self.parameters) if self.parameters else ""
        desc = f"artisan {self.command}"
        if params:
            desc += f" {params}"
        return desc
