"""Extend the accepted native model, preserving MSL manual-valve behavior."""
from pathlib import Path
import json,hashlib,re
B=Path(__file__).resolve().parents[1];D=json.loads((B/'model/design.json').read_text())
s=(B/'inputs/parent-model.mo').read_text().replace('DataCenterBalancing','DataCenterValveComparison')
# The inherited five example classes are replaced by two reusable compiled variants.
s=s[:s.index('  model Case_baseline')]+'''  model ManualNetwork
    extends Baseline(pressureIndependent=false);
  end ManualNetwork;
  model PICVNetwork
    extends Baseline(pressureIndependent=true);
  end PICVNetwork;
end DataCenterValveComparison;
'''
s=s.replace('  model RackBranch', '''  model BalancingElement "Manual or generic pressure-limited ideal PICV"
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

  model RackBranch''')
s=s.replace('parameter SI.PressureDifference valveNominalPa=15000;','parameter Boolean pressureIndependent=false;\n    parameter SI.PressureDifference valveNominalPa=15000;')
start=s.index('    Modelica.Fluid.Fittings.SimpleGenericOrifice balancingValve(')
end=s.index('    Segment returnPipe(',start)
s=s[:start]+'''    BalancingElement balancingValve(pressureIndependent=pressureIndependent,
      diameter=diameter,nominalDP=valveNominalPa,minimumDP=35000);
'''+s[end:]
s=s.replace('parameter Real speedRatio=1;','parameter Real speedRatio=1;\n    parameter Boolean pressureIndependent=false;\n    parameter SI.PressureDifference filterNominalPa=20000;')
vals=','.join(format(z,'.15g') for z in json.loads((B/'inputs/stage04-design.json').read_text())['cases'][3]['valve_nominal_Pa'])
s=s.replace('valveNominalPa[10]=fill(15000,10)',f'valveNominalPa[10]={{{vals}}}')
s=s.replace('dp_nominal=20000,m_flow_nominal=mNom','dp_nominal=filterNominalPa,m_flow_nominal=mNom')
for i in range(1,11):s=s.replace(f'RackBranch rack{i}(valveNominalPa=',f'RackBranch rack{i}(pressureIndependent=pressureIndependent,valveNominalPa=')
s=s.replace('    output Real totalFlowLps', '    output Real commandedSpeedPercent=100*speedRatio;\n    output Real totalFlowLps')
(B/'model/DataCenterValveComparison.mo').write_text(s)
D['model_sha256']=hashlib.sha256(s.encode()).hexdigest();(B/'model/design.json').write_text(json.dumps(D,indent=2)+'\n')
mos=['setCommandLineOptions("--numProcs=2");','loadModel(Modelica,{"4.1.0"});','loadFile("../../model/DataCenterValveComparison.mo");','getErrorString();']
for mode,name in [('manual','ManualNetwork'),('picv','PICVNetwork')]:
 mos += [f'checkModel(DataCenterValveComparison.{name});','getErrorString();',f'buildModel(DataCenterValveComparison.{name},startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="{mode}",cflags="-O1");','getErrorString();']
(B/'source/build.mos').write_text('\n'.join(mos)+'\n')
print('Generated two reusable native variants; model SHA256',D['model_sha256'])
