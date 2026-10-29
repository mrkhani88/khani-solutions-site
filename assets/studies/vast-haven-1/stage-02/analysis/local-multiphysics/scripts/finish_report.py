from pathlib import Path
import json,hashlib,zipfile,csv
ROOT=Path(__file__).resolve().parents[1]
f=json.loads((ROOT/'fea/summary.json').read_text());c=json.loads((ROOT/'cfd-flatpanel/summary.json').read_text())
summary={
 'title':'Local thermal, thermoelastic and forced-ventilation screening',
 'scope':'Independent assumed local submodels informed by public-reference CAD. Not a solved 221-part assembly or flight-qualified Haven-1 model.',
 'physically_tested':False,'manufacturer_validated':False,'execution_host':'Intel (falcon-intel)',
 'thermal':{'solver':f['solver'],'baseline_peak_C':f['thermal_baseline']['peak_C'],'improved_contact_peak_C':f['thermal_improved_contact']['peak_C'],'temperature_reduction_C':f['thermal_baseline']['peak_C']-f['thermal_improved_contact']['peak_C'],'heat_W':80,'coolant_C':20,'contact_h_baseline_W_m2K':500,'contact_h_improved_W_m2K':2000,'plot':'fea/thermal-comparison.png','source_summary':'fea/summary.json'},
 'thermostructural':{'solver':f['solver'],'clamped':f['structure_clamped'],'sliding':f['structure_sliding'],'plot':'fea/stress-comparison.png','interpretation':'Sliding supports reduce restraint-driven stress while permitting more thermal motion. Maximum clamp stress is mesh sensitive; no factor of safety or minimum thickness is established.'},
 'cfd':{'solver':'OpenFOAM v2512 buoyantBoussinesqSimpleFoam, laminar, g=0','heat_to_air_W':2,'baseline':c['baseline'],'double_flow':c['double_flow'],'mesh_fine':c['mesh_fine'],'mesh_finer':c['mesh_finer'],'mesh_sensitivity':c['mesh_sensitivity'],'velocity_plot':'cfd-flatpanel/velocity-comparison.png','temperature_plot':'cfd-flatpanel/temperature-comparison.png','pressure_plot':'cfd-flatpanel/pressure-comparison.png','source_summary':'cfd-flatpanel/summary.json','interpretation':'Bulk temperature rise halves when flow doubles. The coarse-grid local temperature benefit is below baseline mesh sensitivity and is not mesh-qualified. Bay pressure loss is not whole-loop fan power.'},
 'verification':{'fea':f['verification'],'fea_mesh':f['mesh'],'cfd_all_checkMesh_passed':all(c[n]['mesh_check_passed'] for n in ['baseline','double_flow','mesh_fine','mesh_finer']),'cfd_max_mass_error_fraction':max(c[n]['mass_balance_fraction'] for n in ['baseline','double_flow','mesh_fine','mesh_finer']),'cfd_max_heat_error_fraction':max(c[n]['outlet_heat_closure_fraction'] for n in ['baseline','double_flow','mesh_fine','mesh_finer'])},
 'downloads':{'archive':'Local_Multiphysics_Inputs_Results.zip','report':'report.md','fem_nodes':'fea/nodal-results.csv','fem_vtk':'fea/baseline_clamped.vtk'},
 'coupling_boundary':'80W conduction plate,2W air-bay CFD and1D orbital model are independent screening submodels. No common heat budget, temperatures, contacts, mapped CFD h-field or two-way coupling has been established.',
 'next_steps':['Replace assumed geometry/material/contact/loads with actual hardware data','Run matched refined-grid flow cases before claiming a local ventilation optimization','Map CFD heat-transfer coefficients into the coldplate/avionics thermal submodel','Add compliant mounts, bolts, launch loads, modal/vibration and fatigue analyses','Correlate measured temperatures, flow and contact conductance before flight decisions']}
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2))
table='\n'.join(f"| {n} | {c[n]['cells']:,} | {c[n]['heater_area_average_C']:.3f} | {c[n]['air_cell_peak_C']:.3f} | {c[n]['pressure_drop_Pa']:.7f} |" for n in ['baseline','mesh_fine','mesh_finer'])
report=f'''# Local thermal, thermoelastic and cabin-air screening

This first round demonstrates model setup, energy accounting, spatial fields, contact and support trade studies, and numerical verification. All local geometry, loads, contacts, material values and support conditions are analyst-selected. The representative Haven-1 CAD provides system context. These are simplified local analysis geometries, not manufacturer flight drawings. No manufacturer-specific thermal requirements, physical testing or qualification is claimed.

## 1. Three-dimensional equipment-panel conduction

The model is a 300 × 200 × 6 mm flat aluminium-like mounting panel. A central 150 × 100 mm top patch dissipates80W. Two bottom strips, each50mm wide, transfer heat to an assumed20°C coolant boundary through an effective contact/film conductance. Other surfaces are adiabatic. This effective conductance represents a combined interface and coolant-side resistance; it does not model a literal selected thermal pad or a resolved coolant channel.

Inputs: k=167W/(m K), E=69GPa, Poisson ratio0.33, expansion coefficient23×10⁻⁶/K. These constant isotropic values are representative near room temperature. They have not been measured for Vast hardware.

The custom Python/SciPy solver assembles full3D linear-tetrahedral conduction matrices and Robin boundary integrals. Baseline effective h=500W/(m² K) gives a peak{f['thermal_baseline']['peak_C']:.3f}°C. Increasing h to2000W/(m² K), with identical heat and sink temperature, lowers it to{f['thermal_improved_contact']['peak_C']:.3f}°C. The{summary['thermal']['temperature_reduction_C']:.3f}°C change comes from reduced contact resistance. The remaining spatial gradient comes from finite in-plane conduction distance to the sink strips.

Verification:4608 to15552 tetrahedra changes the baseline peak by{f['mesh']['peak_delta_C']:.4f}°C. Both meshes reject80W, with relative energy error below3×10⁻¹². This is an initial sensitivity check, not full proof of spatial convergence or physical accuracy.

Figure: [Contact conductance comparison](fea/thermal-comparison.png). Raw nodal fields and ParaView-readable tetrahedral VTK files accompany the downloads.

## 2. Thermal expansion and mounting restraint

The same baseline3D temperature field drives a linear-elastic small-strain thermoelastic solve, with20°C as the stress-free reference. There are no pressure, launch acceleration, vibration, bolt preload, fatigue, plasticity or buckling loads in this analysis.

The first case fixes all translations on both x-end faces. It gives maximum element von Mises stress{f['structure_clamped']['max_von_mises_MPa']:.2f}MPa,95th percentile{f['structure_clamped']['percentile95_von_mises_MPa']:.2f}MPa and maximum motion{f['structure_clamped']['max_displacement_mm']:.4f}mm. The second permits in-plane thermal expansion through an ideal kinematic/sliding constraint: ux=0 on x=0, one origin node fixed in y/z, and a second y-separated node fixed in z to remove rigid rotation. It gives maximum{f['structure_sliding']['max_von_mises_MPa']:.2f}MPa,95th percentile{f['structure_sliding']['percentile95_von_mises_MPa']:.2f}MPa and maximum motion{f['structure_sliding']['max_displacement_mm']:.4f}mm.

This isolates a support-condition effect. Freedom to expand reduces thermal restraint stress while requiring more motion accommodation. It does not establish a flight mount design or a minimum panel thickness.

The refined thermal/structural mesh raises the clamp-adjacent maximum to{f['mesh']['fine_clamped_max_MPa']:.2f}MPa, while its95th percentile changes only to{f['mesh']['fine_clamped_p95_MPa']:.2f}MPa. Therefore the maximum clamp stress is mesh sensitive and must not be used to claim a qualified factor of safety. A uniform20K free-expansion patch test reproduces u=αΔTx with relative displacement error{f['verification']['uniform_expansion_relative_error']:.3g} and near-zero stress. No experimental correlation has occurred.

Figure: [Restraint comparison](fea/stress-comparison.png). The plotted stress is averaged through thickness and projected onto the panel plane. It is not a recovered surface stress.

## 3. Microgravity forced ventilation CFD

OpenFOAM v2512 buoyantBoussinesqSimpleFoam solves steady incompressible momentum/pressure and the air energy equation. Gravity is exactly zero, so buoyancy is disabled. This is a pressurized cabin-air case. It is not a vacuum exterior cooling analysis and is not conjugate solid-fluid heat transfer.

The bay is1.6 ×0.8 ×0.8m. A0.4 ×0.4 ×0.04m low-profile equipment envelope mounts to its floor. Its five exposed surfaces impose2W total residual heat to air over0.224m². The outer walls are adiabatic. All walls are no-slip. A full-face inlet supplies20°C air at0.02 or0.04m/s. A zero gauge pressure outlet allows developed outflow. Constant assumed properties are ρ=1.2kg/m³, cp=1005J/(kg K), k=0.026W/(m K), ν=1.5×10⁻⁵m²/s, and Pr=0.695769. The effective laminar model is a screening assumption. Reynolds number based on0.8m bay dimension is1067/2133; transition, grille jets and forced mixing remain unrepresented.

The2W air case is an assumed residual load in a low-speed local bay. It is independent of the80W conductive panel and independent of the1D orbital system model. There is no demonstrated common heat ledger or two-way coupling. Most hardware cooling in the concept relies on conduction/coldplates; this residual-air case does not establish total avionics dissipation or full cabin cooling capacity.

On the matching4536-cell grid, flow doubles from12.8 to25.6L/s. The mass-flow-weighted outlet changes from{c['baseline']['outlet_mass_weighted_C']:.5f} to{c['double_flow']['outlet_mass_weighted_C']:.5f}°C, matching the bulk relation ΔT=Q/(ṁcp). Heated-surface area-average temperature changes{c['baseline']['heater_area_average_C']:.3f} to{c['double_flow']['heater_area_average_C']:.3f}°C. The coarse-cell maximum air temperature changes{c['baseline']['air_cell_peak_C']:.3f} to{c['double_flow']['air_cell_peak_C']:.3f}°C.

**The small local temperature improvement is not mesh qualified.** Baseline heater mean changes2.528°C between the first two meshes, larger than the1.031°C flow benefit on the coarse grid. The fine-to-finer change is0.387°C. Air-cell maxima also depend on near-wall cell locations. Only the bulk outlet energy trend is robust in this round. Refined matched-grid flow cases are the next gate before claiming local hotspot optimization.

| Baseline mesh | Cells | Heater mean°C | Max air cell°C | Bay pressure drop Pa |
|---|---:|---:|---:|---:|
{table}

All four cases pass checkMesh and terminate by SIMPLE residual-control convergence, with final initial equation residuals below10⁻⁸. Maximum net flow mismatch is{summary['verification']['cfd_max_mass_error_fraction']:.3g}. Outlet sensible heat recovers the imposed2W to within{summary['verification']['cfd_max_heat_error_fraction']:.3g}fraction. These are numerical consistency checks; they are not experimental validation.

The reported pressure losses, approximately0.00012 and0.00030Pa on the coarse matching grids, belong only to this short, mostly open bay. The corresponding Δp×Q values are aerodynamic power for this domain alone. They exclude filters, ducts, bends, grilles, return paths, heat exchangers and fan motor/efficiency losses, and must not size a real cabin fan or estimate whole-spacecraft electrical use. The prescribed20°C inlet is a boundary condition, not a solved life-support cooler or crew-comfort prediction.

Figures: [Velocity](cfd-flatpanel/velocity-comparison.png), [air temperature](cfd-flatpanel/temperature-comparison.png), [pressure](cfd-flatpanel/pressure-comparison.png). The maps show a central y≈0.4m plane interpolated from actual cell data, with the solid envelope masked.

## 4. Reproducibility, rejected pilots and next decisions

The archive contains the complete final OpenFOAM dictionaries, meshes, fields, logs, cell CSV exports,3D FEM sources/fields and plots. Re-run build_cfd.py, blockMesh, checkMesh and buoyantBoussinesqSimpleFoam on Intel, then post_cfd.py. Re-run solve_fem.py for the3D panel. Python dependencies are NumPy, SciPy and Matplotlib. Solver iteration count is not physical time.

Two exploratory CFD pilots remain on Intel with their original logs: a tall bluff-body case whose refined steady residuals did not converge, and a10W low-speed flat-panel case with large local air-temperature rise that weakened the constant-property assumption. They are excluded from accepted study results. The final case uses the low-profile envelope and2W residual heat, and all final checks above refer to that case. The rejection record is in verification/pilot-rejections.json.

Next decisions require actual hardware dimensions, power maps, interface stackups, flow hardware, orbital heat loads and thermal limits. Numerical mesh sensitivity is separate from uncertainty in those engineering inputs. The principal-level discussion is how to choose the right local fidelity, quantify the remaining uncertainty and connect submodels after correlation data exist.

## Public method/property references

- [NIST aluminium6061-T6 property fits](https://www.nist.gov/mml/acmd/aluminum-6061-t6-uns-aa96061)
- [NASA material comparison with representative aluminium6061 values](https://ntrs.nasa.gov/api/citations/20130010779/downloads/20130010779.pdf)
- [OpenFOAM standard solvers](https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers)
- [OpenFOAM fixedGradient boundary condition](https://doc.openfoam.com/2312/tools/processing/boundary-conditions/rtm/derived/general/fixedGradient/)

These references support generic methods and representative material ranges. They do not document the selected properties or design of Vast flight hardware.
'''
# Add readable spacing around numerical values in prose without altering stored numeric evidence.
import re
report='\n'.join((re.sub(r'(?<=\d)(?=[A-Za-z])',' ',re.sub(r'(?<=[A-Za-z,])(?=\d)',' ',line)).replace('3 D','3D').replace('1 D','1D') if 'https://' not in line else line) for line in report.split('\n'))
(ROOT/'report.md').write_text(report)
(ROOT/'verification').mkdir(exist_ok=True)
(ROOT/'verification/pilot-rejections.json').write_text(json.dumps({'accepted_case':'cfd-flatpanel 2W residual load','rejected_pilots':[{'remote_path':'/home/falcon-admin/projects/vast-haven-1/stage-02-initial-analysis-r1/local-multiphysics/cfd','reason':'Tall bluff-body refined steady laminar case did not achieve residual-control convergence. No accepted flight conclusions.'},{'remote_path':'/home/falcon-admin/projects/vast-haven-1/stage-02-initial-analysis-r1/local-multiphysics/cfd-flatpanel-10w-pilot','reason':'Low-speed 10W residual yielded a large local temperature rise; final constant-property screening reduced load to2W. Original logs retained remotely.'}]},indent=2))
with (ROOT/'comparison.csv').open('w') as g:
 w=csv.writer(g);w.writerow(['discipline','case','metric','value','units','qualification'])
 for name,key in [('baseline','thermal_baseline'),('improved_contact','thermal_improved_contact')]:w.writerow(['3D thermal',name,'peak_temperature',f[key]['peak_C'],'degC','uncalibrated representative panel'])
 for name,key in [('clamped','structure_clamped'),('sliding','structure_sliding')]:w.writerow(['thermoelastic',name,'p95_von_mises',f[key]['percentile95_von_mises_MPa'],'MPa','no design allowables or flight loads'])
 for name in ['baseline','double_flow','mesh_fine','mesh_finer']:
  for key,unit in [('volume_flow_m3_s','m3/s'),('heater_area_average_C','degC'),('outlet_mass_weighted_C','degC'),('pressure_drop_Pa','Pa')]:w.writerow(['CFD',name,key,c[name][key],unit,'local simplified bay; local hotspot benefit not mesh-qualified'])
print('Saved report.md, summary.json, comparison.csv and pilot rejection record')
