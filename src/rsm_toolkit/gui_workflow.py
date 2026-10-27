"""Desktop form validation and run preparation, independent of Tk widgets."""
from __future__ import annotations
import json
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import numpy as np
from .crystallography import Lattice, Orientation, plane_indices, direction_indices
from .errors import RSMError
from .material_library import CIF_MATERIALS, reference_material


def defaults():
    return dict(file='', output=str(Path.cwd()/'outputs'), name='my_map', title='Reciprocal-space map',
                overlays=False, substrate='CdS', film='CdZnS Vegard', zinc='',
                substrate_name='Substrate', substrate_cell='',
                film_name='Film', film_cell='',
                norm='', reflection='', inplane='',
                aligned=True, film_norm='', film_reflection='', film_inplane='',
                sense='Choose axis sense', omega_offset='0', detector_offset='0',
                fwhm_search_tt='0.5', fwhm_search_omega='1', fwhm_window='2', fwhm=False, fwhm_center='', fwhm_half_width='0.2', fwhm_min='', fwhm_max='',
                wavelength='', scale='log', mode='points', decades='4')


def fwhm_selection(form):
    if not form.get('fwhm',False):return None
    values=[number(form[k],label) for k,label in (
        ('fwhm_center','Film 2theta center'),('fwhm_half_width','2theta half width'),
        ('fwhm_min','Minimum omega'),('fwhm_max','Maximum omega'))]
    center,half,low,high=values
    if half<=0 or low>=high or center-half<0 or center+half>180:
        raise RSMError('FWHM: use a positive band half width, increasing omega range and 2theta band within 0?180 degrees.')
    return values


def theoretical_fwhm_fields(form):
    """Suggest corrected physical angles; window is user-selected, not predicted width."""
    from .overlays import phase_from_config
    from .crystallography import reflection_position
    from . import load_xrd
    f={**defaults(),**form}
    config=build_configuration({**f,'overlays':True})
    raw=config['sample']['film']
    if raw is None:raise RSMError('Choose a film material before filling FWHM from theory.')
    material_model,film_orientation=phase_from_config(raw)
    q=reflection_position(material_model,raw['reflections'][0],film_orientation,
                          frame=config['geometry']['frame']).q
    q=np.asarray(config['sample']['frame_alignment']['sample_to_map'])@q
    if abs(q[0])>1e-8:
        raise RSMError('Film reflection is off the coplanar scattering plane; check its orientation and InPlane.')
    wavelength=config['wavelength_angstrom']
    if wavelength is None:
        if not Path(f['file']).is_file():
            raise RSMError('Select a measurement for its wavelength, or enter wavelength on Advanced.')
        wavelength=load_xrd(f['file']).wavelength_angstrom
    if wavelength is None:raise RSMError('No wavelength in measurement; enter it on Advanced.')
    ratio=np.linalg.norm(q)*wavelength/(4*np.pi)
    if not 0<ratio<=1:raise RSMError('Film reflection is inaccessible at this wavelength.')
    theta=np.degrees(np.arcsin(ratio))
    # Qy = |Q| sin(omega-theta), Qz = |Q| cos(omega-theta).
    omega=theta+np.degrees(np.arctan2(q[1],q[2]))
    if not 0<omega<2*theta:
        raise RSMError('Film reflection is outside the reflection-geometry branch; check orientation and axis sense.')
    window=number(f['fwhm_window'],'Suggested omega half width')
    if window<=0:raise RSMError('Suggested omega half width must be positive.')
    return {'fwhm_center':format(2*theta,'.10g'),
            'fwhm_min':format(omega-window,'.10g'),'fwhm_max':format(omega+window,'.10g')}


