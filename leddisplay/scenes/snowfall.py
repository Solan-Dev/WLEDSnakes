from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Set, Tuple

from leddisplay.framebuffer import Color, MatrixFramebuffer
from leddisplay.scenes.base import MatrixScene


@dataclass
class _Snowflake:
	base_x: float
	x: float
	y: float
	fall_speed: float
	drift_speed: float
	drift_phase: float
	twinkle_phase: float
	twinkle_speed: float
	depth: float
	active: bool = True


def _scale_color(color: Color, intensity: float) -> Color:
	intensity = max(0.0, min(1.0, intensity))
	return (
		min(255, int(color[0] * intensity)),
		min(255, int(color[1] * intensity)),
		min(255, int(color[2] * intensity)),
	)


class SnowfallScene(MatrixScene):
	"""Drifting snowfall with adjustable intensity, accumulation, and melt."""

	def __init__(
		self,
		width: int,
		height: int,
		*,
		density: float = 0.06,
		fall_speed_range: Tuple[float, float] = (0.8, 5.0),
		drift_speed_range: Tuple[float, float] = (0.6, 1.6),
		twinkle_speed_range: Tuple[float, float] = (0.8, 2.4),
		drift_amplitude: float | None = None,
		background_color: Color = (0, 0, 20),
		snow_color: Color = (230, 240, 255),
		intensity_range: Tuple[float, float] = (0.4, 1.0),
		intensity_cycle_seconds: float = 24.0,
		melt_rate: float = 0.12,
		target_fps: float = 45.0,
		rng: random.Random | None = None,
	) -> None:
		super().__init__(width, height)
		if width <= 0 or height <= 0:
			raise ValueError("Scene dimensions must be positive")
		if density <= 0:
			raise ValueError("density must be positive")

		low, high = intensity_range
		if low < 0.0 or high <= 0.0 or high < low or high > 1.0:
			raise ValueError("intensity_range must be within 0..1 and ordered")

		self._rng = rng or random.Random()
		self._flakes: List[_Snowflake] = []
		self._active_indices: Set[int] = set()
		self._ground_heights: List[float] = [0.0] * width
		self._last_positions: List[Tuple[int, int]] = []

		self._fall_speed_range = fall_speed_range
		self._drift_speed_range = drift_speed_range
		self._twinkle_speed_range = twinkle_speed_range
		base_amplitude = (width * 0.08) if drift_amplitude is None else float(drift_amplitude)
		self._drift_amplitude = max(0.0, base_amplitude)

		self._background_color = background_color
		self._snow_color = snow_color
		self._intensity_range = (low, high)
		self._cycle_duration = max(0.0, intensity_cycle_seconds)
		self._melt_rate = max(0.0, melt_rate)
		self._frame_interval = 1.0 / target_fps if target_fps > 0 else 0.0
		self._rate_multiplier = 1.0

		self._flake_count = max(1, int(width * height * density))
		self._height_scale = max(1.0, height / 16.0)
		self._width_wrap = float(max(1, width))

		self._accumulator = 0.0
		self._time = 0.0
		self._current_intensity = high

	def reset(self) -> None:
		self._flakes = [self._spawn_flake(initial=True) for _ in range(self._flake_count)]
		for flake in self._flakes:
			flake.active = True
		self._active_indices = set(range(len(self._flakes)))
		self._ground_heights = [0.0] * self.width
		self._last_positions = []
		self._accumulator = 0.0
		self._time = 0.0
		self._current_intensity = self._mid_intensity()
		self._sync_active_flakes(self._target_active_count(self._current_intensity))

	def configure(
		self,
		*,
		rate_multiplier: float | None = None,
		intensity_range: Tuple[float, float] | None = None,
	) -> None:
		if rate_multiplier is not None:
			self._rate_multiplier = max(0.0, rate_multiplier)
		if intensity_range is not None:
			low, high = intensity_range
			if low < 0.0 or high <= 0.0 or high < low or high > 1.0:
				raise ValueError("intensity_range must be within 0..1 and ordered")
			self._intensity_range = (low, high)
		target = self._target_active_count(self._compute_intensity_factor())
		self._sync_active_flakes(target)

	def step(self, framebuffer: MatrixFramebuffer, dt: float) -> None:
		if dt < 0:
			dt = 0.0

		should_render = False
		if self._frame_interval > 0.0:
			self._accumulator += dt
			while self._accumulator >= self._frame_interval:
				self._advance(self._frame_interval)
				self._accumulator -= self._frame_interval
				should_render = True
		else:
			self._advance(dt)
			should_render = True

		if should_render:
			self._render(framebuffer)

	def _advance(self, dt: float) -> None:
		self._time += dt
		self._current_intensity = self._compute_intensity_factor()
		target_active = self._target_active_count(self._current_intensity)
		self._sync_active_flakes(target_active)

		coverage = [False] * self.width
		fall_scale = 0.6 + 0.8 * self._current_intensity

		for idx, flake in enumerate(self._flakes):
			if idx not in self._active_indices:
				continue

			flake.y += flake.fall_speed * dt * fall_scale
			flake.drift_phase += flake.drift_speed * dt
			flake.twinkle_phase += flake.twinkle_speed * dt

			drift_strength = self._drift_amplitude * (0.5 + 0.5 * flake.depth)
			flake.x = (flake.base_x + math.sin(flake.drift_phase) * drift_strength) % self._width_wrap

			col = self._quantize_x(flake.x)
			if col is None:
				continue

			altitude = (self.height - 1) - flake.y
			if flake.y >= self.height - 1 or altitude < self._ground_heights[col]:
				self._ground_heights[col] = min(float(self.height), self._ground_heights[col] + 1.0)
				coverage[col] = True
				self._recycle_flake(flake)
				continue

			if altitude <= self._ground_heights[col] + 1.0:
				coverage[col] = True

		melt_amount = self._melt_rate * dt
		if melt_amount > 0.0:
			for x in range(self.width):
				if not coverage[x]:
					self._ground_heights[x] = max(0.0, self._ground_heights[x] - melt_amount)

	def _render(self, framebuffer: MatrixFramebuffer) -> None:
		width = self.width
		height = self.height

		for x, y in self._last_positions:
			if 0 <= x < width and 0 <= y < height:
				ground_threshold = height - int(math.ceil(self._ground_heights[x]))
				if y < ground_threshold:
					framebuffer.set_pixel(x, y, self._background_color)

		for x in range(width):
			column_height = min(height, int(math.ceil(self._ground_heights[x])))
			for i in range(column_height):
				y = height - 1 - i
				depth_factor = 0.7 + 0.3 * (1.0 - (i / max(1, column_height)))
				framebuffer.set_pixel(x, y, _scale_color(self._snow_color, depth_factor))

		positions: List[Tuple[int, int]] = []
		for idx in self._active_indices:
			flake = self._flakes[idx]
			x = self._quantize_x(flake.x)
			y = self._quantize_y(flake.y)
			if x is None or y is None:
				continue

			ground_threshold = height - int(math.ceil(self._ground_heights[x]))
			if y < 0 or y >= height or y >= ground_threshold:
				continue

			brightness = self._flake_intensity(flake)
			framebuffer.set_pixel(x, y, _scale_color(self._snow_color, brightness))
			positions.append((x, y))

		self._last_positions = positions

	def _flake_intensity(self, flake: _Snowflake) -> float:
		twinkle = 0.7 + 0.3 * (0.5 + 0.5 * math.sin(flake.twinkle_phase))
		depth_term = 0.4 + 0.6 * flake.depth
		scene_term = 0.5 + 0.5 * self._current_intensity
		return min(1.0, depth_term * twinkle * scene_term)

	def _spawn_flake(self, *, initial: bool = False) -> _Snowflake:
		base_x = self._rng.uniform(0.0, self.width - 1.0) if self.width > 1 else 0.0
		y = self._rng.uniform(-self.height, self.height) if initial else -self._rng.random() * self.height

		min_fall, max_fall = self._fall_speed_range
		fall_speed = self._rng.uniform(min_fall, max_fall) * self._height_scale

		min_drift, max_drift = self._drift_speed_range
		drift_speed = self._rng.uniform(min_drift, max_drift)

		min_twinkle, max_twinkle = self._twinkle_speed_range
		twinkle_speed = self._rng.uniform(min_twinkle, max_twinkle)

		depth = self._rng.uniform(0.3, 1.0)

		return _Snowflake(
			base_x=base_x,
			x=base_x,
			y=y,
			fall_speed=fall_speed,
			drift_speed=drift_speed,
			drift_phase=self._rng.uniform(0.0, math.tau),
			twinkle_phase=self._rng.uniform(0.0, math.tau),
			twinkle_speed=twinkle_speed,
			depth=depth,
		)

	def _recycle_flake(self, flake: _Snowflake) -> None:
		replacement = self._spawn_flake(initial=False)
		flake.base_x = replacement.base_x
		flake.x = replacement.x
		flake.y = replacement.y
		flake.fall_speed = replacement.fall_speed
		flake.drift_speed = replacement.drift_speed
		flake.drift_phase = replacement.drift_phase
		flake.twinkle_phase = replacement.twinkle_phase
		flake.twinkle_speed = replacement.twinkle_speed
		flake.depth = replacement.depth

	def _sync_active_flakes(self, target: int) -> None:
		target = max(1, min(target, len(self._flakes)))
		current = len(self._active_indices)
		if current == target:
			return
		if current < target:
			needed = target - current
			candidates = [i for i in range(len(self._flakes)) if i not in self._active_indices]
			self._rng.shuffle(candidates)
			for idx in candidates[:needed]:
				self._active_indices.add(idx)
				self._flakes[idx].active = True
		else:
			removable = list(self._active_indices)
			self._rng.shuffle(removable)
			for idx in removable[: current - target]:
				self._active_indices.remove(idx)
				self._flakes[idx].active = False

	def _compute_intensity_factor(self) -> float:
		low, high = self._intensity_range
		if self._cycle_duration <= 0.0 or math.isclose(low, high):
			return high
		phase = (math.sin((self._time / self._cycle_duration) * math.tau) + 1.0) * 0.5
		return low + (high - low) * phase

	def _target_active_count(self, intensity: float) -> int:
		normalized = max(0.0, min(1.0, intensity))
		return max(1, int(self._flake_count * normalized * self._rate_multiplier))

	def _mid_intensity(self) -> float:
		low, high = self._intensity_range
		return low + (high - low) * 0.5

	def _quantize_x(self, value: float) -> int | None:
		if self.width <= 0:
			return None
		idx = int(round(value))
		return max(0, min(self.width - 1, idx))

	def _quantize_y(self, value: float) -> int | None:
		if self.height <= 0:
			return None
		idx = int(round(value))
		return idx if 0 <= idx < self.height else None
