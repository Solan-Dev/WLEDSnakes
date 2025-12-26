from __future__ import annotations

import time
from typing import List, Tuple

from leddisplay.display import MatrixDisplay
from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.wled_controller import WLEDController

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


def run_row_snake(display: MatrixDisplay, delay_seconds: float = 0.03) -> None:
    """Traverse the panel row-by-row in logical 2D order.

    Goes across each row (x = 0..width-1), then down to the next row (y+1),
    until the entire width x height grid is filled with orange.

    Uses logical (x, y) coordinates; the display layer handles wiring.
    """
    off: Color = (0, 0, 0)
    orange: Color = (255, 165, 0)

    framebuffer = MatrixFramebuffer(display.width, display.height)
    framebuffer.clear(off)
    display.show(framebuffer)

    for y in range(display.height):
        for x in range(display.width):
            framebuffer.set_pixel(x, y, orange)
            display.show(framebuffer)
            time.sleep(delay_seconds)


def run_horizontal_serpentine_snake(display: MatrixDisplay, delay_seconds: float = 0.03) -> None:
    """Traverse the panel in horizontal serpentine rows.

    Visually: first row goes left->right across all 32 pixels, then move
    down one row, go right->left, and so on until the whole grid is filled.

    This traverses the logical grid; the display layer handles wiring.
    """

    off: Color = (0, 0, 0)
    orange: Color = (255, 165, 0)

    framebuffer = MatrixFramebuffer(display.width, display.height)
    framebuffer.clear(off)
    display.show(framebuffer)

    for y in range(display.height):
        if y % 2 == 0:
            x_range = range(display.width)  # left -> right
        else:
            x_range = range(display.width - 1, -1, -1)  # right -> left

        for x in x_range:
            framebuffer.set_pixel(x, y, orange)
            display.show(framebuffer)
            time.sleep(delay_seconds)
