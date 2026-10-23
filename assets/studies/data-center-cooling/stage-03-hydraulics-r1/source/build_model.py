"""Generate the first native Modelica.Fluid hydraulic network from CAD routes.

MSL 4.1.0; fixed water properties near 40 C. This is a steady hydraulic model,
not the thermal/control model. Pump and device curves are assumed test curves.
"""
from pathlib import Path
import csv,json,hashlib
B=Path(__file__).resolve().parents[1]
CAD=B/'inputs/pipe-route-schedule.csv'
if not CAD.exists():CAD=B.parent/'stage-02-design-r1/cad/pipe-route-schedule.csv'
if not CAD.exists():CAD=B.parent/'Stage-02-Design-R1/cad/pipe-route-schedule.csv'
rows={r['tag']:r for r in csv.DictReader(CAD.open())}
L=lambda tag:float(rows[tag]['centerline_m'])
(B/'model').mkdir(exist_ok=True)
src='''within ;
package DataCenterHydraulics
  import SI = Modelica.Units.SI;
  constant SI.Density rho=992.2;
  constant SI.SpecificHeatCapacity cp=4179;
  constant SI.DynamicViscosity mu=0.000653;
  constant SI.Acceleration g=9.80665;
  constant SI.MassFlowRate mNom=1e6/(cp*10);
  constant SI.MassFlowRate mRackNom=mNom/10;
  constant SI.VolumeFlowRate qSingleNom=mNom/rho/2;

  package Water40
    extends Modelica.Media.Water.ConstantPropertyLiquidWater(
      mediumName="StudyWater40C", d_const=992.2, cp_const=4179,
      cv_const=4179, eta_const=0.000653, lambda_const=0.63,
      T_default=313.15);
  end Water40;

  model EquivalentPumpBank "Explicit assumed curve; no switching or check-valve dynamics"
    extends Modelica.Fluid.Interfaces.PartialTwoPortTransport(
      redeclare package Medium=Water40,allowFlowReversal=false,
      m_flow_start=mNom,m_flow_small=1e-6);
    parameter Integer nParallel(min=1)=2;
    parameter Real speedRatio(min=0.05)=1;
    parameter Real hydraulicEfficiency(min=0.1,max=1)=0.75;
    parameter SI.Position shutoffHead=37;
    parameter SI.Position linearHead=0.5;
    parameter SI.Position quadraticHead=9;
    Real ratio=m_flow/rho/nParallel/qSingleNom;
    output SI.Position head=shutoffHead*speedRatio^2-linearHead*speedRatio*ratio-quadraticHead*ratio^2;
    output SI.PressureDifference dp_pump=-dp;
    output SI.Power W_total=dp_pump*m_flow/rho/hydraulicEfficiency;
  equation
    dp=-rho*g*head;
    port_b.h_outflow=inStream(port_a.h_outflow)+g*head/hydraulicEfficiency;
    port_a.h_outflow=inStream(port_b.h_outflow)-g*head/hydraulicEfficiency;
    annotation(Icon(graphics={Ellipse(extent={{-80,80},{80,-80}},lineColor={0,100,170},fillColor={230,240,247},fillPattern=FillPattern.Solid),Polygon(points={{-40,50},{-40,-50},{65,0},{-40,50}},lineColor={0,100,170}),Line(points={{-100,0},{-80,0}},color={0,100,170}),Line(points={{80,0},{100,0}},color={0,100,170}),Text(extent={{-120,130},{120,90}},textString="%name")}));
  end EquivalentPumpBank;

  model Segment "CAD centerline friction plus explicit provisional fitting K"
    extends Modelica.Fluid.Interfaces.PartialTwoPort(redeclare package Medium=Water40);
    parameter SI.Length length=1;
    parameter SI.Diameter diameter=0.125;
    parameter SI.Position dz=0;
    parameter Real K(min=0)=0;
    parameter Integer nParallel(min=1)=1;
    parameter SI.MassFlowRate mStart=mNom;
    Modelica.Fluid.Pipes.StaticPipe pipe(redeclare package Medium=Water40,
      length=length, diameter=diameter, roughness=15e-6,
      height_ab=dz, nParallel=nParallel, allowFlowReversal=false,
      m_flow_start=mStart);
    Modelica.Fluid.Fittings.SimpleGenericOrifice fitting(
      redeclare package Medium=Water40, diameter=diameter*sqrt(nParallel),
      use_zeta=true, zeta=K, allowFlowReversal=false,
      use_Re=false, from_dp=false, m_flow_small=1e-6,
      m_flow_start=mStart) if K>0;
    output SI.PressureDifference dp=port_a.p-port_b.p;
    output SI.MassFlowRate m_flow=port_a.m_flow;
  equation
    connect(port_a,pipe.port_a);
    if K>0 then
      connect(pipe.port_b,fitting.port_a);
      connect(fitting.port_b,port_b);
    else
      connect(pipe.port_b,port_b);
    end if;
    annotation(Icon(graphics={Line(points={{-100,0},{100,0}},color={0,100,170},thickness=3),Text(extent={{-90,70},{90,30}},textString="%name")}));
  end Segment;

  model Elevation "Lossless rack internal elevation; friction is in the rack map"
    extends Modelica.Fluid.Interfaces.PartialTwoPortTransport(
      redeclare package Medium=Water40, allowFlowReversal=false,
      m_flow_start=mRackNom, m_flow_small=1e-6);
    parameter SI.Position dz=-0.9;
  equation
    dp=rho*g*dz;
    port_b.h_outflow=inStream(port_a.h_outflow)-g*dz;
    port_a.h_outflow=inStream(port_b.h_outflow)+g*dz;
  end Elevation;

  model RackBranch "One independently solved rack, its piping, balancing and height"
    parameter SI.Length supplyLength=1.698496;
    parameter SI.Length returnLength=3.048496;
    parameter SI.Diameter diameter=0.04;
    parameter SI.Height headerHeight=2.7;
    parameter Boolean flatGeometry=false;
    Modelica.Fluid.Interfaces.FluidPort_a supply(redeclare package Medium=Water40)
      annotation(Placement(transformation(extent={{-10,90},{10,110}})));
    Modelica.Fluid.Interfaces.FluidPort_b ret(redeclare package Medium=Water40)
      annotation(Placement(transformation(extent={{-10,-110},{10,-90}})));
    Segment supplyPipe(length=supplyLength,diameter=diameter,K=4,
      dz=if flatGeometry then 0 else 1.55-headerHeight,mStart=mRackNom);
    Elevation internalElevation(dz=if flatGeometry then 0 else -0.9);
    Modelica.Fluid.Fittings.SimpleGenericOrifice rackMap(
      redeclare package Medium=Water40,diameter=diameter,
      use_zeta=false,zeta=1,dp_nominal=100000,m_flow_nominal=mRackNom,
      m_flow_start=mRackNom,m_flow_small=1e-6,use_Re=false,from_dp=false,
      allowFlowReversal=false);
    Modelica.Fluid.Fittings.SimpleGenericOrifice balancingValve(
      redeclare package Medium=Water40,diameter=diameter,
      use_zeta=false,zeta=1,dp_nominal=15000,m_flow_nominal=mRackNom,
      m_flow_start=mRackNom,m_flow_small=1e-6,use_Re=false,from_dp=false,
      allowFlowReversal=false);
    Segment returnPipe(length=returnLength,diameter=diameter,K=4,
      dz=if flatGeometry then 0 else headerHeight-0.65,mStart=mRackNom);
    output SI.PressureDifference dp=supply.p-ret.p;
    output Real flowLmin(unit="l/min")=supply.m_flow/rho*60000;
    output SI.MassFlowRate massResidual=supply.m_flow+ret.m_flow;
  equation
    connect(supply,supplyPipe.port_a);
    connect(supplyPipe.port_b,internalElevation.port_a);
    connect(internalElevation.port_b,rackMap.port_a);
    connect(rackMap.port_b,balancingValve.port_a);
    connect(balancingValve.port_b,returnPipe.port_a);
    connect(returnPipe.port_b,ret);
    annotation(Icon(graphics={Rectangle(extent={{-80,80},{80,-80}},lineColor={30,70,90},fillColor={230,240,247},fillPattern=FillPattern.Solid),Text(extent={{-80,45},{80,5}},textString="%name"),Text(extent={{-80,-10},{80,-45}},textString="rack"),Line(points={{0,100},{0,80}},color={0,100,170}),Line(points={{0,-80},{0,-100}},color={200,70,20})}));
  end RackBranch;

  model Baseline "Ten-rack direct return; two equivalent duty pumps, standby isolated"
    parameter Boolean flatGeometry=false "Verification only: remove all hydrostatics, keep pipe lengths";
    parameter SI.Height headerHeight=2.7;
    parameter SI.Diameter headerDiameter=0.125;
    parameter SI.Diameter branchDiameter=0.04;
    parameter Real speedRatio=1;
    parameter SI.AbsolutePressure fillPressure=300000 "Assumed absolute pressure at the reference vessel";
    inner Modelica.Fluid.System system(
      p_start=300000,T_start=313.15,m_flow_start=mNom,
      energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState,
      massDynamics=Modelica.Fluid.Types.Dynamics.SteadyState,
      momentumDynamics=Modelica.Fluid.Types.Dynamics.SteadyState,
      allowFlowReversal=false,m_flow_small=1e-6,use_eps_Re=false)
      annotation(Placement(transformation(extent={{-250,140},{-230,160}})));
    Modelica.Fluid.Vessels.ClosedVolume referenceVolume(
      redeclare package Medium=Water40,V=0.1,nPorts=3,use_portsData=false,
      use_HeatTransfer=true,
      energyDynamics=Modelica.Fluid.Types.Dynamics.SteadyState,
      massDynamics=Modelica.Fluid.Types.Dynamics.SteadyState,T_start=313.15)
      annotation(Placement(transformation(extent={{-235,-20},{-205,10}})));
    Modelica.Fluid.Sources.Boundary_pT pressureReference(
      redeclare package Medium=Water40,p=fillPressure,T=313.15,nPorts=1)
      annotation(Placement(transformation(extent={{-265,-50},{-245,-30}})));
    Modelica.Thermal.HeatTransfer.Sources.FixedTemperature numericalBath(T=313.15)
      "Closes pump-work energy balance; not a data-center HX thermal model"
      annotation(Placement(transformation(extent={{-265,20},{-245,40}})));
    EquivalentPumpBank pumpBank(nParallel=2,speedRatio=speedRatio)
      annotation(Placement(transformation(extent={{-155,50},{-125,80}})));
'''
poses={}
def segment(name,length,d='headerDiameter',dz='0',k=0,n=1,m='mNom',x=0,y=0):
 rot=180 if name=='returnCommon' or (name.startswith('r') and name[1:].isdigit()) else 0
 poses[name]=(x,y,rot)
 return f'    Segment {name}(length={length},diameter={d},dz={dz},K={k},nParallel={n},mStart={m}) annotation(Placement(transformation(origin={{{x},{y}}},rotation={rot},extent={{{{-10,-7}},{{10,7}}}})));\n'
