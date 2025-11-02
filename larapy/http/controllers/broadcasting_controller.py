from larapy.http.controller import Controller


class BroadcastingController(Controller):
    def authenticate(self, request):
        channel_name = request.input("channel_name")
        socket_id = request.input("socket_id")

        if not channel_name:
            return self.error_response("Channel name is required", 400)

        from larapy.broadcasting.channel_authenticator import ChannelAuthenticator

        gate = request.app.make("gate") if request.app.bound("gate") else None

        if not gate:
            return self.error_response("Authorization not configured", 500)

        authenticator = ChannelAuthenticator(gate=gate, request=request)

        result = authenticator.authenticate(channel_name, socket_id)

        if "error" in result:
            return self.error_response(result["error"], result.get("status", 403))

        return self.json(result)

    def json(self, data: dict, status: int = 200):
        import json as json_module

        return {
            "body": json_module.dumps(data),
            "status": status,
            "headers": {"Content-Type": "application/json"},
        }

    def error_response(self, message: str, status: int = 400):
        return self.json({"error": message}, status)
