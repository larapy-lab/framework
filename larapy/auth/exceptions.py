class AuthorizationException(Exception):
    """Exception raised when authorization fails."""

    def __init__(self, message: str = "This action is unauthorized.", status_code: int = 403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
