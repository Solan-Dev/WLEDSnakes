from __future__ import annotations

import time

from leddisplay.display import MatrixDisplay
from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.games.life import LifeGame


def run_game_of_life(
    display: MatrixDisplay,
    tick_seconds: float = 0.2,
    run_seconds: float | None = None,
) -> None:
    """Run a simple Game of Life demo on the matrix.

    The game renders into a logical framebuffer; the display layer handles
    physical wiring/mapping.
    """
    framebuffer = MatrixFramebuffer(display.width, display.height)
    game = LifeGame(display.width, display.height, seconds_per_tick=tick_seconds, wrap_edges=False)
    game.reset()

    # Seed with a random initial pattern so the game actually evolves.
    game.randomize(density=0.3)

    start_time = time.time()
    last_time = start_time

    while game.running:
        now = time.time()
        dt = now - last_time
        last_time = now

        if run_seconds is not None and (now - start_time) >= run_seconds:
            break

        game.update(dt)
        game.render(framebuffer)

        # Push to WLED panel (if reachable)
        display.show(framebuffer)

        # Simple frame pacing; not exact but good enough for a demo
        time.sleep(0.05)
