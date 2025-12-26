from __future__ import annotations

from leddisplay.framebuffer import MatrixFramebuffer


def test_framebuffer_dirty_tracking_on_set_pixel() -> None:
    fb = MatrixFramebuffer(4, 2)
    assert len(fb.get_dirty_pixels()) == 0
    
    fb.set_pixel(1, 0, (255, 0, 0))
    dirty = fb.get_dirty_pixels()
    assert len(dirty) == 1
    assert dirty[0] == (1, (255, 0, 0))
    
    fb.set_pixel(3, 1, (0, 255, 0))
    dirty = fb.get_dirty_pixels()
    assert len(dirty) == 2
    assert (1, (255, 0, 0)) in dirty
    assert (7, (0, 255, 0)) in dirty


def test_framebuffer_dirty_tracking_ignores_unchanged() -> None:
    fb = MatrixFramebuffer(4, 2)
    fb.set_pixel(0, 0, (0, 0, 0))  # Same as default
    assert len(fb.get_dirty_pixels()) == 0


def test_framebuffer_clear_dirty() -> None:
    fb = MatrixFramebuffer(4, 2)
    fb.set_pixel(1, 1, (100, 100, 100))
    assert len(fb.get_dirty_pixels()) == 1
    
    fb.clear_dirty()
    assert len(fb.get_dirty_pixels()) == 0


def test_framebuffer_clear_marks_all_dirty() -> None:
    fb = MatrixFramebuffer(4, 2)
    fb.clear((50, 50, 50))
    dirty = fb.get_dirty_pixels()
    assert len(dirty) == 8  # 4 * 2
    assert all(color == (50, 50, 50) for _, color in dirty)