src+=segment('suctionCommon',L('HX_to_suction')+L('CDU_suction'),x=-195,y=65)
src+=segment('suctionLegs',L('P-101A_in'),'.065',n=2,x=-170,y=65)
src+=segment('dischargeLegs',L('P-101A_out'),'.065','if flatGeometry then 0 else 0.6',k=2,n=2,x=-100,y=65)
src+=segment('dischargeCommon',L('CDU_discharge')+L('CDU_supply_riser'),dz='if flatGeometry then 0 else headerHeight-1.15',k=2,x=-65,y=65)
src+=segment('returnCommon',L('CDU_return_to_HX'),dz='if flatGeometry then 0 else 0.55-headerHeight',k=2,x=-100,y=-85)
src+='''    Modelica.Fluid.Fittings.SimpleGenericOrifice filterMap(
      redeclare package Medium=Water40,diameter=headerDiameter,use_zeta=false,zeta=1,
      dp_nominal=20000,m_flow_nominal=mNom,m_flow_start=mNom,
      m_flow_small=1e-6,use_Re=false,from_dp=false,allowFlowReversal=false)
      annotation(Placement(transformation(extent={{-38,58},{-22,72}})));
    Modelica.Fluid.Fittings.SimpleGenericOrifice hxMap(
      redeclare package Medium=Water40,diameter=headerDiameter,use_zeta=false,zeta=1,
      dp_nominal=45000,m_flow_nominal=mNom,m_flow_start=mNom,
      m_flow_small=1e-6,use_Re=false,from_dp=false,allowFlowReversal=false)
      annotation(Placement(transformation(origin={-160,-85},rotation=180,extent={{-10,-7},{10,7}})));
'''
for i in range(1,11):
 x=20+(i-1)*34;length=.8 if i==1 else 1.2
 src+=segment(f's{i}',length,k=.2,m=f'mNom*{11-i}/10',x=x,y=95)
 src+=segment(f'r{i}',length,k=.2,m=f'mNom*{11-i}/10',x=x,y=-85)
 src+=f'    RackBranch rack{i}(supplyLength={L(f"L-{200+i}S")},returnLength={L(f"L-{200+i}R")},diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{{{{x-12},-25}},{{{x+12},25}}}})));\n'
