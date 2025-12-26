from __future__ import annotations

import random
from typing import List

from leddisplay.framebuffer import Color, MatrixFramebuffer
from leddisplay.games.base import MatrixGame


class LifeGame(MatrixGame):
    """Conway's Game of Life on a 2D grid.
    """

    def __init__(
        self,
        width: int,
        height: int,
        seconds_per_tick: float = 0.2,
        wrap_edges: bool = True,
    ) -> None:
        super().__init__(width, height)
        self.seconds_per_tick = seconds_per_tick
        self.wrap_edges = wrap_edges

        self.alive_color: Color = (0, 255, 0)
        self.dead_color: Color = (0, 0, 0)

        self._tick_accumulator: float = 0.0
        self._grid: List[bool] = [False] * (width * height)
        self._next_grid: List[bool] = [False] * (width * height)

    def reset(self) -> None:
        """Reset to an initial state (e.g. clear or randomize later)."""
        for i in range(self.width * self.height):
            self._grid[i] = False
            self._next_grid[i] = False

    def update(self, dt: float) -> None:
        """Accumulate time and step the simulation when needed.

        The stepping logic will be added later.
        """
        self._tick_accumulator += dt
        if self._tick_accumulator >= self.seconds_per_tick:
            self._tick_accumulator -= self.seconds_per_tick
            self.step()

    def step(self) -> None:
        """Advance the Game of Life by one generation.
        """
        w = self.width
        h = self.height

        def is_alive(x: int, y: int) -> bool:
            if self.wrap_edges:
                x_mod = x % w
                y_mod = y % h
                return self._grid[y_mod * w + x_mod]
            if 0 <= x < w and 0 <= y < h:
                return self._grid[y * w + x]
            return False

        total_cells = w * h
        for index in range(total_cells):
            y = index // w
            x = index % w

            # Count live neighbours
            neighbours = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    if is_alive(x + dx, y + dy):
                        neighbours += 1

            alive = self._grid[index]
            # Conway's rules
            if alive:
                self._next_grid[index] = neighbours == 2 or neighbours == 3
            else:
                self._next_grid[index] = neighbours == 3

        # Swap grids so _grid always holds the current generation
        self._grid, self._next_grid = self._next_grid, self._grid

    def render(self, framebuffer: MatrixFramebuffer) -> None:
        """Render the current generation into the framebuffer.

        Alive cells use alive_color, dead cells use dead_color.
        """
        for y in range(self.height):
            for x in range(self.width):
                index = y * self.width + x
                color = self.alive_color if self._grid[index] else self.dead_color
                framebuffer.set_pixel(x, y, color)

    def set_cell(self, x: int, y: int, alive: bool) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            index = y * self.width + x
            self._grid[index] = alive

    def toggle_cell(self, x: int, y: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            index = y * self.width + x
            self._grid[index] = not self._grid[index]

    def randomize(self, density: float = 0.3) -> None:
        """Fill the grid with random live cells at the given probability.
        """
        total = self.width * self.height
        for i in range(total):
            self._grid[i] = random.random() < density
