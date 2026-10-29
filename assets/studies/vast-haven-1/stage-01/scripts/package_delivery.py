from pathlib import Path
import json,csv,hashlib,zipfile,struct,re,urllib.request,datetime
B=Path(__file__).resolve().parents[1];s=json.loads((B/'scripts/assembly_spec.json').read_text());v=json.loads((B/'verification/cad-verification.json').read_text());m=json.loads((B/'review/mesh.json').read_text())
assert v['native_objects']==len(s['parts'])==len(m['parts'])==221
assert v['all_shapes_valid'] and v['native_reopen_valid'] and v['step_reimport_valid']
assert {r['id'] for r in m['parts']}=={r['id'] for r in s['parts']}
with (B/'cad/Component_Catalog.csv').open('w',newline='') as f:
 fields=['id','label','group','role','evidence','source_ids','thermal_candidate','geometry_m','heat_load_W','material','capacity_or_flow','thermal_input_status'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for p in s['parts']:w.writerow({**{k:p[k] for k in fields if k in p},'source_ids':'; '.join(p['source_ids']),'geometry_m':json.dumps(p['geometry']),'heat_load_W':'','material':'','capacity_or_flow':'','thermal_input_status':'Unassigned: define and source before analysis'})
# Read GLB scene metadata without claiming a render test.
b=(B/'cad/Haven1_Public_Reference_R1.glb').read_bytes();assert b[:4]==b'glTF';n,kind=struct.unpack_from('<II',b,12);g=json.loads(b[20:20+n]);assert len(g['meshes'])==221
# Check every local review asset/download; external links are retained source references.
h=(B/'review/Review.html').read_text();hrefs=re.findall(r'(?:href|src)="([^"]+)"',h)
for u in hrefs:
 if u.startswith(('http:','https:','#')) or u.endswith('.zip'):continue
 assert (B/'review'/u).resolve().is_file(),u
files=[p for d in ['cad','renders','review','scripts','sources','verification'] for p in (B/d).rglob('*') if p.is_file() and not p.name.startswith('.') and '__pycache__' not in str(p)]+[B/'README.md']
receipt=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project='Haven-1 Stage01 CAD R1',intel_root='/home/falcon-admin/projects/vast-haven-1/stage-01-cad-r1',local_root=str(B),components=221,geometric_checks=v,GLB_meshes=len(g['meshes']),browser_UI_verification='Unavailable: local browser use disabled in Work settings; HTTP/source/module checks and native/renders verified separately.',publicly_published=False,physics_solved=False,files={str(p.relative_to(B)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files})
(B/'verification/delivery-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
files.append(B/'verification/delivery-manifest.json')
z=B/'Haven1_Stage01_CAD_Review.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
 for p in files:out.write(p,p.relative_to(B))
with zipfile.ZipFile(z) as check:assert check.testzip() is None
print(json.dumps({'zip':str(z),'bytes':z.stat().st_size,'files':len(files),'components':221,'sha256':hashlib.sha256(z.read_bytes()).hexdigest()},indent=2))
