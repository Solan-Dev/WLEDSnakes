from __future__ import annotations

import random

import pytest

from leddisplay.games.snake import DOWN, LEFT, RIGHT, UP, SnakeGame


def _make_game(
    width: int = 8,
    height: int = 8,
    *,
    snake=((3, 3), (2, 3), (1, 3)),
    direction=RIGHT,
    apple=(6, 6),
    seed: int = 123,
    tick: float = 0.3,
) -> SnakeGame:
    rng = random.Random(seed)
    return SnakeGame(
        width,
        height,
        seconds_per_tick=tick,
        start_on_first_input=False,
        rng=rng,
        initial_snake=list(snake),
        initial_direction=direction,
        initial_apple=apple,
    )


def test_moves_one_cell_per_tick() -> None:
    game = _make_game()

    # Before any tick, update less than tick should not move.
    before = game.snake
    game.update(0.29)
    assert game.snake == before

    # Cross the tick boundary => move exactly 1 cell to the right.
    game.update(0.02)
    assert game.snake[0] == (4, 3)


def test_disallow_180_degree_turn() -> None:
    # Snake is moving LEFT; its body must trail to the RIGHT.
    game = _make_game(snake=((3, 3), (4, 3), (5, 3)), direction=LEFT)

    # Request opposite direction (RIGHT) should be ignored.
    game.request_direction(RIGHT)
    game.update(0.31)

    # Still moving left.
    assert game.snake[0] == (2, 3)


def test_eat_apple_grows_by_one() -> None:
    # Place apple directly in front of head.
    game = _make_game(apple=(4, 3))
    initial_len = len(game.snake)

    game.update(0.31)

    assert len(game.snake) == initial_len + 1
    assert game.snake[0] == (4, 3)


def test_apple_never_spawns_on_snake_after_eat() -> None:
    game = _make_game(width=6, height=6, apple=(4, 3), snake=((3, 3), (2, 3), (1, 3)))
    game.update(0.31)  # eat

    assert game.apple not in set(game.snake)


def test_wall_collision_ends_game() -> None:
    # Head at x=0 moving left => collision on next step.
    game = _make_game(width=5, height=5, snake=((0, 0), (1, 0), (2, 0)), direction=LEFT)
    assert game.running is True

    game.update(0.31)
    assert game.running is False


def test_game_waits_for_first_direction_input() -> None:
    game = SnakeGame(8, 8, seconds_per_tick=0.3, rng=random.Random(1), start_on_first_input=True)

    before = game.snake
    game.update(10.0)
    assert game.snake == before

    game.request_direction(UP)
    game.update(0.31)
    assert game.snake[0] == (before[0][0], before[0][1] - 1)


def test_self_collision_ends_game() -> None:
    # Head moving up into an occupied body cell (not the tail) should end the game.
    snake = ((2, 2), (2, 1), (1, 1), (1, 2))
    game = _make_game(width=5, height=5, snake=snake, direction=UP, apple=(4, 4))

    game.update(0.31)
    assert game.running is False
