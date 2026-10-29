# Local thermal, thermoelastic and cabin-air screening

This first round demonstrates model setup, energy accounting, spatial fields, contact and support trade studies, and numerical verification. All local geometry, loads, contacts, material values and support conditions are analyst-selected. The representative Haven-1 CAD provides system context. These are simplified local analysis geometries, not manufacturer flight drawings. No manufacturer-specific thermal requirements, physical testing or qualification is claimed.

## 1. Three-dimensional equipment-panel conduction

The model is a 300 × 200 × 6 mm flat aluminium-like mounting panel. A central 150 × 100 mm top patch dissipates 80 W. Two bottom strips, each 50 mm wide, transfer heat to an assumed 20°C coolant boundary through an effective contact/film conductance. Other surfaces are adiabatic. This effective conductance represents a combined interface and coolant-side resistance; it does not model a literal selected thermal pad or a resolved coolant channel.

Inputs: k=167 W/(m K), E=69 GPa, Poisson ratio 0.33, expansion coefficient 23×10⁻⁶/K. These constant isotropic values are representative near room temperature. They have not been measured for Vast hardware.

The custom Python/SciPy solver assembles full 3D linear-tetrahedral conduction matrices and Robin boundary integrals. Baseline effective h=500 W/(m² K) gives a peak 46.589°C. Increasing h to 2000 W/(m² K), with identical heat and sink temperature, lowers it to 40.060°C. The 6.529°C change comes from reduced contact resistance. The remaining spatial gradient comes from finite in-plane conduction distance to the sink strips.

Verification:4608 to 15552 tetrahedra changes the baseline peak by 0.0400°C. Both meshes reject 80 W, with relative energy error below 3×10⁻¹². This is an initial sensitivity check, not full proof of spatial convergence or physical accuracy.

Figure: [Contact conductance comparison](fea/thermal-comparison.png). Raw nodal fields and ParaView-readable tetrahedral VTK files accompany the downloads.

## 2. Thermal expansion and mounting restraint

The same baseline 3D temperature field drives a linear-elastic small-strain thermoelastic solve, with 20°C as the stress-free reference. There are no pressure, launch acceleration, vibration, bolt preload, fatigue, plasticity or buckling loads in this analysis.

The first case fixes all translations on both x-end faces. It gives maximum element von Mises stress 57.25 MPa, 95 th percentile 33.11 MPa and maximum motion 0.0639 mm. The second permits in-plane thermal expansion through an ideal kinematic/sliding constraint: ux=0 on x=0, one origin node fixed in y/z, and a second y-separated node fixed in z to remove rigid rotation. It gives maximum 13.01 MPa, 95 th percentile 8.51 MPa and maximum motion 0.1196 mm.

This isolates a support-condition effect. Freedom to expand reduces thermal restraint stress while requiring more motion accommodation. It does not establish a flight mount design or a minimum panel thickness.

The refined thermal/structural mesh raises the clamp-adjacent maximum to 65.93 MPa, while its 95 th percentile changes only to 33.19 MPa. Therefore the maximum clamp stress is mesh sensitive and must not be used to claim a qualified factor of safety. A uniform 20 K free-expansion patch test reproduces u=αΔTx with relative displacement error 2.62 e-11 and near-zero stress. No experimental correlation has occurred.

Figure: [Restraint comparison](fea/stress-comparison.png). The plotted stress is averaged through thickness and projected onto the panel plane. It is not a recovered surface stress.

## 3. Microgravity forced ventilation CFD

OpenFOAM v 2512 buoyantBoussinesqSimpleFoam solves steady incompressible momentum/pressure and the air energy equation. Gravity is exactly zero, so buoyancy is disabled. This is a pressurized cabin-air case. It is not a vacuum exterior cooling analysis and is not conjugate solid-fluid heat transfer.

The bay is 1.6 ×0.8 ×0.8 m. A 0.4 ×0.4 ×0.04 m low-profile equipment envelope mounts to its floor. Its five exposed surfaces impose 2 W total residual heat to air over 0.224 m². The outer walls are adiabatic. All walls are no-slip. A full-face inlet supplies 20°C air at 0.02 or 0.04 m/s. A zero gauge pressure outlet allows developed outflow. Constant assumed properties are ρ=1.2 kg/m³, cp=1005 J/(kg K), k=0.026 W/(m K), ν=1.5×10⁻⁵m²/s, and Pr=0.695769. The effective laminar model is a screening assumption. Reynolds number based on 0.8 m bay dimension is 1067/2133; transition, grille jets and forced mixing remain unrepresented.

