"""Source dispatch and explicit three-column text import; never parse filenames."""
from pathlib import Path
import numpy as np
from ..errors import FormatError, UnsupportedFormatError
from ..models import Measurement, Provenance
from .bruker_raw import load_raw
from .bruker_brml import load_brml


def load_dat(path, *, columns=("Theta", "TwoTheta", "intensity"),
             angle_unit="degree", wavelength_angstrom=None, counting_time_s=None,
             intensity_unit="recorded intensity") -> Measurement:
    """Whitespace table with explicitly declared columns; decimal comma accepted."""
    if len(set(columns)) != len(columns) or "intensity" not in columns:
        raise FormatError("Text columns must be unique and include intensity.")
    try:
        a = np.loadtxt(Path(path).read_text(encoding="utf-8-sig").replace(",", ".").splitlines(),ndmin=2)
    except ValueError as exc:
        raise FormatError(f"Invalid numeric text table: {exc}") from exc
    if a.shape[1] != len(columns) or not a.size:
        raise FormatError("Text table width disagrees with explicit columns.")
    motors = {name:a[:,i] for i,name in enumerate(columns) if name != "intensity"}
    return Measurement(a[:,columns.index("intensity")], motors, {k:angle_unit for k in motors},
                       Provenance.from_file(path,"text","explicit-columns-v1"),intensity_unit,
                       counting_time_s,wavelength_angstrom,{"measurement_type":"unclassified points"},
                       ("Text-table units and motor meanings are user supplied; acquisition geometry is unverified.",))


def load_xrd(path, **kwargs) -> Measurement:
    p = Path(path)
    with p.open("rb") as f:
        magic = f.read(8)
    if magic.startswith(b"RAW"):
        if kwargs:
            raise FormatError("RAW reader does not accept BRML/text options.")
        return load_raw(p)
    if magic.startswith(b"PK"):
        return load_brml(p, **kwargs)
    if p.suffix.lower() in (".dat", ".txt", ".xy"):
        return load_dat(p, **kwargs)
    raise UnsupportedFormatError(f"Unrecognized measurement signature {magic!r}.")
