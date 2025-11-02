from typing import Dict, Optional, Any, Union, Callable
import re


class Translator:

    def __init__(self, loader, locale: str = "en"):
        self.loader = loader
        self.locale = locale
        self.fallback = "en"
        self.selector = MessageSelector()

    def get(
        self, key: str, replace: Optional[Dict[str, Any]] = None, locale: Optional[str] = None
    ) -> str:
        locale = locale or self.locale

        line = self._retrieve(locale, key)

        if line is None and locale != self.fallback:
            line = self._retrieve(self.fallback, key)

        if line is None:
            return key

        return self._make_replacements(str(line), replace or {})

    def _retrieve(self, locale: str, key: str) -> Optional[Any]:
        namespace, group, item = self._parse_key(key)

        translations = self.loader.load(locale, group, namespace)

        if not translations:
            return None

        return self._get_nested(translations, item)

    def _parse_key(self, key: str) -> tuple:
        if "::" in key:
            namespace, key = key.split("::", 1)
        else:
            namespace = None

        if "." in key:
            parts = key.split(".", 1)
            group = parts[0]
            item = parts[1] if len(parts) > 1 else None
        else:
            group = key
            item = None

        return namespace, group, item

    def _get_nested(self, data: Dict, key: Optional[str]) -> Optional[Any]:
        if key is None:
            return data

        parts = key.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _make_replacements(self, line: str, replace: Dict[str, Any]) -> str:
        if not replace:
            return line

        result = line
        for key, value in replace.items():
            placeholder = f":{key}"
            result = result.replace(placeholder, str(value))

            placeholder_upper = f":{key.upper()}"
            if placeholder_upper in result:
                result = result.replace(placeholder_upper, str(value).upper())

            placeholder_title = f":{key.title()}"
            if placeholder_title in result:
                result = result.replace(placeholder_title, str(value).title())

        return result

    def choice(
        self,
        key: str,
        count: Union[int, float],
        replace: Optional[Dict[str, Any]] = None,
        locale: Optional[str] = None,
    ) -> str:
        line = self.get(key, replace, locale)

        replace = replace or {}
        replace["count"] = count

        return self._make_replacements(
            self.selector.choose(line, count, locale or self.locale), replace
        )

    def has(self, key: str, locale: Optional[str] = None, fallback: bool = True) -> bool:
        locale = locale or self.locale

        result = self._retrieve(locale, key) is not None

        if not result and fallback and locale != self.fallback:
            result = self._retrieve(self.fallback, key) is not None

        return result

    def get_locale(self) -> str:
        return self.locale

    def set_locale(self, locale: str) -> None:
        self.locale = locale

    def get_fallback(self) -> str:
        return self.fallback

    def set_fallback(self, fallback: str) -> None:
        self.fallback = fallback

    def add_lines(
        self, lines: Dict[str, str], locale: str, namespace: Optional[str] = None
    ) -> None:
        group = "runtime"
        for key, value in lines.items():
            full_key = self.loader._get_cache_key(locale, f"{group}.{key}", namespace)
            self.loader._cache[full_key] = value

    def add_namespace(self, namespace: str, hint: str) -> None:
        self.loader.add_namespace(namespace, hint)


class MessageSelector:

    def choose(self, line: str, count: Union[int, float], locale: str) -> str:
        if "|" not in line:
            return line

        segments = self._extract_segments(line)

        value = self._get_plural_index(count, locale)

        if len(segments) == 1:
            return segments[0]

        for segment in segments:
            stripped = segment.strip()

            if self._is_exact_match(stripped, count):
                return self._strip_conditions(stripped)

            if self._is_range_match(stripped, count):
                return self._strip_conditions(stripped)

        if value < len(segments):
            return self._strip_conditions(segments[value])

        return self._strip_conditions(segments[-1])

    def _extract_segments(self, line: str) -> list:
        return [segment.strip() for segment in line.split("|")]

    def _is_exact_match(self, segment: str, count: Union[int, float]) -> bool:
        if segment.startswith("{") and "}" in segment:
            condition = segment[1 : segment.index("}")]
            return str(count) == condition
        return False

    def _is_range_match(self, segment: str, count: Union[int, float]) -> bool:
        if segment.startswith("[") and "]" in segment:
            condition = segment[1 : segment.index("]")]
            if "," in condition:
                parts = condition.split(",")
                start = parts[0].strip()
                end = parts[1].strip()

                if start == "*":
                    start_val = float("-inf")
                else:
                    try:
                        start_val = float(start)
                    except ValueError:
                        return False

                if end == "*":
                    end_val = float("inf")
                else:
                    try:
                        end_val = float(end)
                    except ValueError:
                        return False

                return start_val <= count <= end_val
        return False

    def _strip_conditions(self, segment: str) -> str:
        segment = segment.strip()

        if segment.startswith("{") and "}" in segment:
            return segment[segment.index("}") + 1 :].strip()

        if segment.startswith("[") and "]" in segment:
            return segment[segment.index("]") + 1 :].strip()

        return segment

    def _get_plural_index(self, count: Union[int, float], locale: str) -> int:
        count = abs(count)

        base_locale = locale.split("_")[0].split("-")[0].lower()

        if base_locale in ("en", "de", "nl", "sv", "da", "no", "nn", "nb", "fo", "es", "it", "pt"):
            return 0 if count == 1 else 1

        if base_locale in ("fr", "br"):
            return 0 if count <= 1 else 1

        if base_locale in ("lv",):
            if count % 10 == 1 and count % 100 != 11:
                return 0
            elif count != 0:
                return 1
            else:
                return 2

        if base_locale in ("ga", "gd"):
            if count == 1:
                return 0
            elif count == 2:
                return 1
            else:
                return 2

        if base_locale in ("ro", "mo"):
            if count == 1:
                return 0
            elif count == 0 or (1 < count % 100 < 20):
                return 1
            else:
                return 2

        if base_locale in ("lt",):
            if count % 10 == 1 and count % 100 != 11:
                return 0
            elif count % 10 >= 2 and (count % 100 < 10 or count % 100 >= 20):
                return 1
            else:
                return 2

        if base_locale in ("ru", "uk", "be", "sr", "hr", "cs", "sk"):
            if count % 10 == 1 and count % 100 != 11:
                return 0
            elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
                return 1
            else:
                return 2

        if base_locale in ("pl",):
            if count == 1:
                return 0
            elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
                return 1
            else:
                return 2

        if base_locale in ("sl",):
            if count % 100 == 1:
                return 0
            elif count % 100 == 2:
                return 1
            elif count % 100 in (3, 4):
                return 2
            else:
                return 3

        if base_locale in ("ar",):
            if count == 0:
                return 0
            elif count == 1:
                return 1
            elif count == 2:
                return 2
            elif 3 <= count % 100 <= 10:
                return 3
            elif 11 <= count % 100 <= 99:
                return 4
            else:
                return 5

        return 0 if count == 1 else 1
