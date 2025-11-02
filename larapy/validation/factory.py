from larapy.validation.validator import Validator
from typing import Dict, List, Any, Union, Optional, Callable


class Factory:
    def __init__(self):
        self._custom_rules: Dict[str, Callable] = {}

    def make(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Union[str, List]],
        messages: Optional[Dict[str, str]] = None,
    ) -> Validator:
        return Validator(data, rules, messages)

    def extend(self, rule_name: str, callback: Callable):
        self._custom_rules[rule_name] = callback

    def validate(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Union[str, List]],
        messages: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        validator = self.make(data, rules, messages)
        return validator.validate()