def measured_fwhm_fields(form):
    """Brightest finite positive raw bin in an explicit angular box near theory."""
    from . import load_xrd
    f={**defaults(),**form}
    if not Path(f['file']).is_file():raise RSMError('Select a measurement before searching for a measured peak.')
    tt_radius=number(f['fwhm_search_tt'],'2theta search half width')
    om_radius=number(f['fwhm_search_omega'],'Omega search half width')
    if min(tt_radius,om_radius)<=0:raise RSMError('Search half widths must be positive.')
    m=load_xrd(f['file'])
    # Use the file wavelength if no explicit wavelength was entered; avoid a second read.
    if not f['wavelength'].strip() and m.wavelength_angstrom is not None:
        f['wavelength']=str(m.wavelength_angstrom)
    theory=theoretical_fwhm_fields(f)
    tt0=float(theory['fwhm_center'])
    om0=(float(theory['fwhm_min'])+float(theory['fwhm_max']))/2
    angles=[]
    for motor,offset in (('Theta','omega_offset'),('TwoTheta','detector_offset')):
        if motor not in m.motors:raise RSMError(f'Missing search motor {motor}.')
        unit=m.motor_units[motor]
        if unit not in ('degree','radian'):raise RSMError('Peak search requires angular motor units.')
        a=np.rad2deg(m.motors[motor]) if unit=='radian' else m.motors[motor]
        angles.append(a+number(f[offset],offset))
    om,tt=angles
    keep=(np.abs(om-om0)<=om_radius)&(np.abs(tt-tt0)<=tt_radius)
    keep &= np.isfinite(om)&np.isfinite(tt)&np.isfinite(m.intensity)&(m.intensity>0)
    if not keep.any():raise RSMError('No positive finite measured samples in the search region. Review theory, offsets or search widths.')
    index=np.unravel_index(np.argmax(np.where(keep,m.intensity,-np.inf)),m.intensity.shape)
    measured_om,measured_tt=float(om[index]),float(tt[index])
    window=number(f['fwhm_window'],'Suggested omega half width')
    fields={'fwhm_center':format(measured_tt,'.10g'),
            'fwhm_min':format(measured_om-window,'.10g'),'fwhm_max':format(measured_om+window,'.10g')}
    report=(f'Measured maximum: 2theta {measured_tt:.5f}, omega {measured_om:.5f} degrees. '
            f'Shift from theory: {measured_tt-tt0:+.5f}, {measured_om-om0:+.5f} degrees. '
            'Brightest recorded bin, not a fitted center or confirmed film identification. '
            'Check for substrate peaks or hot pixels; narrow the search if needed.')
    if abs(measured_om-om0)>.9*om_radius or abs(measured_tt-tt0)>.9*tt_radius:
        report+=' Maximum is near a search boundary; review the search limits.'
    return fields,report


def indices(text, *, direction=False):
    value=str(text).strip().replace('\u2212','-')
    value=value.translate(str.maketrans({'[':'',']':'','(':'',')':''}))
    if not value:
        raise RSMError('Enter Norm, RSM and InPlane when theoretical markers are enabled.')
    if re.search(r'[,;\s]',value):
        tokens=re.split(r'[,;\s]+',value)
        if any(not re.fullmatch(r'[+-]?\d+',t) for t in tokens):
            raise RSMError('Indices must be integers separated by spaces or commas.')
    else:
        tokens=re.findall(r'-?\d',value)
        if ''.join(tokens)!=value or len(tokens)!=4:
            raise RSMError('Use four compact single-digit indices (11-20), or separated indices (1 1 -2 0).')
    h=list(map(int,tokens))
    (direction_indices if direction else plane_indices)(h)
    return h


def number(value, name):
    try:
        result=float(value)
    except (TypeError,ValueError) as exc:
        raise RSMError(f'{name}: enter a number.') from exc
    if not np.isfinite(result):
        raise RSMError(f'{name}: enter a finite number.')
    return result


def orientation(cell, norm, inplane):
    return Orientation.from_surface(cell,indices(norm),indices(inplane,direction=True))


