within ;
model HAPSEquilibrium "Payload-only fixed-boundary screening; not an indefinitely powered flight"
 parameter Real fixedHour=12,coldOffset=0,mountT=273.15,hullT=240;
 HAPSInterview.MissionEnvironment environment(fixedHour=fixedHour,coldOffset=coldOffset);
 HAPSInterview.Payload payload(improved=1,strapScale=4,radiatorArea=4.5,switchEnabled=1,minFraction=.03);
 Modelica.Thermal.HeatTransfer.Sources.FixedTemperature mount(T=mountT),hull(T=hullT);
 Real netEnergy(start=0,fixed=true);output Real residualJ;
equation
 connect(environment.bus,payload.env);connect(mount.port,payload.mount);connect(hull.port,payload.hull);payload.SOC=.7;
 der(netEnergy)=payload.Qgenerated+payload.Qext+payload.mount.Q_flow+payload.hull.Q_flow;
 residualJ=netEnergy-payload.U;
 annotation(uses(Modelica(version="4.1.0")));
end HAPSEquilibrium;
