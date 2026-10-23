"""Create a hash inventory and portable ZIP of this stage's deliverables.
Compiled binaries and build products belong on Intel and are not in this folder.
"""
from pathlib import Path
import json,hashlib,zipfile
B=Path(__file__).resolve().parents[1];name='Stage-04-Balancing-R1.zip'
files=sorted(p for p in B.rglob('*') if p.is_file() and p.name not in [name,'manifest.json','.DS_Store'] and '__pycache__' not in p.parts)
manifest={'stage':'Stage 04 - Pump speed and rack balancing','inventory_scope':'All deliverable files except this manifest and the ZIP; native compiler build products are retained on Intel','files':[{'path':p.relative_to(B).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(B/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(B/name,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[B/'manifest.json']:z.write(p,p.relative_to(B))
with zipfile.ZipFile(B/name) as z:
 assert z.testzip() is None
 for item in manifest['files']:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
print('Verified',len(files),'files;', (B/name).stat().st_size,'ZIP bytes')
