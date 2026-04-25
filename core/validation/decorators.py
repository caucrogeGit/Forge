"""Decorateurs de validation V1 pour les proprietes d'entite."""

from __future__ import annotations

import re
from functools import wraps
from typing import Any, Callable

from .exceptions import ValidationError

Setter = Callable[..., Any]


def _property_name(func: Setter) -> str:
    return getattr(func, "__name__", "property")


def _raise(property_name: str, detail: str) -> None:
    raise ValidationError(property_name, f"La propriete '{property_name}' {detail}.")


def _mark_nullable(func: Setter) -> None:
    setattr(func, "_forge_nullable", True)


def _is_nullable(func: Setter) -> bool:
    return bool(getattr(func, "_forge_nullable", False))


def typed(expected_type: type) -> Callable[[Setter], Setter]:
    """Valide le type Python sans transformation implicite."""

    if not isinstance(expected_type, type):
        raise TypeError("typed() attend un type Python.")

    def decorator(func: Setter) -> Setter:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            value = args[1] if len(args) > 1 else kwargs.get("value")
            property_name = _property_name(func)

            if value is None:
                return func(*args, **kwargs)

            if expected_type is int and isinstance(value, bool):
                _raise(property_name, "doit etre de type int (bool est refuse)")

            if not isinstance(value, expected_type):
                _raise(property_name, f"doit etre de type {expected_type.__name__}")

            return func(*args, **kwargs)

        if _is_nullable(func):
            _mark_nullable(wrapper)
        return wrapper

    return decorator


def nullable(func: Setter) -> Setter:
    """Marque explicitement une propriete comme nullable."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    _mark_nullable(func)
    _mark_nullable(wrapper)
    return wrapper


def not_empty(func: Setter) -> Setter:
    """Refuse les chaines vides ou blanches."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        value = args[1] if len(args) > 1 else kwargs.get("value")
        property_name = _property_name(func)

        if value is not None:
            if not isinstance(value, str):
                _raise(property_name, "doit etre une chaine pour utiliser not_empty")
            if not value.strip():
                _raise(property_name, "ne doit pas etre vide")

        return func(*args, **kwargs)

    if _is_nullable(func):
        _mark_nullable(wrapper)
    return wrapper


def min_length(size: int) -> Callable[[Setter], Setter]:
    """Impose une longueur minimale sur une chaine."""

    if size < 0:
        raise ValueError("min_length() attend une taille positive ou nulle.")

    def decorator(func: Setter) -> Setter:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            value = args[1] if len(args) > 1 else kwargs.get("value")
            property_name = _property_name(func)

            if value is not None:
                if not isinstance(value, str):
                    _raise(property_name, "doit etre une chaine pour utiliser min_length")
                if len(value) < size:
                    _raise(property_name, f"doit contenir au moins {size} caracteres")

            return func(*args, **kwargs)

        if _is_nullable(func):
            _mark_nullable(wrapper)
        return wrapper

    return decorator


def max_length(size: int) -> Callable[[Setter], Setter]:
    """Impose une longueur maximale sur une chaine."""

    if size < 0:
        raise ValueError("max_length() attend une taille positive ou nulle.")

    def decorator(func: Setter) -> Setter:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            value = args[1] if len(args) > 1 else kwargs.get("value")
            property_name = _property_name(func)

            if value is not None:
                if not isinstance(value, str):
                    _raise(property_name, "doit etre une chaine pour utiliser max_length")
                if len(value) > size:
                    _raise(property_name, f"ne doit pas depasser {size} caracteres")

            return func(*args, **kwargs)

        if _is_nullable(func):
            _mark_nullable(wrapper)
        return wrapper

    return decorator


def min_value(limit: int | float) -> Callable[[Setter], Setter]:
    """Impose une valeur numerique minimale."""

    def decorator(func: Setter) -> Setter:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            value = args[1] if len(args) > 1 else kwargs.get("value")
            property_name = _property_name(func)

            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    _raise(property_name, "doit etre numerique pour utiliser min_value")
                if value < limit:
                    _raise(property_name, f"doit etre superieure ou egale a {limit}")

            return func(*args, **kwargs)

        if _is_nullable(func):
            _mark_nullable(wrapper)
        return wrapper

    return decorator


def max_value(limit: int | float) -> Callable[[Setter], Setter]:
    """Impose une valeur numerique maximale."""

    def decorator(func: Setter) -> Setter:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            value = args[1] if len(args) > 1 else kwargs.get("value")
            property_name = _property_name(func)

            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    _raise(property_name, "doit etre numerique pour utiliser max_value")
                if value > limit:
                    _raise(property_name, f"doit etre inferieure ou egale a {limit}")

            return func(*args, **kwargs)

        if _is_nullable(func):
            _mark_nullable(wrapper)
        return wrapper

    return decorator


def pattern(regex: str) -> Callable[[Setter], Setter]:
    """Impose une expression reguliere."""

    compiled = re.compile(regex)

    def decorator(func: Setter) -> Setter:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            value = args[1] if len(args) > 1 else kwargs.get("value")
            property_name = _property_name(func)

            if value is not None:
                if not isinstance(value, str):
                    _raise(property_name, "doit etre une chaine pour utiliser pattern")
                if compiled.fullmatch(value) is None:
                    _raise(property_name, f"doit respecter le motif {regex!r}")

            return func(*args, **kwargs)

        if _is_nullable(func):
            _mark_nullable(wrapper)
        return wrapper

    return decorator
