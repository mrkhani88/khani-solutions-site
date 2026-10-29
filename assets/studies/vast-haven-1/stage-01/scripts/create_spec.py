from pathlib import Path
import json,math
P=Path(__file__).resolve().parent
parts=[]
C={'structure':[.78,.82,.86],'solar':[.43,.22,.075],'radiator':[.88,.91,.94],'habitation':[.79,.65,.47],'thermal':[.04,.58,.65],'avionics':[.15,.29,.47],'power':[.45,.35,.66],'eclss':[.23,.58,.39],'payload':[.78,.48,.18],'attitude':[.42,.47,.52],'propulsion':[.63,.39,.16],'routes':[.09,.57,.72]}
def add(id,label,group,geom,role='',evidence='Representative geometry; subsystem existence publicly documented',src=['S1'],hide=False,detail=False,thermal=False,color=None):
 parts.append(dict(id=id,label=label,group=group,geometry=geom,role=role,evidence=evidence,source_ids=src,color=color or C[group],cutaway_hide=hide,detail=detail,thermal_candidate=thermal))
def box(id,label,g,p,s,**kw):add(id,label,g,dict(kind='box',p=p,size=s),**kw)
def cyl(id,label,g,p,r,h,axis=[1,0,0],**kw):add(id,label,g,dict(kind='cylinder',p=p,r=r,h=h,axis=axis),**kw)
def shell(id,label,x,r1,r2,L,half,**kw):add(id,label,'structure',dict(kind='shell',p=[x,0,0],r1=r1,r2=r2,h=L,wall=.012,half=half),hide=half=='near',**kw)
for sec,x,r1,r2,L in [('DockCone',.30,.78,2.20,1.70),('Barrel',2.,2.20,2.20,6.30),('AftCone',8.30,2.20,.36,1.80)]:
 for h in ['near','far']:shell(sec+'_'+h,('Window-end cone' if sec=='AftCone' else sec.replace('Cone',' cone'))+' / '+h+' shell',x,r1,r2,L,h,role='Exterior envelope representation; 12 mm CAD display shell is assumed, not a pressure-vessel design',evidence='4.4 m maximum diameter and 10.1 m length public; section lengths, shell gauge and shielding geometry inferred',src=['S1','S3'])
for x in [2.03,3.57,5.14,6.71,8.27]:
 add('Seam_'+str(x).replace('.','_'),'Exterior circumferential seam','structure',dict(kind='torus',p=[x,0,0],r=2.205,t=.009,axis=[1,0,0]),detail=True,evidence='Illustrative seam placement',hide=True)
# Passive docking adapter at X=0; nominal ring proportions are visual assumptions.
add('DockingAdapter','Passive docking adapter','structure',dict(kind='ring',p=[0,0,0],r=.80,inner=.56,h=.30,axis=[1,0,0]),role='Visiting Dragon docking interface',src=['S1','S3'],color=[.18,.23,.28])
cyl('DockingHatch','Docking pressure hatch','structure',[.25,0,0],.55,.045,color=[.77,.81,.85])
for i in range(12):
 a=2*math.pi*i/12;cyl('DockingLug_%02d'%i,'Docking interface lug %02d'%(i+1),'structure',[.03,.69*math.cos(a),.69*math.sin(a)],.032,.08,detail=True,color=[.58,.63,.68])
