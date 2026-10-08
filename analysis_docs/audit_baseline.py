"""Read-only repository audit; writes evidence only under analysis_docs.

Run from repository root: python -B analysis_docs/audit_baseline.py
Does not install dependencies, patch modules, or execute notebook magics.
"""
import sys
sys.dont_write_bytecode = True
import os
from pathlib import Path
import hashlib
import json
import importlib
import traceback
import zipfile
import xml.etree.ElementTree as ET
import math

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'analysis_docs'
sys.path.insert(0, str(ROOT))
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = str(OUT / '.mplconfig')

def inventory():
    return {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(ROOT.rglob('*')) if p.is_file() and 'analysis_docs' not in p.relative_to(ROOT).parts}

before = inventory()
report = {'python': sys.version, 'files': before, 'dependencies': {}, 'imports': {}, 'datasets': {}, 'workbook': {}, 'checks': {}}
for name in ['numpy', 'scipy', 'matplotlib', 'pandas', 'xrayutilities', 'lmfit']:
    try:
        mod = importlib.import_module(name)
        report['dependencies'][name] = getattr(mod, '__version__', 'unknown')
    except Exception:
        report['dependencies'][name] = traceback.format_exc()
for name in ['geometry', 'data_procesing', 'plotting', 'fitting', 'theory', 'line_scan', 'data_analysis', 'Colorsheme']:
    try:
        importlib.import_module('Modules.' + name)
        report['imports'][name] = 'success'
    except Exception:
        report['imports'][name] = traceback.format_exc()

import numpy as np
import pandas as pd
for p in sorted(ROOT.rglob('*.dat')):
    df = pd.read_csv(p, delimiter=r'\s+', decimal=',', engine='python', header=None)
    a = df.values
    u, counts = np.unique(a[:, 0], return_counts=True)
    report['datasets'][p.relative_to(ROOT).as_posix()] = {
        'shape': list(a.shape), 'dtypes': [str(v) for v in df.dtypes],
        'min': a.min(axis=0).tolist(), 'max': a.max(axis=0).tolist(),
        'nonfinite': int((~np.isfinite(a)).sum()), 'negative_intensity': int((a[:,2]<0).sum()),
        'zero_intensity': int((a[:,2]==0).sum()), 'unique_omega': len(u),
        'omega_step_min_max': [float(np.diff(u).min()), float(np.diff(u).max())],
        'rows_per_omega_min_max': [int(counts.min()), int(counts.max())],
        'unique_tt': len(np.unique(a[:,1])), 'duplicate_angle_pairs': int(df.duplicated(subset=[0,1]).sum()),
        'first_row': a[0].tolist(), 'last_row': a[-1].tolist(),
        'minimum_intensity_line': int(np.argmin(a[:,2]))+1,
        'maximum_intensity_line': int(np.argmax(a[:,2]))+1,
        'first_omega_tt_range': [float(a[a[:,0]==u[0],1].min()),float(a[a[:,0]==u[0],1].max())],
        'last_omega_tt_range': [float(a[a[:,0]==u[-1],1].min()),float(a[a[:,0]==u[-1],1].max())],
        'rounded_tt_unique': len(np.unique(np.round(a[:,1],4))),
        'COM_dense_matrix_bytes': int(len(u)*len(np.unique(np.round(a[:,1],4)))*8)}

# Inspect OOXML directly: preserve formulas and cached values, without recalculation.
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(ROOT/'Literature data for analysis'/'Reflections.xlsx') as z:
    strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
    report['workbook']['sheets'] = [n.attrib for n in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns)]
    for name in z.namelist():
        if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
            cells = {}
            for c in ET.fromstring(z.read(name)).findall('.//s:sheetData/s:row/s:c',ns):
                value = c.find('s:v',ns)
                formula = c.find('s:f',ns)
                v = value.text if value is not None else None
                if c.get('t') == 's' and v is not None: v = strings[int(v)]
                if c.get('t') == 'inlineStr': v = ''.join(c.find('s:is',ns).itertext())
                if v is not None or formula is not None:
                    cells[c.get('r')] = {'value': v, 'formula': formula.text if formula is not None else None}
            report['workbook'][name] = cells

from Modules import line_scan, data_analysis
report['checks']['mean_strip'] = [v.tolist() for v in line_scan.average_psd_over_axis(np.array([1,1,2]),np.array([0,0,1]),np.array([2.,4.,8.]),1,0)]
for label, a in [('zero_com', np.zeros((3,3))), ('single_com', np.array([[1.,2.],[3.,4.],[0.,10.]]))]:
    try: report['checks'][label] = list(data_analysis.find_max_tt_om(a,None,None))
    except Exception: report['checks'][label] = traceback.format_exc()
report['checks']['missing_filename_tokens'] = {f: getattr(data_analysis,f)('other.dat') for f in ['read_key_reflection','read_sampleID','read_inplane_direction','read_Temp','read_Norm']}
hc = 12398.419843320026
lam = hc / 8047.8
report['independent_physics'] = {'hc_eV_A': hc, 'wavelength_A': lam, 'theory_300': {}}
for mat,a in [('CdS',4.136), ('Ge',3.9855)]:
    q = 2*math.pi*math.sqrt(12/a**2)
    theta = math.degrees(math.asin(lam*q/(4*math.pi)))
    report['independent_physics']['theory_300'][mat] = {'Q_A^-1':q,'theta_deg':theta,'tt_deg':2*theta,'omega_theta_minus_30_deg':theta-30}
after = inventory()
report['original_files_unchanged'] = before == after
(OUT/'baseline_evidence.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item()),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['files','workbook','imports']},indent=2,default=lambda x:x.item()))
print('Workbook cells:', json.dumps(report['workbook'],ensure_ascii=False))
