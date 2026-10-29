from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
root.mkdir(parents=True,exist_ok=True)
names=['Avionics','Battery','Payload','PowerConversion','ECLSS','Cabin','Wall','ColdPlate','Coolant','Radiator','CMG','SolarArray','TankResources']
C=[30000,80000,24000,18000,40000,80000,600000,30000,80000,70000,40000,120000,50000]
links=[(1,8,35),(1,6,3),(2,8,18),(2,6,3),(3,8,40),(3,6,3),(4,8,30),(4,6,2),(5,9,45),(5,6,10),(6,9,100),(6,7,18),(7,8,4),(8,9,240),(11,8,15),(11,6,2),(12,7,0.3),(13,7,2),(13,6,1)]
G=[[0]*13 for _ in range(13)]
for a,b,g in links:G[a-1][b-1]=G[b-1][a-1]=g
mat=';\n      '.join(','.join(map(str,row)) for row in G)
model='''within ;
package Haven1Thermal
  model Integrated
    parameter Integer N=13;
    parameter Real C[N]={CVAL};
    parameter Real G[N,N]=[GMAT];
    parameter Real radiatorArea=6 "m2 effective one-sided emissive area, study assumption";
    parameter Real environmentScale=1 "0.8 cold case or1 nominal";
    parameter Real equipmentScale=1 "0.5 low-duty or1 full-duty";
    parameter Boolean bypassControl=false "Proposed coolant bypass, not confirmed Haven1 hardware";
    parameter Real sigma=5.670374419e-8;
    parameter Real period=5400;
    parameter Real dayDuration=3600;
    parameter Real initialK=293.15;
    parameter Real energyMax=15*3.6e6 "15kWh assumed battery capacity";
    Real T[N](each start=initialK,each fixed=true) "K";
    Real Q[N] "W external heat into each node, internal links excluded";
    Real sunlight;
    Real radiatorSolar;
    Real wallSolar;
    Real arraySolar;
    Real radiatorIR;
    Real wallIR;
    Real arrayIR;
    Real radiatorEmission;
    Real wallEmission;
    Real arrayEmission;
    Real radiatorLink;
    Real radiatorG;
    Real heaterBattery;
    Real heaterResources;
    Real heaterCoolant;
    Real heaterTotal;
    Real powerLoad;
    Real powerAvailable;
    Real powerPV;
    Real powerCharge;
    Real powerDischarge;
    Real powerBatteryHeat;
    Real powerCurtail;
    Real batteryEnergy(start=0.8*energyMax,fixed=true);
    Real SOC;
    Real energyHeaters(start=0,fixed=true);
    Real energyLoad(start=0,fixed=true);
    Real energyPV(start=0,fixed=true);
    Real energyExternal(start=0,fixed=true);
    Real energyReject(start=0,fixed=true);
    Real energyEnvironment(start=0,fixed=true);
    Real wholeEnergyClosureJ;
    Real storedThermal;
    Real closureJ;
  equation
    sunlight=if mod(time,period)<dayDuration then 1 else 0;
    radiatorSolar=0.12*radiatorArea*1361*0.08*sunlight*environmentScale;
    wallSolar=0.10*12*1361*sunlight*environmentScale;
    arraySolar=0.85*66*1361*sunlight*environmentScale;
    radiatorIR=0.88*radiatorArea*0.35*241*environmentScale;
    wallIR=0.03*110*0.40*241*environmentScale;
    arrayIR=0.85*132*0.20*241*environmentScale;
    radiatorEmission=0.88*radiatorArea*sigma*(T[10]^4-3^4);
    wallEmission=0.03*110*sigma*(T[7]^4-3^4);
    arrayEmission=0.85*132*sigma*(T[12]^4-3^4);
    radiatorG=if bypassControl then 10+590*min(1,max(0,(T[9]-287.15)/8)) else 600;
    radiatorLink=radiatorG*(T[9]-T[10]);
    heaterBattery=min(300,max(0,80*(283.15-T[2])));
    heaterResources=min(100,max(0,30*(278.15-T[13])));
    heaterCoolant=min(600,max(0,100*(281.15-T[9])));
    heaterTotal=heaterBattery+heaterResources+heaterCoolant;
    powerLoad=2130*equipmentScale+180*equipmentScale+heaterTotal;
    powerAvailable=9000*sunlight*environmentScale;
    powerCharge=if powerAvailable>powerLoad then min(0.95*(powerAvailable-powerLoad),max(0,(energyMax-batteryEnergy)/60)) else 0;
    powerDischarge=if powerAvailable<powerLoad then (powerLoad-powerAvailable)/0.95 else 0;
    powerPV=if powerAvailable>powerLoad then powerLoad+powerCharge/0.95 else powerAvailable;
    powerCurtail=powerAvailable-powerPV;
    powerBatteryHeat=powerCharge*(1/0.95-1)+0.05*powerDischarge;
    der(batteryEnergy)=powerCharge-powerDischarge;
    SOC=batteryEnergy/energyMax;
    Q[1]=600*equipmentScale;
    Q[2]=powerBatteryHeat+heaterBattery;
    Q[3]=800*equipmentScale;
    Q[4]=180*equipmentScale;
    Q[5]=450*equipmentScale;
    Q[6]=4*120+100*equipmentScale;
    Q[7]=wallSolar+wallIR-wallEmission;
    Q[8]=0;
    Q[9]=60*equipmentScale+heaterCoolant;
    Q[10]=radiatorSolar+radiatorIR-radiatorEmission;
    Q[11]=120*equipmentScale;
    Q[12]=arraySolar+arrayIR-arrayEmission-powerPV;
    Q[13]=heaterResources;
    for i in 1:N loop
      C[i]*der(T[i])=Q[i]+sum(G[i,j]*(T[j]-T[i]) for j in 1:N)+(if i==9 then -radiatorLink else if i==10 then radiatorLink else 0);
    end for;
    der(energyHeaters)=heaterTotal;
    der(energyLoad)=powerLoad;
    der(energyPV)=powerPV;
    der(energyExternal)=sum(Q);
    der(energyReject)=radiatorEmission+wallEmission+arrayEmission;
    der(energyEnvironment)=radiatorSolar+radiatorIR+wallSolar+wallIR+arraySolar+arrayIR+480-radiatorEmission-wallEmission-arrayEmission;
    wholeEnergyClosureJ=storedThermal+batteryEnergy-0.8*energyMax-energyEnvironment;
    storedThermal=sum(C[i]*(T[i]-initialK) for i in 1:N);
    closureJ=storedThermal-energyExternal;
    annotation(experiment(StartTime=0,StopTime=86400,Interval=10,Tolerance=1e-7),
      Documentation(info="<html><p>Public-reference portfolio study. All loads, areas, capacities, contacts, view factors and duty cycles are assumed. No thermal validation or manufacturer configuration is claimed. Arrays use actual generated electrical power as a thermal sink, curtailed conversion remains array heat. Electrical storage change and charge/discharge loss heat are retained.</p></html>"));
  end Integrated;
end Haven1Thermal;
'''.replace('CVAL',','.join(map(str,C))).replace('GMAT',mat)
# Named thermal-capacitance components give OMEdit a readable native diagram.
node_model = """  model ThermalNode
    parameter Real C=30000;
    parameter Real initialK=293.15;
    input Real Q;
    Real T(start=initialK,fixed=true);
  equation
    C*der(T)=Q;
    annotation(Icon(graphics={Rectangle(extent={{-90,60},{90,-60}},lineColor={50,130,170},fillColor={220,240,250},fillPattern=FillPattern.Solid),Text(extent={{-85,45},{85,5}},textString="%name",fontSize=12),Text(extent={{-85,-5},{85,-45}},textString="C*dT/dt = Q",fontSize=10)}));
  end ThermalNode;
"""
model=model.replace('  model Integrated',node_model+'  model Integrated',1)
node_ids=['avionics','battery','payload','powerConversion','eclss','cabin','wall','coldPlate','coolant','radiator','cmg','solarArray','tankResources']
positions=[(-120,120),(-120,40),(-120,-40),(-120,-120),(0,120),(0,40),(0,-40),(120,120),(120,40),(120,-40),(0,-120),(120,-120),(-120,-200)]
components=[]
for idx,(name,cap,(x,y)) in enumerate(zip(node_ids,C,positions),1):
    components.append(f'    ThermalNode {name}(C=C[{idx}],initialK=initialK) annotation(Placement(transformation(extent={{{{{x-40},{y-25}}},{{{x+40},{y+25}}}}})));')
