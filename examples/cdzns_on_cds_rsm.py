"""Reproduce both supplied CdZnS/CdS measurements without invented orientations.

Run after installation: python examples/cdzns_on_cds_rsm.py
File names identify sources only; no scientific tokens are parsed from them.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"outputs"/".mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rsm_toolkit import (Material,Sample,load_xrd,load_configuration,calculate_rsm,
                         plot_rsm,save_figure,export_data,brightest_point)

# These are actual sources, not parsed sample/reflection configuration.
SOURCES=("22-40_RSM_S0159.brml","2200_RSM_S0155.brml")


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,default=ROOT/"outputs")
    p.add_argument("--config",type=Path,default=ROOT/"examples"/"coplanar_provisional.json")
    p.add_argument("--mode",choices=("points","grid"),default="points")
    args=p.parse_args(argv)
    output=args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    sample=Sample(substrate=Material("CdS",crystal_structure="wurtzite",reference="User-supplied substrate identity; lattice unspecified"),
                  film=Material("CdZnS",crystal_structure="wurtzite",reference="User-supplied film identity; composition/lattice unspecified"))
    config=replace(load_configuration(args.config),sample=sample)
    report={"sample_context":"CdZnS film on CdS, supplied by user; not inferred from filenames",
            "orientation":None,"reflection_indices":None,"film_composition":None,
            "software_python":sys.version,"numpy":np.__version__,"matplotlib":matplotlib.__version__,
            "plot_settings":{"mode":args.mode,"scale":"log","cmap":"viridis","dynamic_range_decades":4},
            "measurements":[],"failed":[]}
    for i,name in enumerate(SOURCES):
        path=ROOT/"example_data"/name
        before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (path,path.with_suffix(".raw"))}
        brml=load_xrd(path)
        raw=load_xrd(path.with_suffix(".raw"))
        np.testing.assert_array_equal(brml.intensity.astype(np.float32),raw.intensity.astype(np.float32))
        for motor in ("Theta","TwoTheta","TwoThetaArm","Chi","Phi"):
            np.testing.assert_allclose(brml.motors[motor],raw.motors[motor],atol=2e-12,rtol=0)
        np.testing.assert_array_equal(brml.counting_time_s,raw.counting_time_s)
        np.testing.assert_equal(brml.wavelength_angstrom,raw.wavelength_angstrom)
        rsm=calculate_rsm(brml,config)
        raw_rsm=calculate_rsm(raw,config)
        q_difference=float(np.max(np.abs(rsm.q-raw_rsm.q)))
        np.testing.assert_allclose(rsm.q,raw_rsm.q,atol=2e-12,rtol=0)
        stem="cdzns_on_cds_rsm" if i==0 else "cdzns_on_cds_rsm_02"
        fig,_=plot_rsm(rsm,mode=args.mode,dynamic_range_decades=4,
                       title=f"CdZnS on CdS — measurement {i+1}")
        for ext in ("png","pdf","svg"):
            save_figure(fig,output/f"{stem}.{ext}")
        plt.close(fig)
        export_data(rsm,output/f"{stem}.npz")
        record={"brml":brml.summary(),"raw":raw.summary(),
                "paired_float32_intensities_identical":True,
                "maximum_Q_difference_angstrom_inverse":q_difference,
                "maximum_intensity_export_rounding":float(np.max(np.abs(brml.intensity-raw.intensity))),
                "brightest_measured_bin":brightest_point(rsm),"outputs_stem":stem,
                "warnings":list(rsm.warnings),"configuration":rsm.configuration}
        for f,digest in before.items():
            if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=digest:
                raise RuntimeError(f"Source unexpectedly changed: {f}")
        report["measurements"].append(record)
        print(f"Processed {name}: {brml.intensity.shape}, {stem}.png; provisional={rsm.provisional}")
    (output/"experimental_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
