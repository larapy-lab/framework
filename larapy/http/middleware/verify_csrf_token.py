"""
CSRF Token Verification Middleware

Provides Cross-Site Request Forgery protection by validating CSRF tokens
on state-changing requests (POST, PUT, PATCH, DELETE).
"""

import secrets
import hmac
from typing import Any, Callable, List, Optional
from larapy.http.middleware.middleware import Middleware


class VerifyCsrfToken(Middleware):
    """
    Verify CSRF token for state-changing HTTP requests.

    This middleware protects against Cross-Site Request Forgery attacks by
    requiring a valid token for POST, PUT, PATCH, and DELETE requests.
    """

    # URIs that should be excluded from CSRF verification
    _except: List[str] = []

    # Additional URIs to exclude (can be added dynamically)
    _exclude_uris: List[str] = []

    def __init__(self):
        """Initialize CSRF middleware."""
        super().__init__()

    def handle(self, request: Any, next_handler: Callable) -> Any:
        """
        Handle incoming request and verify CSRF token.

        Args:
            request: The incoming HTTP request
            next_handler: The next middleware/handler in the pipeline

        Returns:
            Response from next handler or 419 error if token invalid
        """
        # Add token to request if not present
        if not self._has_token(request):
            request._csrf_token = self._generate_token()

            # Store in session if available
            if hasattr(request, "session") and request.session():
                request.session().put("_token", request._csrf_token)
        else:
            # Load token from session
            if hasattr(request, "session") and request.session():
                request._csrf_token = request.session().get("_token")

        # Check if request should be verified
        if self._should_verify(request):
            if not self._tokens_match(request):
                return self._token_mismatch(request)

        # Add token to response for subsequent requests
        response = next_handler(request)

        # Ensure token is in response for form rendering
        if hasattr(response, "with_csrf_token"):
            response.with_csrf_token(self._get_token(request))

        return response

    def _should_verify(self, request: Any) -> bool:
        """
        Determine if the request should be verified.

        Args:
            request: The HTTP request

        Returns:
            True if request should be verified
        """
        # Only verify state-changing methods
        if request.method() not in ["POST", "PUT", "PATCH", "DELETE"]:
            return False

        # Check if URI is excluded
        return not self._is_excluded(request)

    def _is_excluded(self, request: Any) -> bool:
        """
        Check if the request URI is excluded from CSRF verification.

        Args:
            request: The HTTP request

        Returns:
            True if request should be excluded
        """
        path = request.path().strip("/")

        # Check static exclusions
        for excluded in self._except + self._exclude_uris:
            # Simple wildcard matching
            if excluded.endswith("*"):
                prefix = excluded[:-1].strip("/")
                if path.startswith(prefix):
                    return True
            elif excluded.strip("/") == path:
                return True

        return False

    def _tokens_match(self, request: Any) -> bool:
        """
        Verify the CSRF token from the request matches the session token.

        Args:
            request: The HTTP request

        Returns:
            True if tokens match
        """
        session_token = self._get_token(request)
        request_token = self._get_token_from_request(request)

        if not session_token or not request_token:
            return False

        # Use timing-safe comparison to prevent timing attacks
        return hmac.compare_digest(
            str(session_token).encode("utf-8"), str(request_token).encode("utf-8")
        )

    def _get_token(self, request: Any) -> Optional[str]:
        """
        Get the CSRF token from the request/session.

        Args:
            request: The HTTP request

        Returns:
            The CSRF token or None
        """
        # Check request attribute first
        if hasattr(request, "_csrf_token") and request._csrf_token is not None:
            return request._csrf_token

        # Check session
        if hasattr(request, "session") and request.session():
            session = request.session()
            if hasattr(session, "get"):
                return session.get("_token")
            elif isinstance(session, dict):
                return session.get("_token")

        return None

    def _get_token_from_request(self, request: Any) -> Optional[str]:
        """
        Get the CSRF token submitted with the request.

        Args:
            request: The HTTP request

        Returns:
            The submitted CSRF token or None
        """
        # Check X-CSRF-TOKEN header (for AJAX requests)
        token = request.header("X-CSRF-TOKEN")
        if token:
            return token

        # Check X-XSRF-TOKEN header (alternative header name)
        token = request.header("X-XSRF-TOKEN")
        if token:
            return token

        # Check _token input field (for form submissions)
        token = request.input("_token")
        if token:
            return token

        return None

    def _has_token(self, request: Any) -> bool:
        """
        Check if request has a CSRF token.

        Args:
            request: The HTTP request

        Returns:
            True if token exists
        """
        if hasattr(request, "_csrf_token") and request._csrf_token:
            return True

        if hasattr(request, "session") and request.session():
            return request.session().has("_token")

        return False

    def _generate_token(self) -> str:
        """
        Generate a new CSRF token.

        Returns:
            A secure random token string
        """
        return secrets.token_urlsafe(32)

    def _token_mismatch(self, request: Any) -> Any:
        """
        Handle token mismatch error.

        Args:
            request: The HTTP request

        Returns:
            419 Page Expired response
        """
        from larapy.http.response import JsonResponse, Response

        # Return JSON for AJAX requests
        if request.is_ajax() or request.wants_json():
            return JsonResponse(
                {"message": "CSRF token mismatch.", "exception": "TokenMismatchException"}, 419
            )

        # Return HTML error page for regular requests
        return Response("Page Expired", 419)

    def except_uris(self, uris: List[str]) -> "VerifyCsrfToken":
        """
        Add URIs to exclude from CSRF verification.

        Args:
            uris: List of URI patterns to exclude

        Returns:
            Self for method chaining
        """
        self._exclude_uris.extend(uris)
        return self
