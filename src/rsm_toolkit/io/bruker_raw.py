"""Strict RAW4.00 PSD Fix Scan reader.

Binary field definitions follow the public xylib/GSAS-II RAW4 range layout,
not absolute offsets guessed from these files. See docs/file_formats.md.
PSD semantics are independently checked against paired BRML exports. Other
scan types are rejected rather than treated as PSD/coupled scans by analogy.
"""
from __future__ import annotations

from pathlib import Path
import struct
import numpy as np

from ..errors import FormatError, UnsupportedFormatError
from ..models import Measurement, Provenance


def _text(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("latin-1").strip()


def load_raw(path: str | Path) -> Measurement:
    data = Path(path).read_bytes()
    if data[:8] != b"RAW4.00\0":
        raise UnsupportedFormatError(f"RAW variant {data[:8]!r}: only RAW4.00 PSD Fix Scan is supported.")

    def check(offset: int, size: int, end: int | None = None) -> None:
        if offset < 0 or size < 0 or offset + size > (len(data) if end is None else end):
            raise FormatError(f"Truncated or invalid RAW block at byte {offset}, length {size}.")

    def unpack(fmt: str, offset: int):
        check(offset, struct.calcsize(fmt))
        return struct.unpack_from(fmt, data, offset)

    def segment(offset: int, end: int):
        check(offset, 8, end)
        typ, length = unpack("<II", offset)
        if length < 8:
            raise FormatError(f"RAW segment has invalid length {length} at {offset}.")
        check(offset, length, end)
        rec = {"type": typ, "offset": offset, "length": length}
        if typ == 10:
            if length < 36:
                raise FormatError("Truncated RAW VarInfo segment.")
            rec.update(name=_text(data[offset+12:offset+36]), value=_text(data[offset+36:offset+length]))
        elif typ == 50:
            if length < 64:
                raise FormatError("Truncated RAW DriveInfo segment.")
            rec.update(name=_text(data[offset+12:offset+36]), position=unpack("<d", offset+56)[0])
        elif typ == 30:
            if length < 120:
                raise FormatError("Truncated RAW hardware segment.")
            rec.update(zip(("alpha_average", "alpha1", "alpha2", "beta", "alpha_ratio"), unpack("<5d", offset+72)))
            rec["anode"] = _text(data[offset+116:offset+120])
        elif typ == 60:
            if length < 76:
                raise FormatError("Truncated RAW alignment segment.")
            rec.update(name=_text(data[offset+12:offset+36]), flag=unpack("<I",offset+8)[0], delta=unpack("<d",offset+68)[0])
        return rec, offset + length

    check(0, 61)
    pos = 61
    global_segments = []
    while unpack("<I", pos)[0] not in (0, 160):
        rec, pos = segment(pos, len(data))
        global_segments.append(rec)

    ranges, rows, tt_rows, times, waves, drives = [], [], [], [], [], []
    while pos < len(data):
        check(pos, 160)
        if unpack("<I", pos)[0] not in (0, 160):
            raise FormatError(f"Unexpected RAW range marker at byte {pos}.")
        scan_type = _text(data[pos+32:pos+56])
        if scan_type != "PSD Fix Scan":
            raise UnsupportedFormatError(f"RAW4 scan type {scan_type!r} is not supported; no motor coupling is inferred.")
        start, step, count, dwell = unpack("<ddIf", pos+72)
        wave = unpack("<d", pos+112)[0]
        datum_size, extra_size = unpack("<II", pos+136)
        if datum_size != 4:
            raise UnsupportedFormatError(f"RAW4 datum size {datum_size}; this profile requires float32 records.")
        if not 0 < count <= 10_000_000 or not np.isfinite([start,step,dwell,wave]).all() or step == 0:
            raise FormatError("Invalid RAW range dimensions or coordinates.")
        end = pos + 160 + extra_size
        check(pos+160, extra_size + count*datum_size)
        cur, records, axis = pos+160, [], {}
        while cur < end:
            rec, cur = segment(cur, end)
            records.append(rec)
            if rec["type"] == 50:
                if rec["name"] in axis:
                    raise FormatError("Duplicate RAW drive name in a range.")
                axis[rec["name"]] = rec["position"]
        if "Theta" not in axis or "2Theta" not in axis:
            raise FormatError("PSD Fix Scan lacks Theta/2Theta drive metadata.")
        rows.append(np.frombuffer(data, dtype="<f4", count=count, offset=end).astype(float))
        tt_rows.append(start + step*np.arange(count))
        times.append(dwell)
        waves.append(wave)
        drives.append(axis)
        ranges.append({"offset":pos, "scan_type":scan_type, "start":start, "step":step,
                       "count":count, "counting_time_s":dwell, "wavelength_angstrom":wave,
                       "segments":records})
        pos = end + count*datum_size
    if not rows or len({len(r) for r in rows}) != 1:
        raise UnsupportedFormatError("Empty or ragged RAW ranges; export each scan separately.")
    if any(set(a) != set(drives[0]) for a in drives):
        raise UnsupportedFormatError("RAW drive definitions change between ranges.")
    if not np.allclose(waves, waves[0], rtol=0, atol=1e-10):
        raise UnsupportedFormatError("Changing wavelength requires separate reconstructions.")
    motors = {k: np.array([a[k] for a in drives])[:,None] for k in drives[0]}
    motors["TwoThetaArm"] = motors.pop("2Theta")
    motors["TwoTheta"] = np.stack(tt_rows)
    units = {k: ("degree" if k in ("Theta", "TwoTheta", "TwoThetaArm", "Chi", "Phi") else
                 "mm" if k in ("X-Drive","Y-Drive","Z-Drive","BeamTranslation","TrackDistance") else "unspecified") for k in motors}
    notes = ["RAW4 PSD Fix Scan semantics checked on paired BRML exports; other RAW modes are unsupported.",
             "Instrument zeroes and sample orientation are not established by RAW motor positions.",
             "Unknown RAW metadata segments are indexed by source byte offset, not interpreted."]
    metadata = {"measurement_type":"detector_stack" if len(rows)>1 else "detector_profile",
                "scan_type":"PSD Fix Scan", "date":_text(data[12:24]), "time":_text(data[24:34]),
                "global_segments":global_segments, "ranges":ranges,
                "axis_semantics":"TwoTheta = absolute calibrated detector-bin angle; TwoThetaArm = motor position",
                "wavelength_source":"RAW range USED_LAMBDA; angstrom", "intensity_processing":"none"}
    return Measurement(np.stack(rows), motors, units,
                       Provenance.from_file(path,"Bruker RAW4.00","raw4-psd-v1"), "recorded counts",
                       np.array(times)[:,None], waves[0], metadata, tuple(notes))
