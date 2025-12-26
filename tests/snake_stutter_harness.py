"""Test harness to analyze payload efficiency and stutter causes in Snake game."""
from __future__ import annotations

import time
from typing import Any

from leddisplay.display import MatrixDisplay
from leddisplay.framebuffer import MatrixFramebuffer
from leddisplay.games.snake import DOWN, LEFT, RIGHT, UP, SnakeGame
from leddisplay.wled_controller import WLEDController


class MockWLEDController:
    """Mock controller that doesn't send anything."""
    def __init__(self) -> None:
        self.ip = "127.0.0.1"
        self.port = 80
        self.pixel_calls = 0
        self.sparse_calls = 0
        
    def set_pixels(self, colors, bri=None):
        self.pixel_calls += 1
        
    def set_pixels_ddp(self, colors, **kwargs):
        self.pixel_calls += 1
        
    def set_pixels_ddp_sparse(self, pixel_updates, **kwargs):
        self.sparse_calls += 1
        num_pixels = len(list(pixel_updates))
        print(f"    Mock sent sparse update: {num_pixels} pixels")
        
    def close(self):
        pass


class InstrumentedDisplay(MatrixDisplay):
    """Display wrapper that tracks calls and payload sizes."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.call_count = 0
        self.sparse_call_count = 0
        self.full_frame_call_count = 0
        self.total_pixels_sent = 0
        self.calls_per_tick: List[int] = []
        self._tick_call_count = 0
        
    def show(self, framebuffer: MatrixFramebuffer) -> None:
        self.call_count += 1
        self._tick_call_count += 1
        
        # Track how many pixels we're sending
        dirty = framebuffer.get_dirty_pixels()
        threshold = (self.width * self.height) // 2
        
        if len(dirty) < threshold and len(dirty) > 0:
            self.sparse_call_count += 1
            self.total_pixels_sent += len(dirty)
            print(f"  [SPARSE UPDATE] {len(dirty)} pixels changed")
        else:
            self.full_frame_call_count += 1
            self.total_pixels_sent += (self.width * self.height)
            print(f"  [FULL FRAME] {self.width * self.height} pixels (dirty={len(dirty)})")
        
        super().show(framebuffer)
    
    def mark_tick_end(self) -> None:
        """Called at end of each game tick to track calls per tick."""
        self.calls_per_tick.append(self._tick_call_count)
        self._tick_call_count = 0
    
    def print_stats(self) -> None:
        print("\n" + "="*60)
        print("DISPLAY STATS:")
        print("="*60)
        print(f"Total show() calls: {self.call_count}")
        print(f"  - Sparse updates: {self.sparse_call_count}")
        print(f"  - Full frame updates: {self.full_frame_call_count}")
        print(f"Total pixels sent: {self.total_pixels_sent}")
        print(f"Average pixels per call: {self.total_pixels_sent / max(1, self.call_count):.1f}")
        
        if self.calls_per_tick:
            avg_calls = sum(self.calls_per_tick) / len(self.calls_per_tick)
            max_calls = max(self.calls_per_tick)
            multi_call_ticks = sum(1 for c in self.calls_per_tick if c > 1)
            print(f"\nCalls per tick:")
            print(f"  - Average: {avg_calls:.2f}")
            print(f"  - Max: {max_calls}")
            print(f"  - Ticks with multiple calls: {multi_call_ticks}/{len(self.calls_per_tick)}")
        print("="*60)


def test_rapid_input_scenario(display: InstrumentedDisplay, tick_seconds: float = 0.3) -> None:
    """Simulate rapid keyboard input during a single tick."""
    print("\n" + "="*60)
    print("TEST: Rapid Input Simulation")
    print("="*60)
    
    framebuffer = MatrixFramebuffer(display.width, display.height)
    game = SnakeGame(display.width, display.height, seconds_per_tick=tick_seconds)
    
    game.render(framebuffer)
    display.show(framebuffer)
    display.mark_tick_end()
    
    # Start the game
    game.request_direction(RIGHT)
    game.update(0.0001)
    
    # Simulate a tick with multiple rapid inputs
    print("\nTick 1: Multiple direction changes during same tick")
    tick_start = time.monotonic()
    
    # User mashes keyboard multiple times in <10ms
    game.request_direction(DOWN)
    game.request_direction(LEFT)  # Ignored (180° turn)
    game.request_direction(UP)
    game.request_direction(DOWN)
    
    # Advance time to complete the tick
    game.update(tick_seconds)
    
    state = (game.started, game.paused, game.running, game.snake, game.apple)
    game.render(framebuffer)
    display.show(framebuffer)
    display.mark_tick_end()
    
    # Another tick with single input
    print("\nTick 2: Single direction change")
    game.request_direction(RIGHT)
    game.update(tick_seconds)
    game.render(framebuffer)
    display.show(framebuffer)
    display.mark_tick_end()


def test_render_clear_behavior(display: InstrumentedDisplay) -> None:
    """Test what happens when render() is called - does it clear the framebuffer?"""
    print("\n" + "="*60)
    print("TEST: Render Clear Behavior")
    print("="*60)
    
    framebuffer = MatrixFramebuffer(display.width, display.height)
    game = SnakeGame(display.width, display.height)
    
    # Initial render
    print("\nInitial render:")
    game.render(framebuffer)
    dirty_count = len(framebuffer.get_dirty_pixels())
    print(f"  Dirty pixels after render: {dirty_count}")
    
    display.show(framebuffer)
    
    # Second render without game state change
    print("\nSecond render (no game state change):")
    game.render(framebuffer)
    dirty_count = len(framebuffer.get_dirty_pixels())
    print(f"  Dirty pixels after render: {dirty_count}")
    
    if dirty_count > 10:
        print(f"  ⚠️  WARNING: render() is marking {dirty_count} pixels dirty!")
        print("  This defeats sparse update optimization!")


def run_test_harness(display: InstrumentedDisplay) -> None:
    """Run all test scenarios."""
    test_render_clear_behavior(display)
    test_rapid_input_scenario(display, tick_seconds=0.3)
    display.print_stats()


if __name__ == "__main__":
    print("Snake Stutter Test Harness")
    print("="*60)
    
    # Create mock controller and instrumented display
    controller = MockWLEDController()
    display = InstrumentedDisplay(
        controller=controller,
        width=32,
        height=8,
        output="ddp",
    )
    
    run_test_harness(display)
