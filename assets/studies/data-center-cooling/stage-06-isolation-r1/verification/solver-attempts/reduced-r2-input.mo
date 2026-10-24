package DataCenterIsolation
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
    leakEquationResidualLmin=leakFlowLmin-.62*Modelica.Constants.pi*(holeDiameterMM/1000)^2/4*sqrt(2*max(leakNodeAbsKPa*1000-101325,0)/rho)*60000;
    supplyIsolationResidualLmin=0;
    returnIsolationResidualLmin=0;
    leakEquationResidualLmin=0;
  end Network;
  model Case_reference
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=0,supplyOpening=1.0,returnOpening=1.0,supplyStart={141.806,141.806,141.806,141.806,141.806,141.806,141.806,141.806,141.806,141.806},returnStart=141.806,pressureStart=472.9940581772024);
  end Case_reference;
  model Case_d1_unisolated
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=1,supplyOpening=1,returnOpening=1,supplyStart={141.777407060271,141.777117640654,141.776855685868,141.776622762448,142.504374230195,141.776417474568,141.77641559097,141.776414397859,141.776413776876,141.776413575919},returnStart=141.7258001238251,pressureStart=472.8250326479937);
  end Case_d1_unisolated;
  model Case_d1_supply_only
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=1,supplyOpening=0,returnOpening=1,supplyStart={150.004114742491,150.125189995032,150.23398363651,150.329834637722,2.16579476952529e-21,150.412995084311,150.413552706492,150.413906110894,150.41409014398,150.414149718304},returnStart=-0.6250020281214704,pressureStart=341.0840059905016);
  end Case_d1_supply_only;
  model Case_d1_return_only
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=1,supplyOpening=1,returnOpening=0,supplyStart={149.961674676413,150.082173311134,150.190452985875,150.285855813198,0.800423686405034,150.368632288686,150.369186989179,150.369538540919,150.36972160876,150.369780870519},returnStart=2.109113002914694e-22,pressureStart=493.9111890655016);
  end Case_d1_return_only;
  model Case_d1_dual
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=1,supplyOpening=0,returnOpening=0,supplyStart={149.994396943583,150.115228192398,150.22380430192,150.319465589709,-2.86586412350678e-24,150.402464257518,150.403021186106,150.403374150696,150.403557954637,150.403617454759},returnStart=8.13254245324549e-26,pressureStart=102.33825);
  end Case_d1_dual;
  model Case_d1_seat_leak
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=1,supplyOpening=0.01,returnOpening=0.01,supplyStart={149.262059657967,149.372522670303,149.471850308012,149.559439435937,13.1477137399116,149.635516700892,149.63602318855,149.636344169678,149.636511310811,149.636565415346},returnStart=12.43424030834748,pressureStart=413.4585993425391);
  end Case_d1_seat_leak;
  model Case_d1_reset
    extends Network(speedRatio=0.8933213592398361,holeDiameterMM=1,supplyOpening=0.0,returnOpening=0.0,supplyStart={141.806,141.918794308464,142.020251593156,142.109740190051,-5.40680870032804e-26,142.186774546726,142.186798812412,142.186814183222,142.186822183528,142.186824772551},returnStart=2.355676073775401e-26,pressureStart=102.33825);
  end Case_d1_reset;
  model Case_d3_unisolated
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=1,returnOpening=1,supplyStart={141.549330756759,141.54673248888,141.544380078054,141.542287580072,148.070816404895,141.540442471798,141.540425571389,141.540414866473,141.540409294921,141.540407491924},returnStart=141.0765489598895,pressureStart=471.4622279885903);
  end Case_d3_unisolated;
  model Case_d3_supply_only
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=0,returnOpening=1,supplyStart={150.081630723036,150.204651400817,150.315178866566,150.412541346278,-1.86996197602804e-22,150.496989997776,150.497553153087,150.497910066108,150.498095927215,150.49815609349},returnStart=-5.619073312387994,pressureStart=340.5796238632403);
  end Case_d3_supply_only;
  model Case_d3_return_only
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=1,returnOpening=0,supplyStart={149.699758207708,149.817591440002,149.923494730649,150.016824566406,7.19695446074357,150.097817803485,150.098354678789,150.098694927681,150.098872106794,150.098929461691},returnStart=-5.133473801650087e-24,pressureStart=493.1659144855654);
  end Case_d3_return_only;
  model Case_d3_dual
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=0,returnOpening=0,supplyStart={149.994396943583,150.115228192398,150.22380430192,150.319465589709,-2.86586412350678e-24,150.402464257518,150.403021186106,150.403374150696,150.403557954637,150.403617454759},returnStart=8.132542453244514e-26,pressureStart=102.33825);
  end Case_d3_dual;
  model Case_d3_seat_leak
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=0.01,returnOpening=0.01,supplyStart={149.213333398668,149.324010796388,149.42352991241,149.511286303041,15.4869514068082,149.587501038515,149.588004373037,149.588323354933,149.58848945455,149.588543221842},returnStart=9.395186340005164,pressureStart=382.3485973300364);
  end Case_d3_seat_leak;
  model Case_d3_reset
    extends Network(speedRatio=0.893321359239836,holeDiameterMM=3,supplyOpening=0.0,returnOpening=0.0,supplyStart={141.806,141.918794308464,142.020251593156,142.109740190051,4.89625471986777e-26,142.186774546726,142.186798812412,142.186814183222,142.186822183528,142.186824772551},returnStart=-3.752490446294967e-26,pressureStart=102.33825);
  end Case_d3_reset;
  model Case_d6_unisolated
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=6,supplyOpening=1,returnOpening=1,supplyStart={140.788586546279,140.778284272268,140.768947440522,140.760631679608,166.583816258642,140.753287438329,140.753220553158,140.753178189472,140.753156141635,140.753149006989},returnStart=138.7866314876882,pressureStart=466.7307529610005);
  end Case_d6_unisolated;
  model Case_d6_supply_only
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=6,supplyOpening=0,returnOpening=1,supplyStart={150.33863933589,150.468098442016,150.584357054625,150.686707745,5.87952032178427e-32,150.775398569664,150.775980077253,150.776348627922,150.776540552469,150.77660268224},returnStart=-22.28829903045902,pressureStart=336.6109360884071);
  end Case_d6_supply_only;
  model Case_d6_return_only
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=6,supplyOpening=1,returnOpening=0,supplyStart={148.814437697522,148.923220631836,149.021043139165,149.107310383972,28.6852082625948,149.182213351342,149.182690093596,149.182992215245,149.183149531627,149.183200454956},returnStart=1.092159689898619e-40,pressureStart=490.3847941448128);
  end Case_d6_return_only;
  model Case_d6_dual
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=6,supplyOpening=0,returnOpening=0,supplyStart={149.994396943583,150.115228192398,150.22380430192,150.319465589709,-2.86586412350678e-24,150.402464257518,150.403021186106,150.403374150696,150.403557954637,150.403617454759},returnStart=8.132542453244514e-26,pressureStart=102.33825);
  end Case_d6_dual;
  model Case_d6_seat_leak
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=6,supplyOpening=0.01,returnOpening=0.01,supplyStart={149.290503810579,149.405007777193,149.50793867183,149.598670679492,18.5242566622109,149.677415733951,149.677924973534,149.678247699518,149.678415749651,149.678470148521},returnStart=-3.649600037273987,pressureStart=334.2113020381204);
  end Case_d6_seat_leak;
  model Case_d6_reset
    extends Network(speedRatio=0.8933213592399752,holeDiameterMM=6,supplyOpening=0.0,returnOpening=0.0,supplyStart={141.806,141.918794308373,142.020251592843,142.109740189693,-1.9141483484718e-22,142.186774546844,142.186798812529,142.186814183339,142.186822183646,142.186824772668},returnStart=1.583912429974639e-23,pressureStart=102.33825);
  end Case_d6_reset;
  model Case_d3_partial_50
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=0.5,returnOpening=0.5,supplyStart={141.713088761751,141.712985064629,141.712891817063,141.712809421706,145.294506811651,141.712729734372,141.712723796397,141.712720035173,141.71271807756,141.712717444058},returnStart=138.322190451739,pressureStart=469.1489172546282);
  end Case_d3_partial_50;
  model Case_d3_partial_10
    extends Network(speedRatio=0.944820731917674,holeDiameterMM=3,supplyOpening=0.1,returnOpening=0.1,supplyStart={144.429772180141,144.470571365247,144.507422424187,144.540102175291,98.894425970121,144.568679209238,144.568856132477,144.568968219566,144.569026567801,144.569045451852},returnStart=92.23905452438215,pressureStart=436.5582125553203);
  end Case_d3_partial_10;
end DataCenterIsolation;
