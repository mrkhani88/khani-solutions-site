# Haven-1 representative integrated thermal model: first analysis round

## Scope and evidence boundary

This independently constructed study demonstrates thermal-model architecture, coupled energy accounting, design trades and numerical verification. The CAD is a public-reference reconstruction. All unpublished numerical engineering inputs are analyst assumptions. These results do not predict actual Haven-1 performance, reproduce Vast's flight design or establish qualification.

Thirteen named thermal components represent avionics, battery, payload, power conversion, ECLSS, cabin, wall/MLI, cold plate, coolant, radiator, control-moment gyros, solar arrays and tank resources. The native Modelica model includes these named subcomponents, plus electrical storage, heater control, pump/fan heat and an energy ledger. The CAD mapping is an aggregation map, not automatic thermal meshing or a calibrated contact network.

## Inputs defined before solving

The full inputs and provenance appear in `inputs.json` and `input-table.csv`.

| Input | Study value | Status |
|---|---|---|
| Duration | 24 h | Assumed first transient |
| Orbit cycle | 90 min: 60 min sun, 30 min eclipse | Representative illumination, no propagated trajectory |
| Time zero | Sunrise, all nodes initially 20 °C | Assumed |
| Solar flux | 1361 W/m² | Generic NASA reference |
| Earth IR | 241 W/m² | Generic NASA reference, constant effective views |
| Deep-space sink | 3 K | Reference assumption |
| Radiator | 6 or 10 m², emissivity 0.88, absorptivity 0.12 | Assumed effective emitting area and optics |
| Radiator views | Solar projected fraction 0.08, Earth view 0.35 | Assumed |
| Wall/MLI | 110 m², effective IR emissivity 0.03 | Assumed blanket-level behavior |
| Solar array | 66 m² projected, 132 m² radiating | Assumed areas |
| Available solar electrical power | 9 kW in sunlight | Assumed derating from public 13.2 kW peak reference |
| Battery | 15 kWh, initial SOC 80%, 95% charge and discharge efficiencies | Assumed |
| Avionics / payload / ECLSS | 600 / 800 / 450 W | Assumed full-duty heat |
| CMGs / pump / fan / conversion loss | 120 / 60 / 100 / 180 W | Assumed full-duty heat |
| Crew | 4 × 120 W | Assumed sensible-equivalent load, no humidity model |
| Battery heater | 10 °C setpoint, 80 W/K proportional gain, 300 W cap | Assumed controller |
| Resource heater | 5 °C, 30 W/K, 100 W cap | Assumed controller |
| Coolant heater | 8 °C, 100 W/K, 600 W cap | Assumed controller |

The public reference describes twelve solar wings, 13.2 kW peak generation, four crew, and eight MLE slots with 100 W continuous power per slot. Applying all eight payload slots at 100 W is a study load case, not a measured operating heat map. Node capacitances and pair conductances remain explicit assumptions in the input table.

## Equations and energy accounting

Each node satisfies:

`C_i × dT_i/dt = Q_i + Σ G_ij × (T_j − T_i)`

A symmetric conductance matrix makes internal heat transfer conservative. A separate paired link transfers heat between coolant and radiator. Absorbed sunlight is `alpha × projected_area × solar_flux × sunlight`; absorbed Earth IR is `epsilon × area × Earth_view × 241`; emission is `epsilon × area × sigma × (T^4 − T_space^4)`.

The same sun/eclipse clock drives thermal inputs and solar generation. Actual converted PV leaves the array's thermal balance and enters the electrical ledger. Curtailed conversion remains array heat. Electrical loads become heat once, in the assigned equipment node. Battery charge/discharge losses enter the battery node. Battery energy changes by charge power minus discharge power. Adding electrical storage to thermal storage gives an explicit whole-system energy balance.

Exterior transfer uses radiation and conduction. Ambient-air convection is not applied in orbital vacuum. Coolant conductance is an equivalent thermal link, not a hydraulic pump/valve simulation.

## Cases and comparisons

| Case ID | Description | Isolated comparison |
|---|---|---|
| `baseline` | 6 m² fixed radiator, full duty, nominal environment | Reference |
| `larger_radiator` | 10 m², otherwise identical | Radiator area only |
| `cold_fixed` | 10 m², non-crew equipment duty 50%, environmental flux/PV availability 80% | Cold sensitivity reference |
| `cold_bypass` | Same cold inputs, modulated coolant/radiator conductance | Control only |
| `resolution_check` | 10 m² nominal case with 5 s rather than 10 s maximum step | Numerical sensitivity |

The area comparison holds radiator capacitance at 70 kJ/K to isolate area. A real panel-size trade must update mass, capacitance, piping and view factors. The cold condition is a deliberately stylized sensitivity, not a predicted mission orbit. Its two cases have matched inputs, so their difference isolates bypass control.

The proposed bypass proxy ramps equivalent conductance from 10 W/K at/below 14 °C coolant to 600 W/K at/above 22 °C. It represents a candidate strategy, not confirmed Haven-1 hardware or a selected valve.

