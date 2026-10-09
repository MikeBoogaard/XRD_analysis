"""Cell metrics from the bundled crystallographic reference files."""
from importlib.resources import files
import re
import shlex
from .crystallography import Lattice
from .errors import RSMError

CIF_MATERIALS = {
    'CdS': 'CdS.cif',
    'ZnS (wurtzite)': 'ZnS.cif',
    'ZnS (wurtzite, mp-560588)': 'ZnS_WZ_mp-560588_conventional_standard.cif',
    'Ge (cubic)': 'Ge_mp-32_conventional_standard.cif',
    'Ge (hexagonal)': 'Hex_Ge_100_paper.cif',
}


def reference_material(name):
    """Read scalar cell fields; no symmetry expansion or intensity calculation."""
    filename=CIF_MATERIALS[name]
    content=files('rsm_toolkit').joinpath('data','cif',filename).read_text(encoding='utf-8')
    fields={}
    for line in content.splitlines():
        if line.strip().startswith('_'):
            tokens=shlex.split(line,comments=True)
            if len(tokens)==2:
                fields[tokens[0]]=tokens[1]
    keys=('_cell_length_a','_cell_length_b','_cell_length_c',
          '_cell_angle_alpha','_cell_angle_beta','_cell_angle_gamma')
    try:
        values=[float(re.sub(r'\(\d+\)$','',fields[k])) for k in keys]
        cell=Lattice(*values)
    except (KeyError,ValueError) as exc:
        raise RSMError(f'Invalid cell metric in bundled {filename}.') from exc
    return dict(name=name,lattice=dict(zip(('a','b','c','alpha','beta','gamma'),values)),
                crystal_structure=fields.get('_symmetry_space_group_name_H-M'),
                reference=f'Bundled CIF: {filename}; cell lengths and angles'),cell
