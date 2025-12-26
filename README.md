# LEDDisplay

A small Python playground for driving an 8x32 LED matrix via a WLED controller (Dig2Go) from your laptop.

It supports both:
- WLED JSON HTTP API (easy to debug)
- DDP (UDP realtime) output for smoother game-style updates
  - **Automatic sparse updates**: when using DDP, only changed pixels are sent (huge efficiency gain for games like Snake)

## Performance Optimization

When using DDP output, the display layer automatically detects which pixels changed and sends only those pixels over UDP. This provides massive bandwidth savings:

- **Snake game**: ~4-6 pixels change per tick (head + tail + maybe apple)
- **Full frame**: 256 pixels × 3 bytes = 768 bytes
- **Sparse update**: ~6 pixels × 3 bytes = ~18 bytes
- **Bandwidth reduction**: ~97% fewer bytes sent!

This reduces network congestion, packet loss, and display stutter significantly.

## Hardware

- **Controller:** Dig2Go (ESP32) running WLED.
- **Display:** 8x32 LED matrix module (e.g. AZ-Delivery MAX7219-based panel), treated as a 32 (width) x 8 (height) matrix.
- **Wiring / layout:**
	- WLED is treated as a 1D LED strip for output.
	- The Python code renders into a logical (x, y) grid, and a dedicated output layer maps that grid to the panel's physical wiring order.

## Project layout

- `main.py` – entrypoint; loads config and runs a chosen demo.
- `leddisplay/` – Python package with reusable code:
	- `leddisplay/wled_controller.py` – thin client around the WLED JSON HTTP API.
	- `leddisplay/ddp.py` – DDP packet builder + UDP sender (always chunked).
	- `leddisplay/display.py` – output layer that maps a logical framebuffer to physical LED indices and pushes frames to WLED.
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

### Optional: switch output protocol to DDP

In `config.json`, set:

```json
{
	"output": {
		"protocol": "ddp",
		"ddp_port": 4048,
		"ddp_destination_id": 1
	}
}
```

If `output.protocol` is omitted, the default is `json`.

## Running a demo

With the venv active:

```powershell
python main.py
```

`main.py` has commented calls to different demos. Uncomment to run.