## Results and remaining requirements

Values below are maxima during the first 24 hours, including the 20 °C initial condition.

| Case | Avionics °C | Battery °C | Payload °C | Cabin °C | Heater energy kWh | Peak heater W |
|---|---:|---:|---:|---:|---:|---:|
| 6 m² fixed | 69.79 | 59.45 | 72.63 | 52.74 | 0 | 0 |
| 10 m² fixed | 45.73 | 35.55 | 48.56 | 30.06 | 0 | 0 |
| Cold, fixed | 24.79 | 24.72 | 26.47 | 21.24 | 8.967 | 466.1 |
| Cold, bypass | 26.87 | 25.32 | 28.35 | 21.58 | 0 | 0 |

Assumed study bands are avionics 0–55 °C, battery 10–35 °C, payload 10–40 °C, cabin 18–27 °C, coolant 8–35 °C, ECLSS 5–50 °C, power conversion/CMGs 0–55 °C and tank resources 5–40 °C. These are demonstration requirements, not Vast limits or human-rating requirements.

The 6 m² baseline exceeds many assigned limits. Increasing area lowers radiator, coolant, cold-plate and equipment temperatures, but the 10 m² case still exceeds the assumed battery, payload and cabin upper limits. This remains an identified design gap.

In the cold sensitivity, fixed cooling rejects too much heat at low equipment duty. Heater consumption rises while battery, cabin and coolant still miss their lower bands. The P-only heater has a steady offset below setpoint. Modulating radiator coupling retains equipment heat and meets all nine assigned bands in the final orbit, with zero heater energy for this particular assumed case. That does not justify removing survival heaters.

Nominal SOC cycles near 91.9–100% after charging, with the global minimum of 80% at initialization. The assumed solar source comfortably supports the assumed load. This is not a certified power budget or a complete fourteen-day mission analysis.

## Verification

All five OpenModelica DASSL runs reached 86,400 s at tolerance 1e-7. The 10 s versus 5 s maximum-step comparison changes the worst temperature trajectory by 0.000223 K, in the solar-array node.

The integrated whole-system energy ledger closes within 4.2e-6 J. This is primarily a wiring and integration consistency check, not independent physical validation. A separate trapezoidal integration of exported powers preserves BOTH native pre-event and post-event rows at duplicate timestamps. Its nominal 10 m² residual is +0.018453 kWh at 10 s output and +0.004624 kWh at 5 s output. The approximately fourfold decrease is consistent with finite-output quadrature convergence. The residuals and event-row exports are retained in `summary.json` and `data/*-event-rows.csv`.

A deduplicated timeline is suitable for plotting continuous temperatures, but it drops one side of power discontinuities and must not be used for independent energy quadrature. This distinction is implemented in `source/postprocess.py`.

The wall/resource assembly is still settling. The last two orbit-end states differ by about 0.376 K in the baseline, 0.096 K in the nominal 10 m² case, and 0.063 K in the bypass case. These are first-day transient results, not asserted periodic steady states.

## Limits and next work

Missing fidelity includes albedo, propagated attitude/shadows, detailed view factors, coating aging, contact calibration, coolant pressure losses, realistic sensor/valve dynamics, humidity/condensation, visiting-vehicle coupling, launch/reentry and physical test correlation. The radiator location, area and all numerical loads are assumed. Display-shell thickness is not a structural design input.

Next decisions are to feed local 3D cold-plate/contact results into the 1D conductances, close the nominal battery/payload/cabin gaps, add realistic radiator mass and optics sensitivity, then introduce hydraulic flow/control dynamics and heater/sensor fault cases. Thermal-vacuum and cold-plate bench tests need instrument locations, uncertainty budgets and correlation criteria before any validation claim.

## Reproduction and files

`source/Haven1Thermal.mo` is the native Modelica model with thirteen named components. `source/run.mos` runs all five cases. `source/build_model.py` generates the model and inputs. `source/postprocess.py` creates figures, tables and exact selected-column exports. Delivered `data/<case>.csv` temperatures T[1] through T[13] are Kelvin, power is W, and energy is J. The website/deck display °C and kWh. Full native CSVs remain on Intel.

The run used Intel via `falcon-intel`, with OMP threads limited to four and OpenBLAS to one. Other jobs were preserved. Native OMEdit uses named capacitance subcomponents; their equation coupling is defined in the model, rather than implied by decorative connecting lines.

## References

- [Vast Haven-1](https://www.vastspace.com/haven-1): public vehicle and peak-power anchors.
- [Vast Haven-1 Lab](https://www.vastspace.com/haven-1-lab): payload-slot power reference.
- [NASA thermal control](https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/): energy-balance method, radiation, coatings, MLI and heaters.
- [NASA solar irradiance science](https://earth.gsfc.nasa.gov/climate/projects/solar-irradiance/science): 1361 W/m² reference.
- [NASA orbital heating guideline](https://extapps.ksc.nasa.gov/reliability/Documents/Preferred_Practices/2301.pdf): solar, Earth IR and albedo context.
