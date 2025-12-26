from __future__ import annotations

import json
from pathlib import Path

from leddisplay.display import MatrixDisplay
from leddisplay.wled_controller import WLEDController
from leddisplay.demos.index_snake import run_horizontal_serpentine_snake, run_index_snake, run_row_snake
from leddisplay.demos.checkerboards import run_checkerboards
from leddisplay.demos.solid_colors import run_solid_colors
from leddisplay.demos.life_demo import run_game_of_life
from leddisplay.games.snake_runner import run_snake


Brightness = 1


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
    output_cfg = cfg.get("output", {})

    width = matrix_cfg["width"]
    height = matrix_cfg["height"]

    controller = WLEDController(
        ip=wled_cfg["ip"],
        port=wled_cfg.get("port", 80),
        timeout=wled_cfg.get("timeout_seconds", 3.0),
    )
    controller.set_brightness(10)
    # 1) Ping WLED
    info = controller.get_info()
    print(f"Connected to WLED {info.get('ver')} named {info.get('name')}")

    protocol = str(output_cfg.get("protocol", "json")).lower()
    if protocol not in {"json", "ddp"}:
        raise ValueError("output.protocol must be 'json' or 'ddp'")

    output_protocol = "ddp" if protocol == "ddp" else "json"

    display = MatrixDisplay(
        controller=controller,
        width=width,
        height=height,
        output=output_protocol,
        ddp_port=int(output_cfg.get("ddp_port", 4048)),
        ddp_destination_id=int(output_cfg.get("ddp_destination_id", 1)),
    )

    # Always start from a known blank state.
    display.clear()
    controller.set_brightness(Brightness)

    # Choose which demo to run by uncommenting one of these:

    # 1) Solid color test
    # run_solid_colors(controller)

    # 2) Checkerboard patterns (logical grid)
    # run_checkerboards(display)

    # 3) Index-based orange snake (linear strip indices)
    # print("Running orange index snake demo...")
    # run_index_snake(controller, width, height, delay_seconds=0.03)

    # 4) Horizontal serpentine snake matching physical wiring (32 across, down, back)
    # print("Running horizontal serpentine snake demo...")
    # run_horizontal_serpentine_snake(display, delay_seconds=0.03)

    # 4b) Row-by-row snake (logical raster scan)
    # print("Running row snake demo...")
    # run_row_snake(display, delay_seconds=0.03)

    # 5) Conway's Game of Life
    # print("Running Game of Life...")
    # run_game_of_life(display, tick_seconds=0.3)

    # 6) Snake game (WASD, P pause, Q quit)
    print("Running Snake...")
    run_snake(display, tick_seconds=0.2)

    print("Done.")

    # Leave the display in a known state.
    # display.clear()


if __name__ == "__main__":
    main()