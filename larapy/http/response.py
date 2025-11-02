"""
HTTP Response

HTTP response handling with headers, cookies, and content.
"""

import json
from typing import Any, Callable, Dict, Generator, List, Optional, Union


class Response:
    """
    HTTP Response matching Laravel's Response class.

    Handles status codes, headers, cookies, and content.
    """

    def __init__(
        self, content: Any = "", status: int = 200, headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize response.

        Args:
            content: Response content
            status: HTTP status code
            headers: HTTP headers
        """
        self._content = content
        self._status = status
        self._headers = headers or {}
        self._cookies: List[Dict[str, Any]] = []

    def content(self) -> Any:
        """Get response content."""
        return self._content

    def setContent(self, content: Any) -> "Response":
        """Set response content."""
        self._content = content
        return self

    def status(self) -> int:
        """Get status code."""
        return self._status

    @property
    def status_code(self) -> int:
        """Get status code as property (alias for status())."""
        return self._status

    def setStatusCode(self, status: int) -> "Response":
        """Set status code."""
        self._status = status
        return self

    def header(self, key: str, value: str) -> "Response":
        """Add header to response."""
        self._headers[key] = value
        return self

    def withHeaders(self, headers: Dict[str, str]) -> "Response":
        """Add multiple headers."""
        self._headers.update(headers)
        return self

    def getHeaders(self) -> Dict[str, str]:
        """Get all headers."""
        return self._headers

    def cookie(
        self,
        name: str,
        value: str,
        minutes: int = 0,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        http_only: bool = True,
    ) -> "Response":
        """Add cookie to response."""
        self._cookies.append(
            {
                "name": name,
                "value": value,
                "minutes": minutes,
                "path": path,
                "domain": domain,
                "secure": secure,
                "http_only": http_only,
            }
        )
        return self

    def withoutCookie(self, name: str) -> "Response":
        """Remove cookie from response."""
        self._cookies = [c for c in self._cookies if c["name"] != name]
        self._cookies.append(
            {
                "name": name,
                "value": "",
                "minutes": -1,
                "path": "/",
                "domain": None,
                "secure": False,
                "http_only": True,
            }
        )
        return self

    def getCookies(self) -> List[Dict[str, Any]]:
        """Get all cookies."""
        return self._cookies

    def __str__(self) -> str:
        """String representation."""
        if isinstance(self._content, (dict, list)):
            return json.dumps(self._content)
        return str(self._content)


class JsonResponse(Response):
    """
    JSON Response.

    Automatically sets Content-Type and encodes data.
    """

    def __init__(
        self,
        data: Any = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        json_options: int = 0,
    ) -> None:
        """
        Initialize JSON response.

        Args:
            data: Data to encode as JSON
            status: HTTP status code
            headers: HTTP headers
            json_options: JSON encoding options
        """
        content = json.dumps(data, default=str, indent=2 if json_options else None)
        super().__init__(content, status, headers)
        self._data = data
        self._headers["Content-Type"] = "application/json"

    def getData(self) -> Any:
        """Get response data."""
        return self._data

    def get_json(self) -> Any:
        """Get response data (alias for getData())."""
        return self._data

    def setData(self, data: Any) -> "JsonResponse":
        """Set response data."""
        self._data = data
        self._content = json.dumps(data, default=str)
        return self


class RedirectResponse(Response):
    """
    Redirect Response.

    Handles HTTP redirects with status codes and flash data.
    """

    def __init__(
        self, url: str, status: int = 302, headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize redirect response.

        Args:
            url: Redirect URL
            status: HTTP status code (302 or 301)
            headers: HTTP headers
        """
        super().__init__("", status, headers)
        self._url = url
        self._headers["Location"] = url
        self._session_data: Dict[str, Any] = {}

    def getTargetUrl(self) -> str:
        """Get redirect URL."""
        return self._url

    def with_(self, key: str, value: Any) -> "RedirectResponse":
        """Flash data to session."""
        self._session_data[key] = value
        return self

    def withInput(self, input_data: Optional[Dict[str, Any]] = None) -> "RedirectResponse":
        """Flash input to session."""
        self._session_data["_old_input"] = input_data or {}
        return self

    def getSessionData(self) -> Dict[str, Any]:
        """Get session flash data."""
        return self._session_data


class StreamedResponse(Response):
    """
    Streamed Response.

    Streams content using a callback or generator.
    """

    def __init__(
        self,
        callback: Union[Callable, Generator],
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize streamed response.

        Args:
            callback: Streaming callback or generator
            status: HTTP status code
            headers: HTTP headers
        """
        super().__init__("", status, headers)
        self._callback = callback
        self._headers["X-Accel-Buffering"] = "no"

    def getCallback(self) -> Union[Callable, Generator]:
        """Get streaming callback."""
        return self._callback

    def sendContent(self) -> None:
        """Send streamed content."""
        if isinstance(self._callback, Generator):
            for chunk in self._callback:
                print(chunk, end="", flush=True)
        elif callable(self._callback):
            self._callback()


class BinaryFileResponse(Response):
    """
    Binary File Response.

    Serves file downloads or displays.
    """

    def __init__(
        self,
        file_path: str,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        disposition: str = "inline",
        filename: Optional[str] = None,
    ) -> None:
        """
        Initialize binary file response.

        Args:
            file_path: Path to file
            status: HTTP status code
            headers: HTTP headers
            disposition: Content disposition (inline or attachment)
            filename: Download filename
        """
        super().__init__("", status, headers)
        self._file_path = file_path
        self._disposition = disposition
        self._filename = filename or file_path.split("/")[-1]

    def getFile(self) -> str:
        """Get file path."""
        return self._file_path

    def getDisposition(self) -> str:
        """Get content disposition."""
        return self._disposition

    def getFilename(self) -> str:
        """Get filename."""
        return self._filename


def response(
    content: Any = "", status: int = 200, headers: Optional[Dict[str, str]] = None
) -> Response:
    """Create a response instance."""
    if isinstance(content, (dict, list)):
        return JsonResponse(content, status, headers)
    return Response(content, status, headers)


def redirect(
    url: str, status: int = 302, headers: Optional[Dict[str, str]] = None
) -> RedirectResponse:
    """Create a redirect response."""
    return RedirectResponse(url, status, headers)


def back() -> RedirectResponse:
    """Redirect to previous URL."""
    return RedirectResponse("/")


class ViewResponse(Response):
    """
    View response for rendered templates.
    """

    def __init__(
        self,
        view: Any,
        data: Optional[Dict[str, Any]] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize view response.

        Args:
            view: View instance or name
            data: View data
            status: HTTP status code
            headers: HTTP headers
        """
        from larapy.views import View

        if isinstance(view, str):
            view = View.make(view, data or {})
        elif data:
            view.with_(data)

        self.view = view
        content = str(view)

        super().__init__(content, status, headers)

        if "Content-Type" not in self._headers:
            self._headers["Content-Type"] = "text/html; charset=utf-8"

    def getData(self) -> Dict[str, Any]:
        """Get view data."""
        return self.view.data
