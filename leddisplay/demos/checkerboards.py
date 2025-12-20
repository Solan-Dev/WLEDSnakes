from __future__ import annotations

import time
from typing import List, Tuple

from leddisplay.wled_controller import WLEDController
from leddisplay.matrix_mapping import xy_to_index

Color = Tuple[int, int, int]


def _make_checkerboard(width: int,
                       height: int,
                       color1: Color,
                       color2: Color,
                       serpentine: bool) -> List[Color]:
    pixels: List[Color] = [(0, 0, 0)] * (width * height)
    for y in range(height):
        for x in range(width):
            c = color1 if (x + y) % 2 == 0 else color2
            idx = xy_to_index(x, y, width, height, serpentine=serpentine)
            pixels[idx] = c
    return pixels


def run_checkerboards(controller: WLEDController,
                      width: int,
                      height: int,
                      serpentine: bool = False) -> None:
    """Show a couple of checkerboard patterns using per-pixel control.

    For WLED 2D matrices, we normally treat the grid as non-serpentine here
    and let WLED handle the underlying zig-zag wiring.
    """
    checker1 = _make_checkerboard(width, height, (0, 255, 0), (0, 0, 0), serpentine)
    controller.set_pixels(checker1)
    time.sleep(1.0)

    checker2 = _make_checkerboard(width, height, (0, 0, 255), (255, 128, 0), serpentine)
    controller.set_pixels(checker2)
    time.sleep(1.0)
