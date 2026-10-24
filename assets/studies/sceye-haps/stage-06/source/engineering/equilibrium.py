"""Native payload-only hot/cold equilibrium harness, externally powered with fixed mounts."""
from pathlib import Path
import subprocess,json,os,hashlib,time
B=Path(__file__).resolve().parents[2];S=B/'source/engineering';V=B/'verification/engineering';W=V/'native';R=B/'results/engineering'
source='''within ;
model HAPSEquilibrium "Payload-only fixed-boundary screening; not an indefinitely powered flight"
 parameter Real fixedHour=12,coldOffset=0,mountT=273.15,hullT=240;
 HAPSInterview.MissionEnvironment environment(fixedHour=fixedHour,coldOffset=coldOffset);
 HAPSInterview.Payload payload(improved=1,strapScale=4,radiatorArea=4.5,switchEnabled=1,minFraction=.03);
 Modelica.Thermal.HeatTransfer.Sources.FixedTemperature mount(T=mountT),hull(T=hullT);
 Real netEnergy(start=0,fixed=true);output Real residualJ;
equation
 connect(environment.bus,payload.env);connect(mount.port,payload.mount);connect(hull.port,payload.hull);payload.SOC=.7;
 der(netEnergy)=payload.Qgenerated+payload.Qext+payload.mount.Q_flow+payload.hull.Q_flow;
 residualJ=netEnergy-payload.U;
 annotation(uses(Modelica(version="4.1.0")));
end HAPSEquilibrium;
''';(S/'HAPSEquilibrium.mo').write_text(source)
mos='''setCommandLineOptions("--numProcs=2");
loadModel(Modelica,{"4.1.0"});
loadFile("../../../source/engineering/HAPSInterview.mo");
loadFile("../../../source/engineering/HAPSEquilibrium.mo");
getErrorString();
checkModel(HAPSEquilibrium);
getErrorString();
buildModel(HAPSEquilibrium,startTime=0,stopTime=604800,numberOfIntervals=10080,tolerance=1e-8,outputFormat="csv");
getErrorString();
''';(S/'equilibrium.mos').write_text(mos)
with (W/'equilibrium-compile.log').open('w') as f:subprocess.run(['omc',str(S/'equilibrium.mos')],cwd=W,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
records=[]
for id,ov in [('hot_equilibrium',dict(fixedHour=12,coldOffset=10,mountT=293.15,hullT=260)),('cold_equilibrium',dict(fixedHour=0,coldOffset=-10,mountT=233.15,hullT=220))]:
 out=R/(id+'_native.csv');cmd=[str(W/'HAPSEquilibrium'),'-stopTime=604800','-stepSize=60','-maxStepSize=10','-tolerance=1e-8','-r='+str(out),'-lv=LOG_STATS','-override='+','.join(k+'='+str(v) for k,v in ov.items())];start=time.monotonic()
 with (W/(id+'.log')).open('w') as f:p=subprocess.run(cmd,cwd=W,stdout=f,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'OMP_NUM_THREADS':'1'})
 rec=dict(id=id,override=ov,command=cmd,execution_success=p.returncode==0 and 'The simulation finished successfully.' in (W/(id+'.log')).read_text(),native_bytes=out.stat().st_size,native_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),elapsed_s=time.monotonic()-start);records.append(rec);assert rec['execution_success'];print(id,rec['elapsed_s'],flush=True)
(V/'equilibrium-manifest.json').write_text(json.dumps(records,indent=2))
