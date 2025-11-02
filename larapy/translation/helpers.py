from typing import Dict, Optional, Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from larapy.translation.translator import Translator

_translator: Optional["Translator"] = None


def set_translator(translator: "Translator") -> None:
    global _translator
    _translator = translator


def get_translator() -> Optional["Translator"]:
    return _translator


def trans(key: str, replace: Optional[Dict[str, Any]] = None, locale: Optional[str] = None) -> str:
    if _translator is None:
        return key
    return _translator.get(key, replace, locale)


def __(key: str, replace: Optional[Dict[str, Any]] = None, locale: Optional[str] = None) -> str:
    return trans(key, replace, locale)


def trans_choice(
    key: str,
    count: Union[int, float],
    replace: Optional[Dict[str, Any]] = None,
    locale: Optional[str] = None,
) -> str:
    if _translator is None:
        return key
    return _translator.choice(key, count, replace, locale)


def get_locale() -> str:
    if _translator is None:
        return "en"
    return _translator.get_locale()


def set_locale(locale: str) -> None:
    if _translator is not None:
        _translator.set_locale(locale)


def has_trans(key: str, locale: Optional[str] = None) -> bool:
    if _translator is None:
        return False
    return _translator.has(key, locale)


def get_fallback() -> str:
    if _translator is None:
        return "en"
    return _translator.get_fallback()


def set_fallback(fallback: str) -> None:
    if _translator is not None:
        _translator.set_fallback(fallback)
