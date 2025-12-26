from __future__ import annotations

from abc import ABC, abstractmethod

from leddisplay.framebuffer import MatrixFramebuffer


class MatrixGame(ABC):
    """Base class for matrix-based games.

    Games operate on a logical width/height grid and render into a
    MatrixFramebuffer, but do not know about WLED or I/O.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.running: bool = True

    @abstractmethod
    def reset(self) -> None:
        """Reset internal game state to a starting configuration."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance game state by dt seconds."""

    @abstractmethod
    def render(self, framebuffer: MatrixFramebuffer) -> None:
        """Draw the current state into the framebuffer."""

    def handle_input(self, event: object) -> None:  # pragma: no cover - placeholder
        """Handle an input event (optional for games that need input)."""
        return