def material(form, role):
    choice=form[role]
    if choice=='None' and role=='film':
        return None, None
    if choice in CIF_MATERIALS:
        return reference_material(choice)
    if choice=='CdZnS Vegard':
        x=number(form['zinc'],'Zn percentage')/100
        if not 0<=x<=1:
            raise RSMError('Zn percentage must be between 0 and 100.')
        cell=Lattice.hexagonal((1-x)*4.136+x*3.80579647,(1-x)*6.716+x*6.23798163)
        return dict(name='CdZnS',crystal_structure='wurtzite alloy model',
                    composition={'Zn_cation_fraction':x},
                    vegard=dict(first=dict(system='hexagonal',a=4.136,c=6.716),
                                second=dict(system='hexagonal',a=3.80579647,c=6.23798163),
                                fraction_second=x),
                    reference='Relaxed linear Vegard model using repository CdS/ZnS cells; strain not modeled'),cell
    if choice!='Custom cell':
        raise RSMError(f'Unsupported {role} material choice.')
    tokens=re.split(r'[,;\s]+',form[role+'_cell'].strip())
    if len(tokens)!=6:
        raise RSMError(f'{role} cell needs a, b, c, alpha, beta, gamma (angstrom / degrees).')
    cell=Lattice(*[number(t,role+' cell') for t in tokens])
    name=form[role+'_name'].strip()
    if not name:
        raise RSMError(f'Enter a {role} name.')
    return dict(name=name,lattice=dict(zip(('a','b','c','alpha','beta','gamma'),
                                          (cell.a,cell.b,cell.c,cell.alpha,cell.beta,cell.gamma))),
                reference='User-supplied cell; geometric positions, no extinction model'),cell


def build_configuration(values):
    f={**defaults(),**values}
    for k in ('overlays','aligned'):
        if type(f[k]) is not bool:
            raise RSMError(f'{k} must be boolean.')
    wavelength=number(f['wavelength'],'Wavelength') if f['wavelength'].strip() else None
    if wavelength is not None and wavelength<=0:
        raise RSMError('Wavelength must be positive.')
    geometry=dict(type='coplanar',omega_motor='Theta',detector_motor='TwoTheta',
                  omega_sign=1,detector_sign=1,omega_offset_deg=number(f['omega_offset'],'Omega offset'),
                  detector_offset_deg=number(f['detector_offset'],'2theta offset'),
                  calibration_verified=False,calibration_reference=None,
                  frame='sample coplanar')
    plot=dict(title=f['title'],theoretical_overlays=f['overlays'],mode=f['mode'],intensity_scale=f['scale'])
    if f['mode'] not in ('points','grid') or f['scale'] not in ('log','linear'):
        raise RSMError('Choose points/grid and log/linear.')
    if f['scale']=='log' and f['decades'].strip():
        decades=number(f['decades'],'Color range')
        if not 0<decades<=20:
            raise RSMError('Color range must be between 0 and 20 decades.')
        plot['dynamic_range_decades']=decades
    result=dict(geometry=geometry,wavelength_angstrom=wavelength,plot=plot,
                notes='Coplanar reconstruction. InPlane is a direct crystal direction. '+
                      'No automatic offset or peak alignment. Input fields are saved in settings.json.')
    if not f['overlays']:
        return result
    if f['sense'] not in ('Along InPlane (+y)','Opposite InPlane (+y)'):
        raise RSMError('Choose the map +Qy axis sense on the Advanced tab; it is not inferred from peaks.')
    sub,cell=material(f,'substrate')
    so=orientation(cell,f['norm'],f['inplane'])
    sub.update(orientation={'crystal_to_sample':so.crystal_to_sample.tolist()},
               reflections=[indices(f['reflection'])])
    film,fc=material(f,'film')
    if film is not None:
        fo=so if f['aligned'] else orientation(fc,f['film_norm'],f['film_inplane'])
        film.update(orientation={'crystal_to_sample':fo.crystal_to_sample.tolist()},
                    reflections=[indices(f['film_reflection'] or f['reflection'])])
    flip=f['sense']=='Opposite InPlane (+y)'
    result['sample']=dict(identifier=f['name'],substrate=sub,film=film,
                         frame_alignment=dict(map_frame=geometry['frame'],
                             sample_to_map=np.diag([-1,-1,1] if flip else [1,1,1]).tolist(),
                             reference='User-selected coplanar sample frame; '+f['sense']))
    return result


