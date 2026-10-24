"""Build an inspectable report and site section from audited native case data."""
from pathlib import Path
import json,html,sys
B=Path(__file__).resolve().parents[1];D=json.loads((B/'results/comparison.json').read_text());BASE='/assets/studies/data-center-cooling/stage-06-isolation-r1'
def f(v,n=3):return f'{(0 if abs(v)<1e-8 else v):.{n}f}'
def row(c):
 vals=[c['label'],c['diameter_mm'],f(c['leak_Lmin']),f(c['rack05_supply_Lmin'])+' / '+f(c['rack05_return_Lmin']),f"{c['healthy_min_Lmin']:.3f}–{c['healthy_max_Lmin']:.3f}",f"{c['speed_percent']:.2f}",f"{c['electrical_power_kW']:.3f}"]
 return '<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+html.escape(str(v))+('</th>' if i==0 else '</td>') for i,v in enumerate(vals))+'</tr>'
s=(B/'source/section-template.html').read_text().replace('<!-- ALL_ROWS -->','\n'.join(row(c) for c in D['cases'])).replace('<!-- PRESSURE -->',f"{D['steady_leak_pressure_bound_abs_kPa']:.1f}").replace('<!-- BASE -->',BASE)
assert '<!--' not in s
(B/'source/rendered-section.html').write_text(s)
header='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage 06 | Leak isolation | Khani Solutions</title><link rel="stylesheet" href="review.css"><style>body{margin:0;background:#fff;font:16px/1.6 system-ui,sans-serif;color:#17394d}main{max-width:1200px;margin:auto;padding:25px}a{color:#076989}h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.15}</style><script type="module" src="review.mjs"></script></head><body><main><header><p>Khani Solutions · Independent study · 23 October 2026</p><h1>Rack leak isolation and service recovery</h1><a href="https://khanisolutions.com/AISolutions/data-center-cooling.html#leak-isolation">Open the full staged project →</a></header><div class="dc-project">'''
(B/'Report.html').write_text(header+s.replace(BASE,'.')+'</div></main></body></html>')
(B/'review.mjs').write_text((B/'source/website-explorer.mjs').read_text().replace("const base = '"+BASE+"';","const base = '.';"))
if len(sys.argv)>1:Path(sys.argv[1]).write_text(s)
print('Built Stage 06 section and standalone report.')
