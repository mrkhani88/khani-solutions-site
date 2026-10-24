"""Rebuild frozen Stage05 on Intel and reproduce its stored first-day temperatures."""
from pathlib import Path
import subprocess,json,hashlib,os,csv,numpy as np,re
B=Path(__file__).resolve().parents[2];S=B/'source/engineering';V=B/'verification/engineering';W=V/'native';R=B/'results/engineering';prior=B.parent/'stage-05-cold-startup-delays-r1'
keys=['time','TavC','TbatC','TpayC','TmotorC','heaterPower','heaterEnergy','loadEnergy','battery.SOC','systemResidualJ','thermalResidualJ']
vf='('+'|'.join(k.replace('.',r'\.') for k in keys)+')'
mos='setCommandLineOptions("--numProcs=2");\nloadModel(Modelica,{"4.1.0"});\nloadFile("../../../source/engineering/Stage05-reference.mo");\nbuildModel(HAPSDiurnal.IntegratedMission,startTime=0,stopTime=86400,numberOfIntervals=8640,tolerance=1e-7,outputFormat="csv",variableFilter='+json.dumps(vf)+');\ngetErrorString();\n';(S/'reference.mos').write_text(mos)
with (W/'reference-compile.log').open('w') as f:subprocess.run(['omc',str(S/'reference.mos')],cwd=W,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
out=R/'stage05_reference_native.csv';cmd=[str(W/'HAPSDiurnal.IntegratedMission'),'-stopTime=86400','-stepSize=10','-maxStepSize=2','-tolerance=1e-7','-r='+str(out),'-lv=LOG_STATS','-override=switchEnabled=1,motorHeaterScale=3,motorMode=1,motorKp=300,motorKi=2']
with (W/'stage05_reference.log').open('w') as f:p=subprocess.run(cmd,cwd=W,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'OMP_NUM_THREADS':'1'})
def read(f):
 with f.open() as g:h=next(csv.reader(g))
 a=np.loadtxt(f,delimiter=',',skiprows=1);return {k:a[:,h.index(k)] for k in keys}
a=read(out);old=read(R/'stage05-prior-reference.csv');errors={k:float(max(abs(a[k]-np.interp(a['time'],old['time'],old[k])))) for k in ['TavC','TbatC','TpayC','TmotorC','heaterPower','battery.SOC']}
oldSource=(S/'Stage05-reference.mo').read_text();newSource=(S/'HAPSInterview.mo').read_text();classes={}
for name in ['Avionics','Battery','Propulsion','HullSolar','Structure','PowerManager']:
 regex=r'  model '+name+r'(?:\s|\n).*?  end '+name+r';';x=re.search(regex,oldSource,re.S).group();y=re.search(regex,newSource,re.S).group();classes[name]=dict(unchanged=x==y,sha256=hashlib.sha256(x.encode()).hexdigest())
record=dict(passed=max(errors.values())<1e-6 and all(v['unchanged'] for v in classes.values()),max_abs_reproduction_errors=errors,preserved_classes=classes,comparison='Frozen Stage05 reference first24h against its saved native reference run, same solver/maxstep/tolerance and parameters',scope='Code preservation and numerical reproduction, not physical validation',command=cmd,native_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),software={'omc':subprocess.check_output(['omc','--version'],text=True).strip(),'python':subprocess.check_output(['python3','--version'],text=True).strip(),'numpy':np.__version__})
(V/'stage05-reproduction.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2));assert record['passed']
