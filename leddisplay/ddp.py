from __future__ import annotations

import struct
import socket
from dataclasses import dataclass
from typing import Iterable, List, Tuple


Color = Tuple[int, int, int]


DDP_DEFAULT_PORT = 4048
DDP_HEADER_LEN = 10

# DDP v1 flags (byte 0)
DDP_VER1 = 0x40
DDP_PUSH = 0x01

# DDP "datatype" (byte 2)
# Format: C R TTT SSS
# For RGB: TTT=001, and 8-bit elements: SSS=011 => 0b00001011 == 0x0B
DDP_DATATYPE_RGB_8 = 0x0B

# Commonly used maximum payload size (in bytes) for RGB pixels in a single packet.
# 480 pixels * 3 bytes = 1440 bytes, as referenced by the DDP spec sample code.
DDP_DEFAULT_MAX_PIXELS_PER_PACKET = 480


def _clamp_u8(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else int(value)


def rgb_bytes_from_colors(colors: Iterable[Color]) -> bytes:
    buf = bytearray()
    for (r, g, b) in colors:
        buf.append(_clamp_u8(r))
        buf.append(_clamp_u8(g))
        buf.append(_clamp_u8(b))
    return bytes(buf)


def build_ddp_sparse_packets(
    pixel_updates: Iterable[Tuple[int, Color]],
    *,
    sequence: int,
    destination_id: int = 1,
    max_pixels_per_packet: int = DDP_DEFAULT_MAX_PIXELS_PER_PACKET,
    datatype: int = DDP_DATATYPE_RGB_8,
) -> List[bytes]:
    """Build DDP packets for sparse pixel updates.

    Instead of sending the entire frame, send only changed pixels.
    Each update is: (pixel_index, (r, g, b)).

    DDP uses byte offsets, so pixel N is at offset N*3.
    We group consecutive pixels into runs to minimize packet count.
    """
    updates_list = list(pixel_updates)
    if not updates_list:
        # Send a PUSH-only packet to trigger display refresh
        header = struct.pack(
            "!BBBBLH",
            DDP_VER1 | DDP_PUSH,
            sequence & 0xFF,
            datatype & 0xFF,
            destination_id & 0xFF,
            0,
            0,
        )
        return [header]

    # Sort by pixel index to enable run merging
    updates_list.sort(key=lambda x: x[0])

    # Group into runs (consecutive pixels)
    packets: List[bytes] = []
    run_start_idx = updates_list[0][0]
    run_pixels: List[Color] = []

    max_payload = max_pixels_per_packet * 3

    def flush_run() -> None:
        if not run_pixels:
            return
        offset = run_start_idx * 3
        rgb_bytes = bytearray()
        for (r, g, b) in run_pixels:
            rgb_bytes.append(_clamp_u8(r))
            rgb_bytes.append(_clamp_u8(g))
            rgb_bytes.append(_clamp_u8(b))

        # Split into chunks if needed
        chunk_start = 0
        while chunk_start < len(rgb_bytes):
            chunk = rgb_bytes[chunk_start : chunk_start + max_payload]
            flags = DDP_VER1  # PUSH will be set on very last packet

            header = struct.pack(
                "!BBBBLH",
                flags & 0xFF,
                sequence & 0xFF,
                datatype & 0xFF,
                destination_id & 0xFF,
                offset + chunk_start,
                len(chunk),
            )
            packets.append(header + bytes(chunk))
            chunk_start += len(chunk)

    for idx, color in updates_list:
        expected_next = run_start_idx + len(run_pixels)
        if idx == expected_next and len(run_pixels) * 3 < max_payload - 3:
            run_pixels.append(color)
        else:
            flush_run()
            run_start_idx = idx
            run_pixels = [color]

    flush_run()

    # Set PUSH flag only on the very last packet
    if packets:
        last_packet = packets[-1]
        flags_byte = last_packet[0] | DDP_PUSH
        packets[-1] = bytes([flags_byte]) + last_packet[1:]

    return packets
    buf = bytearray()
    for (r, g, b) in colors:
        buf.append(_clamp_u8(r))
        buf.append(_clamp_u8(g))
        buf.append(_clamp_u8(b))
    return bytes(buf)


def build_ddp_packets(
    rgb_bytes: bytes,
    *,
    sequence: int,
    destination_id: int = 1,
    max_pixels_per_packet: int = DDP_DEFAULT_MAX_PIXELS_PER_PACKET,
    datatype: int = DDP_DATATYPE_RGB_8,
) -> List[bytes]:
    """Build one or more DDP UDP payloads.

    This function ALWAYS chunks, even for small frames, by splitting the byte
    stream into packets no larger than `max_pixels_per_packet * 3`.

    Packet format (10 bytes header + data), per the DDP v1 spec:
      - byte0: flags (includes version bits and PUSH on last packet)
      - byte1: sequence number (1-15 recommended; 0 disables sequencing)
      - byte2: datatype
      - byte3: destination ID (1 = default)
      - bytes4-7: offset (big-endian) in BYTES
      - bytes8-9: data length (big-endian)
    """
    if max_pixels_per_packet <= 0:
        raise ValueError("max_pixels_per_packet must be > 0")

    max_data_len = max_pixels_per_packet * 3
    if max_data_len <= 0:
        raise ValueError("max_pixels_per_packet too large")

    if not (0 <= destination_id <= 255):
        raise ValueError("destination_id must be in range 0..255")

    packets: List[bytes] = []
    total_len = len(rgb_bytes)

    # Even if total_len is 0, send a PUSH-only packet to trigger display update.
    if total_len == 0:
        header = struct.pack(
            "!BBBBLH",
            DDP_VER1 | DDP_PUSH,
            sequence & 0xFF,
            datatype & 0xFF,
            destination_id & 0xFF,
            0,
            0,
        )
        return [header]

    offset = 0
    while offset < total_len:
        chunk = rgb_bytes[offset : offset + max_data_len]
        last = (offset + len(chunk)) >= total_len
        flags = DDP_VER1 | (DDP_PUSH if last else 0)

        header = struct.pack(
            "!BBBBLH",
            flags & 0xFF,
            sequence & 0xFF,
            datatype & 0xFF,
            destination_id & 0xFF,
            offset,
            len(chunk),
        )
        packets.append(header + chunk)
        offset += len(chunk)

    return packets


@dataclass
class DDPClient:
    host: str
    port: int = DDP_DEFAULT_PORT
    destination_id: int = 1
    max_pixels_per_packet: int = DDP_DEFAULT_MAX_PIXELS_PER_PACKET

    def __post_init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Sequence is 1..15 (0 disables sequencing). We'll wrap naturally.
        self._sequence = 1

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def send_colors(self, colors: Iterable[Color]) -> None:
        rgb_bytes = rgb_bytes_from_colors(colors)
        self.send_rgb_bytes(rgb_bytes)

    def send_rgb_bytes(self, rgb_bytes: bytes) -> None:
        packets = build_ddp_packets(
            rgb_bytes,
            sequence=self._sequence,
            destination_id=self.destination_id,
            max_pixels_per_packet=self.max_pixels_per_packet,
            datatype=DDP_DATATYPE_RGB_8,
        )

        for payload in packets:
            self._sock.sendto(payload, (self.host, self.port))

        # Wrap 1..15 (like many implementations). 0 is reserved for "not used".
        self._sequence = (self._sequence % 15) + 1

    def send_sparse_update(self, pixel_updates: Iterable[Tuple[int, Color]]) -> None:
        """Send only changed pixels (sparse update).

        pixel_updates is an iterable of (pixel_index, (r, g, b)).
        This is far more efficient than sending the whole frame when only a few pixels change.
        """
        packets = build_ddp_sparse_packets(
            pixel_updates,
            sequence=self._sequence,
            destination_id=self.destination_id,
            max_pixels_per_packet=self.max_pixels_per_packet,
            datatype=DDP_DATATYPE_RGB_8,
        )

        for payload in packets:
            self._sock.sendto(payload, (self.host, self.port))

        self._sequence = (self._sequence % 15) + 1
