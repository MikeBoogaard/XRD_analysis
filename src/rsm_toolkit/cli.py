"""Inspect measurements and reconstruct with explicit JSON geometry."""
from pathlib import Path
import argparse
import json
import sys


def main(argv=None):
    parser=argparse.ArgumentParser(prog="rsm-toolkit")
    subs=parser.add_subparsers(dest="command",required=True)
    inspect=subs.add_parser("inspect",help="Report measurement dimensions, axes, units and warnings")
    inspect.add_argument("files",nargs="+")
    map_parser=subs.add_parser("map",help="Calculate a map using explicit geometry configuration")
    map_parser.add_argument("file")
    map_parser.add_argument("--config",required=True)
    map_parser.add_argument("--output",required=True,help="PNG/PDF/SVG path; also writes same-stem NPZ/JSON")
    map_parser.add_argument("--mode",choices=("points","grid"),default=None)
    map_parser.add_argument("--scale",choices=("linear","log"),default=None)
    args=parser.parse_args(argv)
    import matplotlib
    matplotlib.use("Agg")
    from . import load_xrd,load_configuration,calculate_rsm,plot_rsm,save_figure,export_data,brightest_point
    from .errors import RSMError
    from .overlays import plot_configured_rsm
    from dataclasses import replace
    try:
        if args.command=="inspect":
            print(json.dumps([load_xrd(p).summary() for p in args.files],indent=2))
        else:
            config=load_configuration(args.config)
            rsm=calculate_rsm(load_xrd(args.file),config)
            overrides={}
            if args.mode is not None: overrides['mode']=args.mode
            if args.scale is not None: overrides['intensity_scale']=args.scale
            fig,_,theory=plot_configured_rsm(rsm,config,**overrides)
            rsm=replace(rsm,configuration={**rsm.configuration,
                        'plot_settings':{**config.plot_settings,**overrides},'theoretical_reflections':theory})
            target=Path(args.output)
            save_figure(fig,target)
            export_data(rsm,target.with_suffix(".npz"))
            print(json.dumps(brightest_point(rsm),indent=2))
        return 0
    except (RSMError,OSError) as exc:
        print(f"rsm-toolkit: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
