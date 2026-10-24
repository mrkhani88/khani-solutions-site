from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parents[1]
D=json.loads((B/'model/design.json').read_text())
s='''package DataCenterIsolation
  constant Real rho=992.2;
  constant Real g=9.80665;
  constant Real qn=1e6/(4179*10)/rho;
  constant Real qrn=qn/10;
  function pipeLoss
    input Real q;
    input Real L;
    input Real diameter;
    input Real K=0;
    output Real dp;
  protected
    Real v; Real Re; Real f; Real lo; Real hi; Real mid; Real residual;
  algorithm
    v:=q/(Modelica.Constants.pi*diameter^2/4);
    Re:=rho*abs(v)*diameter/.000653;
    if Re < 1e-8 then dp:=0;
    elseif Re < 2300 then
      dp:=32*.000653*L/diameter^2*v+K*rho*v*abs(v)/2;
    else
      lo:=.005; hi:=.12;
      for j in 1:45 loop
        mid:=(lo+hi)/2;
        residual:=1/sqrt(mid)+2*log10(15e-6/diameter/3.7+2.51/(Re*sqrt(mid)));
        if residual > 0 then lo:=mid; else hi:=mid; end if;
      end for;
      f:=(lo+hi)/2;
      dp:=(f*L/diameter+K)*rho*v*abs(v)/2;
    end if;
  end pipeLoss;
  function isolationFlow
    input Real dp;
    input Real opening;
    output Real q;
  protected
    Real nominalDP; Real x;
  algorithm
    nominalDP:=.5*rho*(qrn/(Modelica.Constants.pi*.04^2/4))^2/2;
    x:=dp/nominalDP;
    q:=opening*qrn*x/(x*x+1e-16)^.25;
  end isolationFlow;
  model Network "Isothermal algebraic hydraulic network; not a physical transient"
    parameter Real speedRatio=.944820731917674;
    parameter Real holeDiameterMM=3;
    parameter Real supplyOpening=1;
    parameter Real returnOpening=1;
    parameter Real supplyStart[10]=fill(144.7,10);
    parameter Real returnStart=144.7;
    parameter Real pressureStart=500;
    parameter Real valve[10]={18866.7088691496,17787.8811622184,16929.7311520889,16267.4138833809,15776.0100295199,15430.5022619264,15205.7394288601,15076.3782891255,15016.777967485,15000.7685365312};
    parameter Real lengths[10]={.8,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2};
    Real rackFlowLmin[10](start=supplyStart,each nominal=144.7);
    Real rack05ReturnLmin(start=returnStart,nominal=144.7);
    Real leakNodeAbsKPa(start=pressureStart,nominal=500);
    Real q[10]; Real t[10]; Real pS[10]; Real pR[10]; Real hS[10]; Real hR[10];
    Real Q; Real Qr; Real commonS; Real commonR; Real dpS; Real dpR;
    output Real totalFlowLps=Q*1000;
    output Real returnTotalFlowLps=Qr*1000;
    output Real leakFlowLmin=(rackFlowLmin[5]-rack05ReturnLmin);
    output Real makeupFlowLmin=(Q-Qr)*60000;
    output Real rack05SupplyLmin=rackFlowLmin[5];
    output Real pumpDPkPa=rho*g*(37*speedRatio^2-.5*speedRatio*(Q/qn)-9*(Q/qn)^2)/1000;
    output Real pumpElectricalW=pumpDPkPa*1000*Q/.675;
    output Real commandedSpeedPercent=speedRatio*100;
    output Real massResidualKgS=(Q-Qr-leakFlowLmin/60000)*rho;
    output Real faultMassResidualKgS=(q[5]-t[5]-leakFlowLmin/60000)*rho;
    output Real pressureResidualPa[10];
    output Real leakEquationResidualLmin;
    output Real supplyIsolationResidualLmin;
    output Real returnIsolationResidualLmin;
  equation
    for i in 1:10 loop
      q[i]=rackFlowLmin[i]/60000;
      t[i]=if i==5 then rack05ReturnLmin/60000 else q[i];
      hS[i]=pipeLoss(sum(q[j] for j in i:10),lengths[i],.125,.2);
      hR[i]=pipeLoss(sum(t[j] for j in i:10),lengths[i],.125,.2);
      pS[i]=300000+pumpDPkPa*1000-commonS-rho*g*2.15-sum(hS[j] for j in 1:i);
      pR[i]=300000+commonR-rho*g*2.15+sum(hR[j] for j in 1:i);
      if i<>5 then
        pressureResidualPa[i]=pS[i]-pR[i]-pipeLoss(q[i],4.746992,.04,8)-(100000+valve[i])*(q[i]/qrn)*abs(q[i]/qrn);
        pressureResidualPa[i]=0;
      else
        pressureResidualPa[i]=pS[i]-pR[i]-pipeLoss(q[i],1.698496,.04,3.5)-pipeLoss(t[i],3.048496,.04,3.5)-(100000+valve[i])*(t[i]/qrn)*abs(t[i]/qrn)-dpS-dpR;
      end if;
    end for;
    Q=sum(q); Qr=sum(t);
    commonS=pipeLoss(Q,2.05,.125)+pipeLoss(Q/2,1.11708,.065,2)+pipeLoss(Q,4.382611,.125,2)+20000*(Q/qn)^2;
    commonR=pipeLoss(Qr,5.678319,.125,2)+45000*(Qr/qn)^2;
    dpS=pS[5]-leakNodeAbsKPa*1000-pipeLoss(q[5],1.698496,.04,3.5)+rho*g*1.15;
    dpR=leakNodeAbsKPa*1000-pR[5]-pipeLoss(t[5],3.048496,.04,3.5)-(100000+valve[5])*(t[5]/qrn)*abs(t[5]/qrn)-rho*g*1.15;
    supplyIsolationResidualLmin=rackFlowLmin[5]-isolationFlow(dpS,supplyOpening)*60000;
    returnIsolationResidualLmin=rack05ReturnLmin-isolationFlow(dpR,returnOpening)*60000;
    leakEquationResidualLmin=leakFlowLmin-.62*Modelica.Constants.pi*(holeDiameterMM/1000)^2/4*sqrt(2*100000/rho)*Modelica.Fluid.Utilities.regRoot((leakNodeAbsKPa*1000-101325)/100000,1e-8)*60000;
    supplyIsolationResidualLmin=0;
    returnIsolationResidualLmin=0;
    leakEquationResidualLmin=0;
  end Network;
'''
for c in D['cases']:
 x=c['independent'];arr=','.join(f'{v*.98:.15g}' for v in x['supply_flow_Lmin'])
 # Start values deliberately offset from independent solution; they are not fixed equations.
 s+=f'  model Case_{c["id"]}\n    extends Network(speedRatio={c["speed_ratio"]:.16g},holeDiameterMM={c["diameter_mm"]},supplyOpening={c["supply_opening"]},returnOpening={c["return_opening"]},supplyStart={{{arr}}},returnStart={x["return_flow_Lmin"][4]*.98:.16g},pressureStart={x["leak_node_abs_kPa"]*1.01:.16g});\n  end Case_{c["id"]};\n'
s+='end DataCenterIsolation;\n'
(B/'model/DataCenterIsolation.mo').write_text(s);D['model_sha256']=hashlib.sha256(s.encode()).hexdigest();D['native_scope']='Reduced isothermal algebraic pressure-flow network. No enthalpy, compressibility or closure dynamics. Start guesses offset from independent solution; not fixed.';(B/'model/design.json').write_text(json.dumps(D,indent=2)+'\n')
mos='setCommandLineOptions("--numProcs=2");\nloadModel(Modelica,{"4.1.0"});\nloadFile("../../model/DataCenterIsolation.mo");\ngetErrorString();\n'
for c in D['cases']:
 mos+=f'simulate(DataCenterIsolation.Case_{c["id"]},startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="{c["id"]}",cflags="-O1",simflags="-nls=hybrid -nlssMaxDensity=0");\ngetErrorString();\n'
(B/'source/run-reduced.mos').write_text(mos)
