from __future__ import annotations

import random

from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.scenes.fireplace import FireplaceScene


def test_fireplace_scene_generates_heat() -> None:
    scene = FireplaceScene(8, 8, rng=random.Random(1234))
    framebuffer = MatrixFramebuffer(8, 8)
    scene.reset()

    for _ in range(10):
        scene.step(framebuffer, 0.05)

    dirty_pixels = framebuffer.get_dirty_pixels()
    assert dirty_pixels, "Fireplace scene should update pixels"
    colors = {color for _, color in dirty_pixels}
    assert any(sum(color) > 0 for color in colors)
