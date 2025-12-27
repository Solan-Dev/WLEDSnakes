from __future__ import annotations

import random
from typing import List, Sequence, Tuple

from leddisplay.framebuffer import Color, MatrixFramebuffer
from leddisplay.scenes.base import MatrixScene


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_color(c1: Color, c2: Color, t: float) -> Color:
    return (
        int(_lerp(c1[0], c2[0], t)),
        int(_lerp(c1[1], c2[1], t)),
        int(_lerp(c1[2], c2[2], t)),
    )


class FireplaceScene(MatrixScene):
    """Procedural fireplace based on the classic "doom fire" algorithm.

    A heat buffer is diffused upward each tick, with the bottom row reseeded with
    fresh heat values. A precomputed 256-color palette maps intensities to RGB.
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        base_heat_range: Tuple[int, int] = (180, 255),
        cooling: int = 3,
        spark_probability: float = 0.02,
        target_fps: float = 45.0,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(width, height)
        if width <= 0 or height <= 0:
            raise ValueError("Scene dimensions must be positive")

        self._rng = rng or random.Random()
        self._base_heat_min, self._base_heat_max = base_heat_range
        self._cooling = max(1, cooling)
        self._spark_probability = max(0.0, min(1.0, spark_probability))
        self._frame_interval = 1.0 / target_fps if target_fps > 0 else 0.0

        self._heat: List[int] = [0] * (width * height)
        self._scratch: List[int] = [0] * (width * height)
        self._palette: List[Color] = self._build_palette()
        self._accumulator = 0.0

    def reset(self) -> None:
        self._heat = [0] * (self.width * self.height)
        self._scratch = [0] * (self.width * self.height)
        self._accumulator = 0.0

    def step(self, framebuffer: MatrixFramebuffer, dt: float) -> None:
        if dt < 0:
            dt = 0.0

        advanced = False
        if self._frame_interval > 0.0:
            self._accumulator += dt
            while self._accumulator >= self._frame_interval:
                self._advance_fire()
                self._accumulator -= self._frame_interval
                advanced = True
        else:
            self._advance_fire()
            advanced = True

        if advanced:
            self._render_to_framebuffer(framebuffer)

    def _advance_fire(self) -> None:
        width = self.width
        height = self.height
        last_row_start = (height - 1) * width

        for x in range(width):
            seed_value = self._rng.randint(self._base_heat_min, self._base_heat_max)
            self._heat[last_row_start + x] = seed_value

        for y in range(height - 1):
            for x in range(width):
                idx = y * width + x
                below = self._heat[(y + 1) * width + x]
                below_left = self._heat[(y + 1) * width + (x - 1) % width]
                below_right = self._heat[(y + 1) * width + (x + 1) % width]
                two_below_y = min(height - 1, y + 2)
                two_below = self._heat[two_below_y * width + x]

                average = (below + below_left + below_right + two_below) >> 2
                decay = self._rng.randint(0, self._cooling)
                value = max(0, average - decay)

                if value > 200 and self._rng.random() < self._spark_probability:
                    value = min(255, value + 25)

                self._scratch[idx] = value

        for x in range(width):
            idx = last_row_start + x
            self._scratch[idx] = self._heat[idx]

        self._heat, self._scratch = self._scratch, self._heat

    def _render_to_framebuffer(self, framebuffer: MatrixFramebuffer) -> None:
        width = self.width
        for idx, value in enumerate(self._heat):
            x = idx % width
            y = idx // width
            color = self._palette[value]
            framebuffer.set_pixel(x, y, color)

    def _build_palette(self) -> List[Color]:
        gradient_stops: Sequence[Tuple[float, Color]] = (
            (0.0, (0, 0, 0)),
            (0.2, (32, 0, 0)),
            (0.35, (180, 20, 0)),
            (0.55, (255, 80, 0)),
            (0.75, (255, 180, 0)),
            (0.9, (255, 235, 128)),
            (1.0, (255, 255, 255)),
        )
        palette: List[Color] = []
        for i in range(256):
            t = i / 255.0
            for idx in range(len(gradient_stops) - 1):
                left_pos, left_color = gradient_stops[idx]
                right_pos, right_color = gradient_stops[idx + 1]
                if left_pos <= t <= right_pos:
                    span = right_pos - left_pos or 1.0
                    local_t = (t - left_pos) / span
                    palette.append(_lerp_color(left_color, right_color, local_t))
                    break
        if len(palette) < 256:
            palette.extend([gradient_stops[-1][1]] * (256 - len(palette)))
        return palette
