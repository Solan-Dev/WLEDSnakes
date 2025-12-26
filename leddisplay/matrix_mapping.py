def xy_to_index(x: int, y: int, width: int, height: int) -> int:
    """Convert (x, y) into a linear LED index for this panel.

    This mapping matches the physical wiring used by the horizontal
    snake demo: columns of ``height`` pixels, wired in a serpentine
    pattern top->bottom then bottom->top.

    Assumes:
      - origin is top-left (x increases to the right, y increases down)
      - width = number of columns, height = number of rows
      - LEDs are wired column-by-column in a vertical serpentine
    """
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Out of bounds: x={x}, y={y}, width={width}, height={height}")

    # Even columns go top->bottom, odd columns bottom->top.
    if x % 2 == 0:
        index = x * height + y
    else:
        index = x * height + (height - 1 - y)

    return index
