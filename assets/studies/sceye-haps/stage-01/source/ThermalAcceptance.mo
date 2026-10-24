package ThermalAcceptance
  model LinearHeating
    parameter Real C=10000 "J/K";
    parameter Real G=2 "W/K";
    parameter Real Q=100 "W";
    parameter Real Tamb=293.15 "K";
    parameter Real T0=293.15 "K";
    Real T(start=T0,fixed=true) "K";
    Real storedEnergyJ=C*(T-T0);
    Real removedEnergyJ(start=0,fixed=true);
    Real sourceEnergyJ(start=0,fixed=true);
    Real balanceResidualJ=sourceEnergyJ-removedEnergyJ-storedEnergyJ;
  equation
    C*der(T)=Q-G*(T-Tamb);
    der(removedEnergyJ)=G*(T-Tamb);
    der(sourceEnergyJ)=Q;
  end LinearHeating;
  model LinearCooling
    extends LinearHeating(Q=0,Tamb=253.15,T0=293.15);
  end LinearCooling;
  model RadiativeEquilibrium
    parameter Real Q=100;
    parameter Real eps=.85;
    parameter Real A=1;
    parameter Real sigma=5.670374419e-8;
    parameter Real Tsink=250;
    Real T(start=280,nominal=300);
    Real residualW=Q-eps*sigma*A*(T^4-Tsink^4);
  equation
    residualW=0;
  end RadiativeEquilibrium;
end ThermalAcceptance;
