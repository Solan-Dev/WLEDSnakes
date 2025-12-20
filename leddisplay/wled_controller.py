from __future__ import annotations

from typing import Iterable, Tuple
import requests


Color = Tuple[int, int, int]


class WLEDController:
    def __init__(self, ip: str, port: int = 80, timeout: float = 3.0) -> None:
        self.base_url = f"http://{ip}:{port}"
        self.timeout = timeout

    def _post_state(self, payload: dict) -> None:
        url = f"{self.base_url}/json/state"
        # Always ensure the strip is on and changes are instant (no fade)
        base_payload = {
            "on": True,
            "tt": 0,  # transition time in ms
        }
        merged = {**base_payload, **payload}
        resp = requests.post(url, json=merged, timeout=self.timeout)
        resp.raise_for_status()

    def get_info(self) -> dict:
        url = f"{self.base_url}/json/info"
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_state(self) -> dict:
        """Return the full current state object from WLED."""
        url = f"{self.base_url}/json/state"
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def set_brightness(self, bri: int) -> None:
        bri = max(0, min(255, bri))
        self._post_state({"bri": bri})

    def set_all_color(self, r: int, g: int, b: int, bri: int | None = None) -> None:
        """Set the entire segment 0 to a single solid RGB color.

        This also clears any per-pixel overrides and unfreezes the segment so
        that the solid color is applied consistently after using `set_pixels`.
        """
        r = int(max(0, min(255, r)))
        g = int(max(0, min(255, g)))
        b = int(max(0, min(255, b)))

        payload: dict = {
            "seg": [
                {
                    "id": 0,
                    "fx": 0,          # solid
                    "frz": False,     # ensure effect is not frozen from `i` usage
                    "col": [[r, g, b]],
                }
            ]
        }
        if bri is not None:
            payload["bri"] = max(0, min(255, bri))

        self._post_state(payload)

    def set_pixels(self, colors: Iterable[Color], bri: int | None = None) -> None:
        """Set per-pixel colors using WLED's per-segment `i` array.

        Per official JSON API docs, you can send either:
          - a list of colors from LED 0 onward: {"seg":{"i":[[255,0,0],[0,255,0],...]}}
          - or index+color pairs. Here we use the simple sequential form.

        `colors` is an iterable of (r, g, b) for LEDs within segment 0.
        """
        color_list: list[list[int]] = []
        for (r, g, b) in colors:
            color_list.append([
                int(max(0, min(255, r))),
                int(max(0, min(255, g))),
                int(max(0, min(255, b))),
            ])

        payload: dict = {
            "seg": [
                {
                    "id": 0,
                    "fx": 0,   # solid effect so per-pixel colors are visible
                    "i": color_list,
                }
            ]
        }
        if bri is not None:
            payload["bri"] = max(0, min(255, bri))

        self._post_state(payload)
