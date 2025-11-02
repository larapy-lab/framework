from larapy.validation.message_bag import MessageBag
from larapy.validation.validation_rule import ValidationRule
from larapy.validation.rules import *
from typing import Dict, List, Any, Union, Callable, Optional
import re


class Validator:
    def __init__(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Union[str, List]],
        messages: Optional[Dict[str, str]] = None,
    ):
        self._data = data
        self._rules = rules
        self._messages = messages or {}
        self._errors = MessageBag()
        self._after_callbacks: List[Callable] = []
        self._validated_data: Dict[str, Any] = {}
        self._stop_on_first_failure = False

    def validate(self) -> Dict[str, Any]:
        if self.fails():
            from larapy.validation.validation_exception import ValidationException

            raise ValidationException(self, self._errors)
        return self.validated()

    def fails(self) -> bool:
        self._errors = MessageBag()
        self._validated_data = {}

        for attribute, rule_set in self._rules.items():
            if self._stop_on_first_failure and self._errors.any():
                break

            value = self._getValue(attribute)
            rules = self._parseRules(rule_set)
            is_nullable = "nullable" in [r.lower() if isinstance(r, str) else None for r in rules]
            is_required = "required" in [r.lower() if isinstance(r, str) else None for r in rules]

            # Skip validation if field is not present and not required
            if value is None and not is_required and not is_nullable:
                continue

            if value is None and is_nullable:
                continue

            if not self._validateAttribute(attribute, value, rules):
                if self._stop_on_first_failure:
                    break

            if not self._errors.has(attribute):
                self._validated_data[attribute] = value

        for callback in self._after_callbacks:
            callback(self)

        return self._errors.any()

    def passes(self) -> bool:
        return not self.fails()

    def validated(self) -> Dict[str, Any]:
        return self._validated_data.copy()

    def errors(self) -> MessageBag:
        return self._errors
    
    def format_errors_for_json(self) -> Dict[str, Any]:
        """
        Format validation errors for JSON API response.
        
        Returns:
            Dictionary with message and errors suitable for JSON
            
        Example:
            ```python
            validator = Validator(data, rules)
            if validator.fails():
                return validator.format_errors_for_json(), 422
            ```
        """
        return {
            "message": "The given data was invalid.",
            "errors": self._errors.messages()
        }
    
    def format_errors_for_html(self) -> str:
        """
        Format validation errors for HTML display.
        
        Returns:
            HTML string with Bootstrap-compatible alert
            
        Example:
            ```python
            validator = Validator(data, rules)
            if validator.fails():
                return validator.format_errors_for_html()
            ```
        """
        lines = ['<div class="alert alert-danger">']
        lines.append('    <p><strong>The given data was invalid.</strong></p>')
        
        if self._errors.any():
            lines.append('    <ul>')
            for field, messages in self._errors.messages().items():
                for msg in messages:
                    lines.append(f'        <li>{msg}</li>')
            lines.append('    </ul>')
        
        lines.append('</div>')
        return '\n'.join(lines)
    
    def format_errors_as_list(self) -> List[str]:
        """
        Format validation errors as a flat list of messages.
        
        Returns:
            List of all error messages across all fields
            
        Example:
            ```python
            validator = Validator(data, rules)
            if validator.fails():
                flash_messages = validator.format_errors_as_list()
            ```
        """
        messages = []
        for field_errors in self._errors.messages().values():
            messages.extend(field_errors)
        return messages
    
    def format_errors_with_fields(self) -> List[Dict[str, str]]:
        """
        Format validation errors with field names for detailed display.
        
        Returns:
            List of dictionaries containing field and message
            
        Example:
            ```python
            validator = Validator(data, rules)
            if validator.fails():
                errors = validator.format_errors_with_fields()
                # [{"field": "email", "message": "The email field is required."}]
            ```
        """
        formatted = []
        for field, messages in self._errors.messages().items():
            for msg in messages:
                formatted.append({"field": field, "message": msg})
        return formatted
    
    def first_error(self, field: Optional[str] = None) -> Optional[str]:
        """
        Get the first error message.
        
        Args:
            field: Optional field name to get error for
            
        Returns:
            First error message or None
            
        Example:
            ```python
            validator = Validator(data, rules)
            if validator.fails():
                print(validator.first_error())  # First error from any field
                print(validator.first_error('email'))  # First error for email field
            ```
        """
        if field:
            messages = self._errors.get(field)
            return messages[0] if messages else None
        
        # Return first error from any field
        for messages in self._errors.messages().values():
            if messages:
                return messages[0]
        return None

    def after(self, callback: Callable) -> "Validator":
        self._after_callbacks.append(callback)
        return self

    def stopOnFirstFailure(self) -> "Validator":
        self._stop_on_first_failure = True
        return self

    def _getValue(self, attribute: str) -> Any:
        if "." in attribute:
            keys = attribute.split(".")
            value = self._data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        return self._data.get(attribute)

    def _parseRules(self, rule_set: Union[str, List]) -> List[Union[str, ValidationRule]]:
        if isinstance(rule_set, str):
            return rule_set.split("|")
        return rule_set

    def _validateAttribute(self, attribute: str, value: Any, rules: List) -> bool:
        for rule in rules:
            if self._stop_on_first_failure and self._errors.has(attribute):
                break

            if isinstance(rule, ValidationRule):
                if not rule.passes(attribute, value, self._data):
                    self._errors.add(attribute, rule.getMessage(attribute))
                    return False
            elif isinstance(rule, str):
                if not self._validateRule(attribute, value, rule):
                    return False

        return True

    def _validateRule(self, attribute: str, value: Any, rule: str) -> bool:
        if ":" in rule:
            rule_name, parameters = rule.split(":", 1)
            params = [p.strip() for p in parameters.split(",")]
        else:
            rule_name = rule
            params = []

        rule_name = rule_name.lower()

        if rule_name == "nullable":
            return True

        if rule_name == "bail":
            self._stop_on_first_failure = True
            return True

        rule_instance = self._getRuleInstance(rule_name, params)
        if rule_instance:
            if not rule_instance.passes(attribute, value, self._data):
                message = self._getCustomMessage(attribute, rule_name) or rule_instance.getMessage(
                    attribute
                )
                self._errors.add(attribute, message)
                return False
            return True

        return True

    def _getRuleInstance(self, rule_name: str, params: List[str]) -> Optional[ValidationRule]:
        rule_map = {
            "required": RequiredRule,
            "email": EmailRule,
            "numeric": NumericRule,
            "string": StringRule,
            "array": ArrayRule,
            "boolean": BooleanRule,
            "integer": IntegerRule,
            "alpha": AlphaRule,
            "alpha_num": AlphaNumRule,
            "alpha_dash": AlphaDashRule,
            "url": UrlRule,
            "ip": IpRule,
            "confirmed": ConfirmedRule,
            "nullable": NullableRule,
            "json": JsonRule,
            "accepted": AcceptedRule,
            "declined": DeclinedRule,
            "uppercase": UppercaseRule,
            "lowercase": LowercaseRule,
            "present": PresentRule,
            "filled": FilledRule,
            "bail": BailRule,
            "ascii": AsciiRule,
            "active_url": ActiveUrlRule,
        }

        if rule_name in rule_map:
            return rule_map[rule_name]()

        if rule_name == "min" and params:
            return MinRule(float(params[0]))
        elif rule_name == "max" and params:
            return MaxRule(float(params[0]))
        elif rule_name == "same" and params:
            return SameRule(params[0])
        elif rule_name == "different" and params:
            return DifferentRule(params[0])
        elif rule_name == "in" and params:
            return InRule(params)
        elif rule_name == "not_in" and params:
            return NotInRule(params)
        elif rule_name == "regex" and params:
            return RegexRule(params[0])
        elif rule_name == "not_regex" and params:
            return NotRegexRule(params[0])
        elif rule_name == "required_if" and len(params) >= 2:
            return RequiredIfRule(params[0], params[1])
        elif rule_name == "required_unless" and len(params) >= 2:
            return RequiredUnlessRule(params[0], params[1])
        elif rule_name == "required_with" and params:
            return RequiredWithRule(params)
        elif rule_name == "required_without" and params:
            return RequiredWithoutRule(params)
        elif rule_name == "required_with_all" and params:
            return RequiredWithAllRule(*params)
        elif rule_name == "required_without_all" and params:
            return RequiredWithoutAllRule(*params)
        elif rule_name == "required_if_accepted" and params:
            return RequiredIfAcceptedRule(params[0])
        elif rule_name == "required_if_declined" and params:
            return RequiredIfDeclinedRule(params[0])
        elif rule_name == "required_array_keys" and params:
            return RequiredArrayKeysRule(*params)
        elif rule_name == "size" and params:
            return SizeRule(int(params[0]))
        elif rule_name == "between" and len(params) >= 2:
            return BetweenRule(int(params[0]), int(params[1]))
        elif rule_name == "digits" and params:
            return DigitsRule(int(params[0]))
        elif rule_name == "digits_between" and len(params) >= 2:
            return DigitsBetweenRule(int(params[0]), int(params[1]))
        elif rule_name == "date" and params:
            return DateRule(params[0])
        elif rule_name == "date_format" and params:
            return DateFormatRule(*params)
        elif rule_name == "date_equals" and params:
            return DateEqualsRule(params[0])
        elif rule_name == "after" and params:
            return AfterRule(params[0])
        elif rule_name == "after_or_equal" and params:
            return AfterOrEqualRule(params[0])
        elif rule_name == "before" and params:
            return BeforeRule(params[0])
        elif rule_name == "before_or_equal" and params:
            return BeforeOrEqualRule(params[0])
        elif rule_name == "timezone" and params:
            return TimezoneRule(params[0] if params else "all")
        elif rule_name == "accepted_if" and len(params) >= 2:
            return AcceptedIfRule(params[0], params[1])
        elif rule_name == "declined_if" and len(params) >= 2:
            return DeclinedIfRule(params[0], params[1])
        elif rule_name == "starts_with" and params:
            return StartsWithRule(*params)
        elif rule_name == "ends_with" and params:
            return EndsWithRule(*params)
        elif rule_name == "doesnt_start_with" and params:
            return DoesntStartWithRule(*params)
        elif rule_name == "doesnt_end_with" and params:
            return DoesntEndWithRule(*params)
        elif rule_name == "uuid" and params:
            return UuidRule(int(params[0]) if params[0].isdigit() else None)
        elif rule_name == "ulid":
            return UlidRule()
        elif rule_name == "gt" and params:
            return GtRule(params[0])
        elif rule_name == "gte" and params:
            return GteRule(params[0])
        elif rule_name == "lt" and params:
            return LtRule(params[0])
        elif rule_name == "lte" and params:
            return LteRule(params[0])
        elif rule_name == "decimal" and params:
            if len(params) >= 2:
                return DecimalRule(params[0], params[1])
            return DecimalRule(params[0])
        elif rule_name == "max_digits" and params:
            return MaxDigitsRule(params[0])
        elif rule_name == "min_digits" and params:
            return MinDigitsRule(params[0])
        elif rule_name == "multiple_of" and params:
            return MultipleOfRule(params[0])
        elif rule_name == "distinct":
            strict = "strict" in params
            ignore_case = "ignore_case" in params
            return DistinctRule(strict, ignore_case)
        elif rule_name == "contains" and params:
            return ContainsRule(*params)
        elif rule_name == "doesnt_contain" and params:
            return DoesntContainRule(*params)
        elif rule_name == "in_array" and params:
            return InArrayRule(params[0])
        elif rule_name == "list":
            return ListRule()
        elif rule_name == "hex_color":
            return HexColorRule()
        elif rule_name == "mac_address":
            return MacAddressRule()

        return None

    def _getCustomMessage(self, attribute: str, rule: str) -> Optional[str]:
        key = f"{attribute}.{rule}"
        return self._messages.get(key)
