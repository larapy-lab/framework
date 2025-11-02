from typing import Callable, Optional, List, Any, Union
import inspect
import asyncio


class Gate:
    """Authorization gate for checking user abilities."""

    def __init__(self, container):
        self.container = container
        self.abilities: dict[str, Callable] = {}
        self.policies: dict[type, type] = {}
        self.before_callbacks: List[Callable] = []
        self.after_callbacks: List[Callable] = []
        self.user_resolver: Optional[Callable] = None

    def define(self, ability: str, callback: Callable) -> "Gate":
        """Define a new ability."""
        self.abilities[ability] = callback
        return self

    def policy(self, model_class: type, policy_class: type) -> "Gate":
        """Register a policy for a model."""
        self.policies[model_class] = policy_class
        return self

    def before(self, callback: Callable) -> "Gate":
        """Register a callback to run before authorization checks."""
        self.before_callbacks.append(callback)
        return self

    def after(self, callback: Callable) -> "Gate":
        """Register a callback to run after authorization checks."""
        self.after_callbacks.append(callback)
        return self

    def allows(self, ability: str, arguments: Any = None) -> bool:
        """Check if the current user has the ability."""
        return self.check(ability, arguments)

    def denies(self, ability: str, arguments: Any = None) -> bool:
        """Check if the current user doesn't have the ability."""
        return not self.allows(ability, arguments)

    def authorize(self, ability: str, arguments: Any = None):
        """Authorize or throw exception."""
        if self.denies(ability, arguments):
            from larapy.auth.exceptions import AuthorizationException

            raise AuthorizationException("This action is unauthorized.")

    def any(self, abilities: List[str], arguments: Any = None) -> bool:
        """Check if user has any of the given abilities."""
        return any(self.allows(ability, arguments) for ability in abilities)

    def none(self, abilities: List[str], arguments: Any = None) -> bool:
        """Check if user has none of the given abilities."""
        return not self.any(abilities, arguments)

    def for_user(self, user) -> "Gate":
        """Get a gate instance for a specific user."""
        gate = Gate(self.container)
        gate.abilities = self.abilities.copy()
        gate.policies = self.policies.copy()
        gate.before_callbacks = self.before_callbacks.copy()
        gate.after_callbacks = self.after_callbacks.copy()
        gate.user_resolver = lambda: user
        return gate

    def check(self, ability: str, arguments: Any = None) -> bool:
        """Check authorization."""
        user = self._resolve_user()

        if user is None:
            return False

        for callback in self.before_callbacks:
            result = self._call_before_callback(callback, user, ability, arguments)
            if result is not None:
                return bool(result)

        result = self._check_ability(user, ability, arguments)

        for callback in self.after_callbacks:
            self._call_after_callback(callback, user, ability, result, arguments)

        return result

    def _check_ability(self, user, ability: str, arguments: Any) -> bool:
        """Check ability using direct definition or policy."""
        if arguments is not None:
            model_class = type(arguments) if not isinstance(arguments, type) else arguments
            if model_class in self.policies:
                return self._check_policy(user, ability, arguments, model_class)

        if ability in self.abilities:
            callback = self.abilities[ability]
            result = self._call_callback(callback, user, ability, arguments)
            return bool(result)

        return False

    def _check_policy(self, user, ability: str, arguments: Any, model_class: type) -> bool:
        """Check policy method."""
        policy_class = self.policies[model_class]
        policy = self.container.make(policy_class)

        if hasattr(policy, "before"):
            result = self._call_policy_method(policy, "before", user, ability, arguments)
            if result is not None:
                return bool(result)

        if hasattr(policy, ability):
            result = self._call_policy_method(policy, ability, user, arguments)
            return bool(result)

        return False

    def _call_callback(self, callback: Callable, user, ability: str, arguments: Any):
        """Call a callback with proper arguments."""
        sig = inspect.signature(callback)
        params = list(sig.parameters.values())

        args = [user]

        if len(params) >= 2:
            args.append(ability if isinstance(arguments, bool) else arguments)

        if len(params) >= 3 and isinstance(arguments, bool):
            args.append(arguments)
        elif len(params) >= 3 and arguments is not None:
            pass

        result = callback(*args)

        if inspect.iscoroutine(result):
            loop = self._get_event_loop()
            return loop.run_until_complete(result)

        return result

    def _call_before_callback(self, callback: Callable, user, ability: str, arguments: Any):
        """Call a before callback."""
        sig = inspect.signature(callback)
        params = list(sig.parameters.values())

        args = [user]
        if len(params) >= 2:
            args.append(ability)

        result = callback(*args)

        if inspect.iscoroutine(result):
            loop = self._get_event_loop()
            return loop.run_until_complete(result)

        return result

    def _call_after_callback(
        self, callback: Callable, user, ability: str, result: bool, arguments: Any
    ):
        """Call an after callback."""
        sig = inspect.signature(callback)
        params = list(sig.parameters.values())

        args = [user, ability, result]

        callback_result = callback(*args)

        if inspect.iscoroutine(callback_result):
            loop = self._get_event_loop()
            return loop.run_until_complete(callback_result)

        return callback_result

    def _call_policy_method(self, policy, method_name: str, user, *args):
        """Call a policy method."""
        method = getattr(policy, method_name)

        if method_name == "before":
            result = method(user, args[0]) if len(args) > 0 else method(user)
        else:
            result = method(user, *args)

        if inspect.iscoroutine(result):
            loop = self._get_event_loop()
            return loop.run_until_complete(result)

        return result

    def _resolve_user(self):
        """Resolve the current user."""
        if self.user_resolver:
            return self.user_resolver()

        try:
            request = self.container.make("request")
            if hasattr(request, "user"):
                user_method = getattr(request, "user")
                if callable(user_method):
                    return user_method()
                return user_method
            return None
        except:
            return None

    def _get_event_loop(self):
        """Get or create event loop."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.new_event_loop()