def preset(asymmetric=False):
    f=defaults()
    f.update(norm='11-20',reflection='12-30' if asymmetric else '11-20',
             inplane='1-100' if asymmetric else '0001',zinc='35',overlays=True,
             sense='Opposite InPlane (+y)' if asymmetric else 'Along InPlane (+y)',
             name='CdZnS_12-30' if asymmetric else 'CdZnS_11-20',
             title='Cd0.65Zn0.35S / CdS - relaxed alloy model')
    return f


def save_settings(path, form):
    Path(path).write_text(json.dumps({'schema':'rsm-gui-2','fields':form},indent=2)+'\n',encoding='utf-8')


def load_settings(path):
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
        if value.get('schema') not in ('rsm-gui-1','rsm-gui-2') or not isinstance(value.get('fields'),dict):
            raise RSMError('Select a GUI settings.json file, not a run configuration or data sidecar.')
        if value['schema']=='rsm-gui-1':
            fields=value['fields']
            if fields.get('convention')=='Old InPlane: reciprocal reference' and fields.get('overlays'):
                raise RSMError('This settings file uses reciprocal-reference indices. Enter the equivalent direct InPlane direction in a new form, then save it. Indices have not been reinterpreted.')
            fields.pop('convention',None)
            fields.pop('nominal',None)
            for role in ('substrate','film'):
                if fields.get(role)=='CdS reference':fields[role]='CdS'
        unknown=set(value['fields'])-set(defaults())
        if unknown:
            raise RSMError(f'Unknown GUI fields: {sorted(unknown)}')
        for key,v in value['fields'].items():
            expected=bool if key in ('overlays','aligned','fwhm') else str
            if type(v) is not expected:
                raise RSMError(f'Invalid type for saved setting {key}.')
        return {**defaults(),**value['fields']}
    except (ValueError,AttributeError) as exc:
        raise RSMError(f'Invalid settings file: {exc}') from exc


def execute(form, *, output_parent=None):
    """Worker pipeline. Creates a unique run folder and records failures there."""
    from . import load_xrd, load_configuration, calculate_rsm, plot_configured_rsm, save_figure, export_data
    import matplotlib.pyplot as plt
    source=Path(form['file']).expanduser()
    if not source.is_file():
        raise RSMError('Select an existing measurement file.')
    config=build_configuration(form)
    selection=fwhm_selection(form)
    m=load_xrd(source)
    safe=re.sub(r'[^\w.-]+','_',form['name']).strip(' ._') or 'map'
    parent=Path(form['output'] if output_parent is None else output_parent).expanduser()
    parent.mkdir(parents=True,exist_ok=True)
    folder=parent/(safe+'_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir()  # Exclusive creation; previous plots are never overwritten.
    fig=None
    try:
        save_settings(folder/'settings.json',form)
        (folder/'run.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
        c=load_configuration(folder/'run.json')
        r=calculate_rsm(m,c)
        fig,axes,theory=plot_configured_rsm(r,c)
        r=replace(r,configuration={**r.configuration,'theoretical_reflections':theory})
        if selection is not None:
            from .film_fwhm import analyze
            try:
                analyze(r,c.geometry,selection,folder,axes)
            except RSMError as exc:
                (folder/'FWHM_FAILED.txt').write_text(str(exc),encoding='utf-8')
        save_figure(fig,folder/'map.png')
        export_data(r,folder/'map.npz')
        return folder
    except Exception as exc:
        (folder/'FAILED.txt').write_text(str(exc),encoding='utf-8')
        raise
    finally:
        if fig is not None:
            plt.close(fig)


def save_preview(source, output):
    """Copy the completed preview, without recalculating or changing its settings."""
    import shutil
    source=Path(source)
    if not (source/'map.png').is_file():raise RSMError('Plot a map before saving results.')
    parent=Path(output).expanduser()
    parent.mkdir(parents=True,exist_ok=True)
    name=load_settings(source/'settings.json')['name']
    safe=re.sub(r'[^\w.-]+','_',name).strip(' ._') or 'map'
    target=parent/(safe+'_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    shutil.copytree(source,target)  # Exclusive destination; never overwrites a previous run.
    return target
