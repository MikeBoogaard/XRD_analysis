"""Portable NPZ + JSON export. No pickle or object arrays are written/read."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json
import numpy as np

from ..models import Measurement, RSM, Provenance
from ..errors import FormatError


def _json(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    if isinstance(value,Path): return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def export_data(data:Measurement|RSM,path:str|Path) -> tuple[Path,Path]:
    """NPZ stores original-shaped arrays; sidecar JSON documents units/provenance."""
    path=Path(path)
    if path.suffix.lower()!=".npz":
        raise FormatError("Intermediate data path must end with .npz.")
    measurement=data.measurement if isinstance(data,RSM) else data
    arrays={"intensity":measurement.intensity}
    motor_keys={name:f"motor_{i}" for i,name in enumerate(measurement.motors)}
    arrays.update({motor_keys[k]:v for k,v in measurement.motors.items()})
    if measurement.counting_time_s is not None:
        arrays["counting_time_s"]=measurement.counting_time_s
    document={"schema":"rsm-toolkit-1","source":asdict(measurement.source),
              "shape":list(measurement.intensity.shape),"motor_keys":motor_keys,
              "motor_units":measurement.motor_units,"intensity_unit":measurement.intensity_unit,
              "wavelength_angstrom":measurement.wavelength_angstrom,"metadata":measurement.metadata,
              "warnings":list(measurement.warnings)}
    if isinstance(data,RSM):
        arrays["q"]=data.q
        document["rsm"]={"wavelength_angstrom":data.wavelength_angstrom,"frame":data.frame,
                          "provisional":data.provisional,"configuration":data.configuration,"warnings":list(data.warnings)}
    path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,**arrays)
    sidecar=path.with_suffix(".json")
    sidecar.write_text(json.dumps(document,indent=2,default=_json,allow_nan=False),encoding="utf-8")
    return path,sidecar


def load_export(path:str|Path) -> Measurement|RSM:
    path=Path(path)
    try:
        d=json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        if d.get("schema")!="rsm-toolkit-1":
            raise FormatError("Unsupported intermediate schema.")
        with np.load(path,allow_pickle=False) as a:
            m=Measurement(a["intensity"],{k:a[v] for k,v in d["motor_keys"].items()},
                          d["motor_units"],Provenance(**d["source"]),d["intensity_unit"],
                          a["counting_time_s"] if "counting_time_s" in a else None,
                          d["wavelength_angstrom"],d["metadata"],tuple(d["warnings"]))
            if list(m.intensity.shape)!=d["shape"]:
                raise FormatError("Intermediate shape mismatch.")
            if "rsm" not in d: return m
            r=d["rsm"]
            return RSM(m,a["q"],r["wavelength_angstrom"],r["frame"],r["provisional"],r["configuration"],tuple(r["warnings"]))
    except (KeyError,OSError,ValueError) as exc:
        if isinstance(exc,FormatError): raise
        raise FormatError(f"Invalid intermediate export: {exc}") from exc
