from __future__ import annotations

import time

from leddisplay.display import MatrixDisplay
from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.scenes.base import MatrixScene
from leddisplay.scenes.fireplace import FireplaceScene
from leddisplay.scenes.snowfall import SnowfallScene


def run_scene(
    display: MatrixDisplay,
    scene: MatrixScene,
    *,
    target_fps: float = 30.0,
) -> None:
    framebuffer = MatrixFramebuffer(display.width, display.height)
    framebuffer.clear()
    scene.reset()

    frame_interval = 1.0 / target_fps if target_fps > 0 else 0.0
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            scene.step(framebuffer, dt)
            display.show(framebuffer)

            if frame_interval > 0:
                elapsed = time.monotonic() - now
                sleep_for = frame_interval - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)
    except KeyboardInterrupt:
        display.clear()


def run_fireplace(display: MatrixDisplay, *, target_fps: float = 30.0) -> None:
    scene = FireplaceScene(display.width, display.height)
    run_scene(display, scene, target_fps=target_fps)


def run_snowfall(display: MatrixDisplay, *, target_fps: float = 30.0) -> None:
    scene = SnowfallScene(display.width, display.height)
    run_scene(display, scene, target_fps=target_fps)
