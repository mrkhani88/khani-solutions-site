from pathlib import Path
import json,numpy as np,csv,hashlib
B=Path(__file__).resolve().parents[1];V=B/'verification'
def get(name):
 p=B/'results'/f'{name}_native.csv';header=next(csv.reader(p.open()));a=np.loadtxt(p,delimiter=',',skiprows=1);return {k:a[:,i] for i,k in enumerate(header)}
def ip(x,key,t):
 _,ix=np.unique(x['time'][::-1],return_index=True);ix=np.sort(len(x['time'])-1-ix);return np.interp(t,x['time'][ix],x[key][ix])
a=get('combined');b=get('combined_fine');keys=[x['key']+'.T' for x in json.loads((B/'inputs/component-nodes.json').read_text())];t=np.arange(604800,691201,60);delta={k:float(max(abs(ip(a,k,t)-ip(b,k,t)))) for k in keys};E=abs((a['heaterEnergy'][-1]-ip(a,'heaterEnergy',[604800])[0])-(b['heaterEnergy'][-1]-ip(b,'heaterEnergy',[604800])[0]))/3600
assert max(delta.values())<.02 and E<1
(V/'combined-refinement.json').write_text(json.dumps(dict(passed=True,max_temperature_difference_K=max(delta.values()),heater_energy_difference_Wh=E,differences=delta),indent=2))
old=B.parent/'stage-02-diurnal-thermal-r1';ref=get('reference');p=old/'results/reference_native.csv';head=next(csv.reader(p.open()));arr=np.loadtxt(p,delimiter=',',skiprows=1);x={k:arr[:,i] for i,k in enumerate(head)};same={k:float(max(abs(ip(x,k,t)-ip(ref,k,t)))) for k in keys};assert max(same.values())<.001
(V/'baseline-reproduction.json').write_text(json.dumps(dict(passed=True,max_temperature_difference_K=max(same.values()),original_model_sha256=hashlib.sha256((old/'source/HAPSDiurnal.mo').read_bytes()).hexdigest(),new_model_sha256=hashlib.sha256((B/'source/HAPSDiurnal.mo').read_bytes()).hexdigest(),scope='Changed thermal-strap implementation with switch disabled reproduces immutable Stage02 reference; no baseline redefinition'),indent=2))
graph=[]
for cls in ['Avionics','Battery','Payload','Propulsion','HullSolar','Structure','PowerManager','IntegratedMission']:
 g=json.loads((V/f'native-{cls}.json').read_text());oldg=json.loads((old/'verification'/f'native-{cls}.json').read_text());assert g.get('connections',[])==oldg.get('connections',[]);assert len(g.get('connections',[]))==int((V/f'connections-{cls}.txt').read_text());graph.append(dict(model=g['name'],connections=len(g.get('connections',[])),same_external_topology_as_baseline=True))
(V/'native-connection-audit.json').write_text(json.dumps(dict(passed=True,models=graph,change='Avionics and Payload strap class becomes ControlledStrap; same conservative heat-port connections and no added thermal mass.'),indent=2))
print('Combined refinement K',max(delta.values()),'heater Wh',E,'baseline reproduction K',max(same.values()))
