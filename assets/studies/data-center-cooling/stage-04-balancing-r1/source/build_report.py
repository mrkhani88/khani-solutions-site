"""Build standalone report and the website section from audited saved results."""
from pathlib import Path
import json,html,sys
B=Path(__file__).resolve().parents[1];s=json.loads((B/'results/comparison.json').read_text());c=s['cases'][3]
section=(B/'source/section-template.html').read_text()
rows=[]
for d in s['cases']:
 vals=[d['label'],f"{d['speed_percent']:.2f}%",f"{min(d['rack_flow_Lmin']):.3f}–{max(d['rack_flow_Lmin']):.3f}",f"{d['total_flow_Lps']:.3f}",f"{d['electrical_power_kW']:.3f}",f"{d['power_saving_percent']:.2f}%"]
 rows.append('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+html.escape(v)+('</th>' if i==0 else '</td>') for i,v in enumerate(vals))+'</tr>')
valverows=[]
for i,q in enumerate(c['rack_flow_Lmin']):
 vals=[f'R-{i+1:02d}',f'{q:.3f}',f'{q-144.7:.3f}',f"{c['valve_dp_kPa'][i]:.3f}",f"{c['valve_Kv_m3h'][i]:.3f}"]
 valverows.append('<tr>'+''.join(('<th scope="row">' if j==0 else '<td>')+html.escape(v)+('</th>' if j==0 else '</td>') for j,v in enumerate(vals))+'</tr>')
section=section.replace('<!-- BALANCE_ROWS -->','\n'.join(rows)).replace('<!-- VALVE_ROWS -->','\n'.join(valverows)).replace('<!-- COMBINED_HEAD -->',f"{c['head_m']:.3f}").replace('<!-- VALVE_RANGE -->',f"{min(c['valve_dp_kPa']):.2f}–{max(c['valve_dp_kPa']):.2f}")
assert '<!-- ' not in section
(B/'source/rendered-section.html').write_text(section)
base='/assets/studies/data-center-cooling/stage-04-balancing-r1'
report='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage 04 | Pump speed and rack balancing | Khani Solutions</title><link rel="stylesheet" href="review.css"><style>body{margin:0;background:#fff;font:16px/1.6 system-ui,sans-serif;color:#17394d}main{max-width:1200px;padding:25px;margin:auto}a{color:#076989}h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.15}header{padding-bottom:20px;border-bottom:1px solid #bfd3db}.dc-section{scroll-margin-top:20px}</style><script type="module" src="review.mjs"></script></head><body><main><header><p>Khani Solutions · Independent engineering study · 23 October 2026</p><h1>Pump speed and rack balancing</h1><p>Stage 04 · Reproducible native OpenModelica results from the same ten-rack hydraulic network.</p><a href="https://khanisolutions.com/AISolutions/data-center-cooling.html#balancing">Open the full project website →</a></header><div class="dc-project">'''+section.replace(base,'.')+'</div></main></body></html>'
(B/'Report.html').write_text(report)
js=(B/'source/website-explorer.mjs').read_text().replace("const base = '"+base+"';","const base = '.';")
(B/'review.mjs').write_text(js)
if len(sys.argv)>1:Path(sys.argv[1]).write_text(section)
print('Built report and website section from verified result JSON.')
