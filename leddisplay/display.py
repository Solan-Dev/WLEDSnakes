from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Tuple

from leddisplay.framebuffer import Color, MatrixFramebuffer
from leddisplay.matrix_mapping import xy_to_index
from leddisplay.wled_controller import WLEDController


@dataclass(frozen=True)
class MatrixDisplay:
    """Display output layer.

    Games/demos render into a logical MatrixFramebuffer (row-major).
    This class is the only place that understands the physical wiring
    (xy -> linear LED index) and pushes pixels to WLED.
    """

    controller: WLEDController
    width: int
    height: int
    output: Literal["json", "ddp"] = "json"
    ddp_port: int = 4048
    ddp_destination_id: int = 1

    def __post_init__(self) -> None:
        # Cache logical-index -> physical-index mapping for consistent performance.
        mapping: List[int] = [0] * (self.width * self.height)
        for y in range(self.height):
            for x in range(self.width):
                logical_index = y * self.width + x
                mapping[logical_index] = xy_to_index(x, y, self.width, self.height)
        object.__setattr__(self, "_logical_to_physical", mapping)

    def clear(self, color: Color = (0, 0, 0)) -> None:
        pixels = [color] * (self.width * self.height)
        if self.output == "ddp":
            self.controller.set_pixels_ddp(
                pixels,
                ddp_port=self.ddp_port,
                destination_id=self.ddp_destination_id,
            )
        else:
            self.controller.set_pixels(pixels)

    def show(self, framebuffer: MatrixFramebuffer) -> None:
        if framebuffer.width != self.width or framebuffer.height != self.height:
            raise ValueError(
                "Framebuffer size does not match display: "
                f"fb={framebuffer.width}x{framebuffer.height}, "
                f"display={self.width}x{self.height}"
            )

        if self.output == "ddp":
            # For DDP: use sparse updates if only a few pixels changed
            dirty_logical = framebuffer.get_dirty_pixels()

            if not dirty_logical:
                framebuffer.clear_dirty()
                return
            
            # Heuristic: if more than 50% of pixels changed, send full frame (cheaper)
            # Otherwise, send only the changed pixels
            threshold = (self.width * self.height) // 2
            
            if len(dirty_logical) < threshold and len(dirty_logical) > 0:
                # Sparse update: map logical dirty pixels to physical indices
                mapping: List[int] = getattr(self, "_logical_to_physical")
                physical_updates: List[Tuple[int, Color]] = []
                for logical_idx, color in dirty_logical:
                    physical_idx = mapping[logical_idx]
                    physical_updates.append((physical_idx, color))
                
                self.controller.set_pixels_ddp_sparse(
                    physical_updates,
                    ddp_port=self.ddp_port,
                    destination_id=self.ddp_destination_id,
                )
            else:
                # Full frame update
                out: List[Color] = [(0, 0, 0)] * (self.width * self.height)
                mapping: List[int] = getattr(self, "_logical_to_physical")
                for y in range(self.height):
                    for x in range(self.width):
                        logical_index = y * self.width + x
                        out[mapping[logical_index]] = framebuffer.get_pixel(x, y)

                self.controller.set_pixels_ddp(
                    out,
                    ddp_port=self.ddp_port,
                    destination_id=self.ddp_destination_id,
                )
            
            # Clear dirty tracking after sending
            framebuffer.clear_dirty()
        else:
            # JSON mode: always send full frame
            out: List[Color] = [(0, 0, 0)] * (self.width * self.height)
            mapping: List[int] = getattr(self, "_logical_to_physical")
            for y in range(self.height):
                for x in range(self.width):
                    logical_index = y * self.width + x
                    out[mapping[logical_index]] = framebuffer.get_pixel(x, y)

            self.controller.set_pixels(out)
