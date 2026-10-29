# Haven-1 thermal engineering: first analysis round

Independent public-reference interview demonstration by Mohammadreza Khani, PhD. All quantitative results below belong to assumed engineering models. They do not predict or qualify actual Haven-1 hardware.

## 1. Evidence and geometry

The original 221-part FreeCAD/Blender assembly uses public exterior anchors and representative internal equipment envelopes. The assembly movie positions all 221 parts in 56 batches, four at a time except the last batch. Names appear above the model and fade after installation. Enclosure and insulation surfaces stay transparent. The video is a CAD presentation, not a manufacturing sequence or physics result.

The public vehicle reference is [Vast Haven-1](https://www.vastspace.com/haven-1). The component evidence register and 25-row thermal-coverage matrix accompany the native CAD package. Published crew, volume, power and geometry values do not establish internal heat loads, materials, interfaces, duty cycles, hardware temperatures or installation details.

## 2. Three independent initial models

The 1D orbital model, 80 W solid panel, and 2 W internal-air bay are separate first-round models. Their loads and boundary conditions have not been reconciled into a common vehicle heat budget. No CFD heat-transfer field has been mapped into the 1D network. Within the local solid model, the solved temperature field does feed the thermoelastic calculation.

### Integrated system thermal model

OpenModelica 1.27.1/DASSL on Intel solves 13 thermal nodes plus electrical storage and energy ledgers over 24 hours. Time zero is assumed sunrise, with every node initially at 20 °C. The assumed illumination is 60 minutes sunlight and 30 minutes eclipse per 90-minute orbit. There is no propagated ephemeris, geometry-resolved shadow model or albedo in this round.

At full duty, assigned electrical loads are 600 W avionics, 800 W payload, 180 W power conversion, 450 W life support, 120 W CMGs, 60 W coolant pump and 100 W fans. Crew adds 480 W of metabolic heat. The assumed battery stores 15 kWh and begins at 80% SOC. Charge and discharge efficiencies are each 95%. Available nominal sunlight PV is 9 kW, distinct from the public peak capability.

Two matched full-duty cases use 6 and 10 m² radiators. Peak temperatures over the 24-hour run are:

| Case | Avionics °C | Battery °C | Payload °C | Cabin °C |
|---|---:|---:|---:|---:|
| 6 m² fixed radiator | 69.79 | 59.46 | 72.63 | 52.74 |
| 10 m² fixed radiator | 45.73 | 35.55 | 48.56 | 30.06 |

Increasing area improves the modeled heat sink, but the 10 m² case still misses the assumed battery upper target of 35 °C, payload target of 40 °C and cabin target of 27 °C in the final orbit. Those are study targets, not manufacturer qualification limits. Further hot-case improvement remains necessary.

A separate matched cold sensitivity applies 50% equipment duty and 80% absorbed environment/PV availability, giving 7.2 kW sunlight PV. Fixed cooling uses 8.96684 kWh of heater energy and still misses the battery, cabin and coolant lower targets. Proposed coolant-to-radiator conductance modulation uses zero heater energy in this particular model and meets all nine assigned limits over its final orbit. This is idealized algebraic conductance modulation, not a resolved pump, valve, delay or hydraulic model. It does not prove that a flight vehicle can remove all heaters.

The nominal 10-second versus 5-second maximum-step check changes temperatures by at most 0.000223 K. Integrated ODE energy-ledger closure is a wiring/integration check. An independent trapezoidal check retains both sides of forcing events and has a whole-energy residual of 0.018453 kWh at 10 seconds and 0.004624 kWh at 5 seconds. These separate numerical checks do not establish physical accuracy. The 24-hour runs include initial transients and are not a proof of indefinitely periodic behavior.

Full source and inputs: [system thermal report](analysis/system-thermal/report.md), `analysis/system-thermal/inputs.json`, `source/Haven1Thermal.mo`, native run scripts, five CSV cases, event rows and Intel verification receipt.

### Local 3D thermal and thermoelastic model

A custom reproducible NumPy/SciPy linear-tetrahedral FEM models an assumed 300 × 200 × 6 mm aluminium-like mounting panel with an 80 W heat patch. Two underside cooling/contact strips connect to a 20 °C sink through effective coefficients of 500 or 2,000 W/(m² K). These are combined thermal-interface/cooling assumptions, not measured TIM properties.

Improving that effective coefficient lowers the calculated peak from 46.59 to 40.06 °C. A 4,608-to-15,552-tetrahedron refinement changes the baseline peak by 0.040 °C. The FEM closes its steady heat balance and passes a uniform thermal-expansion patch test.

With the identical baseline temperature field, ideal both-end clamps produce a P95 element von Mises stress of 33.115 MPa. Kinematic/sliding restraints reduce it to 8.509 MPa while allowing maximum movement to increase from 0.064 to 0.120 mm. The corresponding finer-mesh P95 values are 33.192 and 8.240 MPa. Clamp-adjacent maximum stress is mesh sensitive. Plotted stress contours are through-thickness averages, while annotated maxima are element maxima. No stress allowable, safety factor, minimum thickness, pressure hull, launch load, fatigue, fastener or qualification result is established.

### Local internal-flow CFD

OpenFOAM v2512 solves steady laminar momentum, pressure and air energy in an assumed 1.6 × 0.8 × 0.8 m bay containing a low-profile equipment envelope. Gravity is zero and inlet air is 20 °C. A 2 W residual heat flux enters the air after a hypothetical dominant conductive cooling path. This is a prescribed surface-flux model, not conjugate solid/fluid heat transfer.

Matched coarse-grid cases increase flow from 12.8 to 25.6 L/s. The flux-weighted outlet rise halves from 0.12956 to 0.06478 °C. This agrees with the bulk energy balance. The coarse-grid heated-surface mean falls by 1.031 °C, but the baseline coarse-to-fine mesh change is 2.528 °C. Fine-to-finer change is 0.387 °C. Therefore the local hotspot benefit is not yet mesh qualified. The maximum air-cell temperature also changes with refinement and is not accepted as a converged peak.

The three baseline grids contain 4,536, 36,288 and 122,472 cells. The doubled-flow case uses the matching coarse grid. All four accepted cases converge under the declared SIMPLE criteria and pass `checkMesh`. Worst mass imbalance is below 7.45 × 10⁻¹² fraction and worst outlet heat imbalance below 2.26 × 10⁻⁶ fraction. These global balances do not establish local spatial accuracy.

The calculated pressure loss and ΔpQ cover only this short bay. They exclude filters, ductwork, bends, grilles, fan efficiency and motor losses, so they cannot size the station fan or predict its electrical demand. Rejected pilot geometries/loads and their reasons remain recorded separately.

Full local methods, properties, restraints, cases and limitations: [local multiphysics report](analysis/local-multiphysics/report.md). Native input meshes, final fields and logs are in its complete solver archive.

## 3. Interview evidence and remaining gates

The website links each engineering capability to a model, result or an explicit open gate. [Vast's public Staff Thermal Engineer posting](https://job-boards.greenhouse.io/vast/jobs/4690307006) provides a reference for this mapping. It is not confirmation of the user's exact Principal Engineer requisition.

Demonstrated here: public-reference CAD decomposition, system thermal and electrical bookkeeping, radiator/control trades, local solid conduction, thermal-strain response, internal-flow CFD, numerical checks, evidence tracking and technical communication. This open-source workflow does not demonstrate expertise in Thermal Desktop or substitute for its use when a role requires it.

There have been zero physical tests in this study. Manufacturer requirements, selected parts, measured heat loads, material/optical/interface characterization, sensor uncertainty, calibrated test data, TVAC execution, correlation and flight acceptance remain open.

## 4. Recommended next investigations

1. Close the remaining hot-case battery, payload and cabin targets with controlled radiator/interface/heat-load trades while retaining cold-case bypass control.
2. Establish a common subsystem heat budget and map the appropriate local interfaces back into the system model.
3. Replace algebraic coolant conductance with a pressure-drop/flow network, pump curves, branch balancing, valve dynamics and pump-out cases.
4. Run matched refined CFD cases before claiming a local ventilation optimization. Then add realistic inlet/return locations, obstructions and fan curves.
5. Replace ideal structural restraints with real brackets, contacts, bolts and preload. Add launch/modal/vibration and fatigue load cases as applicable.
6. Plan measured thermal balance and cycling tests with calibrated sensors, uncertainty, fit parameters and independent validation runs. Vacuum-exposed hardware and the pressurized cabin need different test boundaries.

The first analysis round is complete. These next investigations are future stages, not completed results.
