"""Initial analytical environment and heat-rejection screen, not a HAPS solution."""
from pathlib import Path
import math,json,csv
B=Path(__file__).resolve().parents[1];SIGMA=5.670374419e-8;RGAS=287.05287;G=9.80665;RE=6356766

def atmosphere(z):
 H=RE*z/(RE+z)
 if H<11000:
  T=288.15-.0065*H;p=101325*(T/288.15)**(G/(RGAS*.0065))
 elif H<=20000:T=216.65;p=22632.06*math.exp(-G*(H-11000)/(RGAS*T))
 else:T=216.65+.001*(H-20000);p=5474.889*(216.65/T)**(G/(RGAS*.001))
 return {'geometric_altitude_m':z,'geopotential_altitude_m':H,'ambient_C':T-273.15,'pressure_kPa_abs':p/1000,'density_kg_m3':p/(RGAS*T)}
def rejection(Tc=40,Tac=-56.5,h=1.,eps=.85,alpha=.2,solar=1361,cosine=.7,shaded=True,earth=240,sky=80,ThullC=-20,Fearth=.2,Fsky=.4,Fhull=.4):
 T=Tc+273.15;Ta=Tac+273.15
 conv=h*(T-Ta);emit=eps*SIGMA*T**4;ir=eps*(Fearth*earth+Fsky*sky+Fhull*SIGMA*(ThullC+273.15)**4);sun=0 if shaded else alpha*solar*cosine
 net=conv+emit-ir-sun
 return {'convective_rejection_W_m2':conv,'IR_emission_W_m2':emit,'absorbed_environment_IR_W_m2':ir,'absorbed_direct_solar_W_m2':sun,'net_rejection_W_m2':net,'area_for_200W_m2':200/net if net>0 else None}
if __name__=='__main__':
 rows=[atmosphere(z) for z in [0,11000,18000,20000,21000,22000]]
 assert abs(rows[0]['pressure_kPa_abs']-101.325)<1e-8
 assert abs(rows[3]['pressure_kPa_abs']-5.5293)<.001
 checks={'result_kind':'Algebraic presizing; not a thermal trajectory, convection correlation, material selection or vehicle validation','atmosphere_model':'1976 standard layers, geometric input converted to geopotential altitude; dry air through 22 km. Not a weather/season envelope.','environment':rows,'radiator_assumptions':{'surface_C':40,'ambient_C':-56.5,'effective_h_W_m2K':1,'emissivity':.85,'solar_absorptivity':.2,'solar_flux_W_m2':1361,'solar_cosine':.7,'Earth_IR_W_m2':240,'sky_IR_W_m2':80,'hull_C':-20,'view_factors':{'Earth':.2,'sky':.4,'hull':.4},'load_W':200},'radiator_shaded':rejection(),'radiator_sunlit':rejection(shaded=False),'limits':['All radiator inputs are study assumptions, not Sceye data.','h is user-specified; no low-pressure convection solution is claimed.','No reflected solar term in this first screen; add it to absorbed solar for real sizing.','Shaded case removes direct solar only; it does not remove Earth/sky/hull IR.','Areas are isothermal effective rejection area under these assumptions; not selected radiator hardware.','No contact/spreading gradients, time dependence, payload limits, heater control, SOC or array power calculation yet.','The geometric CAD radiator area has not been sized by this screen.']}
 (B/'inputs/first-calculations.json').write_text(json.dumps(checks,indent=2)+'\n')
 with (B/'inputs/standard-atmosphere.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
 print(json.dumps(checks,indent=2))