model=model.replace('    Real T[N](each start=initialK,each fixed=true) "K";', '\n'.join(components)+'\n    Real T[N] "K";')
old='      C[i]*der(T[i])=Q[i]+sum(G[i,j]*(T[j]-T[i]) for j in 1:N)+(if i==9 then -radiatorLink else if i==10 then radiatorLink else 0);'
model=model.replace('    for i in 1:N loop\n'+old+'\n    end for;', '    T={'+','.join(name+'.T' for name in node_ids)+'};\n'+'\n'.join(f'    {name}.Q=Q[{i}]+sum(G[{i},j]*(T[j]-T[{i}]) for j in 1:N)'+(' - radiatorLink' if i==9 else ' + radiatorLink' if i==10 else '')+';' for i,name in enumerate(node_ids,1)))
model=model.replace('annotation(experiment(StartTime=0,StopTime=86400,Interval=10,Tolerance=1e-7),','annotation(Diagram(coordinateSystem(extent={{-190,-250},{190,180}}),graphics={Text(extent={{-180,175},{180,150}},textString="Representative Haven-1 thermal nodes",fontSize=13)}),experiment(StartTime=0,StopTime=86400,Interval=10,Tolerance=1e-7),')
(root/'source/Haven1Thermal.mo').write_text(model)
assumptions={'study':'Representative Haven-1 first-round orbital thermal screening','classification':'Uncalibrated simulation; no manufacturer temperatures or performance claims','nodes':[{'index':i+1,'name':n,'capacitance_J_K':C[i],'initial_C':20,'source':'analyst assumption'} for i,n in enumerate(names)],'links':[{'from':names[a-1],'to':names[b-1],'G_W_K':g,'source':'analyst assumption'} for a,b,g in links], 'orbit':{'period_s':5400,'sunlight_s':3600,'duration_s':86400,'start_phase':'sunrise at t=0, initial all nodes20C','source':'representative rectangular illumination; no propagated Haven1 ephemeris'},'radiation':{'solar_flux_W_m2':1361,'earth_IR_W_m2':241,'space_K':3,'radiator_epsilon':0.88,'radiator_alpha':0.12,'radiator_solar_projection':0.08,'radiator_earth_view':0.35,'wall_area_m2':110,'wall_alpha':0.1,'wall_effective_epsilon':0.03,'wall_solar_projection_m2':12,'wall_earth_view':0.4,'array_solar_projected_m2':66,'array_radiating_area_m2':132,'array_alpha':0.85,'array_epsilon':0.85,'array_earth_view':0.2,'notes':'All surfaces/areas/projections/views/optics are study assumptions. Earth IR241W/m2 and solar1361W/m2 are generic source-backed reference values. Albedo is omitted explicitly in this firstround; must add before flightdesign.'},'heat_loads_W':{'avionics':600,'payload':800,'power_conversion':180,'ECLSS':450,'CMG':120,'coolant_pump':60,'cabin_fans':100,'crew':480},'electrical':{'solar_peak_reference_W':13200,'solar_available_assumed_W':9000,'battery_capacity_assumed_kWh':15,'initial_SOC':0.8,'charge_discharge_efficiency_each':0.95,'notes':'Payload800W applies full100W each to8slots as conservative duty assumption, not measured heat. InitialSOC andcapacityassumed. Allbusloads become internalheat except solaroutside; no useful exportedpayloadpower separately modeled.'},'heater_controls':{'battery':{'setpoint_C':10,'gain_W_K':80,'max_W':300},'resources':{'setpoint_C':5,'gain_W_K':30,'max_W':100},'coolant':{'setpoint_C':8,'gain_W_K':100,'max_W':600}},'radiator_link':{'fixed_G_W_K':600,'bypass_min_W_K':10,'bypass_max_W_K':600,'modulation_start_C':14,'modulation_end_C':22,'notes':'Algebraic conductance represents exchanger flow modulation, not hydraulics. No delay/valve dynamics in R1.'},'source_urls':['https://www.vastspace.com/haven-1','https://www.vastspace.com/haven-1-lab','https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/','https://earth.gsfc.nasa.gov/climate/projects/solar-irradiance/science','https://extapps.ksc.nasa.gov/reliability/Documents/Preferred_Practices/2301.pdf']}
(root/'inputs.json').write_text(json.dumps(assumptions,indent=2))
cases=[('baseline',6,1,1,False,10),('larger_radiator',10,1,1,False,10),('cold_fixed',10,0.8,0.5,False,10),('cold_bypass',10,0.8,0.5,True,10),('resolution_check',10,1,1,False,5)]
mos=['loadFile("source/Haven1Thermal.mo");','getErrorString();']
for name,area,env,load,ctrl,step in cases:
    mos += [f'simulate(Haven1Thermal.Integrated,stopTime=86400,numberOfIntervals={86400//step},tolerance=1e-7,method="dassl",outputFormat="csv",fileNamePrefix="{name}",simflags="-override=radiatorArea={area},environmentScale={env},equipmentScale={load},bypassControl={str(ctrl).lower()} -maxStepSize={step}");','getErrorString();']
(root/'source/run.mos').write_text('\n'.join(mos)+'\n')
(root/'cases.json').write_text(json.dumps([{'id':a,'radiator_area_m2':b,'environment_scale':c,'equipment_scale':d,'bypass_control':e,'max_step_s':f} for a,b,c,d,e,f in cases],indent=2))
print(root)
