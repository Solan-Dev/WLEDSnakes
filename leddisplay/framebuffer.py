from __future__ import annotations

from typing import List, Set, Tuple


Color = Tuple[int, int, int]


class MatrixFramebuffer:
    """In-memory representation of the LED matrix.

    Stores a 2D grid of colors in *logical* row-major order.

    This class intentionally knows nothing about the panel's physical wiring.
    Mapping from (x, y) -> physical LED index is handled by the display/output
    layer (see `leddisplay.display.MatrixDisplay`).
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._pixels: List[Color] = [(0, 0, 0)] * (width * height)
        self._dirty: Set[int] = set()  # Track changed pixel indices

    def clear(self, color: Color = (0, 0, 0)) -> None:
        """Clear the whole framebuffer to a single color."""
        self._pixels = [color] * (self.width * self.height)
        # Mark all as dirty since we changed everything
        self._dirty = set(range(self.width * self.height))

    def fill(self, color: Color) -> None:
        """Alias for clear, provided for readability."""
        self.clear(color)

    def set_pixel(self, x: int, y: int, color: Color) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Out of bounds: x={x}, y={y}, width={self.width}, height={self.height}")
        idx = y * self.width + x
        if self._pixels[idx] != color:
            self._pixels[idx] = color
            self._dirty.add(idx)

    def get_pixel(self, x: int, y: int) -> Color:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Out of bounds: x={x}, y={y}, width={self.width}, height={self.height}")
        return self._pixels[y * self.width + x]

    def get_dirty_pixels(self) -> List[Tuple[int, Color]]:
        """Return list of (logical_index, color) for all dirty pixels."""
        return [(idx, self._pixels[idx]) for idx in sorted(self._dirty)]

    def clear_dirty(self) -> None:
        """Clear the dirty flag set after changes have been sent."""
        self._dirty.clear()
