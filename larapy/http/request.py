"""
HTTP Request

Represents an HTTP request with input data, headers, cookies, and files.
"""

import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse


class Request:
    """
    HTTP Request matching Laravel's Request class.

    Handles input data, headers, cookies, files, and route parameters.
    """

    def __init__(
        self,
        uri: str = "/",
        method: str = "GET",
        server: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, Any]] = None,
        post: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> None:
        """
        Initialize an HTTP request.

        Args:
            uri: Request URI
            method: HTTP method
            server: Server parameters
            headers: HTTP headers
            query: Query string parameters
            post: POST data
            cookies: Cookies
            files: Uploaded files
            content: Raw request body
        """
        self._uri = uri
        self._method = method.upper()
        self._server = server or {}
        self._headers = self._normalize_headers(headers or {})
        self._query = query or {}
        self._post = post or {}
        self._cookies = cookies or {}
        self._files = files or {}
        self._content = content
        self._route_parameters: Dict[str, Any] = {}
        self._route_middleware: List[str] = []
        self._json: Optional[Dict[str, Any]] = None
        self._session: Optional[Dict[str, Any]] = None
        self._input: Dict[str, Any] = {}
        self._csrf_token: Optional[str] = None

        if self._content and self._is_json():
            try:
                self._json = json.loads(self._content)
            except (json.JSONDecodeError, TypeError):
                self._json = None

    def _normalize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Normalize header names to Title-Case."""
        return {
            "-".join(word.capitalize() for word in key.replace("_", "-").split("-")): value
            for key, value in headers.items()
        }

    def _is_json(self) -> bool:
        """Check if request content type is JSON."""
        content_type = self.header("Content-Type", "")
        return "application/json" in content_type

    def path(self) -> str:
        """Get the request path."""
        parsed = urlparse(self._uri)
        path = parsed.path.strip("/")
        return path if path else "/"

    def url(self) -> str:
        """Get the URL without query string."""
        parsed = urlparse(self._uri)
        scheme = self.server("HTTP_SCHEME", "http")
        host = self.server("HTTP_HOST", "localhost")
        path = parsed.path
        return f"{scheme}://{host}{path}"

    def fullUrl(self) -> str:
        """Get the full URL including query string."""
        return self._uri if "?" in self._uri else self.url()

    def fullUrlWithQuery(self, query: Dict[str, Any]) -> str:
        """Append query parameters to current URL."""
        parsed = urlparse(self._uri)
        existing = parse_qs(parsed.query)
        merged = {**existing, **{k: [str(v)] for k, v in query.items()}}
        query_string = "&".join(f"{k}={v[0]}" for k, v in merged.items())
        return f"{self.url()}?{query_string}"

    def fullUrlWithoutQuery(self, keys: Union[str, List[str]]) -> str:
        """Remove query parameters from current URL."""
        if isinstance(keys, str):
            keys = [keys]

        parsed = urlparse(self._uri)
        existing = parse_qs(parsed.query)
        filtered = {k: v for k, v in existing.items() if k not in keys}

        if not filtered:
            return self.url()

        query_string = "&".join(f"{k}={v[0]}" for k, v in filtered.items())
        return f"{self.url()}?{query_string}"

    def is_(self, pattern: str) -> bool:
        """Check if request path matches pattern."""
        path = self.path()
        if path == "/":
            path = ""
        pattern = pattern.strip("/")

        regex_pattern = pattern.replace("*", ".*")
        regex_pattern = f"^{regex_pattern}$"
        return bool(re.match(regex_pattern, path))

    def routeIs(self, pattern: str) -> bool:
        """Check if current route name matches pattern."""
        route = self._route_parameters.get("_route_name")
        if not route:
            return False

        regex_pattern = pattern.replace("*", ".*")
        regex_pattern = f"^{regex_pattern}$"
        return bool(re.match(regex_pattern, route))

    def host(self) -> str:
        """Get request host."""
        host_header = self.header("Host", "")
        if host_header:
            return host_header.split(":")[0]
        return self.server("HTTP_HOST", "localhost")

    def httpHost(self) -> str:
        """Get request HTTP host with port."""
        return self.header("Host", self.server("HTTP_HOST", "localhost"))

    def schemeAndHttpHost(self) -> str:
        """Get scheme and HTTP host."""
        scheme = self.server("HTTP_SCHEME", "http")
        return f"{scheme}://{self.httpHost()}"

    def method(self) -> str:
        """Get HTTP method."""
        return self._method

    def isMethod(self, method: str) -> bool:
        """Check if HTTP method matches."""
        return self._method == method.upper()

    def header(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get header value."""
        normalized_key = "-".join(word.capitalize() for word in key.replace("_", "-").split("-"))
        return self._headers.get(normalized_key, default)

    def hasHeader(self, key: str) -> bool:
        """Check if header exists."""
        normalized_key = "-".join(word.capitalize() for word in key.replace("_", "-").split("-"))
        return normalized_key in self._headers

    def set_header(self, key: str, value: str) -> "Request":
        """Set a header value."""
        normalized_key = "-".join(word.capitalize() for word in key.replace("_", "-").split("-"))
        self._headers[normalized_key] = value
        return self

    def bearerToken(self) -> str:
        """Get bearer token from Authorization header."""
        auth = self.header("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return ""

    def ip(self) -> str:
        """Get client IP address."""
        return self.server("REMOTE_ADDR", "127.0.0.1")

    def ips(self) -> List[str]:
        """Get all client IPs including forwarded."""
        ips = []

        forwarded_for = self.header("X-Forwarded-For")
        if forwarded_for:
            ips.extend([ip.strip() for ip in forwarded_for.split(",")])

        client_ip = self.ip()
        if client_ip not in ips:
            ips.append(client_ip)

        return ips

    def getAcceptableContentTypes(self) -> List[str]:
        """Get acceptable content types from Accept header."""
        accept = self.header("Accept", "*/*")
        types = [t.strip() for t in accept.split(",")]
        return types

    def accepts(self, content_types: List[str]) -> bool:
        """Check if request accepts any of given content types."""
        acceptable = self.getAcceptableContentTypes()

        if "*/*" in acceptable:
            return True

        for ct in content_types:
            if ct in acceptable:
                return True

            for acc in acceptable:
                if acc.endswith("/*"):
                    prefix = acc[:-2]
                    if ct.startswith(prefix):
                        return True

        return False

    def prefers(self, content_types: List[str]) -> Optional[str]:
        """Get preferred content type."""
        acceptable = self.getAcceptableContentTypes()

        for acc in acceptable:
            if acc in content_types:
                return acc

            if acc.endswith("/*"):
                prefix = acc[:-2]
                for ct in content_types:
                    if ct.startswith(prefix):
                        return ct

        return None

    def expectsJson(self) -> bool:
        """Check if request expects JSON response."""
        return self.accepts(["application/json"]) or self.is_("api/*")

    def wants_json(self) -> bool:
        """Alias for expectsJson()."""
        return self.expectsJson()

    def wantsJson(self) -> bool:
        """Alias for expectsJson() (camelCase variant)."""
        return self.expectsJson()

    def is_ajax(self) -> bool:
        """Check if request is AJAX."""
        return self.header("X-Requested-With") == "XMLHttpRequest"

    def ajax(self) -> bool:
        """Alias for is_ajax()."""
        return self.is_ajax()

    def all(self) -> Dict[str, Any]:
        """Get all input data."""
        data = {}
        data.update(self._query)
        data.update(self._post)

        if self._json:
            data.update(self._json)

        data.update(self._input)
        data.update(self._route_parameters)
        return data

    def input(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get input value."""
        if key is None:
            return self.all()

        data = self.all()

        if "." in key:
            return self._get_nested(data, key, default)

        return data.get(key, default)

    def _get_nested(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested value using dot notation."""
        keys = key.split(".")
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            elif isinstance(value, list):
                if k.isdigit():
                    idx = int(k)
                    if idx < len(value):
                        value = value[idx]
                    else:
                        return default
                elif k == "*":
                    return [self._get_nested({"val": v}, "val", default) for v in value]
                else:
                    return default
            else:
                return default

        return value if value is not None else default

    def query(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get query string value."""
        if key is None:
            return self._query

        if "." in key:
            return self._get_nested(self._query, key, default)

        return self._query.get(key, default)

    def string(self, key: str, default: str = "") -> str:
        """Get input as string."""
        value = self.input(key, default)
        return str(value) if value is not None else default

    def integer(self, key: str, default: int = 0) -> int:
        """Get input as integer."""
        value = self.input(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def boolean(self, key: str, default: bool = False) -> bool:
        """Get input as boolean."""
        value = self.input(key, default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ("1", "true", "on", "yes")

        if isinstance(value, (int, float)):
            return value == 1

        return default

    def array(self, key: str) -> List[Any]:
        """Get input as array."""
        value = self.input(key, [])

        if isinstance(value, list):
            return value

        return []

    def date(
        self, key: str, format: str = "%Y-%m-%d", timezone: Optional[str] = None
    ) -> Optional[datetime]:
        """Get input as datetime."""
        value = self.input(key)

        if value is None:
            return None

        try:
            return datetime.strptime(str(value), format)
        except (ValueError, TypeError):
            return None

    def only(self, *keys: str) -> Dict[str, Any]:
        """Get subset of input."""
        if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
            keys = keys[0]

        data = self.all()
        return {k: data[k] for k in keys if k in data}

    def except_(self, *keys: str) -> Dict[str, Any]:
        """Get input except specified keys."""
        if len(keys) == 1 and isinstance(keys[0], (list, tuple)):
            keys = keys[0]

        data = self.all()
        return {k: v for k, v in data.items() if k not in keys}

    def has(self, key: Union[str, List[str]]) -> bool:
        """Check if input key exists."""
        if isinstance(key, str):
            return key in self.all()

        data = self.all()
        return all(k in data for k in key)

    def hasAny(self, keys: List[str]) -> bool:
        """Check if any input keys exist."""
        data = self.all()
        return any(k in data for k in keys)

    def whenHas(self, key: str, callback: Callable, default: Optional[Callable] = None) -> Any:
        """Execute callback if key exists."""
        if self.has(key):
            return callback(self.input(key))
        elif default:
            return default()
        return None

    def filled(self, key: str) -> bool:
        """Check if key exists and is not empty."""
        value = self.input(key)

        if value is None:
            return False

        if isinstance(value, str):
            return value.strip() != ""

        if isinstance(value, (list, dict)):
            return len(value) > 0

        return True

    def isNotFilled(self, key: Union[str, List[str]]) -> bool:
        """Check if key is missing or empty."""
        if isinstance(key, str):
            return not self.filled(key)

        return all(not self.filled(k) for k in key)

    def anyFilled(self, keys: List[str]) -> bool:
        """Check if any keys are filled."""
        return any(self.filled(k) for k in keys)

    def whenFilled(self, key: str, callback: Callable, default: Optional[Callable] = None) -> Any:
        """Execute callback if key is filled."""
        if self.filled(key):
            return callback(self.input(key))
        elif default:
            return default()
        return None

    def missing(self, key: str) -> bool:
        """Check if key is missing."""
        return key not in self.all()

    def whenMissing(self, key: str, callback: Callable, default: Optional[Callable] = None) -> Any:
        """Execute callback if key is missing."""
        if self.missing(key):
            return callback()
        elif default:
            return default()
        return None

    def merge(self, data: Dict[str, Any]) -> "Request":
        """Merge additional input."""
        self._post.update(data)
        self._input.update(data)
        return self

    def replace(self, data: Dict[str, Any]) -> "Request":
        """Replace all input data."""
        self._post = data.copy()
        self._input = data.copy()
        return self

    def mergeIfMissing(self, data: Dict[str, Any]) -> "Request":
        """Merge input if keys don't exist."""
        for key, value in data.items():
            if key not in self.all():
                self._post[key] = value
                self._input[key] = value
        return self

    def cookie(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get cookie value."""
        return self._cookies.get(key, default)

    def hasCookie(self, key: str) -> bool:
        """Check if cookie exists."""
        return key in self._cookies

    def file(self, key: str) -> Optional[Any]:
        """Get uploaded file."""
        return self._files.get(key)

    def hasFile(self, key: str) -> bool:
        """Check if file exists."""
        return key in self._files

    def server(self, key: str, default: Any = None) -> Any:
        """Get server variable."""
        return self._server.get(key, default)

    def setRouteParameters(self, parameters: Dict[str, Any]) -> "Request":
        """Set route parameters."""
        self._route_parameters = parameters
        return self

    def route(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get route parameter."""
        if key is None:
            return self._route_parameters
        return self._route_parameters.get(key, default)

    def setSession(self, session: Dict[str, Any]) -> "Request":
        """Set session data."""
        self._session = session
        return self

    def session(self, key: Optional[str] = None, default: Any = None) -> Any:
        """Get session value."""
        if self._session is None:
            return default

        if key is None:
            return self._session

        return self._session.get(key, default)

    def old(self, key: str, default: Any = None) -> Any:
        """Get old input from session."""
        if self._session is None:
            return default

        old_input = self._session.get("_old_input", {})
        return old_input.get(key, default)

    def flash(self) -> None:
        """Flash all input to session."""
        if self._session is not None:
            self._session["_old_input"] = self.all()

    def flashOnly(self, keys: List[str]) -> None:
        """Flash specific input to session."""
        if self._session is not None:
            self._session["_old_input"] = self.only(*keys)

    def flashExcept(self, keys: List[str]) -> None:
        """Flash input except specific keys to session."""
        if self._session is not None:
            self._session["_old_input"] = self.except_(*keys)

    def collect(self, key: Optional[str] = None) -> List[Any]:
        """Get input as collection."""
        if key:
            value = self.input(key)
            if isinstance(value, dict):
                return list(value.values())
            elif isinstance(value, list):
                return value
            return [value] if value is not None else []

        return list(self.all().values())

    def csrf_token(self) -> Optional[str]:
        """
        Get the CSRF token from the request.

        Returns:
            The CSRF token or None if not set
        """
        # Check request attribute first
        if hasattr(self, "_csrf_token") and self._csrf_token is not None:
            return self._csrf_token

        # Check session
        if self._session is not None:
            if hasattr(self._session, "get"):
                return self._session.get("_token")
            else:
                return (
                    self._session.get("_token", None) if isinstance(self._session, dict) else None
                )

        return None

    def set_csrf_token(self, token: str) -> "Request":
        """
        Set the CSRF token on the request.

        Args:
            token: The CSRF token

        Returns:
            Self for method chaining
        """
        self._csrf_token = token

        # Store in session if available
        if self._session is not None and hasattr(self._session, "put"):
            self._session.put("_token", token)
        elif self._session is not None:
            self._session["_token"] = token

        return self

    def set_method(self, method: str) -> "Request":
        """
        Set the HTTP method for the request (for testing).

        Args:
            method: HTTP method (GET, POST, etc)

        Returns:
            Self for method chaining
        """
        self._method = method.upper()
        return self

    def set_header(self, key: str, value: str) -> "Request":
        """
        Set a header on the request (for testing).

        Args:
            key: Header name
            value: Header value

        Returns:
            Self for method chaining
        """
        normalized_key = "-".join(word.capitalize() for word in key.replace("_", "-").split("-"))
        self._headers[normalized_key] = value
        return self

    def __getattr__(self, name: str) -> Any:
        """Access input via dynamic properties."""
        return self.input(name)
