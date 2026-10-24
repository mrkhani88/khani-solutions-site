from pathlib import Path
import json
from pcb_fem import solve
B=Path(__file__).resolve().parents[1];f=B/'verification/pcb-fem-audit.json';audit=json.loads(f.read_text());refinement=[]
for name,kz,pad,fine in [('nominal',.69,3,audit['runs'][2]),('improved_path',5,3,audit['runs'][3]),('degraded_pad',.69,.5,audit['runs'][4])]:
 coarse,medium=(audit['runs'][0],audit['runs'][1]) if name=='nominal' else (solve(0,kz,pad),solve(1,kz,pad))
 change=abs(medium['peak_rise_K_per_W']-fine['peak_rise_K_per_W'])/fine['peak_rise_K_per_W'];assert change<.03
 refinement.append(dict(design=name,passed=True,coarse=coarse,medium=medium,fine=fine,relative_peak_change=change))
audit['refinement_by_design']=refinement;f.write_text(json.dumps(audit,indent=2));print([(r['design'],r['relative_peak_change']) for r in refinement])
