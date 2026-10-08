"""Plot settings affect display only, never measurements or fitting inputs."""
from __future__ import annotations
from pathlib import Path
import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize

from .models import RSM
from .processing import grid_rsm
from .errors import RSMError


def plot_rsm(rsm:RSM,*,intensity_scale="log",mode="points",bins=(400,400),
             components=(1,2),cmap="viridis",vmin=None,vmax=None,dynamic_range_decades=None,
             xlim=None,ylim=None,reflections=(),plane_tolerance=0.01,ax=None,title=None):
    """Raw points or explicit bin means, with no contour interpolation.

    Returns (figure, axes). Reflections require the same named frame, and their
    omitted coordinate must lie within plane_tolerance (angstrom^-1).
    Nonpositive log values are masked, warned and counted on the plot.
    """
    if len(components)!=2 or len(set(components))!=2 or any(c not in (0,1,2) for c in components):
        raise RSMError("Plot requires two distinct components from (0,1,2).")
    if intensity_scale not in ("linear","log") or mode not in ("points","grid"):
        raise RSMError("Use scale linear/log and mode points/grid.")
    if not np.isfinite(plane_tolerance) or plane_tolerance<0:
        raise RSMError("Reflection plane tolerance must be nonnegative finite.")
    if ax is None:
        fig,ax=plt.subplots(figsize=(8,6),layout="constrained")
    else:
        fig=ax.figure
    grid=None
    if mode=="grid":
        grid=grid_rsm(rsm,bins,components=components)
        values=grid.intensity
    else:
        values=rsm.intensity
    finite=np.isfinite(values)
    good=finite & (values>0) if intensity_scale=="log" else finite
    nonpositive=int(np.sum(finite & (values<=0))) if intensity_scale=="log" else 0
    if not good.any():
        raise RSMError("No valid intensities for the selected display scale.")
    if nonpositive:
        warnings.warn(f"Log display masks {nonpositive} nonpositive values; recorded data are unchanged.",UserWarning,stacklevel=2)
    high=float(np.max(values[good])) if vmax is None else float(vmax)
    low=float(np.min(values[good])) if vmin is None else float(vmin)
    if dynamic_range_decades is not None:
        if intensity_scale!="log" or not np.isfinite(dynamic_range_decades) or dynamic_range_decades<=0 or vmin is not None:
            raise RSMError("Dynamic range needs log scale, positive decades, and no explicit vmin.")
        low=high/10**dynamic_range_decades
    if not np.isfinite([low,high]).all() or (intensity_scale=="log" and low<=0) or high<low:
        raise RSMError("Invalid color limits.")
    if high==low:
        low,high=(low/2,high*2) if intensity_scale=="log" else (low-0.5,high+0.5)
    norm=LogNorm(low,high) if intensity_scale=="log" else Normalize(low,high)
    if grid is not None:
        artist=ax.pcolormesh(grid.x_edges,grid.y_edges,np.ma.array(values,mask=~good),
                             norm=norm,cmap=cmap,shading="flat",rasterized=True)
        display="bin mean of recorded counts; empty cells masked"
    else:
        x,y=rsm.q[...,components[0]],rsm.q[...,components[1]]
        good=good & np.isfinite(x) & np.isfinite(y)
        artist=ax.scatter(x[good],y[good],c=values[good],s=1,edgecolors="none",norm=norm,cmap=cmap,rasterized=True)
        display="recorded detector bins; no interpolation"
    fig.colorbar(artist,ax=ax,label=rsm.measurement.intensity_unit + (" (bin mean)" if mode=="grid" else ""),extend="min" if dynamic_range_decades else "neither")
    labels=("x","y","z")
    for setter,c in ((ax.set_xlabel,components[0]),(ax.set_ylabel,components[1])):
        setter(rf"$Q_{labels[c]}$ ($\mathrm{{\AA}}^{{-1}}$)")
    ax.set_title(title or "Reciprocal-space map")
    status="PROVISIONAL" if rsm.provisional else "Configured calibrated geometry"
    note=f"{status} | {rsm.frame}\n{display}"
    if nonpositive:
        note+=f"\n{nonpositive:,} nonpositive display values masked"
    ax.text(0.01,0.99,note,ha="left",va="top",transform=ax.transAxes,fontsize=8,
            bbox={"facecolor":"white","alpha":0.85,"edgecolor":"none"})
    omitted=next(i for i in range(3) if i not in components)
    for reflection in reflections:
        if reflection.frame!=rsm.frame:
            raise RSMError(f"Reflection frame {reflection.frame!r} differs from map frame {rsm.frame!r}.")
        if abs(reflection.q[omitted])>plane_tolerance:
            warnings.warn(f"Not drawing off-plane reflection {reflection.label}.",UserWarning,stacklevel=2)
            continue
        px,py=reflection.q[list(components)]
        ax.plot(px,py,"x",color="red",ms=8)
        ax.annotate(reflection.label+"\n"+reflection.status,(px,py),xytext=(5,5),textcoords="offset points",fontsize=7)
    if xlim is not None: ax.set_xlim(xlim)
    if ylim is not None: ax.set_ylim(ylim)
    return fig,ax


def save_figure(fig,path:str|Path,*,dpi=300):
    path=Path(path)
    if path.suffix.lower() not in (".png",".pdf",".svg"):
        raise RSMError("Figure output must be PNG, PDF or SVG.")
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=dpi)