The 2 W air case is an assumed residual load in a low-speed local bay. It is independent of the 80 W conductive panel and independent of the 1D orbital system model. There is no demonstrated common heat ledger or two-way coupling. Most hardware cooling in the concept relies on conduction/coldplates; this residual-air case does not establish total avionics dissipation or full cabin cooling capacity.

On the matching 4536-cell grid, flow doubles from 12.8 to 25.6 L/s. The mass-flow-weighted outlet changes from 20.12956 to 20.06478°C, matching the bulk relation ΔT=Q/(ṁcp). Heated-surface area-average temperature changes 33.496 to 32.465°C. The coarse-cell maximum air temperature changes 36.002 to 34.312°C.

**The small local temperature improvement is not mesh qualified.** Baseline heater mean changes 2.528°C between the first two meshes, larger than the 1.031°C flow benefit on the coarse grid. The fine-to-finer change is 0.387°C. Air-cell maxima also depend on near-wall cell locations. Only the bulk outlet energy trend is robust in this round. Refined matched-grid flow cases are the next gate before claiming local hotspot optimization.

| Baseline mesh | Cells | Heater mean°C | Max air cell°C | Bay pressure drop Pa |
|---|---:|---:|---:|---:|
| baseline | 4, 536 | 33.496 | 36.002 | 0.0001243 |
| mesh_fine | 36, 288 | 30.968 | 37.207 | 0.0001514 |
| mesh_finer | 122, 472 | 30.581 | 38.168 | 0.0001586 |

All four cases pass checkMesh and terminate by SIMPLE residual-control convergence, with final initial equation residuals below 10⁻⁸. Maximum net flow mismatch is 7.45 e-12. Outlet sensible heat recovers the imposed 2 W to within 2.26 e-06 fraction. These are numerical consistency checks; they are not experimental validation.

The reported pressure losses, approximately 0.00012 and 0.00030 Pa on the coarse matching grids, belong only to this short, mostly open bay. The corresponding Δp×Q values are aerodynamic power for this domain alone. They exclude filters, ducts, bends, grilles, return paths, heat exchangers and fan motor/efficiency losses, and must not size a real cabin fan or estimate whole-spacecraft electrical use. The prescribed 20°C inlet is a boundary condition, not a solved life-support cooler or crew-comfort prediction.

Figures: [Velocity](cfd-flatpanel/velocity-comparison.png), [air temperature](cfd-flatpanel/temperature-comparison.png), [pressure](cfd-flatpanel/pressure-comparison.png). The maps show a central y≈0.4 m plane interpolated from actual cell data, with the solid envelope masked.

## 4. Reproducibility, rejected pilots and next decisions

The archive contains the complete final OpenFOAM dictionaries, meshes, fields, logs, cell CSV exports, 3D FEM sources/fields and plots. Re-run build_cfd.py, blockMesh, checkMesh and buoyantBoussinesqSimpleFoam on Intel, then post_cfd.py. Re-run solve_fem.py for the 3D panel. Python dependencies are NumPy, SciPy and Matplotlib. Solver iteration count is not physical time.

Two exploratory CFD pilots remain on Intel with their original logs: a tall bluff-body case whose refined steady residuals did not converge, and a 10 W low-speed flat-panel case with large local air-temperature rise that weakened the constant-property assumption. They are excluded from accepted study results. The final case uses the low-profile envelope and 2 W residual heat, and all final checks above refer to that case. The rejection record is in verification/pilot-rejections.json.

Next decisions require actual hardware dimensions, power maps, interface stackups, flow hardware, orbital heat loads and thermal limits. Numerical mesh sensitivity is separate from uncertainty in those engineering inputs. The principal-level discussion is how to choose the right local fidelity, quantify the remaining uncertainty and connect submodels after correlation data exist.

## Public method/property references

- [NIST aluminium6061-T6 property fits](https://www.nist.gov/mml/acmd/aluminum-6061-t6-uns-aa96061)
- [NASA material comparison with representative aluminium6061 values](https://ntrs.nasa.gov/api/citations/20130010779/downloads/20130010779.pdf)
- [OpenFOAM standard solvers](https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers)
- [OpenFOAM fixedGradient boundary condition](https://doc.openfoam.com/2312/tools/processing/boundary-conditions/rtm/derived/general/fixedGradient/)

These references support generic methods and representative material ranges. They do not document the selected properties or design of Vast flight hardware.
