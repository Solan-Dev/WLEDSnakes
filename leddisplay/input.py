from __future__ import annotations

from typing import Optional


def poll_key() -> Optional[str]:
    """Return a single keypress if available, else None.

    - On Windows, uses `msvcrt` for true non-blocking key reads.
    - On non-Windows environments, returns None by default (so the game
      can still run, but without live keyboard control).

    This design keeps CI/test environments simple (they don't rely on
    interactive input).
    """

    try:
        import msvcrt  # type: ignore
    except Exception:
        return None

    if not msvcrt.kbhit():
        return None

    try:
        ch = msvcrt.getwch()
    except Exception:
        return None

    if not ch:
        return None

    return ch.lower()
