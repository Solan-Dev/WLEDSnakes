from __future__ import annotations

import time

from leddisplay.wled_controller import WLEDController


def run_solid_colors(controller: WLEDController) -> None:
    """Cycle through a couple of solid colors on the whole panel."""
    print("Setting panel to red...")
    controller.set_all_color(255, 0, 0, bri=64)
    time.sleep(1.0)

    print("Setting panel to green...")
    controller.set_all_color(0, 255, 0)
    time.sleep(1.0)

    print("Setting panel to blue...")
    controller.set_all_color(0, 0, 255)
    time.sleep(1.0)
