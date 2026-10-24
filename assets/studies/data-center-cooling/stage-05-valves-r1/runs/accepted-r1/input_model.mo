within ;
package DataCenterValveComparison
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

  model BalancingElement "Manual or generic pressure-limited ideal PICV"
    extends Modelica.Fluid.Interfaces.PartialTwoPort(redeclare package Medium=Water40);
    parameter Boolean pressureIndependent=false;
    parameter SI.Diameter diameter=0.04;
    parameter SI.PressureDifference nominalDP=15000;
    parameter SI.PressureDifference minimumDP=35000;
    parameter SI.MassFlowRate targetMassFlow=rho*144.7/60000;
    output SI.PressureDifference dp=port_a.p-port_b.p;
    Modelica.Fluid.Fittings.SimpleGenericOrifice manual(
      redeclare package Medium=Water40,diameter=diameter,
      use_zeta=false,zeta=1,dp_nominal=nominalDP,m_flow_nominal=mRackNom,
      m_flow_start=mRackNom,m_flow_small=1e-6,use_Re=false,from_dp=false,
      allowFlowReversal=false) if not pressureIndependent;
  equation
    if pressureIndependent then
      port_a.m_flow+port_b.m_flow=0;
      port_a.m_flow=targetMassFlow*noEvent(min(1.0,sqrt(max(dp,0.0)/minimumDP)));
      port_a.h_outflow=inStream(port_b.h_outflow);
      port_b.h_outflow=inStream(port_a.h_outflow);
      port_a.Xi_outflow=inStream(port_b.Xi_outflow);
      port_b.Xi_outflow=inStream(port_a.Xi_outflow);
      port_a.C_outflow=inStream(port_b.C_outflow);
      port_b.C_outflow=inStream(port_a.C_outflow);
    else
      connect(port_a,manual.port_a);
      connect(manual.port_b,port_b);
    end if;
  end BalancingElement;

  model RackBranch "One independently solved rack, its piping, balancing and height"
    parameter Boolean pressureIndependent=false;
    parameter SI.PressureDifference valveNominalPa=15000;
    parameter SI.PressureDifference equipmentNominalPa=100000;
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
      use_zeta=false,zeta=1,dp_nominal=equipmentNominalPa,m_flow_nominal=mRackNom,
      m_flow_start=mRackNom,m_flow_small=1e-6,use_Re=false,from_dp=false,
      allowFlowReversal=false);
    BalancingElement balancingValve(pressureIndependent=pressureIndependent,
      diameter=diameter,nominalDP=valveNominalPa,minimumDP=35000);
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
    parameter Boolean pressureIndependent=false;
    parameter SI.PressureDifference filterNominalPa=20000;
    parameter SI.PressureDifference valveNominalPa[10]={18866.7088691496,17787.8811622184,16929.7311520889,16267.4138833809,15776.0100295199,15430.5022619264,15205.7394288601,15076.3782891255,15016.777967485,15000.7685365312};
    parameter SI.PressureDifference equipmentNominalPa[10]=fill(100000,10);
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
    Segment suctionCommon(length=2.05,diameter=headerDiameter,dz=0,K=0,nParallel=1,mStart=mNom) annotation(Placement(transformation(origin={-195,65},rotation=0,extent={{-10,-7},{10,7}})));
    Segment suctionLegs(length=0.4,diameter=.065,dz=0,K=0,nParallel=2,mStart=mNom) annotation(Placement(transformation(origin={-170,65},rotation=0,extent={{-10,-7},{10,7}})));
    Segment dischargeLegs(length=0.71708,diameter=.065,dz=if flatGeometry then 0 else 0.6,K=2,nParallel=2,mStart=mNom) annotation(Placement(transformation(origin={-100,65},rotation=0,extent={{-10,-7},{10,7}})));
    Segment dischargeCommon(length=4.382611,diameter=headerDiameter,dz=if flatGeometry then 0 else headerHeight-1.15,K=2,nParallel=1,mStart=mNom) annotation(Placement(transformation(origin={-65,65},rotation=0,extent={{-10,-7},{10,7}})));
    Segment returnCommon(length=5.678319,diameter=headerDiameter,dz=if flatGeometry then 0 else 0.55-headerHeight,K=2,nParallel=1,mStart=mNom) annotation(Placement(transformation(origin={-100,-85},rotation=180,extent={{-10,-7},{10,7}})));
    Modelica.Fluid.Fittings.SimpleGenericOrifice filterMap(
      redeclare package Medium=Water40,diameter=headerDiameter,use_zeta=false,zeta=1,
      dp_nominal=filterNominalPa,m_flow_nominal=mNom,m_flow_start=mNom,
      m_flow_small=1e-6,use_Re=false,from_dp=false,allowFlowReversal=false)
      annotation(Placement(transformation(extent={{-38,58},{-22,72}})));
    Modelica.Fluid.Fittings.SimpleGenericOrifice hxMap(
      redeclare package Medium=Water40,diameter=headerDiameter,use_zeta=false,zeta=1,
      dp_nominal=45000,m_flow_nominal=mNom,m_flow_start=mNom,
      m_flow_small=1e-6,use_Re=false,from_dp=false,allowFlowReversal=false)
      annotation(Placement(transformation(origin={-160,-85},rotation=180,extent={{-10,-7},{10,7}})));
    Segment s1(length=0.8,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*10/10) annotation(Placement(transformation(origin={20,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r1(length=0.8,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*10/10) annotation(Placement(transformation(origin={20,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack1(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[1],equipmentNominalPa=equipmentNominalPa[1],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{8,-25},{32,25}})));
    Segment s2(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*9/10) annotation(Placement(transformation(origin={54,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r2(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*9/10) annotation(Placement(transformation(origin={54,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack2(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[2],equipmentNominalPa=equipmentNominalPa[2],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{42,-25},{66,25}})));
    Segment s3(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*8/10) annotation(Placement(transformation(origin={88,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r3(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*8/10) annotation(Placement(transformation(origin={88,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack3(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[3],equipmentNominalPa=equipmentNominalPa[3],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{76,-25},{100,25}})));
    Segment s4(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*7/10) annotation(Placement(transformation(origin={122,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r4(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*7/10) annotation(Placement(transformation(origin={122,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack4(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[4],equipmentNominalPa=equipmentNominalPa[4],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{110,-25},{134,25}})));
    Segment s5(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*6/10) annotation(Placement(transformation(origin={156,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r5(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*6/10) annotation(Placement(transformation(origin={156,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack5(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[5],equipmentNominalPa=equipmentNominalPa[5],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{144,-25},{168,25}})));
    Segment s6(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*5/10) annotation(Placement(transformation(origin={190,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r6(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*5/10) annotation(Placement(transformation(origin={190,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack6(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[6],equipmentNominalPa=equipmentNominalPa[6],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{178,-25},{202,25}})));
    Segment s7(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*4/10) annotation(Placement(transformation(origin={224,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r7(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*4/10) annotation(Placement(transformation(origin={224,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack7(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[7],equipmentNominalPa=equipmentNominalPa[7],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{212,-25},{236,25}})));
    Segment s8(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*3/10) annotation(Placement(transformation(origin={258,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r8(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*3/10) annotation(Placement(transformation(origin={258,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack8(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[8],equipmentNominalPa=equipmentNominalPa[8],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{246,-25},{270,25}})));
    Segment s9(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*2/10) annotation(Placement(transformation(origin={292,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r9(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*2/10) annotation(Placement(transformation(origin={292,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack9(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[9],equipmentNominalPa=equipmentNominalPa[9],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{280,-25},{304,25}})));
    Segment s10(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*1/10) annotation(Placement(transformation(origin={326,95},rotation=0,extent={{-10,-7},{10,7}})));
    Segment r10(length=1.2,diameter=headerDiameter,dz=0,K=0.2,nParallel=1,mStart=mNom*1/10) annotation(Placement(transformation(origin={326,-85},rotation=180,extent={{-10,-7},{10,7}})));
    RackBranch rack10(pressureIndependent=pressureIndependent,valveNominalPa=valveNominalPa[10],equipmentNominalPa=equipmentNominalPa[10],supplyLength=1.698496,returnLength=3.048496,diameter=branchDiameter,headerHeight=headerHeight,flatGeometry=flatGeometry) annotation(Placement(transformation(extent={{314,-25},{338,25}})));
    output Real commandedSpeedPercent=100*speedRatio;
    output Real totalFlowLps(unit="l/s")=pumpBank.port_a.m_flow/rho*1000;
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
    output Real rackFlowLmin[10](each unit="l/min")={rack1.flowLmin,rack2.flowLmin,rack3.flowLmin,rack4.flowLmin,rack5.flowLmin,rack6.flowLmin,rack7.flowLmin,rack8.flowLmin,rack9.flowLmin,rack10.flowLmin};
    output Real rackDPkPa[10](each unit="kPa")={rack1.dp/1000,rack2.dp/1000,rack3.dp/1000,rack4.dp/1000,rack5.dp/1000,rack6.dp/1000,rack7.dp/1000,rack8.dp/1000,rack9.dp/1000,rack10.dp/1000};
    output Real supplyPressureAbsKPa[10](each unit="kPa")={s1.port_b.p/1000,s2.port_b.p/1000,s3.port_b.p/1000,s4.port_b.p/1000,s5.port_b.p/1000,s6.port_b.p/1000,s7.port_b.p/1000,s8.port_b.p/1000,s9.port_b.p/1000,s10.port_b.p/1000};
    output Real returnPressureAbsKPa[10](each unit="kPa")={r1.port_a.p/1000,r2.port_a.p/1000,r3.port_a.p/1000,r4.port_a.p/1000,r5.port_a.p/1000,r6.port_a.p/1000,r7.port_a.p/1000,r8.port_a.p/1000,r9.port_a.p/1000,r10.port_a.p/1000};
    output Real supplyHeaderFlowLps[10](each unit="l/s")={s1.m_flow/rho*1000,s2.m_flow/rho*1000,s3.m_flow/rho*1000,s4.m_flow/rho*1000,s5.m_flow/rho*1000,s6.m_flow/rho*1000,s7.m_flow/rho*1000,s8.m_flow/rho*1000,s9.m_flow/rho*1000,s10.m_flow/rho*1000};
    output SI.MassFlowRate branchMassResidual[10]={rack1.massResidual,rack2.massResidual,rack3.massResidual,rack4.massResidual,rack5.massResidual,rack6.massResidual,rack7.massResidual,rack8.massResidual,rack9.massResidual,rack10.massResidual};
    output SI.MassFlowRate systemMassResidual=pumpBank.port_a.m_flow-sum({rack1.supply.m_flow,rack2.supply.m_flow,rack3.supply.m_flow,rack4.supply.m_flow,rack5.supply.m_flow,rack6.supply.m_flow,rack7.supply.m_flow,rack8.supply.m_flow,rack9.supply.m_flow,rack10.supply.m_flow});
    output SI.PressureDifference loopResidualPa[10]={pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+rack1.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+rack2.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+rack3.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+rack4.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+s5.dp+r5.dp+rack5.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+s5.dp+r5.dp+s6.dp+r6.dp+rack6.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+s5.dp+r5.dp+s6.dp+r6.dp+s7.dp+r7.dp+rack7.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+s5.dp+r5.dp+s6.dp+r6.dp+s7.dp+r7.dp+s8.dp+r8.dp+rack8.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+s5.dp+r5.dp+s6.dp+r6.dp+s7.dp+r7.dp+s8.dp+r8.dp+s9.dp+r9.dp+rack9.dp),pumpBank.dp_pump-(suctionCommon.dp+suctionLegs.dp+dischargeLegs.dp+dischargeCommon.dp+filterMap.dp+returnCommon.dp+hxMap.dp+s1.dp+r1.dp+s2.dp+r2.dp+s3.dp+r3.dp+s4.dp+r4.dp+s5.dp+r5.dp+s6.dp+r6.dp+s7.dp+r7.dp+s8.dp+r8.dp+s9.dp+r9.dp+s10.dp+r10.dp+rack10.dp)};
  equation
    connect(referenceVolume.ports[1],suctionCommon.port_a) annotation(Line(points={{-223,-20},{-214.0,-20},{-214.0,65},{-205,65}},color={0,100,170}));
    connect(suctionCommon.port_b,suctionLegs.port_a) annotation(Line(points={{-185,65},{-180,65}},color={0,100,170}));
    connect(suctionLegs.port_b,pumpBank.port_a) annotation(Line(points={{-160,65},{-155,65}},color={0,100,170}));
    connect(pumpBank.port_b,dischargeLegs.port_a) annotation(Line(points={{-125,65},{-110,65}},color={0,100,170}));
    connect(dischargeLegs.port_b,dischargeCommon.port_a) annotation(Line(points={{-90,65},{-75,65}},color={0,100,170}));
    connect(dischargeCommon.port_b,filterMap.port_a) annotation(Line(points={{-55,65},{-38,65}},color={0,100,170}));
    connect(filterMap.port_b,s1.port_a) annotation(Line(points={{-22,65},{-6.0,65},{-6.0,95},{10,95}},color={0,100,170}));
    connect(r1.port_b,returnCommon.port_a) annotation(Line(points={{10,-85},{-90,-85}},color={200,70,20}));
    connect(returnCommon.port_b,hxMap.port_a) annotation(Line(points={{-110,-85},{-150,-85}},color={200,70,20}));
    connect(hxMap.port_b,referenceVolume.ports[2]) annotation(Line(points={{-170,-85},{-195.0,-85},{-195.0,-20},{-220,-20}},color={0,100,170}));
    connect(pressureReference.ports[1],referenceVolume.ports[3]) annotation(Line(points={{-245,-40},{-231.0,-40},{-231.0,-20},{-217,-20}},color={0,100,170}));
    connect(referenceVolume.heatPort,numericalBath.port) annotation(Line(points={{-235,-5},{-240.0,-5},{-240.0,30},{-245,30}},color={200,0,0}));
    connect(s1.port_b,rack1.supply) annotation(Line(points={{30,95},{30,55},{20,55},{20,25}},color={0,100,170}));
    connect(rack1.ret,r1.port_a) annotation(Line(points={{20,-25},{20,-55},{30,-55},{30,-85}},color={200,70,20}));
    connect(s1.port_b,s2.port_a) annotation(Line(points={{30,95},{44,95}},color={0,100,170}));
    connect(r2.port_b,r1.port_a) annotation(Line(points={{44,-85},{30,-85}},color={200,70,20}));
    connect(s2.port_b,rack2.supply) annotation(Line(points={{64,95},{64,55},{54,55},{54,25}},color={0,100,170}));
    connect(rack2.ret,r2.port_a) annotation(Line(points={{54,-25},{54,-55},{64,-55},{64,-85}},color={200,70,20}));
    connect(s2.port_b,s3.port_a) annotation(Line(points={{64,95},{78,95}},color={0,100,170}));
    connect(r3.port_b,r2.port_a) annotation(Line(points={{78,-85},{64,-85}},color={200,70,20}));
    connect(s3.port_b,rack3.supply) annotation(Line(points={{98,95},{98,55},{88,55},{88,25}},color={0,100,170}));
    connect(rack3.ret,r3.port_a) annotation(Line(points={{88,-25},{88,-55},{98,-55},{98,-85}},color={200,70,20}));
    connect(s3.port_b,s4.port_a) annotation(Line(points={{98,95},{112,95}},color={0,100,170}));
    connect(r4.port_b,r3.port_a) annotation(Line(points={{112,-85},{98,-85}},color={200,70,20}));
    connect(s4.port_b,rack4.supply) annotation(Line(points={{132,95},{132,55},{122,55},{122,25}},color={0,100,170}));
    connect(rack4.ret,r4.port_a) annotation(Line(points={{122,-25},{122,-55},{132,-55},{132,-85}},color={200,70,20}));
    connect(s4.port_b,s5.port_a) annotation(Line(points={{132,95},{146,95}},color={0,100,170}));
    connect(r5.port_b,r4.port_a) annotation(Line(points={{146,-85},{132,-85}},color={200,70,20}));
    connect(s5.port_b,rack5.supply) annotation(Line(points={{166,95},{166,55},{156,55},{156,25}},color={0,100,170}));
    connect(rack5.ret,r5.port_a) annotation(Line(points={{156,-25},{156,-55},{166,-55},{166,-85}},color={200,70,20}));
    connect(s5.port_b,s6.port_a) annotation(Line(points={{166,95},{180,95}},color={0,100,170}));
    connect(r6.port_b,r5.port_a) annotation(Line(points={{180,-85},{166,-85}},color={200,70,20}));
    connect(s6.port_b,rack6.supply) annotation(Line(points={{200,95},{200,55},{190,55},{190,25}},color={0,100,170}));
    connect(rack6.ret,r6.port_a) annotation(Line(points={{190,-25},{190,-55},{200,-55},{200,-85}},color={200,70,20}));
    connect(s6.port_b,s7.port_a) annotation(Line(points={{200,95},{214,95}},color={0,100,170}));
    connect(r7.port_b,r6.port_a) annotation(Line(points={{214,-85},{200,-85}},color={200,70,20}));
    connect(s7.port_b,rack7.supply) annotation(Line(points={{234,95},{234,55},{224,55},{224,25}},color={0,100,170}));
    connect(rack7.ret,r7.port_a) annotation(Line(points={{224,-25},{224,-55},{234,-55},{234,-85}},color={200,70,20}));
    connect(s7.port_b,s8.port_a) annotation(Line(points={{234,95},{248,95}},color={0,100,170}));
    connect(r8.port_b,r7.port_a) annotation(Line(points={{248,-85},{234,-85}},color={200,70,20}));
    connect(s8.port_b,rack8.supply) annotation(Line(points={{268,95},{268,55},{258,55},{258,25}},color={0,100,170}));
    connect(rack8.ret,r8.port_a) annotation(Line(points={{258,-25},{258,-55},{268,-55},{268,-85}},color={200,70,20}));
    connect(s8.port_b,s9.port_a) annotation(Line(points={{268,95},{282,95}},color={0,100,170}));
    connect(r9.port_b,r8.port_a) annotation(Line(points={{282,-85},{268,-85}},color={200,70,20}));
    connect(s9.port_b,rack9.supply) annotation(Line(points={{302,95},{302,55},{292,55},{292,25}},color={0,100,170}));
    connect(rack9.ret,r9.port_a) annotation(Line(points={{292,-25},{292,-55},{302,-55},{302,-85}},color={200,70,20}));
    connect(s9.port_b,s10.port_a) annotation(Line(points={{302,95},{316,95}},color={0,100,170}));
    connect(r10.port_b,r9.port_a) annotation(Line(points={{316,-85},{302,-85}},color={200,70,20}));
    connect(s10.port_b,rack10.supply) annotation(Line(points={{336,95},{336,55},{326,55},{326,25}},color={0,100,170}));
    connect(rack10.ret,r10.port_a) annotation(Line(points={{326,-25},{326,-55},{336,-55},{336,-85}},color={200,70,20}));
    annotation(experiment(StopTime=1,Interval=1,Tolerance=1e-8),
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
  model ManualNetwork
    extends Baseline(pressureIndependent=false);
  end ManualNetwork;
  model PICVNetwork
    extends Baseline(pressureIndependent=true);
  end PICVNetwork;
end DataCenterValveComparison;
