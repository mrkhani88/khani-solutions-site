"""Illustrative presizing, not AWS/Google design data or a solved network.

Run with Python 3. Standard library only. Outputs are written beside this file.
Water properties at approximately 40 C are assumed constants. Haaland gives
Darcy friction factor. Header losses conservatively use full module flow along
the full length; the OpenModelica model must instead resolve each tee segment.
"""
from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parent
P = dict(liquid_load_W=1e6, racks=10, delta_T_K=10, rho_kg_m3=992.2,
         cp_J_kgK=4179.0, mu_Pas=0.000653, roughness_m=15e-6,
         header_total_length_m=40, rack_branch_total_length_m=20,
         header_K=6, rack_pipe_fitting_K=8, assumed_wire_to_water_efficiency=0.65,
         pressure_margin_fraction=0.15)
mass = P['liquid_load_W'] / (P['cp_J_kgK'] * P['delta_T_K'])
q = mass / P['rho_kg_m3']

def pipe(flow, diameter, length, K):
    v = flow / (math.pi * diameter**2 / 4)
    re = P['rho_kg_m3'] * v * diameter / P['mu_Pas']
    f = 64/re if re < 2300 else (-1.8 * math.log10((P['roughness_m']/diameter/3.7)**1.11 + 6.9/re))**-2
    dyn = P['rho_kg_m3'] * v*v/2
    return dict(ID_mm=diameter*1000, flow_L_s=flow*1000, velocity_m_s=v,
                Re=re, Darcy_f=f, straight_dp_kPa=f*length/diameter*dyn/1000,
                fitting_dp_kPa=K*dyn/1000,
                total_dp_kPa=(f*length/diameter+K)*dyn/1000)

candidates = []
for d in [0.100, 0.125, 0.150]:
    candidates.append(dict(service='module_header_pair', **pipe(q,d,40,6)))
for d in [0.032,0.040,0.050]:
    candidates.append(dict(service='one_rack_branch_pair', **pipe(q/10,d,20,8)))
selected_header = pipe(q,0.125,40,6)
selected_rack = pipe(q/10,0.040,20,8)
budget = {
    'common_header_straight_and_fittings': selected_header['total_dp_kPa'],
    'one_rack_pipe_pair_and_standard_fittings': selected_rack['total_dp_kPa'],
    'one_rack_internal_path_cold_plates_QDs_hoses_ASSUMED': 100,
    'CDU_heat_exchanger_secondary_side_ASSUMED': 45,
    'common_filter_dirty_design_allowance_ASSUMED': 20,
    'branch_control_valve_ASSUMED': 15,
}
dp = sum(budget.values())
design_dp = dp*(1+P['pressure_margin_fraction'])
summary = dict(status='illustrative_presizing_only_not_a_network_simulation',
               assumptions=P, mass_flow_kg_s=mass, module_flow_L_s=q*1000,
               module_flow_m3_h=q*3600, rack_flow_L_s=q*100,
               pipe_candidates=candidates, critical_path_budget_kPa=budget,
               critical_path_dp_before_margin_kPa=dp, design_dp_kPa=design_dp,
               design_head_m=design_dp*1000/(P['rho_kg_m3']*9.80665),
               total_pump_electrical_kW=q*design_dp/P['assumed_wire_to_water_efficiency'],
               pump_concept='3 x 50% pumps: 2 duty + 1 standby; curves not selected',
               individual_duty_pump_m3_h=q*3600/2,
               open_system_extra_head_for_5m_kPa=P['rho_kg_m3']*9.80665*5/1000,
               deltaT_sensitivity_L_s={str(t):P['liquid_load_W']/(P['cp_J_kgK']*t*P['rho_kg_m3'])*1000 for t in [5,10,15]})
assert all(c['Re'] > 4000 for c in candidates)
assert 0 < summary['total_pump_electrical_kW'] < 0.05*P['liquid_load_W']/1000
(ROOT/'concept-sizing.json').write_text(json.dumps(summary,indent=2)+'\n')
with (ROOT/'pipe-candidates.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(candidates[0]));writer.writeheader();writer.writerows(candidates)
print(json.dumps(summary,indent=2))