# Radial 1.1 m domed observation window. Cut exact roof opening in the barrel in builder.
add('WindowBezel','Observation window bezel','structure',dict(kind='ring',p=[7.75,0,2.10],r=.63,inner=.55,h=.18,axis=[0,0,1]),role='Radial window near common area',evidence='1.1 m window diameter published; location inferred from July 2026 cutaway',src=['S1','S3'],thermal=True,color=[.4,.45,.49])
add('DomedWindow','1.1 m domed window','structure',dict(kind='dome',p=[7.75,0,2.27],r=.55,height=.28,axis=[0,0,1]),role='Optical / conductive / radiative thermal interface; pane construction unknown',evidence='Diameter documented; curvature/thickness/location modeled',src=['S1','S3'],thermal=True,color=[.16,.46,.65])
# Four visual banks, three wing assemblies per bank = 12; exact segmentation and deployment inferred.
for side in [-1,1]:
 for bank,start in enumerate([2.13,5.30]):
  for w in range(3):
   ident=f'SolarWing_{"L" if side<0 else "R"}_{bank*3+w+1:02d}'
   x=start+w*.94;y=2.18 if side>0 else -5.18
   box(ident,'Solar wing '+ident.split('_')[-2]+'-'+str(bank*3+w+1),'solar',[x,y,.05],[.91,3.0,.035],role='Deployable PV wing; published rating 1.1 kW per wing, not its heat dissipation',evidence='12 wings documented; four-bank grouping and wing dimensions inferred from imagery',src=['S1','S3'],thermal=True)
   for k in range(6):
    box(ident+'_Cell_'+str(k+1),'PV tile (visual subdivision)','solar',[x+.035,y+k*.5+.025,.087],[.84,.45,.007],detail=True,evidence='Decorative subdivision, not flight solar cell count',color=[.28,.16,.07])
# Candidate radiator faces on back side; no actual radiator location or area inferred as verified.
for i in range(3):
 box('Radiator_'+str(i+1),'Candidate radiator panel '+str(i+1),'radiator',[3.0+i*1.4,2.15,-.65],[1.30,.07,1.30],role='Representative radiator envelope for later area/optical trade study',evidence='External radiator existence documented; flat-panel location, count and area assumed',src=['S2','S6'],thermal=True)
# Representative interior deck/aisle and crew quarters, consistent with public cutaway themes.
box('CabinDeck','Cabin deck / equipment-bay boundary','habitation',[2.1,-1.55,-1.10],[6.2,3.10,.08],role='Internal layout reference; not a confirmed pressure boundary',evidence='Layout inferred from public cutaway; dimensions assumed',src=['S3'])
box('Aisle','Central aisle floor strip','habitation',[2.15,-.47,-1.005],[5.9,.94,.012],color=[.30,.35,.40],evidence='Illustrative clear aisle')
for side in [-1,1]:
 for tier,z in enumerate([-.82,.28]):
  y=.55 if side>0 else -1.51
  k=('R' if side>0 else 'L')+str(tier+1)
  add('CrewQuarter_'+k,'Private crew quarter '+k,'habitation',dict(kind='quarter',p=[2.65,y,z],size=[2.2,.96,.90],side=side),role='Four crew accommodation envelopes; use as crew/metabolic-load zones later',evidence='Four private quarters documented; packaging dimensions inferred',src=['S1','S3'],thermal=True)
  box('Bunk_'+k,'Crew restraint / mattress '+k,'habitation',[2.70,y+.04,z+.04],[2.08,.88,.09],detail=True,color=[.9,.86,.74],evidence='Illustrative habitation detail')
# Lab rack with eight MLE slots.
box('LabRack','Haven-1 Lab rack envelope','payload',[6.15,.82,-.96],[1.22,.60,1.95],role='Eight MLE slots, each published 100 W continuous interface; not an assumed mission heat map',evidence='8 MLE slots documented; rack dimensions/location representative',src=['S4'],thermal=True)
for col in range(2):
 for row in range(4):
  box('MLE_%02d'%(col*4+row+1),'Lab payload MLE slot %02d'%(col*4+row+1),'payload',[6.20+col*.55,.76,-.88+row*.45],[.49,.08,.40],role='Candidate electronics/biolab thermal submodel',evidence='Published interface count; slot/box dimensions modeled',src=['S4'],thermal=True,color=[.88,.67,.34])
box('UtilityTable','Deployable common-area table (deployed)','habitation',[7.48,-.7,-.20],[.72,1.4,.06],role='Common area near window',evidence='Table shown in public interior cutaway; dimensions assumed',src=['S3'])
# Under-deck engineering bays: all placements/envelopes explicitly assumed.
for i,x in enumerate([3.,3.65]):
 box('ColdPlate_'+str(i+1),'Avionics cold plate '+str(i+1),'thermal',[x,-1.2,-1.37],[.55,.72,.055],role='Conduct equipment heat to a pumped loop; channel detail deferred',src=['S1','S6'],thermal=True)
 box('VCU' if i==0 else 'Comms','Vast Control Unit envelope' if i==0 else 'Communications electronics envelope','avionics',[x+.04,-1.16,-1.31],[.45,.62,.23],role='Electronics heat source; representative box, no PCB claimed',src=['S1'],thermal=True)
