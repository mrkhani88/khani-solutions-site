from pathlib import Path
import csv,json,math
B=Path(__file__).resolve().parents[1];R=B/'verification/native-acceptance';log=(R/'run.log').read_text();assert log.count('The simulation finished successfully.')==3
out=[]
for name,Q,Ta in [('heating',100,293.15),('cooling',0,253.15)]:
 rows=list(csv.DictReader((R/(name+'_res.csv')).open()));errors=[]
 for row in rows:
  x={k:float(v) for k,v in row.items()};assert all(math.isfinite(v) for v in x.values());t=x['time'];exact=Ta+Q/2+(293.15-Ta-Q/2)*math.exp(-2*t/10000);errors.append(abs(x['T']-exact));assert abs(x['balanceResidualJ'])<.0001
 assert abs(t-3600)<1e-10 and max(errors)<1e-5
 out.append({'case':name,'max_analytic_temperature_error_K':max(errors),'native_final_C':x['T']-273.15,'balance_residual_J':abs(x['balanceResidualJ'])})
x={k:float(v) for k,v in list(csv.DictReader((R/'radiation_res.csv').open()))[-1].items()};exact=(250**4+100/(.85*5.670374419e-8))**.25;assert abs(x['T']-exact)<1e-7 and abs(x['residualW'])<1e-7
out.append({'case':'radiation','temperature_error_K':abs(x['T']-exact),'native_equilibrium_C':x['T']-273.15,'balance_residual_W':abs(x['residualW'])})
(B/'verification/thermal-acceptance.json').write_text(json.dumps({'passed':True,'scope':'Three solver/code verification benchmarks only; not a HAPS mission thermal model or physical validation','software':'OpenModelica 1.27.1','cases':out},indent=2)+'\n');print(json.dumps(out,indent=2))
