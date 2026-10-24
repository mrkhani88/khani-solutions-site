# Representative electronics test and correlation plan

Status: **planned / not physically executed**. This document is an execution package, not a laboratory report. No purchased hardware, measured temperature, qualification or flight-readiness claim is made.

## Objective and article

Characterize a representative conduction-cooled telecom/server thermal path, quantify sensor and interface uncertainty, and predict a held-out operating cycle. Use a small low-voltage electrically heated board/plate assembly, not a flight battery, high-power RF transmitter or production Sceye article.

Proposed article: an approximately 240 × 180 × 2 mm representative board matching the Stage 06 assembly, electrically insulated resistive heater blocks at component footprints, a conductive mounting plate, interchangeable documented pad/strap interfaces, thermally defined supports and a removable insulation enclosure. The earlier Stage 03 board was 120 × 80 mm and is a different configuration. Match the retained Stage 06 CAD/thermal model; record every deviation. A reduced coupon needs its own geometry/model and cannot directly validate the larger assembly. Start with a current-limited isolated 24 V DC bench supply, separate heater channels and a total power cap chosen after the assembled article review. The mock heaters reproduce heat input, not processor/RF functionality.

Record article ID, CAD and model hashes, board stack/material data, plate dimensions/mass, heater resistance, interface product/lot/thickness, compression method, bolt torque, contact area, surface finish, harness gauge/length/routing and photographs before each configuration. Select real part limits before authorizing operation. Do not use the simulation's guessed component allowables as laboratory abort ratings.

## Instrumentation and data

The downloadable Sensor-Map.csv defines candidate locations. Use sensors with calibration records at low/mid/high temperatures spanning the intended range. Record channel calibration correction, reference uncertainty, DAQ resolution, cold-junction effects (if thermocouples are used), attachment method and placement repeatability. Use a small bonded contact sensor adjacent to each heater; avoid claiming it measures an inaccessible semiconductor junction. Include plate center/corners, sink/strap, air, radiative shroud and chamber pressure.

Sample synchronized temperature, voltage, current, pressure, chamber/plate commands and discrete enable states at 1 Hz during transients; preserve unfiltered raw samples. Use four-wire power metrology where needed. `P=VI` uses measured terminal voltage/current; quantify lead losses separately. Record exact timestamps and transitions. The empty Test-Data-Template.csv contains only headers; no rows of fabricated measurements are included.

## Environment ladder

| Phase | Environment | Purpose | What it cannot establish |
|---|---|---|---|
| A | Room air, measured ambient, mounting plate controlled/measured | Power accounting, sensor attachment, thermal capacities and gross heat paths | Stratospheric convection or radiative extremes |
| B | Controlled cold/hot chamber at room pressure | Startup/cycling behavior and controller response | Low-pressure heat transfer; a cold chamber wall is not necessarily a known radiative boundary |
| C | Altitude chamber near selected 17 km and 20 km standard-atmosphere pressures, measured gas composition/temperature/flow | Pressure-dependent convection and electrical/component operation | Vacuum conditions, complete HAPS external flow or unknown weather |
| D | Facility-approved low-pressure/radiative-boundary arrangement with measured shroud temperatures/view geometry | Separate radiation from convection; bracket optical/heat-path behavior | Mission reproduction unless absorbed fluxes, orientation and view factors are matched |

Vacuum alone is not a HAPS atmosphere. Chamber-gas temperature, pressure, flow and wall radiation must be logged separately. Solar loading needs a characterized source or equivalent absorbed-power allocation; shroud temperature alone does not duplicate sunlight. Obtain facility approval for low-pressure electrical operation and pressure equalization of enclosed volumes. No improvised pressure/vacuum vessel is specified.

## Test sequence

1. Review hardware limits, instrumentation, electrical protection and chamber procedures; approve a conservative abort envelope below selected part/adhesive limits. Record reviewer names/date; blank fields are not approvals.
2. Perform sensor comparison and zero-load equilibrium check. Verify power-channel polarity and independent overtemperature shutdown.
3. Run a low-power pulse to estimate capacities and wiring heat leaks; inspect residuals before raising power.
4. Execute the calibration pulse/multilevel sequence in Test-Matrix.csv. Preserve boundary-condition and raw power histories, including controller limits.
5. Freeze fitted parameters and model/source hashes. Run the held-out duty cycle, changed base temperature and changed pressure without retuning.
6. Repeat nominal assembly and selected interface reassembly to measure repeatability. Compare a degraded interface intentionally and reversibly; do not damage an article to create a fault.
7. Run cold startup and permitted fault injections only after the preceding checks. A sensor open/bias can be emulated electronically/software-side without disabling the independent trip.
8. Review deviations, aborts, failed requirements and corrective actions; rerun only after documenting a new configuration identity.

## Correlation and uncertainty

Fit only a small identifiable parameter set (for example component-to-plate conductance and effective capacity). Do not fit every heat path from one temperature trace. Use several sensor locations and power levels to distinguish capacity from conductance. Known measured boundary conditions are inputs, not free fitting knobs. Fit and report sensor bias separately from thermal resistance if independently calibrated.

Proposed **study acceptance objectives**, chosen for this exercise and not imposed by a standard: per-sensor held-out RMSE ≤2 K, maximum absolute error ≤5 K, equilibrium component-to-plate rise error ≤10% for rises ≥10 K, and warm-up/acquisition-time error ≤10% when acquisition is identifiable. Also inspect signed residuals, sensor-to-sensor gradients, transient shape and energy residuals. Passing a mean RMSE alone does not establish local validity or safe margins. For small temperature rises use absolute error/uncertainty instead of an unstable percentage.

Uncertainty-Budget.csv is an illustrative allocation, not an instrument certificate. Combine independent standard-uncertainty terms by root-sum-square, propagate correlated terms explicitly, and report coverage factor and assumptions. Sensor placement and contact variation can dominate nominal DAQ accuracy. The NIST guidance supports uncertainty terminology and combination, not the example numerical allocations: [NIST TN 1297](https://www.nist.gov/pml/nist-technical-note-1297).

The supplied synthetic calibration/held-out demonstration exercises the workflow with generated data. It does not replace independent measurements, establish real heat-path values, or close the physical-test job requirement.

## Data release and closure

Retain raw data read-only with SHA-256 hashes, unedited event log, calibration certificates, article photographs, source/CAD identity, environment history, processed data, fitting script, parameter covariance/identifiability assessment, held-out residuals, deviations and review disposition. Replace empty templates with real identified records. The physical gap closes only after the article is built, the approved tests are executed and the measured-data report is reviewed.