arr=lambda fmt:'{'+','.join(fmt.format(i=i) for i in range(1,11))+'}'
src+='''    output Real totalFlowLps(unit="l/s")=pumpBank.port_a.m_flow/rho*1000;
    output Real flowPerDutyPumpM3h(unit="m3/h")=pumpBank.port_a.m_flow/rho/2*3600;
    output SI.Length pumpHeadM=pumpBank.head;
    output Real pumpDPkPa(unit="kPa")=pumpBank.dp_pump/1000;
    output SI.Power pumpHydraulicW=pumpBank.dp_pump*pumpBank.port_a.m_flow/rho;
    output SI.Power pumpShaftW=pumpBank.W_total;
    output SI.Power pumpElectricalW=pumpBank.W_total/0.90;
    output Real pumpSuctionAbsKPa(unit="kPa")=pumpBank.port_a.p/1000;
    output SI.MassFlowRate referenceMakeupKgS=pressureReference.ports[1].m_flow;
    output SI.Power numericalBathHeatRemovedW=numericalBath.port.Q_flow;
    output SI.Power pumpEnergyResidualW=pumpBank.W_total-numericalBath.port.Q_flow;
'''
src+=f'    output Real rackFlowLmin[10](each unit="l/min")={arr("rack{i}.flowLmin")};\n'
src+=f'    output Real rackDPkPa[10](each unit="kPa")={arr("rack{i}.dp/1000")};\n'
src+=f'    output Real supplyPressureAbsKPa[10](each unit="kPa")={arr("s{i}.port_b.p/1000")};\n'
src+=f'    output Real returnPressureAbsKPa[10](each unit="kPa")={arr("r{i}.port_a.p/1000")};\n'
src+=f'    output Real supplyHeaderFlowLps[10](each unit="l/s")={arr("s{i}.m_flow/rho*1000")};\n'
src+=f'    output SI.MassFlowRate branchMassResidual[10]={arr("rack{i}.massResidual")};\n'
src+=f'    output SI.MassFlowRate systemMassResidual=pumpBank.port_a.m_flow-sum({arr("rack{i}.supply.m_flow")});\n'
common='suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp'
paths=['pumpBank.dp_pump-('+common+'+'+'+'.join(f's{k}.dp+r{k}.dp' for k in range(1,i+1))+f'+rack{i}.dp)' for i in range(1,11)]
src+='    output SI.PressureDifference loopResidualPa[10]={'+','.join(paths)+'};\n'
src+='  equation\n'
conns=[('referenceVolume.ports[1]','suctionCommon.port_a'),('suctionCommon.port_b','suctionLegs.port_a'),('suctionLegs.port_b','pumpBank.port_a'),('pumpBank.port_b','dischargeLegs.port_a'),('dischargeLegs.port_b','dischargeCommon.port_a'),('dischargeCommon.port_b','filterMap.port_a'),('filterMap.port_b','s1.port_a'),('r1.port_b','returnCommon.port_a'),('returnCommon.port_b','hxMap.port_a'),('hxMap.port_b','referenceVolume.ports[2]'),('pressureReference.ports[1]','referenceVolume.ports[3]'),('referenceVolume.heatPort','numericalBath.port')]
for i in range(1,11):
 conns+=[(f's{i}.port_b',f'rack{i}.supply'),(f'rack{i}.ret',f'r{i}.port_a')]
 if i<10:conns+=[(f's{i}.port_b',f's{i+1}.port_a'),(f'r{i+1}.port_b',f'r{i}.port_a')]
