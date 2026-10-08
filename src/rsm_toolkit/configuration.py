"""Scientific configuration, independent of storage filenames and plot style."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from .geometry import CoplanarGeometry, VectorGeometry, MotorRotation
from .crystallography import Sample
from .errors import RSMError


@dataclass(frozen=True)
class RSMConfiguration:
    geometry: CoplanarGeometry | VectorGeometry | None = None
    wavelength_angstrom: float | None = None
    sample: Sample | None = None
    allow_provisional: bool = False
    wavelength_override_reason: str | None = None


def load_configuration(path: str | Path) -> RSMConfiguration:
    """JSON geometry configuration. Materials/orientations use the Python API."""
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    allowed={"geometry","wavelength_angstrom","allow_provisional","wavelength_override_reason","notes"}
    unknown=set(value)-allowed
    if unknown:
        raise RSMError(f"Unknown configuration keys: {sorted(unknown)}")
    geo=dict(value.get("geometry") or {})
    kind=geo.pop("type",None)
    try:
        if kind=="coplanar":
            geometry=CoplanarGeometry(**geo)
        elif kind=="vector":
            for key in ("sample_rotations","detector_rotations"):
                geo[key]=tuple(MotorRotation(**r) for r in geo.get(key,[]))
            geometry=VectorGeometry(**geo)
        elif kind is None:
            geometry=None
        else:
            raise RSMError(f"Unsupported geometry type {kind!r}.")
        return RSMConfiguration(geometry=geometry,**{k:v for k,v in value.items() if k not in ("geometry","notes")})
    except TypeError as exc:
        raise RSMError(f"Invalid geometry configuration: {exc}") from exc
