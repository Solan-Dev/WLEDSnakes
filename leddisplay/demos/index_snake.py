from __future__ import annotations

import time
from typing import List, Tuple

from leddisplay.wled_controller import WLEDController
from leddisplay.matrix_mapping import xy_to_index

Color = Tuple[int, int, int]


def run_index_snake(controller: WLEDController,
                    width: int,
                    height: int,
                    delay_seconds: float = 0.03) -> None:
    """Walk a snake through the linear indices, turning LEDs orange.

    This ignores 2D position and just uses raw indices 0..N-1, which is
    useful for understanding the physical wiring order.
    """
    num_leds = width * height

    off: Color = (0, 0, 0)
    orange: Color = (255, 165, 0)

    pixels: List[Color] = [off] * num_leds
    controller.set_pixels(pixels)

    for idx in range(num_leds):
        pixels[idx] = orange
        controller.set_pixels(pixels)
        time.sleep(delay_seconds)


def run_row_snake(controller: WLEDController,
                  width: int,
                  height: int,
                  serpentine: bool = True,
                  delay_seconds: float = 0.03) -> None:
    """Traverse the panel row-by-row in logical 2D order.

    Goes across each row (x = 0..width-1), then down to the next row (y+1),
    until the entire width x height grid is filled with orange.

    Uses xy_to_index() so the visual path is a clean raster scan, even though
    the physical wiring is serpentine.
    """
    num_leds = width * height

    off: Color = (0, 0, 0)
    orange: Color = (255, 165, 0)

    pixels: List[Color] = [off] * num_leds
    controller.set_pixels(pixels)

    for y in range(height):
        for x in range(width):
            idx = xy_to_index(x, y, width, height, serpentine=serpentine)
            pixels[idx] = orange
            controller.set_pixels(pixels)
            time.sleep(delay_seconds)


def run_horizontal_serpentine_snake(controller: WLEDController,
                                    width: int,
                                    height: int,
                                    delay_seconds: float = 0.03) -> None:
    """Traverse the panel in horizontal serpentine rows.

    Visually: first row goes left->right across all 32 pixels, then move
    down one row, go right->left, and so on until the whole grid is filled.

    This assumes the underlying physical wiring is serpentine *per column*
    (8 LEDs tall) as on common 8x32 MAX7219-style modules.
    """

    def col_serpentine_xy_to_index(x: int, y: int) -> int:
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError("x/y out of bounds")
        # Even columns go top->bottom, odd columns bottom->top.
        if x % 2 == 0:
            return x * height + y
        return x * height + (height - 1 - y)

    num_leds = width * height
    off: Color = (0, 0, 0)
    orange: Color = (255, 165, 0)

    pixels: List[Color] = [off] * num_leds
    controller.set_pixels(pixels)

    for y in range(height):
        if y % 2 == 0:
            x_range = range(width)  # left -> right
        else:
            x_range = range(width - 1, -1, -1)  # right -> left

        for x in x_range:
            idx = col_serpentine_xy_to_index(x, y)
            pixels[idx] = orange
            controller.set_pixels(pixels)
            time.sleep(delay_seconds)
