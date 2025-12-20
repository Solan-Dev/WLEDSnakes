def xy_to_index(x: int,
                y: int,
                width: int,
                height: int,
                serpentine: bool = True,
                start_corner: str = "top_left") -> int:
    """Convert (x, y) into a linear LED index for a matrix.

    Assumes:
      - origin is top-left
      - rows go left->right, then next row, etc.
      - if serpentine=True, every second row is reversed.
    """
    if start_corner != "top_left":
        raise NotImplementedError("Only top_left start_corner is implemented for now.")

    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Out of bounds: x={x}, y={y}, width={width}, height={height}")

    if serpentine:
        if y % 2 == 0:
            # even row: left to right
            index = y * width + x
        else:
            # odd row: right to left
            index = y * width + (width - 1 - x)
    else:
        index = y * width + x

    return index