box('PowerDistribution','Power distribution / conversion tray','power',[4.42,-1.25,-1.39],[.85,.77,.30],role='Electrical conversion and distribution; heat map TBD',src=['S1'],thermal=True)
for i in range(4):box('Battery_'+str(i+1),'Battery module envelope '+str(i+1),'power',[4.45+i*.70,.45,-1.53],[.62,.76,.42],role='Battery thermal submodel candidate; count, chemistry and capacity not public',evidence='Battery existence documented; four-module count and packaging assumed',src=['S1'],thermal=True)
box('PumpTray','Thermal pump tray assembly envelope','thermal',[5.45,-1.20,-1.46],[1.0,.72,.36],role='Pumped coolant circulation; pump count/curve/coolant unknown',src=['S1','S6'],thermal=True)
for i in range(2):cyl('Pump_'+str(i+1),'Representative pump cartridge '+str(i+1),'thermal',[5.60+i*.4,-.95,-1.03],.11,.25,axis=[0,0,1],evidence='Two cartridges are an engineering assumption, not verified redundant pump count',thermal=True)
box('AirRevitalization','Air revitalization / filter assembly','eclss',[5.23,.40,-.95],[.72,.95,1.0],role='Cabin air quality and trace contaminant control',src=['S1','S5'],thermal=True)
box('AirHeatExchanger','Cabin air-to-coolant heat exchanger','eclss',[6.75,-1.20,-1.40],[.65,.70,.32],role='Proposed air-handler heat exchanger for later coupled CFD',evidence='Proposed study interface; exact Haven-1 air-to-coolant heat exchanger implementation unverified',src=['S1','S5'],thermal=True)
for i in range(2):cyl('CabinFan_'+str(i+1),'Cabin ventilation fan '+str(i+1),'eclss',[6.87+i*.27,-.82,-.94],.11,.10,axis=[0,0,1],role='Forced circulation in microgravity; fan count/flow assumed',thermal=True)
# Six CMG envelopes with brackets.
for i in range(6):
 a=2*math.pi*i/6
 cyl('CMG_'+str(i+1),'Control moment gyro '+str(i+1),'attitude',[1.65,.92*math.cos(a),.92*math.sin(a)],.22,.25,role='Attitude control flywheel/gimbal envelope',evidence='Six CMGs documented; placement and size assumed',src=['S1'],thermal=True)
for i in range(2):box('CrewControl_'+str(i+1),'Crew control panel '+str(i+1),'avionics',[2.13,-.80+i*1.30,.08],[.15,.38,.32],role='Crew controls / display heat and electrical load interface',evidence='Two stationary panels documented; dimensions and exact positions inferred',src=['S5'],thermal=True)
# Three visible tanks represent two propellants and life-support gas; not a confirmed installation inventory.
for id,label,p,r,h,g in [('OxidizerTank','N2O propellant tank envelope',[8.5,.50,-.45],.35,.80,'propulsion'),('FuelTank','Ethane propellant tank envelope',[8.5,-.50,-.45],.30,.80,'propulsion'),('LifeSupportTank','Oxygen / nitrox tank envelope',[1.25,0,-.50],.24,.65,'eclss')]:
 cyl(id,label,g,p,r,h,role='Tank packaging placeholder; pressure, capacity and mass unspecified',evidence='Gas system documented; tank sizes/count/location assumed',src=['S2','S7'],thermal=True)
