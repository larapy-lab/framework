from larapy.console.scheduling.event import Event
import subprocess


class ExecEvent(Event):
    def __init__(self, container, command: str, parameters: list):
        super().__init__(container)
        self.command = command
        self.parameters = parameters

    async def run(self):
        cmd_str = self.command
        if self.parameters:
            cmd_str += " " + " ".join(self.parameters)

        try:
            if self.output_path:
                mode = "a" if self.output_append else "w"
                with open(self.output_path, mode) as f:
                    result = subprocess.run(cmd_str, shell=True, stdout=f, stderr=subprocess.STDOUT)
            else:
                result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)

            return result.returncode == 0
        except Exception:
            return False

    def _build_description(self) -> str:
        params = " ".join(self.parameters) if self.parameters else ""
        desc = self.command
        if params:
            desc += f" {params}"
        return desc
