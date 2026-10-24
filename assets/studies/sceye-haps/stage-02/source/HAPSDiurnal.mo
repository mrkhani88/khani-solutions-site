within ;
package HAPSDiurnal "Independent public-reference HAPS mission thermal-energy model"
  import SI=Modelica.Units.SI;
  constant Real sigma=5.670374419e-8;
  constant Real pi=Modelica.Constants.pi;
  function clamp
    input Real x; input Real low=0; input Real high=1; output Real y;
  algorithm y:=min(high,max(low,x)); end clamp;
  function window
    input Real h; input Real a; input Real b; output Real y;
  algorithm y:=max(0,min(1,min((h-a)/0.5,(b-h)/0.5))); end window;
  connector EnvironmentBus "Mission signals, not a heat-flow connector"
    input Real Tair(unit="K"); input Real sx; input Real sy; input Real sz; input Real DNI(unit="W/m2");
    input Real earthIR(unit="W/m2"); input Real skyIR(unit="W/m2"); input Real reflected(unit="W/m2");
    input Real wind(unit="m/s"); input Real hour; input Real day; input Real heading(unit="deg"); input Real density(unit="kg/m3");
    annotation(Icon(graphics={Rectangle(extent={{-15,100},{15,-100}},lineColor={120,100,20},fillColor={255,225,130},fillPattern=FillPattern.Solid)}));
  end EnvironmentBus;
  connector EnvironmentSource "Mission signals, not a heat-flow connector"
    output Real Tair(unit="K"); output Real sx; output Real sy; output Real sz; output Real DNI(unit="W/m2");
    output Real earthIR(unit="W/m2"); output Real skyIR(unit="W/m2"); output Real reflected(unit="W/m2");
    output Real wind(unit="m/s"); output Real hour; output Real day; output Real heading(unit="deg"); output Real density(unit="kg/m3");
    annotation(Icon(graphics={Rectangle(extent={{-15,100},{15,-100}},lineColor={120,100,20},fillColor={255,225,130},fillPattern=FillPattern.Solid)}));
  end EnvironmentSource;
  model ThermalMass "Lumped capacity with one conservative heat port"
    parameter SI.HeatCapacity C=10000;
    parameter SI.Temperature T0=293.15;
    input SI.Power Q=0 "Local heat source; negative for exported panel electricity";
    SI.Temperature T(start=T0,fixed=true);
    output SI.Energy U;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a port annotation(Placement(transformation(extent={{-110,-10},{-90,10}})));
  equation
    port.T=T; C*der(T)=port.Q_flow+Q; U=C*(T-T0);
    annotation(Icon(graphics={Rectangle(extent={{-80,60},{80,-60}},lineColor={28,85,105},fillColor={220,237,245},fillPattern=FillPattern.Solid),Text(extent={{-75,45},{75,-25}},textString="%name"),Text(extent={{-75,-25},{75,-55}},textString="C=%C J/K")}),Diagram(coordinateSystem(extent={{-100,-100},{100,100}})));
  end ThermalMass;
  model Heater "Ideal averaged modulating heater, no hardware lag modeled"
    parameter Real enabled=1;
    parameter SI.Temperature setT=281.15;
    parameter SI.Power maxP=400;
    parameter Real gain(unit="W/K")=80;
    input SI.Temperature T;
    output SI.Power P;
    SI.Energy E(start=0,fixed=true);
  equation
    P=enabled*noEvent(clamp(gain*(setT-T),0,maxP)); der(E)=P;
    annotation(Icon(graphics={Rectangle(extent={{-80,55},{80,-55}},lineColor={170,90,20},fillColor={255,236,205},fillPattern=FillPattern.Solid),Text(extent={{-75,40},{75,-30}},textString="%name")}));
  end Heater;
  model ExternalSurface "Signed external exchange plus reciprocal hull IR port"
    parameter SI.Area A=1;
    parameter Real alpha=0.15,eps=0.85,Fearth=0.25,Fsky=0.55,Fhull=0.20;
    parameter Real nx=0,ny=0.8660254038,nz=0.5;
    parameter Real hRef(unit="W/(m2.K)")=1.2;
    parameter Real directExposure=1;
    parameter Boolean curvedPV=false;
    EnvironmentBus env annotation(Placement(transformation(extent={{-10,90},{10,110}})));
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a surface annotation(Placement(transformation(extent={{-110,-10},{-90,10}})));
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b hull annotation(Placement(transformation(extent={{90,-10},{110,10}})));
    output SI.Power Qext,Qdirect,Qreflected,Qconv,Qir,Qhull;
    Real projection,h(unit="W/(m2.K)");
  equation
    projection=if curvedPV then 0.5*max(0,env.sz)+0.25*max(0,0.7071067812*(env.sy+env.sz))+0.25*max(0,0.7071067812*(-env.sy+env.sz)) else max(0,nx*env.sx+ny*env.sy+nz*env.sz);
    h=hRef*sqrt(env.density/0.088909874)*sqrt(env.wind/8);
    Qdirect=alpha*A*env.DNI*projection*directExposure;
    Qreflected=alpha*A*Fearth*env.reflected;
    Qconv=h*A*(env.Tair-surface.T);
    Qir=eps*A*(Fearth*env.earthIR+Fsky*env.skyIR-(Fearth+Fsky)*sigma*surface.T^4);
    Qhull=eps*A*Fhull*sigma*(hull.T^4-surface.T^4);
    Qext=Qdirect+Qreflected+Qconv+Qir;
    surface.Q_flow=-(Qext+Qhull); hull.Q_flow=Qhull;
    annotation(Icon(graphics={Rectangle(extent={{-80,60},{80,-60}},lineColor={80,100,120},fillColor={235,241,246},fillPattern=FillPattern.Solid),Text(extent={{-75,45},{75,-15}},textString="%name"),Text(extent={{-75,-20},{75,-55}},textString="convection + radiation")}));
  end ExternalSurface;
  model MissionEnvironment "20 km illustrative equinox station keeping; local solar time"
    parameter Real coldOffset(unit="K")=0;
    parameter Real yawOffset(unit="deg")=0;
    EnvironmentSource bus annotation(Placement(transformation(extent={{90,-10},{110,10}})));
    Real hourAngle,latitude=35*pi/180,headingRad,rollRad,pitchRad;
    Real e,n,u,x0,y0,z0,x1,y1,z1;
  equation
    bus.hour=mod(time/3600,24);
    hourAngle=2*pi*(bus.hour-12)/24;
    e=-sin(hourAngle);n=-sin(latitude)*cos(hourAngle);u=cos(latitude)*cos(hourAngle);
    bus.heading=20+yawOffset+10*sin(2*pi*bus.hour/24);
    headingRad=bus.heading*pi/180;
    rollRad=3*pi/180*sin(4*pi*bus.hour/24);
    pitchRad=2*pi/180*sin(2*pi*(bus.hour-3)/24);
    x0=e*sin(headingRad)+n*cos(headingRad);y0=-e*cos(headingRad)+n*sin(headingRad);z0=u;
    x1=cos(pitchRad)*x0-sin(pitchRad)*z0;y1=y0;z1=sin(pitchRad)*x0+cos(pitchRad)*z0;
    bus.sx=x1;bus.sy=cos(rollRad)*y1+sin(rollRad)*z1;bus.sz=-sin(rollRad)*y1+cos(rollRad)*z1;
    bus.DNI=if u>0 then 1250 else 0;
    bus.day=noEvent(clamp(u/0.08));
    bus.reflected=0.2*1250*max(0,u);
    bus.Tair=216.65+coldOffset+4*cos(2*pi*(bus.hour-15)/24);
    bus.earthIR=240;bus.skyIR=80;
    bus.wind=8+2*sin(2*pi*(bus.hour-4)/24)+3*window(bus.hour,15,18);
    bus.density=5529.3054/(287.05287*bus.Tair);
    annotation(Icon(graphics={Rectangle(extent={{-80,60},{80,-60}},lineColor={50,100,140},fillColor={225,242,255},fillPattern=FillPattern.Solid),Text(extent={{-75,45},{75,-30}},textString="Environment")}),Documentation(info="<html>Assumed 35 degree latitude equinox, 20 km geometric altitude, direct-normal solar 1250 W/m2 when Sun is above horizon, 0.2 ground albedo, prescribed wind and yaw/roll/pitch. No geographic trajectory, flight controller or weather forecast is solved.</html>"));
  end MissionEnvironment;
  model Avionics
    parameter Real heaterEnabled=1,strapScale=1,shadeFactor=0.05;
    EnvironmentBus env annotation(Placement(transformation(extent={{-10,90},{10,110}})));
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a mount,hull;
    Modelica.Blocks.Interfaces.RealInput Qdc,Qmppt;
    Modelica.Blocks.Interfaces.RealOutput Pelec,Pheat;
    Real Pcpu,Pnav,Pcom;
    ThermalMass cpu(C=1800,Q=Pcpu) annotation(Placement(transformation(extent={{-285,118},{-195,162}}))),
      nav(C=600,Q=Pnav) annotation(Placement(transformation(extent={{-125,118},{-35,162}}))),
      telemetry(C=1800,Q=Pcom) annotation(Placement(transformation(extent={{35,118},{125,162}})));
    ThermalMass converter(C=5000,Q=Qdc) annotation(Placement(transformation(extent={{195,118},{285,162}}))),
      mppt(C=5000,Q=Qmppt) annotation(Placement(transformation(extent={{-285,38},{-195,82}})));
    ThermalMass tray(C=18000,Q=heater.P) annotation(Placement(transformation(extent={{-125,38},{-35,82}}))),
      radiator(C=6000,T0=273.15) annotation(Placement(transformation(extent={{35,38},{125,82}})));
    Heater heater(enabled=heaterEnabled,T=tray.T,setT=276.15,maxP=100,gain=40) annotation(Placement(transformation(extent={{195,38},{285,82}})));
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor cpuContact(G=8) annotation(Placement(transformation(extent={{-125,-42},{-35,2}}))),
      navContact(G=3) annotation(Placement(transformation(extent={{35,-42},{125,2}}))),
      comContact(G=6) annotation(Placement(transformation(extent={{195,-42},{285,2}}))),
      dcContact(G=20) annotation(Placement(transformation(extent={{-285,-122},{-195,-78}}))),
      mpptContact(G=25) annotation(Placement(transformation(extent={{-125,-122},{-35,-78}}))),
      strap(G=25*strapScale) annotation(Placement(transformation(extent={{35,-122},{125,-78}}))),
      mountPath(G=0.7) annotation(Placement(transformation(extent={{195,-122},{285,-78}})));
    ExternalSurface boundary(A=3.12,ny=-0.8660254038,directExposure=shadeFactor) annotation(Placement(transformation(extent={{-285,-42},{-195,2}})));
    output SI.Energy U;output SI.Power Qext,Qgenerated;
  equation
    Pcpu=65+20*env.day;Pnav=12;Pcom=35+15*env.day;Pelec=Pcpu+Pnav+Pcom;Pheat=heater.P;
    connect(cpu.port,cpuContact.port_a) annotation(Line(points={{-240,140},{-80,-20}},color={165,85,25}));connect(cpuContact.port_b,tray.port) annotation(Line(points={{-80,-20},{-80,60}},color={165,85,25}));
    connect(nav.port,navContact.port_a) annotation(Line(points={{-80,140},{80,-20}},color={165,85,25}));connect(navContact.port_b,tray.port) annotation(Line(points={{80,-20},{-80,60}},color={165,85,25}));
    connect(telemetry.port,comContact.port_a) annotation(Line(points={{80,140},{240,-20}},color={165,85,25}));connect(comContact.port_b,tray.port) annotation(Line(points={{240,-20},{-80,60}},color={165,85,25}));
    connect(converter.port,dcContact.port_a) annotation(Line(points={{240,140},{-240,-100}},color={165,85,25}));connect(dcContact.port_b,tray.port) annotation(Line(points={{-240,-100},{-80,60}},color={165,85,25}));
    connect(mppt.port,mpptContact.port_a) annotation(Line(points={{-240,60},{-80,-100}},color={165,85,25}));connect(mpptContact.port_b,tray.port) annotation(Line(points={{-80,-100},{-80,60}},color={165,85,25}));
    connect(tray.port,strap.port_a) annotation(Line(points={{-80,60},{80,-100}},color={165,85,25}));connect(strap.port_b,radiator.port) annotation(Line(points={{80,-100},{80,60}},color={165,85,25}));
    connect(tray.port,mountPath.port_a) annotation(Line(points={{-80,60},{240,-100}},color={165,85,25}));connect(mountPath.port_b,mount) annotation(Line(points={{240,-100},{290,0}},color={165,85,25}));
    connect(boundary.surface,radiator.port) annotation(Line(points={{-240,-20},{80,60}},color={165,85,25}));connect(boundary.env,env) annotation(Line(points={{-240,-20},{290,0}},color={0,105,135}));connect(boundary.hull,hull) annotation(Line(points={{-240,-20},{290,0}},color={165,85,25}));
    U=cpu.U+nav.U+telemetry.U+converter.U+mppt.U+tray.U+radiator.U;
    Qext=boundary.Qext;Qgenerated=Pelec+Qdc+Qmppt+Pheat;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="Avionics")}));
    // STAGE02_NATIVE_DIAGRAM
  end Avionics;
  model Battery
    parameter Real heaterEnabled=1;
    parameter SI.Energy capacity=60*3.6e6;
    EnvironmentBus env;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a mount,hull;
    Modelica.Blocks.Interfaces.RealInput Pcharge,Pdischarge;
    Modelica.Blocks.Interfaces.RealOutput SOC(start=0.7,fixed=true),Pheat,chargePermission;
    Real etaCharge,etaDischarge;SI.Power Qloss;
    ThermalMass core(C=200000,T0=288.15,Q=Qloss) annotation(Placement(transformation(extent={{-285,118},{-195,162}}))),
      caseNode(C=30000,T0=288.15,Q=heater.P) annotation(Placement(transformation(extent={{-125,118},{-35,162}}))),
      blanket(C=6000,T0=250) annotation(Placement(transformation(extent={{35,118},{125,162}})));
    Heater heater(enabled=heaterEnabled,T=caseNode.T,setT=281.15,maxP=400,gain=80) annotation(Placement(transformation(extent={{195,118},{285,162}})));
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor coreContact(G=8) annotation(Placement(transformation(extent={{-125,38},{-35,82}}))),
      insulation(G=2) annotation(Placement(transformation(extent={{35,38},{125,82}}))),
      mountPath(G=0.2) annotation(Placement(transformation(extent={{195,38},{285,82}})));
    ExternalSurface boundary(A=5,alpha=0.2,eps=0.65,Fearth=0.5,Fsky=0.15,Fhull=0.35,ny=0,nz=-1,hRef=0.8,directExposure=0.1) annotation(Placement(transformation(extent={{-285,38},{-195,82}})));
    output SI.Energy U,chemicalDelta;output SI.Power Qext,Qgenerated;
  equation
    etaCharge=0.97-0.03*noEvent(clamp((288.15-core.T)/30));
    etaDischarge=0.97-0.04*noEvent(clamp((288.15-core.T)/30));
    chargePermission=noEvent(clamp((core.T-273.15)/5));
    der(SOC)=(etaCharge*Pcharge-Pdischarge/etaDischarge)/capacity;
    Qloss=(1-etaCharge)*Pcharge+(1/etaDischarge-1)*Pdischarge;
    connect(core.port,coreContact.port_a) annotation(Line(points={{-240,140},{-80,60}},color={165,85,25}));connect(coreContact.port_b,caseNode.port) annotation(Line(points={{-80,60},{-80,140}},color={165,85,25}));
    connect(caseNode.port,insulation.port_a) annotation(Line(points={{-80,140},{80,60}},color={165,85,25}));connect(insulation.port_b,blanket.port) annotation(Line(points={{80,60},{80,140}},color={165,85,25}));
    connect(caseNode.port,mountPath.port_a) annotation(Line(points={{-80,140},{240,60}},color={165,85,25}));connect(mountPath.port_b,mount) annotation(Line(points={{240,60},{290,0}},color={165,85,25}));
    connect(blanket.port,boundary.surface) annotation(Line(points={{80,140},{-240,60}},color={165,85,25}));connect(boundary.env,env) annotation(Line(points={{-240,60},{290,0}},color={0,105,135}));connect(boundary.hull,hull) annotation(Line(points={{-240,60},{290,0}},color={165,85,25}));
    Pheat=heater.P;U=core.U+caseNode.U+blanket.U;chemicalDelta=capacity*(SOC-0.7);
    Qext=boundary.Qext;Qgenerated=Qloss+Pheat;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="Battery")}));
    // STAGE02_NATIVE_DIAGRAM
  end Battery;
  model Payload
    parameter Real loadScale=1,heaterEnabled=1,strapScale=1,shadeFactor=0.05;
    EnvironmentBus env;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a mount,hull;
    Modelica.Blocks.Interfaces.RealOutput Pelec,Prf,Pheat;
    ThermalMass rf(C=4500,Q=Pelec-Prf) annotation(Placement(transformation(extent={{-285,118},{-195,162}}))),
      plate(C=16000,Q=heater.P) annotation(Placement(transformation(extent={{-125,118},{-35,162}}))),
      radiator(C=8000,T0=273.15) annotation(Placement(transformation(extent={{35,118},{125,162}})));
    Heater heater(enabled=heaterEnabled,T=plate.T,setT=273.15,maxP=120,gain=40) annotation(Placement(transformation(extent={{195,118},{285,162}})));
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor rfContact(G=12) annotation(Placement(transformation(extent={{-125,38},{-35,82}}))),
      strap(G=15*strapScale) annotation(Placement(transformation(extent={{35,38},{125,82}}))),
      mountPath(G=0.7) annotation(Placement(transformation(extent={{195,38},{285,82}})));
    ExternalSurface boundary(A=3.12,ny=0.8660254038,directExposure=shadeFactor) annotation(Placement(transformation(extent={{-285,38},{-195,82}})));
    output SI.Energy U;output SI.Power Qext,Qgenerated;
  equation
    Pelec=loadScale*(350+150*env.day+300*window(env.hour,11,14));Prf=0.35*Pelec;Pheat=heater.P;
    connect(rf.port,rfContact.port_a) annotation(Line(points={{-240,140},{-80,60}},color={165,85,25}));connect(rfContact.port_b,plate.port) annotation(Line(points={{-80,60},{-80,140}},color={165,85,25}));
    connect(plate.port,strap.port_a) annotation(Line(points={{-80,140},{80,60}},color={165,85,25}));connect(strap.port_b,radiator.port) annotation(Line(points={{80,60},{80,140}},color={165,85,25}));
    connect(plate.port,mountPath.port_a) annotation(Line(points={{-80,140},{240,60}},color={165,85,25}));connect(mountPath.port_b,mount) annotation(Line(points={{240,60},{290,0}},color={165,85,25}));
    connect(radiator.port,boundary.surface) annotation(Line(points={{80,140},{-240,60}},color={165,85,25}));connect(env,boundary.env) annotation(Line(points={{-290,0},{-240,60}},color={0,105,135}));connect(hull,boundary.hull) annotation(Line(points={{-290,0},{-240,60}},color={165,85,25}));
    U=rf.U+plate.U+radiator.U;Qext=boundary.Qext;Qgenerated=Pelec-Prf+Pheat;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="Payload")}));
    // STAGE02_NATIVE_DIAGRAM
  end Payload;
  model Propulsion
    parameter Real heaterEnabled=1;
    EnvironmentBus env;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a mount,hull;
    Modelica.Blocks.Interfaces.RealOutput Pelec,Pshaft,Pheat;
    Real Pmotor,Qmotor,Qcontroller;
    ThermalMass winding(C=10000,Q=0.85*Qmotor) annotation(Placement(transformation(extent={{-285,118},{-195,162}}))),
      housing(C=35000,Q=0.15*Qmotor+heater.P) annotation(Placement(transformation(extent={{-125,118},{-35,162}}))),
      controller(C=6000,Q=Qcontroller) annotation(Placement(transformation(extent={{35,118},{125,162}}))),
      bracket(C=8000) annotation(Placement(transformation(extent={{195,118},{285,162}})));
    Heater heater(enabled=heaterEnabled,T=housing.T,setT=268.15,maxP=100,gain=30) annotation(Placement(transformation(extent={{-285,38},{-195,82}})));
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor motorContact(G=20) annotation(Placement(transformation(extent={{195,38},{285,82}}))),
      escContact(G=2) annotation(Placement(transformation(extent={{-285,-42},{-195,2}}))),
      bracketContact(G=3) annotation(Placement(transformation(extent={{-125,-42},{-35,2}}))),
      mountPath(G=0.15) annotation(Placement(transformation(extent={{35,-42},{125,2}})));
    ExternalSurface motorSurface(A=0.9,alpha=0.3,eps=0.8,Fearth=0.35,Fsky=0.5,Fhull=0.15,nx=-1,ny=0,nz=0,hRef=3) annotation(Placement(transformation(extent={{-125,38},{-35,82}})));
    ExternalSurface controllerSurface(A=0.35,alpha=0.2,eps=0.85,Fearth=0.4,Fsky=0.4,Fhull=0.2,nx=-1,ny=0,nz=0,hRef=2) annotation(Placement(transformation(extent={{35,38},{125,82}})));
    output SI.Energy U;output SI.Power Qext,Qgenerated;
  equation
    Pshaft=1200*(env.wind/8)^3;Pmotor=Pshaft/0.9;Pelec=Pmotor/0.96;
    Qmotor=Pmotor-Pshaft;Qcontroller=Pelec-Pmotor;Pheat=heater.P;
    connect(winding.port,motorContact.port_a) annotation(Line(points={{-240,140},{240,60}},color={165,85,25}));connect(motorContact.port_b,housing.port) annotation(Line(points={{240,60},{-80,140}},color={165,85,25}));
    connect(controller.port,escContact.port_a) annotation(Line(points={{80,140},{-240,-20}},color={165,85,25}));connect(escContact.port_b,housing.port) annotation(Line(points={{-240,-20},{-80,140}},color={165,85,25}));
    connect(housing.port,bracketContact.port_a) annotation(Line(points={{-80,140},{-80,-20}},color={165,85,25}));connect(bracketContact.port_b,bracket.port) annotation(Line(points={{-80,-20},{240,140}},color={165,85,25}));
    connect(bracket.port,mountPath.port_a) annotation(Line(points={{240,140},{80,-20}},color={165,85,25}));connect(mountPath.port_b,mount) annotation(Line(points={{80,-20},{290,0}},color={165,85,25}));
    connect(housing.port,motorSurface.surface) annotation(Line(points={{-80,140},{-80,60}},color={165,85,25}));connect(controller.port,controllerSurface.surface) annotation(Line(points={{80,140},{80,60}},color={165,85,25}));
    connect(env,motorSurface.env) annotation(Line(points={{-290,0},{-80,60}},color={0,105,135}));connect(env,controllerSurface.env) annotation(Line(points={{-290,0},{80,60}},color={0,105,135}));connect(hull,motorSurface.hull) annotation(Line(points={{-290,0},{-80,60}},color={165,85,25}));connect(hull,controllerSurface.hull) annotation(Line(points={{-290,0},{80,60}},color={165,85,25}));
    U=winding.U+housing.U+controller.U+bracket.U;Qext=motorSurface.Qext+controllerSurface.Qext;Qgenerated=Qmotor+Qcontroller+Pheat;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="Propulsion")}));
    // STAGE02_NATIVE_DIAGRAM
  end Propulsion;
  model HullSolar
    parameter Real area=2019.60011724,solarArea=100;
    parameter SI.HeatCapacity gasC=205970.67737047;
    EnvironmentBus env;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a underside;
    Modelica.Blocks.Interfaces.RealInput Ppanel;
    Modelica.Blocks.Interfaces.RealOutput Pavailable;
    ThermalMass upper(C=(area/4-solarArea)*180,T0=250) annotation(Placement(transformation(extent={{-285,118},{-195,162}}))),
      left(C=area/4*180,T0=250) annotation(Placement(transformation(extent={{-125,118},{-35,162}}))),
      right(C=area/4*180,T0=250) annotation(Placement(transformation(extent={{35,118},{125,162}}))),
      lower(C=area/4*180,T0=250) annotation(Placement(transformation(extent={{195,118},{285,162}}))),
      solar(C=solarArea*2000,T0=250,Q=-Ppanel) annotation(Placement(transformation(extent={{-285,38},{-195,82}}))),
      gas(C=gasC,T0=236.65) annotation(Placement(transformation(extent={{-125,38},{-35,82}})));
    ExternalSurface upperSurface(A=area/4-solarArea,alpha=0.16,eps=0.08,Fearth=0,Fsky=1,Fhull=0,ny=0,nz=1,hRef=2) annotation(Placement(transformation(extent={{35,38},{125,82}})));
    ExternalSurface leftSurface(A=area/4,alpha=0.16,eps=0.08,Fearth=0.5,Fsky=0.5,Fhull=0,ny=1,nz=0,hRef=2) annotation(Placement(transformation(extent={{195,38},{285,82}})));
    ExternalSurface rightSurface(A=area/4,alpha=0.16,eps=0.08,Fearth=0.5,Fsky=0.5,Fhull=0,ny=-1,nz=0,hRef=2) annotation(Placement(transformation(extent={{-285,-42},{-195,2}})));
    ExternalSurface lowerSurface(A=area/4-3.903,alpha=0.16,eps=0.08,Fearth=1,Fsky=0,Fhull=0,ny=0,nz=-1,hRef=2) annotation(Placement(transformation(extent={{-125,-42},{-35,2}})));
    ExternalSurface solarSurface(A=solarArea,alpha=0.90,eps=0.85,Fearth=0.0732233,Fsky=0.9267767,Fhull=0,curvedPV=true,hRef=2) annotation(Placement(transformation(extent={{35,-42},{125,2}})));
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor upperGas(G=0.25*(area/4-solarArea)) annotation(Placement(transformation(extent={{195,-42},{285,2}}))),
      leftGas(G=0.25*area/4) annotation(Placement(transformation(extent={{-285,-122},{-195,-78}}))),
      rightGas(G=0.25*area/4) annotation(Placement(transformation(extent={{-125,-122},{-35,-78}}))),
      lowerGas(G=0.25*area/4) annotation(Placement(transformation(extent={{35,-122},{125,-78}}))),
      solarGas(G=0.25*solarArea) annotation(Placement(transformation(extent={{195,-122},{285,-78}})));
    Real etaCell;
    output SI.Energy U;output SI.Power Qext;
  equation
    etaCell=noEvent(clamp(0.24*(1-0.0035*(solar.T-298.15)),0.15,0.28));
    Pavailable=solarArea*etaCell*solarSurface.projection*env.DNI*0.97;
    connect(upper.port,upperSurface.surface) annotation(Line(points={{-240,140},{80,60}},color={165,85,25}));connect(left.port,leftSurface.surface) annotation(Line(points={{-80,140},{240,60}},color={165,85,25}));connect(right.port,rightSurface.surface) annotation(Line(points={{80,140},{-240,-20}},color={165,85,25}));connect(lower.port,lowerSurface.surface) annotation(Line(points={{240,140},{-80,-20}},color={165,85,25}));connect(solar.port,solarSurface.surface) annotation(Line(points={{-240,60},{80,-20}},color={165,85,25}));
    connect(upper.port,upperGas.port_a) annotation(Line(points={{-240,140},{240,-20}},color={165,85,25}));connect(upperGas.port_b,gas.port) annotation(Line(points={{240,-20},{-80,60}},color={165,85,25}));
    connect(left.port,leftGas.port_a) annotation(Line(points={{-80,140},{-240,-100}},color={165,85,25}));connect(leftGas.port_b,gas.port) annotation(Line(points={{-240,-100},{-80,60}},color={165,85,25}));
    connect(right.port,rightGas.port_a) annotation(Line(points={{80,140},{-80,-100}},color={165,85,25}));connect(rightGas.port_b,gas.port) annotation(Line(points={{-80,-100},{-80,60}},color={165,85,25}));
    connect(lower.port,lowerGas.port_a) annotation(Line(points={{240,140},{80,-100}},color={165,85,25}));connect(lowerGas.port_b,gas.port) annotation(Line(points={{80,-100},{-80,60}},color={165,85,25}));
    connect(solar.port,solarGas.port_a) annotation(Line(points={{-240,60},{240,-100}},color={165,85,25}));connect(solarGas.port_b,gas.port) annotation(Line(points={{240,-100},{-80,60}},color={165,85,25}));
    connect(env,upperSurface.env) annotation(Line(points={{-290,0},{80,60}},color={0,105,135}));connect(env,leftSurface.env) annotation(Line(points={{-290,0},{240,60}},color={0,105,135}));connect(env,rightSurface.env) annotation(Line(points={{-290,0},{-240,-20}},color={0,105,135}));connect(env,lowerSurface.env) annotation(Line(points={{-290,0},{-80,-20}},color={0,105,135}));connect(env,solarSurface.env) annotation(Line(points={{-290,0},{80,-20}},color={0,105,135}));
    connect(lower.port,underside) annotation(Line(points={{240,140},{290,0}},color={165,85,25}));
    // Unused zero-view hull ports still need a defined temperature.
    connect(lower.port,upperSurface.hull) annotation(Line(points={{240,140},{80,60}},color={165,85,25}));connect(lower.port,leftSurface.hull) annotation(Line(points={{240,140},{240,60}},color={165,85,25}));connect(lower.port,rightSurface.hull) annotation(Line(points={{240,140},{-240,-20}},color={165,85,25}));connect(lower.port,lowerSurface.hull) annotation(Line(points={{240,140},{-80,-20}},color={165,85,25}));connect(lower.port,solarSurface.hull) annotation(Line(points={{240,140},{80,-20}},color={165,85,25}));
    U=upper.U+left.U+right.U+lower.U+solar.U+gas.U;
    Qext=upperSurface.Qext+leftSurface.Qext+rightSurface.Qext+lowerSurface.Qext+solarSurface.Qext;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="HullSolar")}));
    // STAGE02_NATIVE_DIAGRAM
  end HullSolar;
  model Structure
    EnvironmentBus env;
    Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a mount,hull;
    ThermalMass tray(C=30000,T0=273.15) annotation(Placement(transformation(extent={{-285,118},{-195,162}})));
    ExternalSurface boundary(A=2,alpha=0.25,eps=0.5,Fearth=0.5,Fsky=0.15,Fhull=0.35,ny=0,nz=-1,hRef=1) annotation(Placement(transformation(extent={{-125,118},{-35,162}})));
    Modelica.Thermal.HeatTransfer.Components.ThermalConductor hullPath(G=0.1) annotation(Placement(transformation(extent={{35,118},{125,162}})));
    output SI.Energy U;output SI.Power Qext;
  equation
    connect(mount,tray.port) annotation(Line(points={{-290,0},{-240,140}},color={165,85,25}));connect(tray.port,boundary.surface) annotation(Line(points={{-240,140},{-80,140}},color={165,85,25}));connect(env,boundary.env) annotation(Line(points={{-290,0},{-80,140}},color={0,105,135}));connect(hull,boundary.hull) annotation(Line(points={{-290,0},{-80,140}},color={165,85,25}));
    connect(tray.port,hullPath.port_a) annotation(Line(points={{-240,140},{80,140}},color={165,85,25}));connect(hullPath.port_b,hull) annotation(Line(points={{80,140},{290,0}},color={165,85,25}));
    U=tray.U;Qext=boundary.Qext;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="Structure")}));
    // STAGE02_NATIVE_DIAGRAM
  end Structure;
  model PowerManager "Conservative DC dispatch with finite charge power and temperature permission"
    Modelica.Blocks.Interfaces.RealInput Pavailable,Pav,Ppay,Pmotor,Pheat,SOC,chargePermission;
    Modelica.Blocks.Interfaces.RealOutput Pload,Pcharge,Pdischarge,Ppanel,Qdc,Qmppt;
    output SI.Power Ppv,Pcurtailed,balance;
  equation
    Pload=(Pav+Ppay+Pmotor+Pheat)/0.96;
    Pcharge=noEvent(min(12000,max(0,Pavailable-Pload))*clamp((0.92-SOC)/0.03)*chargePermission);
    Pdischarge=noEvent(max(0,Pload-Pavailable));
    Ppv=noEvent(min(Pavailable,Pload+Pcharge));Ppanel=Ppv/0.97;
    Pcurtailed=Pavailable-Ppv;Qdc=Pload-(Pav+Ppay+Pmotor+Pheat);Qmppt=Ppanel-Ppv;
    balance=Ppv+Pdischarge-Pload-Pcharge;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="PowerManager")}));
    // STAGE02_NATIVE_DIAGRAM
  end PowerManager;
  model IntegratedMission "Hierarchical 24-hour thermal-energy mission, repeated to assess settling"
    parameter Real coldOffset=0,yawOffset=0,payloadScale=1,heaterEnabled=1,strapScale=1,shadeFactor=0.05;
    MissionEnvironment environment(coldOffset=coldOffset,yawOffset=yawOffset) annotation(Placement(transformation(extent={{-285,128},{-195,172}})));
    HullSolar hull annotation(Placement(transformation(extent={{-125,128},{-35,172}})));
    Avionics avionics(heaterEnabled=heaterEnabled,strapScale=strapScale,shadeFactor=shadeFactor) annotation(Placement(transformation(extent={{-285,-32},{-195,12}})));
    Battery battery(heaterEnabled=heaterEnabled) annotation(Placement(transformation(extent={{-125,-32},{-35,12}})));
    Payload payload(loadScale=payloadScale,heaterEnabled=heaterEnabled,strapScale=strapScale,shadeFactor=shadeFactor) annotation(Placement(transformation(extent={{35,-32},{125,12}})));
    Propulsion propulsion(heaterEnabled=heaterEnabled) annotation(Placement(transformation(extent={{195,-32},{285,12}})));
    Structure structure annotation(Placement(transformation(extent={{-45,-182},{45,-138}})));
    PowerManager power annotation(Placement(transformation(extent={{95,128},{185,172}})));
    output SI.Power heaterPower,Qexternal,Qgenerated;
    output SI.Energy thermalStorage,chemicalStorage;
    SI.Energy externalEnergy(start=0,fixed=true),shaftEnergy(start=0,fixed=true),rfEnergy(start=0,fixed=true),thermalNetEnergy(start=0,fixed=true),heaterEnergy(start=0,fixed=true),loadEnergy(start=0,fixed=true),solarEnergy(start=0,fixed=true),chargeEnergy(start=0,fixed=true),dischargeEnergy(start=0,fixed=true);
    output Real systemResidualJ,thermalResidualJ;
    output Real TavC,TbatC,TpayC,TmotorC;
  equation
    connect(environment.bus,hull.env) annotation(Line(points={{-240,150},{-80,150}},color={0,105,135}));connect(environment.bus,avionics.env) annotation(Line(points={{-240,150},{-240,-10}},color={0,105,135}));connect(environment.bus,battery.env) annotation(Line(points={{-240,150},{-80,-10}},color={0,105,135}));connect(environment.bus,payload.env) annotation(Line(points={{-240,150},{80,-10}},color={0,105,135}));connect(environment.bus,propulsion.env) annotation(Line(points={{-240,150},{240,-10}},color={0,105,135}));connect(environment.bus,structure.env) annotation(Line(points={{-240,150},{0,-160}},color={0,105,135}));
    connect(avionics.mount,structure.mount) annotation(Line(points={{-240,-10},{0,-160}},color={40,80,150}));connect(battery.mount,structure.mount) annotation(Line(points={{-80,-10},{0,-160}},color={40,80,150}));connect(payload.mount,structure.mount) annotation(Line(points={{80,-10},{0,-160}},color={40,80,150}));connect(propulsion.mount,structure.mount) annotation(Line(points={{240,-10},{0,-160}},color={40,80,150}));
    connect(avionics.hull,hull.underside) annotation(Line(points={{-240,-10},{-80,150}},color={40,80,150}));connect(battery.hull,hull.underside) annotation(Line(points={{-80,-10},{-80,150}},color={40,80,150}));connect(payload.hull,hull.underside) annotation(Line(points={{80,-10},{-80,150}},color={40,80,150}));connect(propulsion.hull,hull.underside) annotation(Line(points={{240,-10},{-80,150}},color={40,80,150}));connect(structure.hull,hull.underside) annotation(Line(points={{0,-160},{-80,150}},color={40,80,150}));
    connect(hull.Pavailable,power.Pavailable) annotation(Line(points={{-80,150},{140,150}},color={40,80,150}));connect(avionics.Pelec,power.Pav) annotation(Line(points={{-240,-10},{140,150}},color={40,80,150}));connect(payload.Pelec,power.Ppay) annotation(Line(points={{80,-10},{140,150}},color={40,80,150}));connect(propulsion.Pelec,power.Pmotor) annotation(Line(points={{240,-10},{140,150}},color={40,80,150}));connect(battery.SOC,power.SOC) annotation(Line(points={{-80,-10},{140,150}},color={40,80,150}));connect(battery.chargePermission,power.chargePermission) annotation(Line(points={{-80,-10},{140,150}},color={40,80,150}));
    connect(power.Ppanel,hull.Ppanel) annotation(Line(points={{140,150},{-80,150}},color={40,80,150}));connect(power.Pcharge,battery.Pcharge) annotation(Line(points={{140,150},{-80,-10}},color={40,80,150}));connect(power.Pdischarge,battery.Pdischarge) annotation(Line(points={{140,150},{-80,-10}},color={40,80,150}));connect(power.Qdc,avionics.Qdc) annotation(Line(points={{140,150},{-240,-10}},color={40,80,150}));connect(power.Qmppt,avionics.Qmppt) annotation(Line(points={{140,150},{-240,-10}},color={40,80,150}));
    heaterPower=avionics.Pheat+battery.Pheat+payload.Pheat+propulsion.Pheat;power.Pheat=heaterPower;
    Qexternal=hull.Qext+avionics.Qext+battery.Qext+payload.Qext+propulsion.Qext+structure.Qext;
    Qgenerated=avionics.Qgenerated+battery.Qgenerated+payload.Qgenerated+propulsion.Qgenerated;
    thermalStorage=hull.U+avionics.U+battery.U+payload.U+propulsion.U+structure.U;chemicalStorage=battery.chemicalDelta;
    der(externalEnergy)=Qexternal;der(shaftEnergy)=propulsion.Pshaft;der(rfEnergy)=payload.Prf;
    der(thermalNetEnergy)=Qexternal+Qgenerated-power.Ppanel;
    der(heaterEnergy)=heaterPower;der(loadEnergy)=power.Pload;der(solarEnergy)=power.Ppv;der(chargeEnergy)=power.Pcharge;der(dischargeEnergy)=power.Pdischarge;
    systemResidualJ=externalEnergy-shaftEnergy-rfEnergy-thermalStorage-chemicalStorage;
    thermalResidualJ=thermalNetEnergy-thermalStorage;
    TavC=avionics.cpu.T-273.15;TbatC=battery.core.T-273.15;TpayC=payload.rf.T-273.15;TmotorC=propulsion.winding.T-273.15;
    annotation(Diagram(coordinateSystem(extent={{-320,-260},{320,220}})),Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="IntegratedMission")}),experiment(StartTime=0,StopTime=691200,Interval=60,Tolerance=1e-7),uses(Modelica(version="4.1.0")),Documentation(info="<html>Independent thermal-energy demonstration. All hardware parameters, loss maps and operating profiles are assumptions. A 24-hour station-keeping cycle is repeated eight times; report the final cycle only after checking repeatability. No flight dynamics, pressure control, spatial CHT, OEM limits or physical validation. See downloaded design basis and audits.</html>"));
    // STAGE02_NATIVE_DIAGRAM
  end IntegratedMission;
  annotation(uses(Modelica(version="4.1.0")),Documentation(info="<html>Khani Solutions independent public-reference study. Open IntegratedMission in OMEdit, then open individual subsystem classes. Native connection diagrams and all assumptions are included.</html>"));
end HAPSDiurnal;
