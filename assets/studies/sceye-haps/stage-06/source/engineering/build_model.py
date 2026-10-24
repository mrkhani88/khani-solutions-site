"""Generate the native Modelica mission from frozen Stage05 and 3D-derived paths."""
from pathlib import Path
import json,re,hashlib
B=Path(__file__).resolve().parents[2];R=B/'results/engineering';S=B/'source/engineering';V=B/'verification/engineering'
old=S/'Stage05-reference.mo'
if not old.exists():old=B.parent/'stage-05-cold-startup-delays-r1/source/HAPSDiurnal.mo'
if not old.exists():old=B.parent/'Stage-05-Cold-Startup-Delays-R1/source/HAPSDiurnal.mo'
text=old.read_text().replace('package HAPSDiurnal','package HAPSInterview').replace('end HAPSDiurnal;','end HAPSInterview;')
data=json.loads((R/'conduction-reduction.json').read_text());base=data['runs']['baseline_fine'];imp=data['runs']['improved_fine']
ids=['tx','beamformer','baseband','server','powerNode'];powers=['Qtx','Pbf','Pbb','Pserver','Pdc'];C=imp['C_J_K']
def arr(x):return '{'+','.join(arr(v) if isinstance(v,list) else format(v,'.12g') for v in x)+'}'
nodes='\n'.join(f'    ThermalMass {n}(C={C[i]:.12g},T0=initialT,Q={powers[i]}+Gb[{i+1}]*(plate.T-{n}.T)+sum(Gm[{i+1},j]*(temp[j]-{n}.T) for j in 1:5));' for i,n in enumerate(ids))
payload='''  model Payload "Representative telecom and edge server; reduced spatial heat paths"
    parameter Real loadScale=1,heaterEnabled=1,strapScale=1,shadeFactor=.05,heaterScale=1,switchEnabled=1,minFraction=.03;
    parameter Real improved=1,initialT=293.15,startupGate=0,thermalManagement=0,socReserve=.20;
    parameter Real radiatorArea=3.12,mountScale=1,heaterFault=0,sensorBias=0,heaterCeiling=240,insulationFactor=1;
    parameter Real Gb[5]=if improved>.5 then IMPGB else BASEGB;
    parameter Real Gm[5,5]=if improved>.5 then IMPGM else BASEGM;
    EnvironmentBus env;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a mount,hull;
    Modelica.Blocks.Interfaces.RealInput SOC;
    Modelica.Blocks.Interfaces.RealOutput Pelec,Prf,Pheat;
    Real temp[5],Ptx,Pbf,Pbb,Pserver,Pdc,Qtx,ready,workFactor,thermalFactor;
    Real sensedT(unit="K",start=initialT,fixed=true),heaterCommand(unit="W"),Pdelivered(unit="W",start=0,fixed=true);
    output Real service,readyFlag,loadFactor,caseMinC,caseMaxC;
NODES
    ThermalMass plate(C=2250,T0=initialT,Q=Pheat+sum(Gb[j]*(temp[j]-plate.T) for j in 1:5));
    ThermalMass radiator(C=8000*radiatorArea/3.12,T0=273.15);
    ControlledStrap strap(Gday=15*strapScale,enabled=switchEnabled,minFraction=minFraction,coldT=275.15);
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor mountPath(G=.7*mountScale);
    ExternalSurface boundary(A=radiatorArea,ny=.8660254038,directExposure=shadeFactor,hRef=1.2*insulationFactor);
    output SI.Energy U;output SI.Power Qext,Qgenerated;
  equation
    temp={tx.T,beamformer.T,baseband.T,server.T,powerNode.T};
    ready=if startupGate>.5 and min(temp)<268.15 then 0 else 1;
    thermalFactor=if thermalManagement>.5 then noEvent(clamp((343.15-max(temp))/10,.4,1)) else 1;
    workFactor=if thermalManagement>.5 and SOC<socReserve then .4 else 1;
    loadFactor=ready*min(thermalFactor,workFactor);
    Ptx=loadScale*(5+(300+200*env.day+200*window(env.hour,11,14)-5)*loadFactor);
    Pbf=loadScale*(5+(50+30*env.day+20*window(env.hour,11,14)-5)*loadFactor);
    Pbb=loadScale*(5+(60+40*env.day-5)*loadFactor);
    Pserver=loadScale*(10+(120+100*env.day+80*window(env.hour,11,14)-10)*loadFactor);
    Prf=.35*max(0,Ptx-5);Pdc=(Ptx+Pbf+Pbb+Pserver)*(1/.94-1);
    Pelec=Ptx+Pbf+Pbb+Pserver+Pdc;Qtx=Ptx-Prf;
    der(sensedT)=(plate.T+sensorBias-sensedT)/30;
    heaterCommand=if heaterFault>.5 and heaterFault<1.5 then 0 else if heaterFault>=1.5 then heaterCeiling else heaterEnabled*noEvent(clamp(60*(273.15-sensedT),0,heaterCeiling));
    der(Pdelivered)=(heaterCommand-Pdelivered)/5;Pheat=Pdelivered;
    readyFlag=ready;caseMinC=min(temp)-273.15;caseMaxC=max(temp)-273.15;
    service=if ready>.5 and min(temp)>=263.15 and max(temp)<=343.15 and SOC>.20 then 1 else 0;
    connect(plate.port,strap.port_a);connect(strap.port_b,radiator.port);
    connect(plate.port,mountPath.port_a);connect(mountPath.port_b,mount);
    connect(boundary.surface,radiator.port);connect(boundary.env,env);connect(boundary.hull,hull);
    U=tx.U+beamformer.U+baseband.U+server.U+powerNode.U+plate.U+radiator.U;
    Qext=boundary.Qext;Qgenerated=Pelec-Prf+Pheat;
    annotation(Icon(graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110}),Text(extent={{-85,50},{85,-30}},textString="Telecom + server")}));
  end Payload;'''.replace('NODES',nodes).replace('IMPGB',arr(imp['G_base_W_K'])).replace('BASEGB',arr(base['G_base_W_K'])).replace('IMPGM',arr(imp['G_between_W_K'])).replace('BASEGM',arr(base['G_between_W_K']))
