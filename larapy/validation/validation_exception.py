from larapy.validation.validator import Validator
from larapy.validation.message_bag import MessageBag
from typing import Dict, List, Any, Union, Optional


class ValidationException(Exception):
    def __init__(self, validator: Validator, errors: MessageBag):
        self.validator = validator
        self.errors = errors
        super().__init__("The given data was invalid.")

    def getErrors(self) -> MessageBag:
        return self.errors

    def getValidator(self) -> Validator:
        return self.validator
