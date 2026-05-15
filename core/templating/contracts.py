from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderer(Protocol):
    def render(self, template: str, context: dict) -> str: ...
