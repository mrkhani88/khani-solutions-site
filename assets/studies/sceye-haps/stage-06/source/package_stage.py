"""Package the frozen compact study and publishable static assets.

Usage: python3 source/package_stage.py /absolute/website/checkout
Run only after engineering, documents and frontend have finished writing.
No deploy or credential operations. Existing study assets are preserved.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile

B=Path(__file__).resolve().parents[1]
ZIP_NAME='Stage-06-Interview-Evidence-R1.zip'
EXCLUDED={'existing-thermal-page.html','.DS_Store',ZIP_NAME,'manifest.json'}

def selected():
    for folder in ['source','inputs','results','verification','documents','cad','plots','website']:
        for p in sorted((B/folder).rglob('*')):
            if p.is_file() and not p.is_symlink() and p.name not in EXCLUDED and '__pycache__' not in p.parts:
                yield p
    for name in ['README.md','completion.json']:
        p=B/name
        if p.exists():yield p

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

files=list(selected())
manifest={'study':'Stage-06-Interview-Evidence-R1',
          'scope':'Independent public-reference engineering study; numerical evidence and planned physical tests. Synthetic correlation is not physical validation.',
          'files':[{'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
(B/'manifest.json').write_text(json.dumps(manifest,indent=2))
files.append(B/'manifest.json')
with zipfile.ZipFile(B/ZIP_NAME,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:z.write(p,p.relative_to(B))
with zipfile.ZipFile(B/ZIP_NAME) as z:
    assert z.testzip() is None
    for entry in manifest['files']:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
if len(sys.argv)>1:
    dest=Path(sys.argv[1])
    asset=dest/'assets/studies/sceye-haps/stage-06'
    asset.mkdir(parents=True,exist_ok=True)
    for p in files:
        rel=p.relative_to(B)
        target=asset/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
    shutil.copy2(B/ZIP_NAME,asset/ZIP_NAME)
    html=B/'website/AISolutions/sceye-thermal-interview.html'
    shutil.copy2(html,dest/'AISolutions/sceye-thermal-interview.html')
print(json.dumps({'files':len(manifest['files']),'zip_bytes':(B/ZIP_NAME).stat().st_size,
                  'zip_sha256':sha(B/ZIP_NAME),'manifest_sha256':sha(B/'manifest.json')}))
