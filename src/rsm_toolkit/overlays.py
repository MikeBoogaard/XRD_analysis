"""Explicit sample configuration and frame-safe reciprocal-lattice predictions."""
from dataclasses import replace
import numpy as np

from .crystallography import (Lattice, Material, Orientation, Sample, AtomSite,
                              reflection_position, vegard_lattice)
from .geometry import validate_rotation
from .errors import RSMError, MissingMetadataError


def object_keys(value, allowed, context):
    if not isinstance(value, dict):
        raise RSMError(f"{context} must be a JSON object.")
    unknown = set(value) - set(allowed)
    if unknown:
        raise RSMError(f"Unknown {context} keys: {sorted(unknown)}")
    return value


def lattice_from_config(value):
    if value is None:
        return None
    v = object_keys(value, ('system', 'a', 'b', 'c', 'alpha', 'beta', 'gamma'), 'lattice')
    system = v.get('system', 'general')
    if system == 'hexagonal':
        if set(v) - {'system', 'a', 'c'}:
            raise RSMError("Hexagonal lattice takes only a and c in angstrom.")
        return Lattice.hexagonal(v['a'], v['c'])
    if system != 'general':
        raise RSMError("Lattice system must be general or hexagonal.")
    return Lattice(**{k: x for k, x in v.items() if k != 'system'})


def phase_from_config(value):
    if value is None:
        return None, None
    v = object_keys(value, ('name', 'crystal_structure', 'composition', 'lattice',
                           'vegard', 'orientation', 'reflections', 'reference', 'sites'), 'phase')
    cell = lattice_from_config(v.get('lattice'))
    composition = v.get('composition')
    if composition is not None:
        if not isinstance(composition, dict) or any(
                not isinstance(x, (int, float)) or isinstance(x, bool) or
                not np.isfinite(x) or not 0 <= x <= 1 for x in composition.values()):
            raise RSMError("Composition fractions must be finite numbers in [0,1], or composition null.")
    if v.get('vegard') is not None:
        if cell is not None:
            raise RSMError("Choose an explicit lattice OR a Vegard model, not both.")
        model = object_keys(v['vegard'], ('first', 'second', 'fraction_second'), 'vegard')
        x = model.get('fraction_second')
        if x is None:
            raise MissingMetadataError("Vegard fraction_second is unknown; no alloy fraction is assumed.")
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise RSMError("Vegard fraction_second must be a number.")
        first, second = lattice_from_config(model['first']), lattice_from_config(model['second'])
        if first is None or second is None:
            raise MissingMetadataError("Vegard model requires both end-member lattices.")
        cell = vegard_lattice(first, second, x)
    orientation = None
    if v.get('orientation') is not None:
        o = object_keys(v['orientation'], ('surface_plane', 'in_plane_direction',
                                          'crystal_to_sample'), 'orientation')
        if o.get('crystal_to_sample') is not None:
            if o.get('surface_plane') is not None or o.get('in_plane_direction') is not None:
                raise RSMError("Choose orientation indices OR crystal_to_sample matrix.")
            orientation = Orientation(o['crystal_to_sample'])
        elif o.get('surface_plane') is not None and o.get('in_plane_direction') is not None:
            if cell is None:
                raise MissingMetadataError("Orientation indices require a lattice.")
            orientation = Orientation.from_surface(cell, o['surface_plane'], o['in_plane_direction'])
    sites = tuple(AtomSite(**s) for s in v.get('sites', []))
    return Material(v['name'], cell, v.get('crystal_structure'), composition,
                    sites, v.get('reference')), orientation


def sample_from_config(value):
    if value is None:
        return None
    v = object_keys(value, ('identifier', 'substrate', 'film', 'frame_alignment'), 'sample')
    substrate, so = phase_from_config(v.get('substrate'))
    film, fo = phase_from_config(v.get('film'))
    return Sample(substrate, film, so, fo, v.get('identifier'))


