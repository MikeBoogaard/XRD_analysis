from pathlib import Path
from dataclasses import replace
import struct
import zipfile
import numpy as np
import pytest
from rsm_toolkit import *

ROOT=Path(__file__).resolve().parents[1]
PAIRS=("22-40_RSM_S0159","2200_RSM_S0155")


@pytest.mark.parametrize("stem",PAIRS)
def test_real_paired_exports(stem):
    b=load_xrd(ROOT/"new_data"/(stem+".brml"))
    r=load_xrd(ROOT/"new_data"/(stem+".raw"))
    assert b.intensity.shape==r.intensity.shape==(1401,477)
    np.testing.assert_array_equal(b.intensity.astype(np.float32),r.intensity.astype(np.float32))
    for motor in ("Theta","TwoTheta","TwoThetaArm","Chi","Phi"):
        np.testing.assert_allclose(b.motors[motor],r.motors[motor],atol=2e-12,rtol=0)
    assert b.wavelength_angstrom==r.wavelength_angstrom==1.5406
    np.testing.assert_array_equal(b.counting_time_s,r.counting_time_s)
    assert np.all(b.counting_time_s==.5)
    assert b.metadata["measurement_type"]=="UltraFastRSM"
    assert r.metadata["ranges"][0]["scan_type"]=="PSD Fix Scan"
    assert not b.intensity.flags.writeable
    # Compare with the source bytes, independently of the common model.
    with zipfile.ZipFile(ROOT/"new_data"/(stem+".brml")) as z:
        payload=z.read(next(n for n in z.namelist() if n.endswith(".bin")))
    np.testing.assert_array_equal(b.intensity.ravel(),np.frombuffer(payload,dtype="<f8"))


@pytest.mark.parametrize("magic",[b"RAW ",b"RAW2",b"RAW1.01",b"RAW5.00"])
def test_unknown_raw_variants(tmp_path,magic):
    p=tmp_path/"unrelated.raw"
    p.write_bytes(magic+b"\0"*100)
    with pytest.raises(UnsupportedFormatError,match="variant"):load_xrd(p)


@pytest.mark.parametrize("cut",[12,65,1515,3000,-1])
def test_truncated_raw(tmp_path,cut):
    source=(ROOT/"new_data"/(PAIRS[0]+".raw")).read_bytes()
    p=tmp_path/"truncated.raw"
    p.write_bytes(source[:cut])
    with pytest.raises(FormatError):load_xrd(p)


def test_bad_raw_lengths_and_scan_type(tmp_path):
    original=(ROOT/"new_data"/(PAIRS[0]+".raw")).read_bytes()
    broken=bytearray(original)
    struct.pack_into("<I",broken,65,0)
    p=tmp_path/"bad.raw";p.write_bytes(broken)
    with pytest.raises(FormatError,match="length"):load_xrd(p)
    broken=bytearray(original)
    # Locate first range by the declared global segment chain.
    pos=61
    while struct.unpack_from("<I",broken,pos)[0] not in (0,160):
        pos+=struct.unpack_from("<I",broken,pos+4)[0]
    broken[pos+32:pos+56]=b"Unknown Scan".ljust(24,b"\0")
    p.write_bytes(broken)
    with pytest.raises(UnsupportedFormatError,match="scan type"):load_xrd(p)


def rewrite_brml(source,target,transform):
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(target,"w") as dst:
        for name in src.namelist():
            payload=transform(name,src.read(name))
            if payload is not None:dst.writestr(name,payload)


def test_brml_missing_payload_and_unknown_profile(tmp_path):
    source=ROOT/"new_data"/(PAIRS[0]+".brml")
    target=tmp_path/"unnamed.zip"
    rewrite_brml(source,target,lambda n,b:None if n.endswith(".bin") else b)
    with pytest.raises(FormatError):load_xrd(target)
    rewrite_brml(source,target,lambda n,b:b.replace(b"8.6.2.0",b"9.0.0.0") if n.endswith("DataContainer.xml") else b)
    with pytest.raises(UnsupportedFormatError,match="profile"):load_xrd(target)


def test_brml_schema_axis_change_detected(tmp_path):
    source=ROOT/"new_data"/(PAIRS[0]+".brml")
    target=tmp_path/"changed.brml"
    rewrite_brml(source,target,lambda n,b:b.replace(b"<Start>17.5</Start>",b"<Start>18.5</Start>") if n.endswith("RawData0.xml") else b)
    with pytest.raises(FormatError,match="disagrees"):load_xrd(target)


def test_invalid_archive(tmp_path):
    p=tmp_path/"bad.brml";p.write_bytes(b"PKbad data")
    with pytest.raises(FormatError):load_xrd(p)


def test_filename_not_used(tmp_path):
    source=ROOT/"new_data"/(PAIRS[0]+".raw")
    renamed=tmp_path/"arbitrary_name.bin";renamed.write_bytes(source.read_bytes())
    a,b=load_xrd(source),load_xrd(renamed)
    np.testing.assert_array_equal(a.intensity,b.intensity)
    np.testing.assert_array_equal(a.motors["Theta"],b.motors["Theta"])
    assert a.source.sha256==b.source.sha256


def test_text_and_bad_columns(tmp_path):
    p=tmp_path/"anything.dat"
    p.write_text("10,5 20,2 0\n11,5 21,2 -4\n")
    a=load_xrd(p,wavelength_angstrom=1.5)
    np.testing.assert_array_equal(a.intensity,[0,-4])
    np.testing.assert_allclose(a.motors["Theta"],[10.5,11.5])
    p.write_text("1 2\n3 4\n")
    with pytest.raises(FormatError,match="width"):load_xrd(p)


def test_export_roundtrip(rsm,tmp_path):
    path=tmp_path/"roundtrip.npz"
    export_data(rsm,path)
    restored=load_export(path)
    np.testing.assert_array_equal(restored.q,rsm.q)
    np.testing.assert_array_equal(restored.intensity,rsm.intensity)
    assert restored.configuration==rsm.configuration
    assert restored.measurement.source==rsm.measurement.source
    for key in rsm.measurement.motors:
        np.testing.assert_array_equal(restored.measurement.motors[key],rsm.measurement.motors[key])
