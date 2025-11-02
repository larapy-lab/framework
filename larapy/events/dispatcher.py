import fnmatch
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union


class Dispatcher:
    def __init__(self, container=None):
        self._listeners: Dict[str, List[Callable]] = {}
        self._wildcards: Dict[str, List[Callable]] = {}
        self._container = container
        self._queued_listeners: List[tuple] = []

    def listen(self, events: Union[str, List[str]], listener: Union[Callable, str, Type]) -> None:
        if isinstance(events, str):
            events = [events]

        for event in events:
            if "*" in event:
                if event not in self._wildcards:
                    self._wildcards[event] = []
                self._wildcards[event].append(listener)
            else:
                if event not in self._listeners:
                    self._listeners[event] = []
                self._listeners[event].append(listener)

    def has_listeners(self, event_name: str) -> bool:
        return event_name in self._listeners or self._has_wildcard_listeners(event_name)

    def _has_wildcard_listeners(self, event_name: str) -> bool:
        for pattern in self._wildcards.keys():
            if fnmatch.fnmatch(event_name, pattern):
                return True
        return False

    def subscribe(self, subscriber: Union[Type, object]) -> None:
        if inspect.isclass(subscriber):
            subscriber = self._resolve_subscriber(subscriber)

        subscriptions = subscriber.subscribe(self)

        if subscriptions:
            for event, listeners in subscriptions.items():
                if not isinstance(listeners, list):
                    listeners = [listeners]
                for listener in listeners:
                    self.listen(event, listener)

    def _resolve_subscriber(self, subscriber_class: Type) -> object:
        if self._container:
            return self._container.make(subscriber_class)
        return subscriber_class()

    def until(self, event: Union[str, object], payload: Any = None) -> Optional[Any]:
        return self.dispatch(event, payload, halt=True)

    def dispatch(
        self, event: Union[str, object], payload: Any = None, halt: bool = False
    ) -> Optional[List[Any]]:
        if isinstance(event, str):
            event_name = event
            event_obj = None
        else:
            event_name = self._get_event_name(event)
            event_obj = event
            if payload is None:
                payload = event

        listeners = self._get_listeners(event_name)

        if not listeners:
            return [] if not halt else None

        responses = []

        for listener in listeners:
            response = self._call_listener(listener, event_obj or payload, event_name)

            if halt and response is not None:
                return response

            if response is not False:
                responses.append(response)

        return responses if not halt else None

    def _get_event_name(self, event: object) -> str:
        return event.__class__.__module__ + "." + event.__class__.__name__

    def _get_listeners(self, event_name: str) -> List[Callable]:
        listeners = []

        if event_name in self._listeners:
            listeners.extend(self._listeners[event_name])

        for pattern, pattern_listeners in self._wildcards.items():
            if fnmatch.fnmatch(event_name, pattern):
                listeners.extend(pattern_listeners)

        return listeners

    def _call_listener(
        self, listener: Union[Callable, str, Type], event: Any, event_name: str
    ) -> Any:
        if isinstance(listener, str):
            listener = self._resolve_listener(listener)
        elif inspect.isclass(listener):
            listener = self._resolve_listener(listener)

        if hasattr(listener, "handle"):
            if hasattr(listener, "should_queue") and callable(listener.should_queue):
                if listener.should_queue(event):
                    self._queue_listener(listener, event)
                    return None
            return listener.handle(event)

        if callable(listener):
            sig = inspect.signature(listener)
            params = list(sig.parameters.values())

            if len(params) == 0:
                return listener()
            elif len(params) == 1:
                return listener(event)
            else:
                return listener(event, event_name)

        return None

    def _resolve_listener(self, listener: Union[str, Type]) -> object:
        if self._container:
            if isinstance(listener, str):
                return self._container.make(listener)
            return self._container.make(listener)

        if isinstance(listener, str):
            raise ValueError(f"Cannot resolve string listener '{listener}' without container")

        return listener()

    def _queue_listener(self, listener: object, event: Any) -> None:
        self._queued_listeners.append((listener, event))

    def forget(self, event: str) -> None:
        if event in self._listeners:
            del self._listeners[event]

        if event in self._wildcards:
            del self._wildcards[event]

    def flush(self, event: str) -> None:
        self.forget(event)

    def get_listeners(self, event_name: str) -> List[Callable]:
        return self._get_listeners(event_name)
