"""One-time reproducible, non-destructive archive of retired implementation.

Run from any directory. Refuses to overwrite an existing archive. Deletion of
the original paths is a separate operation after byte-level verification.
"""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT/'docs/legacy_source.zip'
files = sorted((ROOT/'Modules').glob('*.py')) + [ROOT/'RSM_main.ipynb', ROOT/'Theoretical_RSM_main.ipynb']
files += sorted((ROOT/'__pycache__').glob('*.pyc'))
manifest = {}
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        payload = path.read_bytes()
        manifest[name] = hashlib.sha256(payload).hexdigest()
        z.writestr(name, payload)
with zipfile.ZipFile(archive) as z:
    for name, digest in manifest.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == digest
        assert z.read(name) == (ROOT/name).read_bytes()
(ROOT/'docs/legacy_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
parts = ['# Retired notebook scientific content\n',
         'Verbatim cell sources and textual outputs; embedded images and complete metadata remain in [legacy_source.zip](legacy_source.zip). These are historical observations, not validated inputs for new scans.\n']
for path in files:
    if path.suffix != '.ipynb':
        continue
    parts.append(f'\n## {path.name}\n')
    notebook=json.loads(path.read_text(encoding='utf-8'))
    for index, cell in enumerate(notebook['cells']):
        parts.append(f'\n### Cell {index+1} ({cell["cell_type"]})\n\n````text\n'+''.join(cell.get('source',[]))+'\n````\n')
        for output in cell.get('outputs',[]):
            value = output.get('text',output.get('data',{}).get('text/plain',[]))
            if value:
                parts.append('\nStored output:\n\n````text\n'+''.join(value)+'\n````\n')
            if output.get('ename'):
                parts.append(f'\nStored error: {output["ename"]}: {output.get("evalue", "")}\n')
(ROOT/'docs/legacy_notebook_content.md').write_text(''.join(parts),encoding='utf-8')
print(f'Archived and byte-verified {len(manifest)} files; originals not deleted.')
