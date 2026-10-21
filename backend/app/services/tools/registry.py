from typing import Any, Callable


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not registered."""

    pass


class ToolRegistry:
    """
    Central registry for tools that AgentShield is allowed to execute.

    The registry creates a controlled mapping between a tool name and
    the actual callable that performs the operation.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, tool: Callable[..., Any]) -> None:
        """Register a tool under a specific name."""
        if not name:
            raise ValueError("Tool name cannot be empty")

        self._tools[name] = tool

    def get(self, name: str) -> Callable[..., Any]:
        """Return a registered tool by name."""
        try:
            return self._tools[name]
        except KeyError:
            raise ToolNotFoundError(
                f"Tool '{name}' is not registered"
            )

    def has(self, name: str) -> bool:
        """Check whether a tool is registered."""
        return name in self._tools

    def list_tools(self) -> list[str]:
        """Return all registered tool names."""
        return sorted(self._tools.keys())