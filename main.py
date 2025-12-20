from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from leddisplay.wled_controller import WLEDController
from leddisplay.demos.index_snake import (
    run_index_snake,
    run_row_snake,
    run_horizontal_serpentine_snake,
)
from leddisplay.demos.checkerboards import run_checkerboards
from leddisplay.demos.solid_colors import run_solid_colors


Color = Tuple[int, int, int]


def load_config() -> dict:
    """Load configuration, preferring a local, untracked file if present.

    Order:
      1. config.local.json (ignored by git, safe for real IPs)
      2. config.json (project-level config, may be committed)
    """
    base_dir = Path(__file__).parent

    local_path = base_dir / "config.local.json"
    if local_path.exists():
        with local_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    config_path = base_dir / "config.json"
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    cfg = load_config()
    wled_cfg = cfg["wled"]
    matrix_cfg = cfg["matrix"]

    width = matrix_cfg["width"]
    height = matrix_cfg["height"]
    serpentine = matrix_cfg.get("serpentine", True)

    controller = WLEDController(
        ip=wled_cfg["ip"],
        port=wled_cfg.get("port", 80),
        timeout=wled_cfg.get("timeout_seconds", 3.0),
    )

    # 1) Ping WLED
    info = controller.get_info()
    print(f"Connected to WLED {info.get('ver')} named {info.get('name')}")

    # Choose which demo to run by uncommenting one of these:

    # 1) Solid color test
    # run_solid_colors(controller)

    # 2) Checkerboard patterns (logical non-serpentine grid by default)
    # run_checkerboards(controller, width, height)

    # 3) Index-based orange snake (linear strip indices)
    # print("Running orange index snake demo...")
    # run_index_snake(controller, width, height, delay_seconds=0.03)

    # 4) Horizontal serpentine snake matching physical wiring (32 across, down, back)
    print("Running horizontal serpentine snake demo...")
    run_horizontal_serpentine_snake(controller, width, height, delay_seconds=0.03)

    print("Done.")

    controller.set_brightness(10)


if __name__ == "__main__":
    main()