def endpoint(port):
 name=port.split('.')[0]
 if name in poses:
  x,y,rot=poses[name];sign=-1 if port.endswith('port_a') else 1
  return (x+sign*10*(-1 if rot==180 else 1),y)
 if name.startswith('rack'):
  i=int(name[4:]);return (20+(i-1)*34,25 if port.endswith('supply') else -25)
 explicit={'pumpBank.port_a':(-155,65),'pumpBank.port_b':(-125,65),'filterMap.port_a':(-38,65),'filterMap.port_b':(-22,65),'hxMap.port_a':(-150,-85),'hxMap.port_b':(-170,-85),'referenceVolume.ports[1]':(-223,-20),'referenceVolume.ports[2]':(-220,-20),'referenceVolume.ports[3]':(-217,-20),'referenceVolume.heatPort':(-235,-5),'numericalBath.port':(-245,30),'pressureReference.ports[1]':(-245,-40)}
 return explicit[port]
for a,b in conns:
 x,y=endpoint(a);u,v=endpoint(b)
 if x==u or y==v:points=[(x,y),(u,v)]
 elif a.startswith('s') and b.startswith('rack'):points=[(x,y),(x,55),(u,55),(u,v)]
 elif a.startswith('rack'):points=[(x,y),(x,-55),(u,-55),(u,v)]
 else:points=[(x,y),((x+u)/2,y),((x+u)/2,v),(u,v)]
 points_s='{'+','.join('{'+str(x)+','+str(y)+'}' for x,y in points)+'}'
 color='{200,70,20}' if a.startswith('r') and not a.startswith('reference') else '{0,100,170}'
 if 'heatPort' in a:color='{200,0,0}'
 src+=f'    connect({a},{b}) annotation(Line(points={points_s},color={color}));\n'

