"""
Unit tests for the IoC Container
"""

import pytest

from larapy.container import (
    BindingResolutionException,
    CircularDependencyException,
    Container,
)


# Test classes for dependency injection
class SimpleDependency:
    """A simple dependency with no dependencies."""

    def __init__(self):
        self.value = "simple"


class AnotherDependency:
    """Another simple dependency."""

    def __init__(self):
        self.value = "another"


class ComplexDependency:
    """A class with dependencies."""

    def __init__(self, simple: SimpleDependency, another: AnotherDependency):
        self.simple = simple
        self.another = another


class OptionalDependency:
    """A class with optional parameters."""

    def __init__(self, simple: SimpleDependency, name: str = "default"):
        self.simple = simple
        self.name = name


# Define CircularB first (forward reference issue)
class CircularB:
    """For testing circular dependency detection."""

    def __init__(self, circular_a):  # Type hint added in CircularA
        self.circular_a = circular_a


class CircularA:
    """For testing circular dependency detection."""

    def __init__(self, circular_b: CircularB):
        self.circular_b = circular_b


# Now add the type hint to CircularB's __init__ parameter
CircularB.__init__.__annotations__['circular_a'] = CircularA


# Interfaces for testing
class CacheInterface:
    """Abstract cache interface."""

    def get(self, key: str) -> str:
        raise NotImplementedError


class RedisCache(CacheInterface):
    """Concrete Redis cache implementation."""

    def __init__(self):
        self.storage = {}

    def get(self, key: str) -> str:
        return self.storage.get(key, "")

    def set(self, key: str, value: str) -> None:
        self.storage[key] = value


class FileCache(CacheInterface):
    """Concrete File cache implementation."""

    def __init__(self):
        self.files = {}

    def get(self, key: str) -> str:
        return self.files.get(key, "")


# Test fixtures
@pytest.fixture
def container():
    """Create a fresh container for each test."""
    return Container()


class TestContainerBasics:
    """Test basic container operations."""

    def test_container_creation(self, container):
        """Test that container can be created."""
        assert container is not None
        assert isinstance(container, Container)

    def test_bind_simple_class(self, container):
        """Test binding a simple class."""
        container.bind("simple", SimpleDependency)
        assert container.bound("simple")

    def test_make_simple_class(self, container):
        """Test resolving a simple class."""
        container.bind("simple", SimpleDependency)
        instance = container.make("simple")

        assert isinstance(instance, SimpleDependency)
        assert instance.value == "simple"

    def test_make_without_binding(self, container):
        """Test auto-wiring without explicit binding."""
        instance = container.make(SimpleDependency)
        assert isinstance(instance, SimpleDependency)

    def test_resolve_alias(self, container):
        """Test that resolve() is an alias for make()."""
        container.bind("simple", SimpleDependency)
        instance = container.resolve("simple")
        assert isinstance(instance, SimpleDependency)


class TestSingletons:
    """Test singleton (shared) bindings."""

    def test_singleton_binding(self, container):
        """Test registering a singleton."""
        container.singleton("simple", SimpleDependency)
        instance1 = container.make("simple")
        instance2 = container.make("simple")

        assert instance1 is instance2

    def test_bind_with_shared_flag(self, container):
        """Test bind with shared=True."""
        container.bind("simple", SimpleDependency, shared=True)
        instance1 = container.make("simple")
        instance2 = container.make("simple")

        assert instance1 is instance2

    def test_non_shared_binding(self, container):
        """Test that non-shared bindings create new instances."""
        container.bind("simple", SimpleDependency)
        instance1 = container.make("simple")
        instance2 = container.make("simple")

        assert instance1 is not instance2

    def test_instance_registration(self, container):
        """Test registering an existing instance."""
        instance = SimpleDependency()
        instance.value = "modified"

        container.instance("simple", instance)
        resolved = container.make("simple")

        assert resolved is instance
        assert resolved.value == "modified"


