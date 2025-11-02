from typing import Any


class Event:
    pass


class Dispatchable:
    @classmethod
    def dispatch(cls, *args, **kwargs):
        from larapy.events import event

        instance = cls(*args, **kwargs)
        return event(instance)

    @classmethod
    def dispatch_if(cls, condition: bool, *args, **kwargs):
        if condition:
            return cls.dispatch(*args, **kwargs)
        return None

    @classmethod
    def dispatch_unless(cls, condition: bool, *args, **kwargs):
        if not condition:
            return cls.dispatch(*args, **kwargs)
        return None
