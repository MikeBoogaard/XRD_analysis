"""Common measurement model. Arrays are copied and made read-only on entry."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import hashlib
import numpy as np

from .errors import RSMError


def readonly(value: Any) -> np.ndarray:
    a = np.array(value, dtype=float, copy=True)
    a.setflags(write=False)
    return a


@dataclass(frozen=True)
class Provenance:
    path: str
    sha256: str
    format: str
    reader: str

    @classmethod
    def from_file(cls, path: str | Path, format: str, reader: str) -> Provenance:
        p = Path(path)
        return cls(str(p.resolve()), hashlib.sha256(p.read_bytes()).hexdigest(), format, reader)


@dataclass(frozen=True)
class Measurement:
    """Original detector values, same-shaped motor arrays, explicit units.

    A 2D array is (scan step, detector bin). Motors include per-bin TwoTheta
    and separately the detector-arm position where available. No implicit
    correction or normalization is performed. Metadata retains source schema.
    """

    intensity: np.ndarray
    motors: dict[str, np.ndarray]
    motor_units: dict[str, str]
    source: Provenance
    intensity_unit: str = "recorded intensity"
    counting_time_s: np.ndarray | None = None
    wavelength_angstrom: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        a = readonly(self.intensity)
        if a.ndim not in (1, 2) or not a.size:
            raise RSMError("Intensity must be a nonempty 1D or 2D array.")
        object.__setattr__(self, "intensity", a)
        motors = {}
        for name, value in self.motors.items():
            try:
                motors[name] = readonly(np.broadcast_to(value, a.shape))
            except ValueError as exc:
                raise RSMError(f"Motor {name!r} shape does not match intensity {a.shape}.") from exc
            if name not in self.motor_units:
                raise RSMError(f"Missing unit for motor {name!r}.")
        object.__setattr__(self, "motors", motors)
        if self.counting_time_s is not None:
            try:
                t = readonly(np.broadcast_to(self.counting_time_s, a.shape))
            except ValueError as exc:
                raise RSMError("Counting time shape does not match intensity.") from exc
            object.__setattr__(self, "counting_time_s", t)
        if self.wavelength_angstrom is not None:
            w = self.wavelength_angstrom
            if not np.isfinite(w) or w <= 0:
                raise RSMError("Wavelength must be positive and finite in angstrom.")

    def summary(self) -> dict[str, Any]:
        finite = self.intensity[np.isfinite(self.intensity)]
        return {
            "source": self.source.__dict__, "shape": list(self.intensity.shape),
            "intensity_unit": self.intensity_unit,
            "intensity_range": [float(finite.min()), float(finite.max())] if finite.size else None,
            "nonpositive_intensities": int(np.sum(self.intensity <= 0)),
            "wavelength_angstrom": self.wavelength_angstrom,
            "motors": {k: {"min": float(np.nanmin(v)), "max": float(np.nanmax(v)),
                            "unit": self.motor_units[k]} for k, v in self.motors.items()},
            "warnings": list(self.warnings),
            "measurement_type": self.metadata.get("measurement_type", "unclassified"),
        }


@dataclass(frozen=True)
class RSM:
    measurement: Measurement
    q: np.ndarray
    wavelength_angstrom: float
    frame: str
    provisional: bool
    configuration: dict[str, Any]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        q = readonly(self.q)
        if q.shape != self.measurement.intensity.shape + (3,):
            raise RSMError("Q must have intensity.shape + (3,) components.")
        object.__setattr__(self, "q", q)

    @property
    def intensity(self) -> np.ndarray:
        return self.measurement.intensity
