"""BRML XML descriptors and the validated DIFFRAC 8.6.2 Eiger memory profile.

No XML Datum column index, motor position or detector calibration is guessed.
External float64 payload profile is gated and paired-export-tested; see docs.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

from ..errors import FormatError, UnsupportedFormatError
from ..models import Measurement, Provenance

XSI = "{http://www.w3.org/2001/XMLSchema-instance}type"


def _xml(z: zipfile.ZipFile, member: str) -> ET.Element:
    try:
        info = z.getinfo(member)
        if info.file_size > 100_000_000:
            raise FormatError(f"BRML XML exceeds supported size: {member}")
        raw = z.read(member)
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise FormatError("DTD/entity declarations are not supported in BRML.")
        return ET.fromstring(raw)
    except (KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise FormatError(f"Invalid or missing BRML XML member {member}: {exc}") from exc


def _number(node: ET.Element | None, child: str) -> float:
    if node is None or node.find(child) is None:
        raise FormatError(f"BRML missing numeric field {child}.")
    item = node.find(child)
    return float(item.get("Value", item.text or ""))


def _describe(node: ET.Element | None):
    if node is None:
        return None
    return {"tag":node.tag, "attributes":dict(node.attrib), "text":(node.text or "").strip(),
            "children":[_describe(c) for c in node]}


def load_brml(path: str | Path, *, scan_index: int = 0, route_index: int = 0) -> Measurement:
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                raise FormatError("Duplicate archive member names are ambiguous.")
            containers = sorted(n for n in names if n.endswith("/DataContainer.xml"))
            scans = []
            for member in containers:
                container = _xml(z,member)
                refs = container.findall("RawDataReferenceList/string")
                for ref in refs:
                    target = (ref.text or "").replace("\\", "/")
                    if target not in names:
                        raise FormatError(f"BRML manifest refers to missing scan {target}.")
                    scans.append((target,container.findtext("CreatingVersion")))
            if not 0 <= scan_index < len(scans):
                raise FormatError(f"BRML scan_index={scan_index}; archive has {len(scans)} manifest scans.")
            member, version = scans[scan_index]
            root = _xml(z,member)
            routes = root.findall("DataRoutes/DataRoute")
            if not 0 <= route_index < len(routes):
                raise FormatError("BRML route_index out of range.")
            route = routes[route_index]
            if route.get("RouteFlag") != "Measured" or route.get("ProcLevel", "0") != "0":
                raise UnsupportedFormatError("Select an originally measured, unprocessed BRML route.")
            scan = route.find("ScanInformation")
            if scan is None:
                raise FormatError("BRML route has no ScanInformation.")
            datums = route.findall("Datum")
            values = np.array([[float(x) for x in (d.text or "").split(",")] for d in datums])
            n = int(scan.findtext("MeasurementPoints", "0"))
            if values.ndim != 2 or len(values) != n or n == 0:
                raise FormatError("BRML Datum dimensions disagree with MeasurementPoints.")
            views = route.findall("DataViews/RawDataView")
            motor_columns, fields, count_views = {}, {}, []
            for view in views:
                kind = view.get(XSI, "")
                start, length = int(view.get("Start","0")), int(view.get("Length","0"))
                if "ExtMemory" not in kind and (start < 0 or length < 1 or start+length > values.shape[1]):
                    raise FormatError("BRML DataView exceeds Datum width.")
                if kind == "FixedRawDataView":
                    fields[view.get("LogicName", "")] = values[:,start:start+length]
                varying = view.find("Varying")
                if varying is not None and varying.get("LogicName") == "ScanAxes":
                    defs = varying.findall("FieldDefinitions")
                    if len(defs) != length:
                        raise FormatError("BRML axis definitions disagree with vector length.")
                    for j, definition in enumerate(defs):
                        motor_columns[definition.get("AxisId")] = values[:,start+j]
                recording = view.find("Recording")
                if recording is not None and recording.get("Category") == "Count":
                    count_views.append(view)
            if len(count_views) != 1:
                raise UnsupportedFormatError("BRML requires one unambiguous count DataView per selected route.")
            view = count_views[0]
            width = int(view.get("Length","0"))
            recording = view.find("Recording")
            if recording.find("Unit").get("Base") != "Counts":
                raise UnsupportedFormatError("Unsupported BRML recorded-intensity unit.")
            external = view.get(XSI) == "ExtMemoryRecordedRawDataView"
            if external:
                # This is a narrowly validated codec profile, not generic .bin autodetection.
                if version != "8.6.2.0" or recording.get("ParentBeringObjectName") != "Eiger2R_250K" or view.get("Start") != "0":
                    raise UnsupportedFormatError("Unsupported external BRML memory profile/version. No binary encoding is guessed.")
                if _number(recording.find("Size"),"X") != width or _number(recording.find("Size"),"Y") != 1:
                    raise UnsupportedFormatError("Only the validated Eiger 1D external profile is supported.")
                link = route.find("ScanDataExternalLink")
                if link is None or link.get("LinkType") != "MemoryMapped" or link.get("Location") != "@\\MemoryMappedFiles":
                    raise UnsupportedFormatError("Unsupported BRML external link.")
                filename = link.get("Name", "")
                if PurePosixPath(filename).name != filename or "\\" in filename:
                    raise FormatError("Invalid external archive member name.")
                binary_member = "MemoryMappedFiles/" + filename
                if z.getinfo(binary_member).file_size != n*width*8:
                    raise FormatError("BRML memory payload size disagrees with declared step/channel dimensions.")
                intensity = np.frombuffer(z.read(binary_member),dtype="<f8").reshape(n,width)
            else:
                start = int(view.get("Start","0"))
                intensity = values[:,start:start+width]
            if not {"Theta","TwoTheta"} <= set(motor_columns):
                raise UnsupportedFormatError("BRML route lacks explicit Theta and TwoTheta scan axes; no coupling is invented.")
            axis_meta = {a.get("AxisId"): a for a in scan.findall("ScanAxes/ScanAxisInfo")}
            for name in ("Theta","TwoTheta"):
                axis = axis_meta.get(name)
                if axis is None or axis.find("Unit") is None or axis.find("Unit").get("Base") != "Degree":
                    raise UnsupportedFormatError(f"BRML {name} is not explicitly in degrees.")
                expected = _number(axis,"Start") + np.arange(n)*_number(axis,"Increment")
                if not np.allclose(motor_columns[name],expected,rtol=0,atol=1e-7):
                    raise FormatError(f"BRML {name} Datum disagrees with scan definition.")
            scales = scan.findall("ScaleAxes/ScaleAxisInfo")
            if width > 1:
                if len(scales) != 1 or scales[0].get("AxisId") != "TwoTheta_Relative" or scales[0].get(XSI) != "ScaleAxisInfoRegular":
                    raise UnsupportedFormatError("Detector bins require an explicit regular TwoTheta_Relative scale.")
                scale = scales[0]
                if scale.find("Unit").get("Base") != "Degree":
                    raise UnsupportedFormatError("Detector-relative axis is not in degrees.")
                relative = _number(scale,"Start") + np.arange(width)*_number(scale,"Increment")
                if not np.isclose(relative[-1],_number(scale,"Stop"),rtol=0,atol=1e-8):
                    raise FormatError("BRML detector scale endpoint disagrees with channel count.")
            else:
                relative = np.zeros(1)
            motors = {k:v[:,None] for k,v in motor_columns.items()}
            motors["TwoThetaArm"] = motors["TwoTheta"]
            motors["TwoTheta"] = motors["TwoThetaArm"] + relative[None,:]
            units = {k:"degree" for k in motors}
            fixed = root.find("FixedInformation")
            for drive in root.findall("FixedInformation/Drives/InfoData"):
                name = drive.get("LogicName")
                motors[name] = _number(drive,"Position")
                units[name] = "degree" if name in ("Chi","Phi") else "mm" if name in ("X","Y","Z","BeamTranslation","TrackDistance") else "unspecified"
            wavelengths = root.findall("FixedInformation/MethodInformation/InfoData/MethodAlignment/WaveLength")
            wavelength = float(wavelengths[0].get("Value")) if len(wavelengths)==1 else None
            notes = ["Motor positions are targets; surface orientation and Chi/Phi calibration are not certified.",
                     "Recorded detector counts can be fractional after instrument ROI rebinning; no Poisson variance is inferred."]
            if external:
                notes.append("External memory codec is validated for DIFFRAC 8.6.2.0 Eiger2R_250K using paired RAW exports, not a universal BRML binary specification.")
            if len(scans)>1 or len(routes)>1:
                notes.append(f"Selected scan {scan_index}/{len(scans)} and route {route_index}/{len(routes)}; other routes are not merged.")
            if wavelength is None:
                notes.append("No unique method wavelength: supply wavelength_angstrom explicitly.")
            if "MeasuredTime" not in fields:
                notes.append("No per-step MeasuredTime: count-rate normalization unavailable.")
            metadata = {"measurement_type":scan.findtext("ScanMode", "unknown"),
                        "scan_name":scan.get("ScanName"),"ipa_mode":scan.findtext("IPAmode"),
                        "creating_version":version,"archive_member":member,"scan_index":scan_index,
                        "route_index":route_index,"scan_count":len(scans),"route_count":len(routes),
                        "scan_information":_describe(scan),"fixed_information":_describe(fixed),
                        "data_views":_describe(route.find("DataViews")),"datum_columns":values.tolist(),
                        "wavelength_source":"FixedInformation/MethodInformation/InfoData/MethodAlignment/WaveLength (angstrom)",
                        "started":root.findtext("TimeStampStarted"),"finished":root.findtext("TimeStampFinished"),
                        "intensity_processing":"none", "archive_members":names}
            return Measurement(intensity, motors, units, Provenance.from_file(path,"Bruker BRML","brml-xml-eiger-v1"),
                               "recorded counts", fields.get("MeasuredTime"), wavelength, metadata, tuple(notes))
    except (zipfile.BadZipFile, KeyError, TypeError, AttributeError, ValueError) as exc:
        if isinstance(exc, (FormatError, UnsupportedFormatError)):
            raise
        raise FormatError(f"Cannot decode BRML {Path(path).name}: {exc}") from exc
