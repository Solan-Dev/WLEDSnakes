from __future__ import annotations

import time
from typing import Tuple

from leddisplay.display import MatrixDisplay
from leddisplay.framebuffer import MatrixFramebuffer

Color = Tuple[int, int, int]


def _draw_checkerboard(framebuffer: MatrixFramebuffer, color1: Color, color2: Color) -> None:
    for y in range(framebuffer.height):
        for x in range(framebuffer.width):
            c = color1 if (x + y) % 2 == 0 else color2
            framebuffer.set_pixel(x, y, c)


def run_checkerboards(display: MatrixDisplay) -> None:
    """Show a couple of checkerboard patterns using per-pixel control.
    """
    framebuffer = MatrixFramebuffer(display.width, display.height)

    _draw_checkerboard(framebuffer, (0, 255, 0), (0, 0, 0))
    display.show(framebuffer)
    time.sleep(1.0)

    _draw_checkerboard(framebuffer, (0, 0, 255), (255, 128, 0))
    display.show(framebuffer)
    time.sleep(1.0)
