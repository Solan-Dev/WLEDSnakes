from __future__ import annotations

import random

from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.scenes.snowfall import SnowfallScene


def test_snowfall_scene_generates_snow_pixels() -> None:
    scene = SnowfallScene(
        10,
        10,
        density=0.1,
        background_color=(0, 0, 0),
        target_fps=0.0,
        rng=random.Random(123),
    )
    framebuffer = MatrixFramebuffer(10, 10)
    scene.reset()

    for _ in range(12):
        scene.step(framebuffer, 0.05)

    dirty_pixels = framebuffer.get_dirty_pixels()
    assert dirty_pixels, "Snowfall scene should update pixels"
    assert any(color != (0, 0, 0) for _, color in dirty_pixels)


def test_snowfall_scene_builds_ground() -> None:
    scene = SnowfallScene(
        8,
        8,
        density=0.15,
        intensity_range=(1.0, 1.0),
        melt_rate=0.0,
        target_fps=0.0,
        rng=random.Random(42),
    )
    framebuffer = MatrixFramebuffer(8, 8)
    scene.reset()

    for _ in range(150):
        scene.step(framebuffer, 0.04)

    assert any(height > 0.0 for height in scene._ground_heights)