class TestDependencyInjection:
    """Test automatic dependency injection."""

    def test_auto_wire_dependencies(self, container):
        """Test automatic dependency resolution."""
        instance = container.make(ComplexDependency)

        assert isinstance(instance, ComplexDependency)
        assert isinstance(instance.simple, SimpleDependency)
        assert isinstance(instance.another, AnotherDependency)

    def test_optional_parameters(self, container):
        """Test handling of optional parameters."""
        instance = container.make(OptionalDependency)

        assert isinstance(instance, OptionalDependency)
        assert instance.name == "default"

    def test_override_optional_parameters(self, container):
        """Test overriding optional parameters."""
        instance = container.make(
            OptionalDependency,
            parameters={"name": "custom"},
        )

        assert instance.name == "custom"

    def test_nested_dependencies(self, container):
        """Test resolving nested dependencies."""

        class Level1:
            def __init__(self, simple: SimpleDependency):
                self.simple = simple

        class Level2:
            def __init__(self, level1: Level1):
                self.level1 = level1

        class Level3:
            def __init__(self, level2: Level2):
                self.level2 = level2

        instance = container.make(Level3)

        assert isinstance(instance.level2.level1.simple, SimpleDependency)


class TestInterfaceBinding:
    """Test binding interfaces to implementations."""

    def test_bind_interface_to_implementation(self, container):
        """Test binding an interface to a concrete class."""
        container.bind(CacheInterface, RedisCache)
        cache = container.make(CacheInterface)

        assert isinstance(cache, RedisCache)

    def test_singleton_interface(self, container):
        """Test singleton interface binding."""
        container.singleton(CacheInterface, RedisCache)

        cache1 = container.make(CacheInterface)
        cache1.set("key", "value")

        cache2 = container.make(CacheInterface)

        assert cache2.get("key") == "value"

    def test_bind_with_callable(self, container):
        """Test binding with a factory function."""

        def create_cache(c: Container) -> CacheInterface:
            cache = RedisCache()
            cache.set("initialized", "true")
            return cache

        container.bind(CacheInterface, create_cache)
        cache = container.make(CacheInterface)

        assert cache.get("initialized") == "true"


class TestAliases:
    """Test alias functionality."""

    def test_create_alias(self, container):
        """Test creating an alias for a binding."""
        container.bind("app.cache", RedisCache)
        container.alias("app.cache", "cache")

        cache = container.make("cache")
        assert isinstance(cache, RedisCache)

    def test_multiple_aliases(self, container):
        """Test multiple aliases for one binding."""
        container.singleton("app.cache", RedisCache)
        container.alias("app.cache", "cache")
        container.alias("app.cache", "redis")

        cache1 = container.make("cache")
        cache2 = container.make("redis")

        assert cache1 is cache2


class TestTags:
    """Test tagging functionality."""

    def test_tag_bindings(self, container):
        """Test tagging multiple bindings."""
        container.bind("redis", RedisCache)
        container.bind("file", FileCache)
        container.tag(["redis", "file"], ["cache"])

        caches = container.tagged("cache")

        assert len(caches) == 2
        assert any(isinstance(c, RedisCache) for c in caches)
        assert any(isinstance(c, FileCache) for c in caches)

    def test_multiple_tags(self, container):
        """Test assigning multiple tags."""
        container.bind("redis", RedisCache)
        container.tag(["redis"], ["cache", "storage", "redis"])

        cache_items = container.tagged("cache")
        storage_items = container.tagged("storage")

        assert len(cache_items) == 1
        assert len(storage_items) == 1

    def test_tagged_empty(self, container):
        """Test tagged with no matches."""
        items = container.tagged("nonexistent")
        assert items == []


class TestCallMethod:
    """Test the call() method for method injection."""

    def test_call_function_with_dependencies(self, container):
        """Test calling a function with dependency injection."""

        def process(simple: SimpleDependency, another: AnotherDependency) -> str:
            return f"{simple.value}-{another.value}"

        result = container.call(process)
        assert result == "simple-another"

    def test_call_with_parameters(self, container):
        """Test call with provided parameters."""

        def greet(name: str, simple: SimpleDependency) -> str:
            return f"Hello {name}, {simple.value}"

        result = container.call(greet, {"name": "World"})
        assert result == "Hello World, simple"

    def test_call_with_defaults(self, container):
        """Test call with default parameters."""

        def greet(simple: SimpleDependency, greeting: str = "Hi") -> str:
            return f"{greeting} {simple.value}"

        result = container.call(greet)
        assert result == "Hi simple"


