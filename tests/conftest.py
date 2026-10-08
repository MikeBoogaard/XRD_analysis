from pathlib import Path
import os
os.environ["MPLBACKEND"]="Agg"
os.environ["MPLCONFIGDIR"]=str(Path(__file__).resolve().parents[1]/"outputs"/".mplconfig")
import pytest
import numpy as np
from rsm_toolkit import Measurement,Provenance,RSMConfiguration,CoplanarGeometry,calculate_rsm

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def measurement():
    om,tt=np.meshgrid(np.linspace(18,22,15),np.linspace(38,42,11),indexing="ij")
    intensity=2+100*np.exp(-((om-20)**2+(tt-40)**2))
    return Measurement(intensity,{"Theta":om,"TwoTheta":tt},{"Theta":"degree","TwoTheta":"degree"},
                       Provenance("synthetic","synthetic","synthetic","test"),"recorded counts",
                       np.ones_like(intensity)*2,1.54)


@pytest.fixture
def rsm(measurement):
    return calculate_rsm(measurement,RSMConfiguration(CoplanarGeometry(),allow_provisional=True))
