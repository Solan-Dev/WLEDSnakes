from __future__ import annotations

import struct

import pytest

from leddisplay.ddp import (
    DDP_DATATYPE_RGB_8,
    DDP_PUSH,
    DDP_VER1,
    build_ddp_packets,
    build_ddp_sparse_packets,
)


def unpack_header(packet: bytes) -> tuple[int, int, int, int, int, int]:
    if len(packet) < 10:
        raise ValueError("packet too short")
    flags1, sequence, dtype, dest_id, offset, length = struct.unpack("!BBBBLH", packet[:10])
    return flags1, sequence, dtype, dest_id, offset, length


def test_build_ddp_packets_zero_length_sends_push_only() -> None:
    packets = build_ddp_packets(b"", sequence=7, destination_id=1, max_pixels_per_packet=480)
    assert len(packets) == 1
    flags1, sequence, dtype, dest_id, offset, length = unpack_header(packets[0])
    assert flags1 == (DDP_VER1 | DDP_PUSH)
    assert sequence == 7
    assert dtype == DDP_DATATYPE_RGB_8
    assert dest_id == 1
    assert offset == 0
    assert length == 0
    assert len(packets[0]) == 10


def test_build_ddp_packets_chunks_and_sets_offsets_and_push() -> None:
    # 481 pixels => 1443 bytes => requires 2 packets if max=480 pixels/1440 bytes
    rgb_bytes = bytes([1, 2, 3]) * 481
    packets = build_ddp_packets(rgb_bytes, sequence=1, destination_id=1, max_pixels_per_packet=480)
    assert len(packets) == 2

    flags1a, seq_a, dtype_a, dest_a, offset_a, length_a = unpack_header(packets[0])
    flags1b, seq_b, dtype_b, dest_b, offset_b, length_b = unpack_header(packets[1])

    assert flags1a == DDP_VER1
    assert flags1b == (DDP_VER1 | DDP_PUSH)

    assert seq_a == 1 and seq_b == 1
    assert dtype_a == DDP_DATATYPE_RGB_8 and dtype_b == DDP_DATATYPE_RGB_8
    assert dest_a == 1 and dest_b == 1

    assert offset_a == 0
    assert length_a == 480 * 3

    assert offset_b == 480 * 3
    assert length_b == 1 * 3

    assert len(packets[0]) == 10 + (480 * 3)
    assert len(packets[1]) == 10 + (1 * 3)


def test_build_ddp_packets_rejects_invalid_max_pixels() -> None:
    with pytest.raises(ValueError):
        build_ddp_packets(b"abc", sequence=1, max_pixels_per_packet=0)


def test_build_ddp_packets_rejects_invalid_destination_id() -> None:
    with pytest.raises(ValueError):
        build_ddp_packets(b"abc", sequence=1, destination_id=999)


def test_build_ddp_sparse_packets_empty_sends_push_only() -> None:
    packets = build_ddp_sparse_packets([], sequence=5, destination_id=1)
    assert len(packets) == 1
    flags1, seq, dtype, dest, offset, length = unpack_header(packets[0])
    assert flags1 == (DDP_VER1 | DDP_PUSH)
    assert seq == 5
    assert offset == 0
    assert length == 0


def test_build_ddp_sparse_packets_single_pixel() -> None:
    # Pixel 10 => offset 30, length 3
    updates = [(10, (255, 0, 128))]
    packets = build_ddp_sparse_packets(updates, sequence=1, destination_id=1)
    assert len(packets) == 1
    
    flags1, seq, dtype, dest, offset, length = unpack_header(packets[0])
    assert flags1 == (DDP_VER1 | DDP_PUSH)
    assert offset == 30
    assert length == 3
    assert packets[0][10:13] == bytes([255, 0, 128])


def test_build_ddp_sparse_packets_consecutive_run() -> None:
    # Pixels 5, 6, 7 should be merged into one packet
    updates = [(5, (1, 2, 3)), (6, (4, 5, 6)), (7, (7, 8, 9))]
    packets = build_ddp_sparse_packets(updates, sequence=2, destination_id=1)
    assert len(packets) == 1
    
    flags1, seq, dtype, dest, offset, length = unpack_header(packets[0])
    assert flags1 == (DDP_VER1 | DDP_PUSH)
    assert offset == 5 * 3
    assert length == 9
    assert packets[0][10:19] == bytes([1, 2, 3, 4, 5, 6, 7, 8, 9])


def test_build_ddp_sparse_packets_gaps_create_multiple_packets() -> None:
    # Pixels 0 and 100 (non-consecutive) should create 2 packets
    updates = [(0, (255, 0, 0)), (100, (0, 255, 0))]
    packets = build_ddp_sparse_packets(updates, sequence=3, destination_id=1)
    assert len(packets) == 2
    
    # First packet: pixel 0, no PUSH
    flags1a, seq_a, dtype_a, dest_a, offset_a, length_a = unpack_header(packets[0])
    assert flags1a == DDP_VER1  # No PUSH on first
    assert offset_a == 0
    assert length_a == 3
    
    # Second packet: pixel 100, has PUSH
    flags1b, seq_b, dtype_b, dest_b, offset_b, length_b = unpack_header(packets[1])
    assert flags1b == (DDP_VER1 | DDP_PUSH)
    assert offset_b == 300
    assert length_b == 3
