"""Scientific configuration, independent of storage filenames and plot style."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json
from .geometry import CoplanarGeometry, VectorGeometry, MotorRotation
from .crystallography import Sample
from .errors import RSMError
from .overlays import sample_from_config, object_keys


@dataclass(frozen=True)
class RSMConfiguration:
    geometry: CoplanarGeometry | VectorGeometry | None = None
    wavelength_angstrom: float | None = None
    sample: Sample | None = None
    allow_provisional: bool = False
    wavelength_override_reason: str | None = None
    sample_settings: dict | None = None
    plot_settings: dict = field(default_factory=dict)

    def __post_init__(self):
        if type(self.allow_provisional) is not bool:
            raise RSMError("allow_provisional must be a boolean, not text or a number.")
        object_keys(self.plot_settings, ('intensity_scale', 'mode', 'bins', 'components',
                    'cmap', 'vmin', 'vmax', 'dynamic_range_decades', 'xlim', 'ylim',
                    'plane_tolerance', 'title', 'theoretical_overlays'), 'plot')
        if type(self.plot_settings.get('theoretical_overlays', False)) is not bool:
            raise RSMError("plot.theoretical_overlays must be boolean.")


def load_configuration(path: str | Path) -> RSMConfiguration:
    """Unified JSON settings, retaining support for geometry-only files."""
    try:
        value=json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RSMError(f"Invalid configuration JSON: {exc}") from exc
    if not isinstance(value,dict):
        raise RSMError("Configuration must be a JSON object.")
    allowed={"geometry","wavelength_angstrom","allow_provisional","wavelength_override_reason","notes","sample","plot"}
    unknown=set(value)-allowed
    if unknown:
        raise RSMError(f"Unknown configuration keys: {sorted(unknown)}")
    if value.get("geometry") is not None and not isinstance(value["geometry"],dict):
        raise RSMError("geometry must be an object or null.")
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
        return RSMConfiguration(geometry=geometry,sample=sample_from_config(value.get('sample')),
                                sample_settings=value.get('sample'),plot_settings=value.get('plot',{}),
                                **{k:v for k,v in value.items() if k not in ("geometry","notes","sample","plot")})
    except (TypeError, KeyError, ValueError) as exc:
        if isinstance(exc,RSMError): raise
        raise RSMError(f"Invalid run configuration: {exc}") from exc
