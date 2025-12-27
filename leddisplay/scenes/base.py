from __future__ import annotations

from typing import Protocol

from leddisplay.framebuffer import MatrixFramebuffer


class MatrixScene:
    """Base class for non-interactive scenes rendered on the matrix."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def reset(self) -> None:
        """Reset internal state to a known baseline."""
        pass

    def step(self, framebuffer: MatrixFramebuffer, dt: float) -> None:
        """Advance the scene by ``dt`` seconds and render to ``framebuffer``."""
        raise NotImplementedError