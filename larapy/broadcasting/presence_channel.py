from typing import Dict, List, Optional
from datetime import datetime


class PresenceChannel:
    def __init__(self, channel_name: str):
        self.name = channel_name
        self.members: Dict[str, dict] = {}

    def subscribe(self, socket_id: str, user_info: dict):
        self.members[socket_id] = {**user_info, "joined_at": datetime.now().isoformat()}
        return self.members[socket_id]

    def unsubscribe(self, socket_id: str) -> bool:
        if socket_id in self.members:
            del self.members[socket_id]
            return True
        return False

    def get_members(self) -> List[dict]:
        return list(self.members.values())

    def has_member(self, socket_id: str) -> bool:
        return socket_id in self.members

    def get_member(self, socket_id: str) -> Optional[dict]:
        return self.members.get(socket_id)

    def count(self) -> int:
        return len(self.members)

    def clear(self):
        self.members.clear()
