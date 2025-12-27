# LEDDisplay — Project Narrative (from Git History + Current Workspace)

This document summarizes the project’s evolution as reflected by the git commit history in this repository **plus** the next stage of work that currently exists in the working tree but is not committed yet.

## Snapshot: What the repo is for

LEDDisplay is a Python playground for driving an **8×32 LED matrix** (logically treated as **32×8**) via a **WLED controller** (e.g., Dig2Go/ESP32).

Two output modes are supported:

- **WLED JSON HTTP API** (easy to debug, full-frame style updates)
- **DDP over UDP** (real-time updates, optimized for games/animations)
  - Supports **sparse updates**: send only changed pixels rather than the full frame

## Timeline (chronological)

### 2025-12-20 — Commit `525dbbb`: “inital WLEDSnakes”

**Intent:** get hardware output working quickly and establish a basic demo workflow.

**What was introduced**

- **Project scaffolding and basic demos**
  - Main entrypoint and demo runner patterns: [main.py](main.py)
  - Demo scripts:
    - [leddisplay/demos/checkerboards.py](leddisplay/demos/checkerboards.py)
    - [leddisplay/demos/index_snake.py](leddisplay/demos/index_snake.py)
    - [leddisplay/demos/solid_colors.py](leddisplay/demos/solid_colors.py)

- **WLED JSON client**
  - Thin API wrapper for per-pixel control via HTTP: [leddisplay/wled_controller.py](leddisplay/wled_controller.py)

- **Coordinate/index mapping helpers**
  - Basic mapping utilities: [leddisplay/matrix_mapping.py](leddisplay/matrix_mapping.py)

- **Configuration + setup docs**
  - Config templates and local configuration:
    - [config.example.json](config.example.json)
    - [config.json](config.json)
  - Getting started instructions: [README.md](README.md)

**Narrative takeaway**

This first commit is the “proof of life” milestone: it establishes the repo’s purpose, provides a workable config + demo loop, and validates that Python can drive the panel through WLED.

---

### 2025-12-26 — Commit `26224c2`: “Refactor snake runner into games package”

**Intent (as the commit message suggests):** reorganize Snake into a cleaner game structure.

**What actually happened:** this is a major expansion commit that upgrades the architecture (output pipeline + performance + tests).

**Major additions**

- **DDP output support + packet builder**
  - DDP packet chunking and sparse update building: [leddisplay/ddp.py](leddisplay/ddp.py)

- **Framebuffer abstraction + dirty tracking**
  - Logical pixel buffer that tracks changed pixels, enabling sparse updates: [leddisplay/framebuffer.py](leddisplay/framebuffer.py)

- **Display/output layer (physical mapping + protocol selection)**
  - Central “output boundary” that:
    - maps logical (x,y) pixels to physical LED indices
    - chooses JSON full-frame or DDP full-frame
    - uses DDP sparse updates when only a few pixels changed
  - Implementation: [leddisplay/display.py](leddisplay/display.py)

- **Games package refactor**
  - New game architecture:
    - Base class: [leddisplay/games/base.py](leddisplay/games/base.py)
    - Snake: [leddisplay/games/snake.py](leddisplay/games/snake.py)
    - Snake runner: [leddisplay/games/snake_runner.py](leddisplay/games/snake_runner.py)
    - Life game: [leddisplay/games/life.py](leddisplay/games/life.py)
  - Input handling abstraction: [leddisplay/input.py](leddisplay/input.py)
  - Additional demos:
    - [leddisplay/demos/snake_demo.py](leddisplay/demos/snake_demo.py)
    - [leddisplay/demos/life_demo.py](leddisplay/demos/life_demo.py)

- **Performance work formalized**
  - The root cause of stutter was documented and validated:
    - `framebuffer.clear()` every frame marked **all pixels dirty**, defeating sparse updates.
    - The fix was **incremental rendering** in Snake: update only changed pixels.
  - Write-up: [OPTIMIZATION_RESULTS.md](OPTIMIZATION_RESULTS.md)

- **Tests + CI**
  - Unit tests added for critical building blocks:
    - [tests/test_ddp.py](tests/test_ddp.py)
    - [tests/test_framebuffer.py](tests/test_framebuffer.py)
    - [tests/test_snake_game.py](tests/test_snake_game.py)
  - Diagnostic harness:
    - [tests/snake_stutter_harness.py](tests/snake_stutter_harness.py)
  - CI workflow:
    - [.github/workflows/ci.yml](.github/workflows/ci.yml)

- **Documentation/config updated to match new capabilities**
  - README updated to describe JSON vs DDP and sparse updates: [README.md](README.md)
  - Output protocol config added/adjusted: [config.example.json](config.example.json)

**Narrative takeaway**

This commit turns the repo from “a few demos” into a small, testable system with:

- a proper render pipeline (framebuffer → mapping → output)
- a UDP protocol optimized for real-time animation (DDP)
- a performance philosophy centered on **dirty pixels** and **sparse updates**

---

## Current “Stage 3” (uncommitted work in the working tree)

Git status indicates a newer phase of work exists locally but is not committed yet:

- Modified: [main.py](main.py)
- Untracked: the entire scenes framework and new tests
- Untracked: a Snowfall development log

### Scenes framework and ambient effects

This stage introduces non-interactive “scenes” (ambient animations) parallel to games.

- Base scene interface: [leddisplay/scenes/base.py](leddisplay/scenes/base.py)
- Fireplace scene: [leddisplay/scenes/fireplace.py](leddisplay/scenes/fireplace.py)
- Snowfall scene: [leddisplay/scenes/snowfall.py](leddisplay/scenes/snowfall.py)
- Shared runner helpers: [leddisplay/scenes/runner.py](leddisplay/scenes/runner.py)
- Scene exports: [leddisplay/scenes/__init__.py](leddisplay/scenes/__init__.py)

### Tests added for scenes

- Fireplace tests: [tests/test_fireplace_scene.py](tests/test_fireplace_scene.py)
- Snowfall tests: [tests/test_snowfall_scene.py](tests/test_snowfall_scene.py)

### Snowfall design/dev narrative

A detailed day-by-day implementation log exists locally:

- [SNOWFALL_DEVELOPMENT.md](SNOWFALL_DEVELOPMENT.md)

### Narrative takeaway

The project’s focus expands from “games + demos” into a more complete “content system”:

- **Games**: interactive, tick-driven, input-handled.
- **Scenes**: continuous ambience, parameterized simulation, often with higher-level visual goals.

Importantly, this stage still benefits from the same core foundation created in commit `26224c2`: a logical framebuffer + sparse DDP output.

## Suggested next commit boundaries (if you want clean history)

If you want the repo history to reflect this third stage clearly, a clean split would be:

1. Add scenes framework + fireplace scene + tests
2. Add snowfall scene + tests
3. Add development logs/docs (optional)

(These are suggestions only; no changes are made by this document.)
