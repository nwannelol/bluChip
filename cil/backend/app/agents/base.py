"""Base agent abstract class.

All CIL agents (Fan, Media, Scout, Ops) must inherit from BaseAgent
and implement the `process` method.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for all CIL agents."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Process an incoming message and return an updated state.

        Args:
            state: The CILState dictionary.

        Returns:
            Updated CILState dictionary with agent_response populated.
        """
        ...

    @property
    def is_stub(self) -> bool:
        """Whether this agent is a stub (not fully implemented)."""
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
