"""Check source/evidence references and finite data in the compact stage."""
from pathlib import Path
import json
import math
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

B=Path(__file__).resolve().parents[1]
PREFIX='/assets/studies/sceye-haps/stage-06/'
errors=[]
checks=[]

def finite(x,path):
    if isinstance(x,float) and not math.isfinite(x):errors.append('Non-finite number: '+path)
    if isinstance(x,dict):
        for k,v in x.items():finite(v,path+'/'+k)
    if isinstance(x,list):
        for i,v in enumerate(x):finite(v,path+'/'+str(i))

for p in B.rglob('*.json'):
    try:finite(json.loads(p.read_text()),str(p.relative_to(B)))
    except Exception as e:errors.append(str(p.relative_to(B))+': '+str(e))

matrix=json.loads((B/'inputs/requirements-matrix.json').read_text())
registry=json.loads((B/'inputs/lifecycle-evidence-registry.json').read_text())
requirements=matrix['requirements']
evidence=registry['evidence']
ids={e['id'] for e in evidence}
assert len(ids)==len(evidence),'Duplicate evidence identifiers'
assert len({r['id'] for r in requirements})==len(requirements),'Duplicate requirement identifiers'
for r in requirements:
    if not r.get('evidenceIds'):errors.append('No evidence for '+r['id'])
    for eid in r.get('evidenceIds',[]):
        if eid not in ids:errors.append('Unknown evidence '+eid+' in '+r['id'])
    if r['status']=='physically_tested':errors.append('Unsupported physical-test status: '+r['id'])

def check_href(href,where):
    path=unquote(urlsplit(href).path)
    if path.startswith(PREFIX):
        target=B/path.removeprefix(PREFIX)
        if target.name=='Stage-06-Interview-Evidence-R1.zip' and not target.exists():return
        if not target.is_file():errors.append('Missing '+str(target.relative_to(B))+' from '+where)
        else:checks.append(href)

for e in evidence:
    if e.get('href'):check_href(e['href'],e['id'])
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        for key in ['href','src']:
            if a.get(key):check_href(a[key],'main HTML')
Links().feed((B/'website/AISolutions/sceye-thermal-interview.html').read_text())
result={'passed':not errors,'requirements':len(requirements),'evidence_records':len(evidence),
        'physical_tested_requirement_rows':0,'local_stage_links_checked':len(checks),
        'errors':errors}
(B/'verification/package-check.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
if errors:raise SystemExit(1)
