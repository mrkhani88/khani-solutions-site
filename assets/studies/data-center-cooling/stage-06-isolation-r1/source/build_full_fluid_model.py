"""Add a reversible faulted rack and two isolation boundaries to the native model."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parents[1];D=json.loads((B/'model/design.json').read_text())
s=(B/'inputs/parent-model.mo').read_text().replace('DataCenterValveComparison','DataCenterIsolation')
s=s[:s.index('  model ManualNetwork')]+'''  model ReferenceNetwork
    extends Baseline(pressureIndependent=false,leakEnabled=false,holeDiameterMM=0);
  end ReferenceNetwork;
  model OpenNetwork
    extends Baseline(pressureIndependent=false,leakEnabled=true,supplyClosed=false,returnClosed=false);
  end OpenNetwork;
  model SupplyClosedNetwork
    extends Baseline(pressureIndependent=false,leakEnabled=true,supplyClosed=true,returnClosed=false);
  end SupplyClosedNetwork;
  model ReturnClosedNetwork
    extends Baseline(pressureIndependent=false,leakEnabled=true,supplyClosed=false,returnClosed=true);
  end ReturnClosedNetwork;
  model DualClosedNetwork
    extends Baseline(pressureIndependent=false,leakEnabled=true,supplyClosed=true,returnClosed=true);
  end DualClosedNetwork;
end DataCenterIsolation;
'''
seg=s[s.index('  model Segment '):s.index('  model Elevation ')]
seg=seg.replace('model Segment ','model ReversibleSegment ').replace('end Segment;','end ReversibleSegment;').replace('allowFlowReversal=false','allowFlowReversal=true')
elev=s[s.index('  model Elevation '):s.index('  model BalancingElement ')]
elev=elev.replace('model Elevation ','model ReversibleElevation ').replace('end Elevation;','end ReversibleElevation;').replace('allowFlowReversal=false','allowFlowReversal=true')
new=seg+elev+'''  model IsolationElement "Opening is relative hydraulic conductance, not valve stroke"
    extends Modelica.Fluid.Interfaces.PartialTwoPortTransport(
      redeclare package Medium=Water40,allowFlowReversal=true,
      m_flow_start=mRackNom,m_flow_small=1e-8);
    parameter Boolean closed=false annotation(Evaluate=true);
    parameter Real opening(min=0,max=1)=1;
    parameter SI.Diameter diameter=0.04;
    parameter SI.PressureDifference nominalDP=0.5*rho/2*(mRackNom/rho/(Modelica.Constants.pi*diameter^2/4))^2;
  equation
    if closed then
      m_flow=0;
    else
      m_flow=opening*mRackNom*Modelica.Fluid.Utilities.regRoot(dp/nominalDP,1e-8);
    end if;
    port_b.h_outflow=inStream(port_a.h_outflow);
    port_a.h_outflow=inStream(port_b.h_outflow);
  end IsolationElement;

  model LeakOpening "Equivalent water orifice to atmospheric receiver; accepted flows outward"
    extends Modelica.Fluid.Interfaces.PartialTwoPortTransport(
      redeclare package Medium=Water40,allowFlowReversal=true,
      m_flow_start=0,m_flow_small=1e-9);
    parameter Boolean enabled=true annotation(Evaluate=true);
    parameter SI.Diameter diameter=0.003;
    parameter Real Cd=0.62;
    parameter SI.PressureDifference pressureScale=100000;
  equation
    if enabled then
      m_flow=Cd*Modelica.Constants.pi*diameter^2/4*sqrt(2*rho*pressureScale)*Modelica.Fluid.Utilities.regRoot(dp/pressureScale,1e-8);
    else
      m_flow=0;
    end if;
    port_b.h_outflow=inStream(port_a.h_outflow);
    port_a.h_outflow=inStream(port_b.h_outflow);
  end LeakOpening;

  model FaultRackBranch "Leak inside two isolation valves; permits return backfeed"
    parameter Boolean pressureIndependent=false "Not used: faulted branch is manual";
    parameter SI.PressureDifference valveNominalPa=15000;
    parameter SI.PressureDifference equipmentNominalPa=100000;
    parameter SI.Length supplyLength=1.698496;
    parameter SI.Length returnLength=3.048496;
    parameter SI.Diameter diameter=.04;
    parameter SI.Height headerHeight=2.7;
    parameter Boolean flatGeometry=false;
    parameter Real supplyOpening(min=0,max=1)=1;
    parameter Real returnOpening(min=0,max=1)=1;
    parameter Boolean supplyClosed=false annotation(Evaluate=true);
    parameter Boolean returnClosed=false annotation(Evaluate=true);
    parameter Boolean leakEnabled=true annotation(Evaluate=true);
    parameter SI.Diameter holeDiameter=0.003;
    Modelica.Fluid.Interfaces.FluidPort_a supply(redeclare package Medium=Water40);
    Modelica.Fluid.Interfaces.FluidPort_b ret(redeclare package Medium=Water40);
    IsolationElement supplyIsolation(closed=supplyClosed,opening=supplyOpening,diameter=diameter);
    IsolationElement returnIsolation(closed=returnClosed,opening=returnOpening,diameter=diameter);
    ReversibleSegment supplyPipe(length=supplyLength,diameter=diameter,K=3.5,
      dz=if flatGeometry then 0 else 1.55-headerHeight,mStart=mRackNom);
    ReversibleElevation internalElevation(dz=if flatGeometry then 0 else -0.9);
    Modelica.Fluid.Fittings.SimpleGenericOrifice rackMap(
      redeclare package Medium=Water40,diameter=diameter,
      use_zeta=false,zeta=1,dp_nominal=equipmentNominalPa,m_flow_nominal=mRackNom,
      m_flow_start=mRackNom,m_flow_small=1e-6,use_Re=false,from_dp=false,
      allowFlowReversal=true);
    Modelica.Fluid.Fittings.SimpleGenericOrifice balancingValve(
      redeclare package Medium=Water40,diameter=diameter,
      use_zeta=false,zeta=1,dp_nominal=valveNominalPa,m_flow_nominal=mRackNom,
      m_flow_start=mRackNom,m_flow_small=1e-6,use_Re=false,from_dp=false,
      allowFlowReversal=true);
    ReversibleSegment returnPipe(length=returnLength,diameter=diameter,K=3.5,
      dz=if flatGeometry then 0 else headerHeight-.65,mStart=mRackNom);
    LeakOpening leak(enabled=leakEnabled,diameter=holeDiameter);
    Modelica.Fluid.Sources.Boundary_pT receiver(
      redeclare package Medium=Water40,p=101325,T=313.15,nPorts=1);
    output SI.PressureDifference dp=supply.p-ret.p;
    output Real flowLmin(unit="l/min")=supply.m_flow/rho*60000;
    output SI.MassFlowRate massResidual=supply.m_flow+ret.m_flow-leak.m_flow;
  equation
    connect(supply,supplyIsolation.port_a);
    connect(supplyIsolation.port_b,supplyPipe.port_a);
    connect(supplyPipe.port_b,internalElevation.port_a);
    connect(supplyPipe.port_b,leak.port_a);
    connect(leak.port_b,receiver.ports[1]);
    connect(internalElevation.port_b,rackMap.port_a);
    connect(rackMap.port_b,balancingValve.port_a);
    connect(balancingValve.port_b,returnPipe.port_a);
    connect(returnPipe.port_b,returnIsolation.port_a);
    connect(returnIsolation.port_b,ret);
  end FaultRackBranch;

'''
s=s.replace('  model Baseline ',new+'  model Baseline ')
s=s.replace('parameter SI.PressureDifference filterNominalPa=20000;','parameter SI.PressureDifference filterNominalPa=20000;\n    parameter Real supplyOpening(min=0,max=1)=1;\n    parameter Real returnOpening(min=0,max=1)=1;\n    parameter Real holeDiameterMM(min=0)=3;\n    parameter Boolean supplyClosed=false annotation(Evaluate=true);\n    parameter Boolean returnClosed=false annotation(Evaluate=true);\n    parameter Boolean leakEnabled=true annotation(Evaluate=true);')
s=s.replace('RackBranch rack5(', 'FaultRackBranch rack5(supplyClosed=supplyClosed,returnClosed=returnClosed,leakEnabled=leakEnabled,supplyOpening=supplyOpening,returnOpening=returnOpening,holeDiameter=holeDiameterMM/1000,')
s=s.replace('output SI.Power pumpEnergyResidualW=', 'output SI.Power legacyClosedLoopEnergyResidualW=')
outs='''    output Real commandedSupplyConductance=if supplyClosed then 0 else supplyOpening;
    output Real commandedReturnConductance=if returnClosed then 0 else returnOpening;
    output Real leakFlowLmin=rack5.leak.m_flow/rho*60000;
    output Real leakNodeAbsKPa=rack5.leak.port_a.p/1000;
    output Real makeupFlowLmin=-pressureReference.ports[1].m_flow/rho*60000;
    output Real returnTotalFlowLps=returnCommon.m_flow/rho*1000;
    output Real rack05SupplyLmin=rack5.supply.m_flow/rho*60000;
    output Real rack05ReturnLmin=-rack5.ret.m_flow/rho*60000;
    output SI.Power openSystemEnergyResidualW=pumpBank.W_total-numericalBath.port.Q_flow-pressureReference.ports[1].m_flow*actualStream(pressureReference.ports[1].h_outflow)-rack5.leak.m_flow*actualStream(rack5.leak.port_a.h_outflow)-rack5.leak.m_flow*g*1.0;
    output SI.Power volumeEnergyResidualW=sum(referenceVolume.ports[j].m_flow*actualStream(referenceVolume.ports[j].h_outflow) for j in 1:3)+referenceVolume.heatPort.Q_flow;
'''
s=s.replace('    output Real commandedSpeedPercent',outs+'    output Real commandedSpeedPercent')
(B/'model/DataCenterIsolation.mo').write_text(s)
D['model_sha256']=hashlib.sha256(s.encode()).hexdigest();(B/'model/design.json').write_text(json.dumps(D,indent=2)+'\n')
mos='setCommandLineOptions("--numProcs=2");\nloadModel(Modelica,{"4.1.0"});\nloadFile("../../model/DataCenterIsolation.mo");\ngetErrorString();\n'
for binary,cls in [('reference','ReferenceNetwork'),('open','OpenNetwork'),('supply_closed','SupplyClosedNetwork'),('return_closed','ReturnClosedNetwork'),('dual_closed','DualClosedNetwork')]:
 mos+=f'checkModel(DataCenterIsolation.{cls});\ngetErrorString();\nbuildModel(DataCenterIsolation.{cls},startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="{binary}",cflags="-O1");\ngetErrorString();\n'
(B/'source/build.mos').write_text(mos)
print('Native isolation model',D['model_sha256'])
