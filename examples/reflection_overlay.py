"""Synthetic orientation illustration only, NOT configuration of the real data."""
import numpy as np
from rsm_toolkit import Lattice,Material,Orientation,reflection_position,AtomSite


def demonstrate():
    cell=Lattice.hexagonal(4.136,6.716)  # illustrative reference, not a measured film
    orientation=Orientation.from_surface(cell,(0,0,0,1),(1,-1,0,0))
    reference=Material("Illustrative hexagonal cell",cell)
    reflection=reflection_position(reference,(1,0,-1,2),orientation,frame="illustrative sample")
    print(reflection)
    print("Do not overlay on experimental data without a matching verified frame.")
    # Independent body-centering cancellation example, with a full-cell motif.
    bcc=Material("Example BCC",Lattice(3,3,3),sites=(AtomSite("A",(0,0,0)),AtomSite("A",(.5,.5,.5))))
    assert np.isclose(bcc.structure_factor((1,0,0),{"A":1}),0)


if __name__=="__main__": demonstrate()
