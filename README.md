# LEDDisplay

A small Python playground for driving an 8x32 LED matrix via a WLED controller (Dig2Go) from your laptop. It uses the WLED JSON HTTP API for per-pixel control and a few demo animations.

## Hardware

- **Controller:** Dig2Go (ESP32) running WLED.
- **Display:** 8x32 LED matrix module (e.g. AZ-Delivery MAX7219-based panel), treated as a 32 (width) x 8 (height) matrix.
- **Wiring / layout:**
	- Configured in WLED as a 2D matrix with serpentine wiring, starting from the top-left corner.
	- The Python code generally treats the matrix as a simple grid and lets WLED handle the physical zig-zag mapping for per-pixel JSON updates.

## Project layout

- `main.py` – entrypoint; loads config and runs a chosen demo.
- `leddisplay/` – Python package with reusable code:
	- `leddisplay/wled_controller.py` – thin client around the WLED JSON HTTP API.
	- `leddisplay/matrix_mapping.py` – helpers to map 2D (x, y) coordinates to linear LED indices.
	- `leddisplay/demos/` – individual demo scripts (solid colors, checkerboards, snakes).
- `config.example.json` – example configuration file (copy to `config.json` or `config.local.json`).

## Setup

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
cd LEDDisplay
py -3 -m venv .venv
. .venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create your real config file based on the example:

```powershell
copy config.example.json config.json
```

Then edit `config.json` and set your WLED IP address.

## Running a demo

With the venv active:

```powershell
python main.py
```

`main.py` has commented calls to different demos. Uncomment to run.