text=re.sub(r'  model Payload\n.*?  end Payload;',payload,text,flags=re.S)
text=text.replace('parameter Real coldOffset(unit="K")=0;','parameter Real coldOffset(unit="K")=0;\n    parameter Real pressure=5529.3054,fixedHour=-1;')
text=text.replace('bus.hour=mod(time/3600,24);','bus.hour=if fixedHour>=0 then fixedHour else mod(time/3600,24);').replace('bus.density=5529.3054/','bus.density=pressure/')
text=text.replace('    MissionEnvironment environment(coldOffset=coldOffset,yawOffset=yawOffset)', '    parameter Real pressure=5529.3054,fixedHour=-1,improved=1,payloadInitialT=293.15,startupGate=0,thermalManagement=0,socReserve=.20,payloadStrapScale=1,payloadMinFraction=.03,payloadRadiatorArea=3.12,mountScale=1,payloadHeaterFault=0,payloadSensorBias=0,payloadHeaterCeiling=240,insulationFactor=1;\n    MissionEnvironment environment(coldOffset=coldOffset,yawOffset=yawOffset,pressure=pressure,fixedHour=fixedHour)')
text=text.replace('minFraction=minFraction) annotation(Placement(transformation(extent={{35,-32},{125,12}})))','minFraction=payloadMinFraction,radiatorArea=payloadRadiatorArea,improved=improved,initialT=payloadInitialT,startupGate=startupGate,thermalManagement=thermalManagement,socReserve=socReserve,mountScale=mountScale,heaterFault=payloadHeaterFault,sensorBias=payloadSensorBias,heaterCeiling=payloadHeaterCeiling,insulationFactor=insulationFactor) annotation(Placement(transformation(extent={{35,-32},{125,12}})))')
text=text.replace('Payload payload(loadScale=payloadScale,heaterEnabled=heaterEnabled,strapScale=strapScale', 'Payload payload(loadScale=payloadScale,heaterEnabled=heaterEnabled,strapScale=payloadStrapScale')
(S/'Stage05-reference.mo').write_bytes(old.read_bytes())
text=text.replace('    heaterPower=avionics.Pheat', '    connect(battery.SOC,payload.SOC);\n    heaterPower=avionics.Pheat').replace('TpayC=payload.rf.T','TpayC=payload.tx.T')
text=text.replace('Hierarchical 24-hour thermal-energy mission','28-node extended telecom/server thermal-energy mission')
(S/'HAPSInterview.mo').write_text(text)
manifest=dict(stage05_source_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),new_source_sha256=hashlib.sha256(text.encode()).hexdigest(),reduction_source_sha256=hashlib.sha256((R/'conduction-reduction.json').read_bytes()).hexdigest(),preserved_subsystems=['Avionics','Battery','Propulsion','HullSolar','Structure','PowerManager'],changed=['Payload replaced with five package-case terminals plus plate/radiator','Environment pressure and fixed-hour test inputs','Payload SOC input and integrated displayed payload temperature'],thermal_state_nodes=28,scope='Representative independent study, not OEM geometry or limits; no hardware correlation')
(V/'source-provenance.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
variables=['time','TavC','TbatC','TpayC','TmotorC','heaterPower','systemResidualJ','thermalResidualJ','thermalStorage','chemicalStorage','externalEnergy','shaftEnergy','rfEnergy','thermalNetEnergy','heaterEnergy','loadEnergy','solarEnergy','chargeEnergy','dischargeEnergy','payload.*','battery.SOC','battery.Qloss','power.balance','power.Pload','power.Pcharge','power.Pdischarge','power.Ppv','propulsion.housing.T','propulsion.Pheat','environment.bus.Tair','environment.bus.wind','environment.bus.DNI']
vf='('+'|'.join(v.replace('.',r'\.') if '*' not in v else v.replace('payload.*',r'payload\..*') for v in variables)+')'
mos='setCommandLineOptions("--numProcs=2");\nloadModel(Modelica,{"4.1.0"});\nloadFile("../../../source/engineering/HAPSInterview.mo");\ngetErrorString();\ncheckModel(HAPSInterview.IntegratedMission);\ngetErrorString();\nbuildModel(HAPSInterview.IntegratedMission,startTime=0,stopTime=691200,numberOfIntervals=11520,tolerance=1e-7,outputFormat="csv",variableFilter='+json.dumps(vf)+');\ngetErrorString();\n'
(S/'compile.mos').write_text(mos)
