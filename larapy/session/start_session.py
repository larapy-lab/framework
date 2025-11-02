from typing import Any, Callable
from larapy.session.session_manager import SessionManager


class StartSession:
    def __init__(self, manager: SessionManager):
        self._manager = manager

    def handle(self, request: Any, next_handler: Callable) -> Any:
        session = self._start_session(request)
        request.setSession(session.all())

        response = next_handler(request)

        self._save_session(request, session)
        self._add_cookie_to_response(response, session)

        return response

    def _start_session(self, request: Any):
        session = self._get_session(request)
        session.setId(self._get_session_id(request))
        session.start()
        return session

    def _get_session(self, request: Any):
        return self._manager.driver()

    def _get_session_id(self, request: Any) -> str:
        return request.cookie(self._get_session_name())

    def _get_session_name(self) -> str:
        session = self._manager.driver()
        return session.getName()

    def _save_session(self, request: Any, session):
        if hasattr(request, "_session") and request._session:
            for key, value in request._session.items():
                session.put(key, value)

        session.save()

    def _add_cookie_to_response(self, response, session):
        response.cookie(session.getName(), session.getId(), minutes=120)

    def terminate(self, request: Any, response: Any):
        pass