box('GasValveTray','Oxygen / nitrox solenoid valve tray','eclss',[1.82,-.65,-.60],[.25,1.30,.30],src=['S1'],thermal=True)
for i in range(8):cyl('WasteTank_'+str(i+1),'Wet-trash container '+str(i+1),'eclss',[2.30+i*.70,-.15,-1.65],.16,.31,axis=[0,0,1],role='Waste storage envelope',evidence='Eight containers documented; installation positions and sizes assumed',src=['S1'],thermal=True)
# Representative closed tubing paths with separate named supply/return sections; unconnected ends deferred, no hydraulic solve.
for route,y,z,color in [('Supply',-1.32,-1.12,[.04,.45,.85]),('Return',-1.42,-1.18,[.85,.27,.12])]:
 add('Coolant'+route,'Coolant '+route.lower()+' header','routes',dict(kind='tube',p=[2.75,y,z],r=.015,inner=.012,h=4.85,axis=[1,0,0]),role='Representative coolant routing, 24 mm clear bore assumption',evidence='Pumped loop documented; topology and bore assumed',src=['S1','S6'],thermal=True,color=color)
 for i,x in enumerate([3.22,3.87,4.80,5.90,7.05]):
  add(route+'Branch_'+str(i+1),route+' branch '+str(i+1),'routes',dict(kind='tube',p=[x,y,z],r=.010,inner=.008,h=.50,axis=[0,1,0]),role='Illustrative branch; thermal/hydraulic connections not sized',src=['S6'],thermal=True,color=color)
add('IMVDuct','Dragon intermodule ventilation duct envelope','eclss',dict(kind='tube',p=[.38,.48,.35],r=.10,inner=.09,h=1.70,axis=[1,0,0]),role='Intermodule ventilation in docking tunnel',evidence='Tunnel IMV duct documented; routing and diameter assumed',src=['S5'],thermal=True)
add('CabinDuct','Cabin ventilation duct envelope','eclss',dict(kind='tube',p=[2.20,1.38,1.0],r=.11,inner=.10,h=5.5,axis=[1,0,0]),role='Representative forced-air distribution; no buoyant natural-convection assumption',src=['S1'],thermal=True)
for i in range(4):
 a=math.pi/4+i*math.pi/2;y=1.9*math.cos(a);z=1.9*math.sin(a)
 add('ThrusterEnvelope_'+str(i+1),'Saiph thruster envelope '+str(i+1),'propulsion',dict(kind='cone',p=[8.65,y,z],r1=.07,r2=.14,h=.25,axis=[1,0,0]),role='Propulsion-adjacent thermal interface; nozzle count and placement not confirmed',evidence='Saiph propulsion documented; four envelope count and geometry assumed',src=['S7'],thermal=True)
# Proposed study hardware extends coverage beyond what the public flight layout discloses.
proposed='Proposed study element; exact Haven-1 implementation, quantity, dimensions and placement unverified'
for ident,label,pt,sz in [
 ('MPPT_A','Solar MPPT / charge regulator A',[3.0,.45,-1.92],[.50,.70,.18]),('MPPT_B','Solar MPPT / charge regulator B',[3.62,.45,-1.92],[.50,.70,.18]),
 ('BMS','Battery management electronics',[6.82,.45,-1.52],[.40,.75,.20]),('HeaterController','Heater controller / switching electronics',[4.42,-1.23,-1.78],[.65,.70,.18]),
 ('ThermalController','Thermal control electronics',[5.23,-1.23,-1.85],[.55,.68,.18]),('FanDrive','Ventilation fan drive electronics',[7.40,-1.12,-1.49],[.35,.60,.22])]:
 box(ident,label,'power',pt,sz,role='Indirect thermal-control energy resource / electrical conversion waste heat; ratings and efficiency TBD',evidence=proposed,thermal=True)
for i,x in enumerate([3.03,3.68,4.50,5.2,5.90,6.60]):
 box('HeaterPad_'+str(i+1),'Candidate thermostatic heater patch '+str(i+1),'thermal',[x,.47 if i>1 else -1.15,-1.555 if i>1 else -1.38],[.40,.50,.008],role='Electrical power to controlled heat; wattage and setpoint not assigned',evidence=proposed,thermal=True,color=[.82,.25,.14])
for i,(x,y,z) in enumerate([(3.3,-1.1,-1.05),(4.7,.6,-1.1),(6.1,.6,-1.1),(5.8,-1.15,-1.05),(7.2,-.82,-1.05),(6.5,.75,.2)]):
 cyl('TemperatureSensor_'+str(i+1),'Candidate temperature sensor '+str(i+1),'thermal',[x,y,z],.025,.055,axis=[0,0,1],role='Feedback to heater/flow control; placement, lag, calibration and uncertainty TBD',evidence=proposed,thermal=True,color=[.9,.65,.1])