class TestBound:
    """Test the bound() and has() methods."""

    def test_bound_returns_true_for_binding(self, container):
        """Test bound() returns true for bound abstracts."""
        container.bind("simple", SimpleDependency)
        assert container.bound("simple")

    def test_bound_returns_true_for_instance(self, container):
        """Test bound() returns true for registered instances."""
        container.instance("simple", SimpleDependency())
        assert container.bound("simple")

    def test_bound_returns_false_for_unbound(self, container):
        """Test bound() returns false for unbound abstracts."""
        assert not container.bound("nonexistent")

    def test_has_alias(self, container):
        """Test has() is an alias for bound()."""
        container.bind("simple", SimpleDependency)
        assert container.has("simple")


class TestCircularDependencies:
    """Test circular dependency detection."""

    def test_circular_dependency_detection(self, container):
        """Test that circular dependencies are detected."""
        container.bind(CircularA, CircularA)
        container.bind(CircularB, CircularB)

        with pytest.raises(CircularDependencyException) as exc_info:
            container.make(CircularA)

        assert "CircularA" in str(exc_info.value)


class TestErrorHandling:
    """Test error handling."""

    def test_unresolvable_dependency(self, container):
        """Test error when dependency cannot be resolved."""

        class UnresolvableClass:
            def __init__(self, missing_param):  # No type hint
                self.missing_param = missing_param

        with pytest.raises(BindingResolutionException):
            container.make(UnresolvableClass)

    def test_bind_string_without_concrete(self, container):
        """Test error when binding string without concrete."""
        with pytest.raises(BindingResolutionException):
            container.bind("abstract")


class TestFlush:
    """Test container flushing."""

    def test_flush_clears_bindings(self, container):
        """Test that flush clears all bindings."""
        container.bind("simple", SimpleDependency)
        container.singleton("cache", RedisCache)
        container.instance("another", AnotherDependency())

        assert container.bound("simple")
        assert container.bound("cache")
        assert container.bound("another")

        container.flush()

        assert not container.bound("simple")
        assert not container.bound("cache")
        assert not container.bound("another")

    def test_flush_clears_tags(self, container):
        """Test that flush clears tags."""
        container.bind("redis", RedisCache)
        container.tag(["redis"], ["cache"])

        container.flush()

        caches = container.tagged("cache")
        assert caches == []


class TestContainerRepr:
    """Test container string representation."""

    def test_repr(self, container):
        """Test __repr__ output."""
        container.bind("simple", SimpleDependency)
        container.singleton("cache", RedisCache)

        repr_str = repr(container)
        assert "Container" in repr_str
        assert "bindings=" in repr_str
        assert "instances=" in repr_str


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_service_with_multiple_dependencies(self, container):
        """Test a service with multiple complex dependencies."""

        class Database:
            def query(self):
                return "data"

        class Logger:
            def log(self, msg):
                return f"LOG: {msg}"

        class UserRepository:
            def __init__(self, db: Database, logger: Logger):
                self.db = db
                self.logger = logger

            def find(self, user_id: int):
                self.logger.log(f"Finding user {user_id}")
                return self.db.query()

        repo = container.make(UserRepository)
        result = repo.find(1)

        assert result == "data"

    def test_mixed_binding_types(self, container):
        """Test mixing different binding types."""
        # Regular binding
        container.bind("simple", SimpleDependency)

        # Singleton
        container.singleton("cache", RedisCache)

        # Instance
        another = AnotherDependency()
        container.instance("another", another)

        # Resolve all
        simple = container.make("simple")
        cache = container.make("cache")
        resolved_another = container.make("another")

        assert isinstance(simple, SimpleDependency)
        assert isinstance(cache, RedisCache)
        assert resolved_another is another
