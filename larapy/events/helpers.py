_event_dispatcher = None


def set_event_dispatcher(dispatcher):
    global _event_dispatcher
    _event_dispatcher = dispatcher


def get_event_dispatcher():
    return _event_dispatcher


def event(event_instance=None, payload=None, halt=False):
    if _event_dispatcher is None:
        raise RuntimeError("Event dispatcher not set. Call set_event_dispatcher() first.")

    if event_instance is None:
        return _event_dispatcher

    return _event_dispatcher.dispatch(event_instance, payload, halt)
