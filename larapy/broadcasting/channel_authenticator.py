from typing import Optional, Dict, Any
import hashlib
import hmac
import json


class ChannelAuthenticator:
    def __init__(self, gate, request):
        self.gate = gate
        self.request = request

    def authenticate(self, channel_name: str, socket_id: str = None) -> Dict[str, Any]:
        if channel_name.startswith("private-"):
            return self.authenticate_private(channel_name, socket_id)
        elif channel_name.startswith("presence-"):
            return self.authenticate_presence(channel_name, socket_id)

        return {"auth": None}

    def authenticate_private(self, channel_name: str, socket_id: str = None) -> Dict[str, Any]:
        user = self.get_user()

        if not user:
            return {"error": "Unauthorized", "status": 403}

        if not self.authorize_channel(user, channel_name):
            return {"error": "Forbidden", "status": 403}

        auth_signature = self.generate_auth_signature(channel_name, socket_id)

        return {"auth": auth_signature, "channel_data": None}

    def authenticate_presence(self, channel_name: str, socket_id: str = None) -> Dict[str, Any]:
        user = self.get_user()

        if not user:
            return {"error": "Unauthorized", "status": 403}

        result = self.authorize_channel(user, channel_name)

        if result is False:
            return {"error": "Forbidden", "status": 403}

        channel_data = result if isinstance(result, dict) else self.get_default_user_info(user)

        auth_signature = self.generate_auth_signature(channel_name, socket_id, channel_data)

        return {"auth": auth_signature, "channel_data": json.dumps(channel_data)}

    def authorize_channel(self, user, channel_name: str):
        from larapy.broadcasting.channel_router import ChannelRouter

        router = (
            self.gate.container.make("broadcast.channel")
            if self.gate.container.bound("broadcast.channel")
            else None
        )

        if not router or not isinstance(router, ChannelRouter):
            return True

        return router.authorize(user, channel_name)

    def get_user(self):
        if hasattr(self.request, "user"):
            return self.request.user

        if hasattr(self.gate, "for_user"):
            return self.gate.for_user(self.request)

        return None

    def get_default_user_info(self, user) -> Dict[str, Any]:
        return {
            "id": user.id if hasattr(user, "id") else str(user),
            "name": user.name if hasattr(user, "name") else "User",
        }

    def generate_auth_signature(
        self, channel_name: str, socket_id: str = None, channel_data: Dict = None
    ) -> str:
        string_to_sign = f"{socket_id}:{channel_name}"

        if channel_data:
            string_to_sign += f":{json.dumps(channel_data)}"

        app_key = self.get_app_key()
        app_secret = self.get_app_secret()

        signature = hmac.new(
            app_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return f"{app_key}:{signature}"

    def get_app_key(self) -> str:
        if hasattr(self.gate, "container") and self.gate.container.bound("config"):
            config = self.gate.container.make("config")
            return config.get("broadcasting.connections.pusher.key", "default-key")
        return "default-key"

    def get_app_secret(self) -> str:
        if hasattr(self.gate, "container") and self.gate.container.bound("config"):
            config = self.gate.container.make("config")
            return config.get("broadcasting.connections.pusher.secret", "default-secret")
        return "default-secret"
