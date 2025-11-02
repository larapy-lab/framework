from typing import Optional


class AuthorizeMiddleware:
    """Middleware to authorize requests."""

    def __init__(self, ability: str, model_param: Optional[str] = None):
        self.ability = ability
        self.model_param = model_param

    async def handle(self, request, next):
        """Handle the authorization check."""
        gate = request.container.make("gate")

        model = None
        if self.model_param:
            model = request.route_params.get(self.model_param)

        gate.authorize(self.ability, model)

        return await next(request)
