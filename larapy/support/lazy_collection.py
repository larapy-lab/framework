from typing import Generator, Callable, Any, Optional, Iterable, Union
import itertools


class LazyCollection:

    def __init__(self, source: Union[Callable[[], Generator], Generator, Iterable]):
        if callable(source) and not isinstance(source, (Generator, type(iter([])))):
            self._source = source
        elif isinstance(source, Generator):
            self._source = lambda: source
        elif hasattr(source, "__iter__"):
            self._source = lambda: iter(source)
        else:
            raise ValueError("Source must be iterable, generator, or callable returning generator")

    def get_iterator(self) -> Generator:
        result = self._source()
        if not hasattr(result, "__iter__"):
            raise ValueError("Source must return an iterable")
        return iter(result)

    def map(self, callback: Callable) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                yield callback(item)

        return LazyCollection(generator)

    def filter(self, callback: Callable = None) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                if callback is None:
                    if item:
                        yield item
                elif callback(item):
                    yield item

        return LazyCollection(generator)

    def take(self, limit: int) -> "LazyCollection":
        def generator():
            yield from itertools.islice(self.get_iterator(), limit)

        return LazyCollection(generator)

    def take_while(self, callback: Callable) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                if not callback(item):
                    break
                yield item

        return LazyCollection(generator)

    def take_until(self, callback: Callable) -> "LazyCollection":
        return self.take_while(lambda item: not callback(item))

    def skip(self, count: int) -> "LazyCollection":
        def generator():
            skipped = 0
            for item in self.get_iterator():
                if skipped < count:
                    skipped += 1
                    continue
                yield item

        return LazyCollection(generator)

    def skip_while(self, callback: Callable) -> "LazyCollection":
        def generator():
            skip_mode = True
            for item in self.get_iterator():
                if skip_mode and callback(item):
                    continue
                skip_mode = False
                yield item

        return LazyCollection(generator)

    def skip_until(self, callback: Callable) -> "LazyCollection":
        return self.skip_while(lambda item: not callback(item))

    def chunk(self, size: int) -> "LazyCollection":
        def generator():
            chunk = []
            for item in self.get_iterator():
                chunk.append(item)
                if len(chunk) >= size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk

        return LazyCollection(generator)

    def chunk_while(self, callback: Callable) -> "LazyCollection":
        def generator():
            chunk = []
            prev_item = None
            for item in self.get_iterator():
                if prev_item is not None and not callback(item, prev_item):
                    yield chunk
                    chunk = []
                chunk.append(item)
                prev_item = item
            if chunk:
                yield chunk

        return LazyCollection(generator)

    def sliding(self, size: int = 2, step: int = 1) -> "LazyCollection":
        def generator():
            window = []
            iterator = self.get_iterator()

            for item in iterator:
                window.append(item)
                if len(window) == size:
                    yield list(window)
                    for _ in range(step):
                        if window:
                            window.pop(0)
                        else:
                            break

        return LazyCollection(generator)

    def tap(self, callback: Callable) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                callback(item)
                yield item

        return LazyCollection(generator)

    def each(self, callback: Callable) -> "LazyCollection":
        for item in self.get_iterator():
            callback(item)
        return self

    def flatten(self, depth: int = float("inf")) -> "LazyCollection":
        def generator():
            def flatten_recursive(items, current_depth):
                for item in items:
                    if isinstance(item, (list, tuple)) and current_depth > 0:
                        yield from flatten_recursive(item, current_depth - 1)
                    else:
                        yield item

            yield from flatten_recursive(self.get_iterator(), depth)

        return LazyCollection(generator)

    def unique(self, key: Optional[Callable] = None) -> "LazyCollection":
        def generator():
            seen = set()
            for item in self.get_iterator():
                value = key(item) if key else item
                if isinstance(value, (list, dict)):
                    value = str(value)
                if value not in seen:
                    seen.add(value)
                    yield item

        return LazyCollection(generator)

    def values(self) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                if isinstance(item, dict):
                    yield from item.values()
                else:
                    yield item

        return LazyCollection(generator)

    def keys(self) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                if isinstance(item, dict):
                    yield from item.keys()

        return LazyCollection(generator)

    def zip(self, *iterables) -> "LazyCollection":
        def generator():
            for items in zip(self.get_iterator(), *iterables):
                yield items

        return LazyCollection(generator)

    def remember(self) -> "LazyCollection":
        cached = []
        original_iterator = self.get_iterator()
        consumed = False

        def generator():
            nonlocal consumed

            for item in cached:
                yield item

            if not consumed:
                for item in original_iterator:
                    cached.append(item)
                    yield item
                consumed = True

        return LazyCollection(generator)

    def eager(self) -> "Collection":
        from larapy.database.orm.collection import Collection

        return Collection(list(self.get_iterator()))

    def all(self) -> list:
        return list(self.get_iterator())

    def to_list(self) -> list:
        return self.all()

    def count(self) -> int:
        return sum(1 for _ in self.get_iterator())

    def first(self, callback: Callable = None, default: Any = None) -> Any:
        for item in self.get_iterator():
            if callback is None or callback(item):
                return item
        return default

    def last(self, callback: Callable = None, default: Any = None) -> Any:
        result = default
        for item in self.get_iterator():
            if callback is None or callback(item):
                result = item
        return result

    def is_empty(self) -> bool:
        try:
            next(self.get_iterator())
            return False
        except StopIteration:
            return True

    def is_not_empty(self) -> bool:
        return not self.is_empty()

    def contains(self, value_or_callback: Union[Any, Callable]) -> bool:
        if callable(value_or_callback):
            for item in self.get_iterator():
                if value_or_callback(item):
                    return True
            return False
        else:
            for item in self.get_iterator():
                if item == value_or_callback:
                    return True
            return False

    def pluck(self, key: str) -> "LazyCollection":
        def generator():
            for item in self.get_iterator():
                if isinstance(item, dict):
                    yield item.get(key)
                elif hasattr(item, key):
                    yield getattr(item, key)
                elif hasattr(item, "get_attribute"):
                    yield item.get_attribute(key)

        return LazyCollection(generator)

    def sum(self, key: Optional[str] = None) -> Union[int, float]:
        if key:
            return sum(
                (
                    item.get(key, 0)
                    if isinstance(item, dict)
                    else (
                        getattr(item, key, 0)
                        if hasattr(item, key)
                        else item.get_attribute(key) if hasattr(item, "get_attribute") else 0
                    )
                )
                for item in self.get_iterator()
            )
        return sum(self.get_iterator())

    def avg(self, key: Optional[str] = None) -> Optional[float]:
        total = 0
        count = 0

        for item in self.get_iterator():
            if key:
                if isinstance(item, dict):
                    value = item.get(key, 0)
                elif hasattr(item, key):
                    value = getattr(item, key, 0)
                elif hasattr(item, "get_attribute"):
                    value = item.get_attribute(key)
                else:
                    value = 0
            else:
                value = item

            total += value
            count += 1

        return total / count if count > 0 else None

    def min(self, key: Optional[str] = None) -> Any:
        min_value = None

        for item in self.get_iterator():
            if key:
                if isinstance(item, dict):
                    value = item.get(key)
                elif hasattr(item, key):
                    value = getattr(item, key)
                elif hasattr(item, "get_attribute"):
                    value = item.get_attribute(key)
                else:
                    continue
            else:
                value = item

            if min_value is None or (value is not None and value < min_value):
                min_value = value

        return min_value

    def max(self, key: Optional[str] = None) -> Any:
        max_value = None

        for item in self.get_iterator():
            if key:
                if isinstance(item, dict):
                    value = item.get(key)
                elif hasattr(item, key):
                    value = getattr(item, key)
                elif hasattr(item, "get_attribute"):
                    value = item.get_attribute(key)
                else:
                    continue
            else:
                value = item

            if max_value is None or (value is not None and value > max_value):
                max_value = value

        return max_value

    @staticmethod
    def make(source) -> "LazyCollection":
        return LazyCollection(source)

    @staticmethod
    def times(count: int, callback: Callable = None) -> "LazyCollection":
        def generator():
            for i in range(count):
                yield callback(i + 1) if callback else i + 1

        return LazyCollection(generator)

    @staticmethod
    def range(start: int, end: int, step: int = 1) -> "LazyCollection":
        return LazyCollection(range(start, end + 1, step))

    def __iter__(self):
        return self.get_iterator()

    def __repr__(self):
        return "LazyCollection(<generator>)"
