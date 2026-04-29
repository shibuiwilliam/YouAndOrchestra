"""Generator registry — strategy pattern for composition generators.

Allows selecting generators by name in composition specs, enabling
same spec + different strategy = different output (PROJECT_IMPROVEMENT §5.1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yao.errors import SpecValidationError

if TYPE_CHECKING:
    from yao.generators.base import GeneratorBase

_REGISTRY: dict[str, type[GeneratorBase]] = {}


def register_generator(name: str) -> Any:
    """Decorator to register a generator class by name.

    Args:
        name: Unique name for the generator (e.g., "rule_based", "stochastic").

    Returns:
        Decorator that registers the class.

    Example:
        @register_generator("rule_based")
        class RuleBasedGenerator(GeneratorBase): ...
    """

    def decorator(cls: type[GeneratorBase]) -> type[GeneratorBase]:
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_generator(name: str) -> GeneratorBase:
    """Instantiate a generator by its registered name.

    Args:
        name: Registered generator name.

    Returns:
        A new generator instance.

    Raises:
        SpecValidationError: If no generator is registered with the given name.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise SpecValidationError(
            f"Unknown generator '{name}'. Available: {available}",
            field="generation.strategy",
        )
    return cls()


def available_generators() -> list[str]:
    """Return sorted list of registered generator names."""
    return sorted(_REGISTRY.keys())