cyl('CoolantAccumulator','Coolant reservoir / accumulator envelope','thermal',[5.35,-1.1,-1.82],.16,.50,axis=[1,0,0],role='Coolant inventory, fill/expansion and pump inlet conditioning; volume/coolant TBD',evidence=proposed,thermal=True)
for i,x in enumerate([3.0,5.4,7.35]):
 box('CoolantValve_'+str(i+1),'Candidate coolant control / isolation valve '+str(i+1),'thermal',[x,-1.49,-1.23],[.13,.15,.15],role='Flow regulation, radiator bypass/isolation; actuator dissipation and K-value TBD',evidence=proposed,thermal=True,color=[.25,.39,.43])
box('FlowSensor','Candidate flow / pressure sensor envelope','thermal',[6.50,-1.48,-1.25],[.22,.14,.15],role='Thermal-loop sensing; pressure, flow and electrical input TBD',evidence=proposed,thermal=True)
box('AirWaterSeparator','Condensate separator envelope','eclss',[7.1,.65,-.98],[.45,.58,.50],role='Humidity/latent-load resource interface; water separation design not public',evidence=proposed,thermal=True)
cyl('WaterTank','Water resource tank envelope','eclss',[7.64,.20,-1.65],.22,.42,axis=[0,0,1],role='Representative potable/condensate resource; inventory/type/function allocation TBD',evidence=proposed,thermal=True)
for i,x in enumerate([3.0,3.65]):
 box('TIM_'+str(i+1),'Candidate equipment-to-coldplate interface '+str(i+1),'thermal',[x+.04,-1.16,-1.316],[.45,.62,.003],role='Conductive thermal contact, pad/TIM thickness and resistance TBD',evidence=proposed,thermal=True,color=[.45,.47,.49])
for i,y in enumerate([-1.15,1.15]):
 box('EquipmentRail_'+str(i+1),'Equipment mounting rail '+str(i+1),'structure',[2.25,y,-1.72],[5.75,.08,.09],role='Structural conduction path; contact properties, loads and material TBD',evidence=proposed,thermal=True)
for side in ['near','far']:
 add('Insulation_'+side,'Candidate multilayer insulation zone / '+side,'structure',dict(kind='shell',p=[2.04,0,0],r1=2.17,r2=2.17,h=6.22,wall=.006,half=side),role='MLI represented as an envelope, not six millimetres of solid metal; effective emissivity/conductivity unknown',evidence=proposed,hide=side=='near',thermal=True,color=[.64,.50,.23])
for i,z in enumerate([-.5,.5]):
 add('RadiatorRoute_'+str(i+1),'Candidate radiator fluid connection '+str(i+1),'routes',dict(kind='tube',p=[5.8,1.3,z],r=.015,inner=.012,h=.9,axis=[0,1,0]),role='Schematic radiator interface; unconnected routing must be completed before hydraulic/CFD meshing',evidence=proposed,thermal=True)
meta=dict(title='Haven-1 public-reference assembly R1',stage='CAD review only — no thermal/CFD solution',units='m',source_anchors={'overall_length_m':10.1,'maximum_exterior_diameter_m':4.4,'window_diameter_m':1.1,'solar_wing_count':12,'crew_count':4,'cmg_count':6,'wet_trash_count':8,'lab_MLE_slots':8},axis='X docking end 0 to window/opposite end 10.1 m; Y lateral; Z window/up',assumptions=['Exterior section lengths and all internal dimensions inferred; not manufacturer CAD.','12 mm display shell is not a selected or verified wall thickness.','Representative cabin layout is not calibrated to published 80 m3 pressure/45 m3 habitable volumes. Those values are source metadata, not model-derived volumes.','Radiator panel location/count/area and all piping topology are candidate assumptions.','Equipment colors identify systems, not temperatures.','No Dragon vehicle is included. No fabricated mission temperatures, powers, stresses or mesh convergence.'])
(P/'assembly_spec.json').write_text(json.dumps(dict(metadata=meta,parts=parts),indent=2))
print(len(parts),'parts')