def configured_reflections(config, rsm):
    """Resolve reflections only with an explicit sample-to-map rotation and evidence.

    A frame name alone never establishes alignment. Returns reflections
    and a JSON-safe report of full vectors (including the omitted coordinate).
    """
    settings = config.plot_settings
    if not settings.get('theoretical_overlays', False):
        return (), []
    raw = config.sample_settings
    sample = config.sample
    if raw is None or sample is None:
        raise MissingMetadataError("Theoretical overlays require sample configuration.")
    alignment = raw.get('frame_alignment')
    if alignment is None:
        raise MissingMetadataError("Missing sample.frame_alignment; no theoretical markers drawn.")
    a = object_keys(alignment, ('map_frame', 'sample_to_map', 'verified', 'reference',
                                'allow_provisional'), 'frame_alignment')
    if a.get('map_frame') != rsm.frame or a.get('sample_to_map') is None:
        raise MissingMetadataError("Frame alignment requires the exact map_frame and sample_to_map rotation.")
    for key in ('verified', 'allow_provisional'):
        if type(a.get(key, False)) is not bool:
            raise RSMError(f"frame_alignment.{key} must be boolean.")
    if not isinstance(a.get('reference'), str) or not a['reference'].strip():
        raise MissingMetadataError("Frame alignment needs a reference describing mounting evidence or explicit assumptions.")
    rotation = validate_rotation(a['sample_to_map'])
    components = settings.get('components', (1, 2))
    if len(components) != 2 or len(set(components)) != 2 or any(c not in (0, 1, 2) for c in components):
        raise RSMError("Plot components must be two distinct indices from 0,1,2.")
    omitted = next(i for i in range(3) if i not in components)
    tolerance = settings.get('plane_tolerance', 0.01)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise RSMError("plane_tolerance must be finite and nonnegative.")
    reflections, report = [], []
    for role in ('substrate', 'film'):
        material = getattr(sample, role)
        if material is None:
            continue
        orientation = getattr(sample, role + '_orientation')
        indices = raw[role].get('reflections')
        if orientation is None or material.lattice is None or not indices:
            raise MissingMetadataError(f"{role}: lattice, orientation and reflections are required for overlays.")
        for h in indices:
            predicted = reflection_position(material, h, orientation, frame=rsm.frame)
            q = rotation @ predicted.q
            if np.linalg.norm(q) > 4*np.pi/rsm.wavelength_angstrom + 1e-12:
                raise RSMError(f"{role} {h}: reflection is inaccessible at the configured wavelength.")
            if abs(q[omitted]) > tolerance:
                raise RSMError(f"{role} {h}: off-plane Q{omitted}={q[omitted]:.6g}; no projection onto measured plane.")
            status = predicted.status
            reflection = replace(predicted, q=q, label=f"{role}: {predicted.label}", status=status,
                                 marker='o' if role == 'substrate' else 'D',
                                 color='cyan' if role == 'substrate' else 'magenta')
            reflections.append(reflection)
            report.append({'role': role, 'label': reflection.label, 'indices': list(h),
                           'q_angstrom_inverse': q.tolist(), 'frame': rsm.frame,
                           'd_angstrom': material.lattice.d_spacing(h), 'status': status,
                           'lattice': {'a': material.lattice.a, 'b': material.lattice.b,
                                       'c': material.lattice.c, 'alpha': material.lattice.alpha,
                                       'beta': material.lattice.beta, 'gamma': material.lattice.gamma}})
    if not reflections:
        raise MissingMetadataError("No configured phases/reflections for requested overlays.")
    return tuple(reflections), report


def plot_configured_rsm(rsm, config, **overrides):
    """Plot with configured markers; return figure, axes, numerical theory report."""
    from .plotting import plot_rsm
    settings = {**config.plot_settings, **overrides}
    settings.pop('theoretical_overlays', None)
    effective = replace(config, plot_settings={**config.plot_settings, **overrides})
    reflections, report = configured_reflections(effective, rsm)
    fig, ax = plot_rsm(rsm, reflections=reflections, **settings)
    return fig, ax, report
