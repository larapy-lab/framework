from typing import Any, Dict, List, Union


class EventSubscriber:
    def subscribe(self, dispatcher) -> Dict[str, Union[str, List[str]]]:
        raise NotImplementedError("EventSubscriber must implement subscribe method")
