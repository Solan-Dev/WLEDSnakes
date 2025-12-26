from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from leddisplay.framebuffer import Color, MatrixFramebuffer
from leddisplay.games.base import MatrixGame


Point = Tuple[int, int]
Direction = Tuple[int, int]


UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)


def _is_opposite(a: Direction, b: Direction) -> bool:
    return a[0] == -b[0] and a[1] == -b[1]


@dataclass(frozen=True)
class SnakeColors:
    background: Color = (0, 0, 0)
    head: Color = (255, 255, 0)   # yellow
    body: Color = (255, 165, 0)   # orange
    apple: Color = (0, 255, 0)    # green


class SnakeGame(MatrixGame):
    """Classic Snake on a logical grid.

    Rules:
    - Moves exactly 1 cell per tick.
    - Dies on wall collision.
    - Dies on self-collision.
    - Disallows 180° turns (opposite direction inputs are ignored).
    - Eating an apple grows the snake by 1 segment.
    - 'p' toggles pause; 'q' quits.
    """

    def __init__(
        self,
        width: int,
        height: int,
        seconds_per_tick: float = 0.3,
        start_on_first_input: bool = True,
        rng: Optional[random.Random] = None,
        initial_snake: Optional[Sequence[Point]] = None,
        initial_direction: Direction = RIGHT,
        initial_apple: Optional[Point] = None,
        colors: SnakeColors = SnakeColors(),
    ) -> None:
        super().__init__(width, height)
        self.seconds_per_tick = float(seconds_per_tick)
        self.start_on_first_input = bool(start_on_first_input)
        self.colors = colors

        self._rng = rng or random.Random()

        self.paused: bool = False
        self.started: bool = False
        self._tick_accumulator: float = 0.0

        self._direction: Direction = initial_direction
        self._pending_direction: Direction = initial_direction

        self._snake: List[Point] = []
        self._apple: Point = (0, 0)

        self._initial_snake = list(initial_snake) if initial_snake is not None else None
        self._initial_apple = initial_apple
        self._initial_direction = initial_direction

        # Track previous render state to enable incremental updates
        self._last_rendered_snake: List[Point] = []
        self._last_rendered_apple: Point | None = None

        self.reset()

    def reset(self) -> None:
        self.running = True
        self.paused = False
        self.started = not self.start_on_first_input
        self._tick_accumulator = 0.0

        if self._initial_snake is not None:
            self._snake = list(self._initial_snake)
        else:
            # Default: single-segment snake centered on the display.
            # This avoids a “first move can instantly collide with body” problem
            # and guarantees any initial WASD direction is valid.
            cx = self.width // 2
            cy = self.height // 2
            self._snake = [(cx, cy)]

        self._direction = self._initial_direction
        self._pending_direction = self._initial_direction

        if self._initial_apple is not None:
            self._apple = self._initial_apple
        else:
            self._apple = self._spawn_apple()
        
        # Clear previous render state
        self._last_rendered_snake = []
        self._last_rendered_apple = None

    def update(self, dt: float) -> None:
        if not self.running:
            return
        if self.paused:
            return
        if not self.started:
            return

        self._tick_accumulator += dt
        while self._tick_accumulator >= self.seconds_per_tick and self.running and not self.paused:
            self._tick_accumulator -= self.seconds_per_tick
            self.step()

    def step(self) -> None:
        # Apply latest legal direction at tick boundary
        self._direction = self._pending_direction

        head_x, head_y = self._snake[0]
        dx, dy = self._direction
        new_head = (head_x + dx, head_y + dy)

        # Wall collision
        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.running = False
            return

        # Self collision (note: moving into the tail is allowed only if the tail moves away;
        # easiest correct approach: compute next snake and then check duplicates.)
        eating = new_head == self._apple

        new_snake: List[Point] = [new_head] + list(self._snake)
        if not eating:
            new_snake.pop()  # tail moves

        if len(set(new_snake)) != len(new_snake):
            self.running = False
            return

        self._snake = new_snake

        if eating:
            self._apple = self._spawn_apple()

    def render(self, framebuffer: MatrixFramebuffer) -> None:
        """Render only changed pixels for optimal DDP sparse updates."""
        # Clear old apple position if it moved
        if self._last_rendered_apple is not None and self._last_rendered_apple != self._apple:
            old_ax, old_ay = self._last_rendered_apple
            if 0 <= old_ax < framebuffer.width and 0 <= old_ay < framebuffer.height:
                framebuffer.set_pixel(old_ax, old_ay, self.colors.background)
        
        # Clear old snake positions that are no longer occupied
        current_snake_set = set(self._snake)
        for old_x, old_y in self._last_rendered_snake:
            if (old_x, old_y) not in current_snake_set:
                if 0 <= old_x < framebuffer.width and 0 <= old_y < framebuffer.height:
                    framebuffer.set_pixel(old_x, old_y, self.colors.background)
        
        # Draw new apple position
        ax, ay = self._apple
        if 0 <= ax < framebuffer.width and 0 <= ay < framebuffer.height:
            framebuffer.set_pixel(ax, ay, self.colors.apple)
        
        if self._snake:
            # Draw head
            hx, hy = self._snake[0]
            framebuffer.set_pixel(hx, hy, self.colors.head)
            
            # Draw body
            for (x, y) in self._snake[1:]:
                framebuffer.set_pixel(x, y, self.colors.body)
        
        # Update tracking
        self._last_rendered_snake = list(self._snake)
        self._last_rendered_apple = self._apple

    def request_direction(self, direction: Direction) -> None:
        """Request a direction change.

        Opposite direction (180° turn) requests are ignored.
        """
        if direction not in (UP, DOWN, LEFT, RIGHT):
            return

        # If configured, the first valid direction input starts the game.
        if self.start_on_first_input and not self.started:
            self.started = True
            self._direction = direction
            self._pending_direction = direction
            return

        # Use the current direction (not pending) for 180° checks.
        if _is_opposite(self._direction, direction):
            return

        self._pending_direction = direction

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def quit(self) -> None:
        self.running = False

    @property
    def snake(self) -> Tuple[Point, ...]:
        return tuple(self._snake)

    @property
    def apple(self) -> Point:
        return self._apple

    def _spawn_apple(self) -> Point:
        free: List[Point] = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self._snake
        ]
        if not free:
            # Filled board: treat as win/stop.
            self.running = False
            return self._snake[0]
        return self._rng.choice(free)