src+='''    annotation(experiment(StopTime=1,Interval=1,Tolerance=1e-8),
      Diagram(coordinateSystem(extent={{-280,-150},{370,180}})),
      Documentation(info="<html><p>Steady hydraulic network using MSL 4.1.0 Modelica.Fluid components and CAD-derived centerline lengths. Fixed water properties near 40 C. Assumed pump, rack, filter, HX and balancing loss curves, not selected vendor data. Two identical duty pumps are reduced to an equivalent parallel bank; standby is isolated. CDU shared manifolds use full-flow equivalent lengths. Blind header tails are excluded from circulating flow. Header tee K=0.2 per run segment and branch K=8 per pair are provisional. No heat-load, temperature-control, pump-switching, expansion sizing or water-hammer claim. The 1 second output horizon repeats a steady algebraic solution and is not a startup transient. A fixed-temperature numerical volume closes pump-work energy balance only.</p></html>"));
  end Baseline;

  model FlatGeometryCheck
    extends Baseline(flatGeometry=true);
  end FlatGeometryCheck;
  model RaisedHeaderCheck
    extends Baseline(headerHeight=3.0);
  end RaisedHeaderCheck;
  annotation(uses(Modelica(version="4.1.0")));
end DataCenterHydraulics;
'''
(B/'model/DataCenterHydraulics.mo').write_text(src)
assumptions={'cad_route_sha256':hashlib.sha256(CAD.read_bytes()).hexdigest(),'rho_kg_m3':992.2,'cp_J_kgK':4179,'mu_Pa_s':.000653,'roughness_m':15e-6,'rack_target_Lmin':1e6/(4179*10)/992.2/10*60000,'pump_curve_per_duty':{'rpm':1500,'q_m3s':[0,1e6/(4179*10)/992.2/2,1e6/(4179*10)/992.2],'head_m':[37,27.5,0],'provenance':'Assumed test curve, not a purchased pump'},'pump_hydraulic_efficiency':.75,'motor_efficiency':.90,'fill_pressure_absolute_Pa':300000,'rack_map_Pa_at_nominal':100000,'balancing_valve_Pa_at_nominal':15000,'filter_Pa_at_nominal_total':20000,'HX_Pa_at_nominal_total':45000,'header_tee_K_per_segment':.2,'branch_total_K':8,'pump_leg_K':2,'common_supply_K':2,'common_return_K':2,'active_header_segments_m':[.8]+[1.2]*9,'blind_tail_per_header_m':.6,'limitations':['Fixed-property hydraulic study; rack 1 MW heat is used only to set flow target','Pump and equipment curves and all K factors are provisional','No transient startup, thermal control or standby switching','CDU manifolds and equal pump branches are equivalent reductions','Elevation verification holds lengths fixed; not a new CAD reroute']}
(B/'model/assumptions.json').write_text(json.dumps(assumptions,indent=2)+'\n')
(B/'source/run.mos').write_text('''setCommandLineOptions("--numProcs=2");
loadModel(Modelica,{"4.1.0"});
loadFile("../../model/DataCenterHydraulics.mo");
getErrorString();
checkModel(DataCenterHydraulics.Baseline);
getErrorString();
simulate(DataCenterHydraulics.Baseline,startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="baseline",cflags="-O1");
getErrorString();
simulate(DataCenterHydraulics.FlatGeometryCheck,startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="flat",cflags="-O1");
getErrorString();
simulate(DataCenterHydraulics.RaisedHeaderCheck,startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="raised",cflags="-O1");
getErrorString();
''')
print('Generated native Modelica.Fluid network and three baseline/verification runs.')
