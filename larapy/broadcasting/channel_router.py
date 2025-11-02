import re
from typing import Callable, List, Optional, Dict, Any


class BroadcastChannelRoute:
    def __init__(self, channel_pattern: str, callback: Callable):
        self.pattern = channel_pattern
        self.callback = callback
        self.regex = self._compile_pattern(channel_pattern)

    def _compile_pattern(self, pattern: str):
        pattern = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"(?P<\1>[^.]+)", pattern)
        pattern = pattern.replace(".", r"\.")
        pattern = pattern.replace("*", r"[^.]+")
        return re.compile(f"^{pattern}$")

    def matches(self, channel_name: str) -> bool:
        return self.regex.match(channel_name) is not None

    def extract_parameters(self, channel_name: str) -> Dict[str, str]:
        match = self.regex.match(channel_name)
        if match:
            return match.groupdict()
        return {}

    def authorize(self, user, channel_name: str):
        parameters = self.extract_parameters(channel_name)
        return self.callback(user, **parameters)


class ChannelRouter:
    def __init__(self):
        self.routes: List[BroadcastChannelRoute] = []

    def channel(self, pattern: str, callback: Callable):
        route = BroadcastChannelRoute(pattern, callback)
        self.routes.append(route)
        return route

    def private(self, pattern: str, callback: Callable):
        return self.channel(f"private-{pattern}", callback)

    def presence(self, pattern: str, callback: Callable):
        return self.channel(f"presence-{pattern}", callback)

    def authorize(self, user, channel_name: str):
        for route in self.routes:
            if route.matches(channel_name):
                return route.authorize(user, channel_name)

        return True

    def find_route(self, channel_name: str) -> Optional[BroadcastChannelRoute]:
        for route in self.routes:
            if route.matches(channel_name):
                return route
        return None
