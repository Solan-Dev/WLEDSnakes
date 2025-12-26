from __future__ import annotations

import time

from leddisplay.display import MatrixDisplay
from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.games.snake import DOWN, LEFT, RIGHT, UP, SnakeGame
from leddisplay.input import poll_key


def run_snake(
    display: MatrixDisplay,
    tick_seconds: float = 0.3,
) -> None:
    """Run the interactive Snake game on the LED matrix."""

    framebuffer = MatrixFramebuffer(display.width, display.height)
    game = SnakeGame(display.width, display.height, seconds_per_tick=tick_seconds)

    framebuffer.clear((0, 0, 0))
    framebuffer.clear_dirty()

    game.render(framebuffer)
    display.show(framebuffer)

    last_time = time.monotonic()
    last_state = (game.started, game.paused, game.running, game.snake, game.apple)

    while game.running:
        now = time.monotonic()
        dt = now - last_time
        last_time = now

        key: str | None = None
        while True:
            next_key = poll_key()
            if next_key is None:
                break
            key = next_key

        if key is not None:
            key_actions = {
                "w": lambda: game.request_direction(UP),
                "a": lambda: game.request_direction(LEFT),
                "s": lambda: game.request_direction(DOWN),
                "d": lambda: game.request_direction(RIGHT),
                "p": game.toggle_pause,
                "q": game.quit,
            }
            action = key_actions.get(key)
            if action is not None:
                action()

        game.update(dt)

        state = (game.started, game.paused, game.running, game.snake, game.apple)
        if state != last_state:
            last_state = state
            game.render(framebuffer)
            display.show(framebuffer)

        time.sleep(0.005)

    display.clear()
