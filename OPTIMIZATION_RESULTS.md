# Snake Game Optimization Results

## Problem Identified

The `render()` method was calling `framebuffer.clear()` on **every frame**, which marked all 256 pixels (32×8) as dirty. This completely defeated the sparse update optimization.

## Solution Implemented

### 1. Incremental Rendering
Changed `Snake.render()` to track previous state and only update changed pixels:
- Clear old snake tail positions that moved
- Clear old apple position if it moved
- Draw new snake head/body at current positions
- Draw new apple at current position

### 2. Sparse Update Results

**Before Optimization (with `framebuffer.clear()` every render):**
```
[FULL FRAME] 256 pixels (dirty=256)
```
- Every tick: 256 pixels × 3 bytes = **768 bytes sent**
- Total bandwidth at 5 ticks/second: **3,840 bytes/sec**

**After Optimization (incremental render):**
```
[SPARSE UPDATE] 2 pixels changed
```
- Every tick: ~2 pixels × 3 bytes = **6 bytes sent**
- Total bandwidth at 5 ticks/second: **30 bytes/sec**
- **128× reduction in bandwidth! (99.2% savings)**

## Test Harness Output

```
Snake Stutter Test Harness
============================================================

TEST: Render Clear Behavior
------------------------------------------------------------
Initial render:
  Dirty pixels after render: 2  ✅ Only changed pixels!
  [SPARSE UPDATE] 2 pixels changed

Second render (no game state change):
  Dirty pixels after render: 0  ✅ No unnecessary updates!

TEST: Rapid Input Simulation
------------------------------------------------------------
Tick 1: Multiple direction changes during same tick
  [SPARSE UPDATE] 2 pixels changed  ✅ Still just 2 pixels!

Tick 2: Single direction change
  [SPARSE UPDATE] 2 pixels changed  ✅ Consistent!

DISPLAY STATS:
============================================================
Total show() calls: 4
  - Sparse updates: 4      ✅ 100% sparse!
  - Full frame updates: 0  ✅ No full frames!
Total pixels sent: 8
Average pixels per call: 2.0  ✅ Minimal payload!
============================================================
```

## Impact on Stutter

### Root Causes Eliminated:

1. **Bandwidth waste**: Reduced from 768 bytes → 6 bytes per frame
2. **Network congestion**: Far fewer bytes over Wi-Fi = less packet loss
3. **WLED processing**: WLED only updates 2 pixels instead of 256
4. **UDP packet size**: Tiny packets have lower loss probability

### Rapid Keyboard Input Handling:

The test shows that even with **multiple direction changes during a single tick**, the game still only sends:
- **One update per tick** (not multiple)
- **Only 2 pixels** (head moved, tail moved)

This is because:
1. `request_direction()` only changes internal `_pending_direction` state
2. The state tuple `(started, paused, running, snake, apple)` doesn't change until tick boundary
3. Only one `render()` + `display.show()` happens per tick when snake actually moves

## Why This Works

**Typical Snake movement:**
- Old head becomes body (orange)
- New head position (yellow)
- Old tail disappears (black background)
- = **Exactly 2-3 pixel changes** (unless apple eaten = 1 more pixel)

The sparse DDP update only sends these 2-3 changed pixels instead of the entire 256-pixel frame.

## Running the Test Harness

```powershell
$env:PYTHONPATH="C:\Users\JamesSolan\Desktop\Projects\LEDDisplay"
.venv/Scripts/python.exe tests/snake_stutter_harness.py
```

## Summary

**Question: "What payload is being sent at the end of each tick?"**
- **Answer**: Now only ~2 pixels (6 bytes) instead of 256 pixels (768 bytes)

**Question: "If there are multiple updates per tick, reduce payload to last input only"**
- **Answer**: Already handled! The state-change gating ensures only one update per tick, and incremental rendering ensures minimal pixels sent.

**Result**: Stutter should be **dramatically reduced** due to 128× less network traffic.
