"""Bounded Intel native solver cases; raw CSVs remain on Intel, compact views exported."""
from pathlib import Path
import json,os,subprocess,time,hashlib,datetime,sys
B=Path(__file__).resolve().parents[2];V=B/'verification/engineering';W=V/'native';R=B/'results/engineering'
common=dict(switchEnabled=1,minFraction=.1,batteryInsulationG=2,motorHeaterScale=3,motorMode=1,motorKp=300,motorKi=2,motorSensorLag=30,motorCommandDelay=2,motorHeaterLag=5,motorCommandCeiling=270)
cases=[
 dict(id='detailed_baseline',label='Detailed payload / ordinary PCB',description='Unmanaged full service; ordinary PCB kz0.69 and0.5mm pad. A deliberately preserved feasibility failure.',override=dict(improved=0,switchEnabled=0)),
 dict(id='improved_interface',label='Improved board / fixed radiator link',description='Effective thermal vias kz10 and0.25mm k6 interface; constant radiator conductance.',override=dict(improved=1,switchEnabled=0)),
 dict(id='night_isolation_only',label='Improved interface + night isolation only',description='Improved interface and controlled15W/K radiator link; full demanded payload workload. Preserved as an intermediate failing trade.',override=dict(improved=1)),
 dict(id='compact_design',label='Compact4m² direct radiator attachment',description='Improved board,60W/K direct attachment and4m² panel: nominal pass but hotfixedboundaryscreen fails.',override=dict(improved=1,payloadStrapScale=4,payloadRadiatorArea=4)),
 dict(id='selected_design',label='Selected direct attachment +4.5m² radiator',description='Improved board/interface,60W/K direct radiator attachment and4.5m² radiator with night isolation; full demanded workload.',override=dict(improved=1,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='altitude_17km',label='17km pressure sensitivity',description='Pressure8790Pa; same prescribed air temperature, radiation, wind and mission so only density/convection changes. Not an actual route replay.',override=dict(pressure=8790,improved=1,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='cold_start',label='Cold payload / startup interlock',description='Only payload package/plate start−40°C; payload operation inhibited until all package cases exceed−5°C.30s sensor and5s delivered heater response.',override=dict(payloadInitialT=233.15,startupGate=1,thermalManagement=0,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='sensor_bias',label='Heater sensor +10K bias',description='Payload heater reads10K too warm during coldstartup; standbyloads remainenabled while the idealtrue-state readinessgate inhibitsfullworkload.',override=dict(payloadSensorBias=10,payloadInitialT=233.15,startupGate=1,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='heater_failed',label='Cold payload / heater open circuit',description='Cold startup with no payload heater; readiness gate remains active. This case is allowed to fail service.',override=dict(payloadInitialT=233.15,startupGate=1,payloadHeaterFault=1,thermalManagement=1)),
 dict(id='heater_stuck_on',label='Payload heater stuck on',description='240W delivered continuously; tests upper-temperature margin and excess energy use.',override=dict(payloadHeaterFault=2,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='mount_degraded',label='Damaged PCB thermal interface',description='Conservative whole assembly reverts to ordinary PCB/pad paths; thermal derating is enabled. This does not represent one isolated failed solder joint.',override=dict(improved=0,thermalManagement=1,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='low_soc_shedding',label='Reserve-driven payload shedding',description='Illustrative40%workload policy when SOC<65%; shows energy versus communications service trade.',override=dict(thermalManagement=1,socReserve=.65,payloadStrapScale=4,payloadRadiatorArea=4.5)),
 dict(id='selected_fine',label='Selected design numerical refinement',description='Same selected design;20s output and2.5s maximum solver step, tolerance1e−8.',override=dict(improved=1,payloadStrapScale=4,payloadRadiatorArea=4.5))]
records=json.loads((V/'run-manifest.json').read_text()) if (V/'run-manifest.json').exists() else []
for c in cases:
 if len(sys.argv)>1 and c['id'] not in sys.argv[1:]:continue
 fine=c['id']=='selected_fine';override={**common,**c['override']};out=R/(c['id']+'_native.csv');log=W/(c['id']+'.log')
 cmd=[str(W/'HAPSInterview.IntegratedMission'),'-stopTime=691200','-stepSize='+('20' if fine else '60'),'-maxStepSize='+('2.5' if fine else '10'),'-tolerance='+('1e-8' if fine else '1e-7'),'-r='+str(out),'-lv=LOG_STATS','-override='+','.join(k+'='+str(v) for k,v in override.items())]
 start=time.monotonic()
 with log.open('w') as f:p=subprocess.run(cmd,cwd=W,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},stdout=f,stderr=subprocess.STDOUT,timeout=300)
 ok=p.returncode==0 and out.exists() and 'The simulation finished successfully.' in log.read_text();rec={**c, 'override':override,'command':cmd,'execution_success':ok,'returncode':p.returncode,'elapsed_s':time.monotonic()-start,'native_bytes':out.stat().st_size if out.exists() else 0,'native_sha256':hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};records=[x for x in records if x['id']!=c['id']]+[rec]
 (V/'run-manifest.json').write_text(json.dumps(records,indent=2));print(c['id'],ok,round(rec['elapsed_s'],2),flush=True)
 if not ok:raise RuntimeError(log.read_text()[-4000:])
(R/'case-definitions.json').write_text(json.dumps(cases,indent=2))
