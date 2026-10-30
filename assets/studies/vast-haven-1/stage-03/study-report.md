# Haven-1 integrated thermal-control demonstrator

Independent public-reference interview study. All unpublished design values and limits are analyst assumptions. Not manufacturer CAD, flight-performance prediction or qualification. Physical tests: **zero**.

## Completed calculations

- Intel: OpenModelica nine24h DASSL cases; thirteen thermal nodes, electrical storage, steady pump/loop pressure balance, heater/bypass control,20s sensor lag and latched payload shedding.
- Intel: OpenFOAM v2512 five accepted laminar water-channel cases:0.5,1,2L/min on5760cells;1and2L/min on46080cells. All residual-control converged and checkMesh passes. One incorrectly copied high-flow pilot is quarantined on Intel and excluded.
- Intel: CalculiX2.21 thermal and thermoelastic analyses.600W spreader, baseline/interface-only/improved/refined variants. Original SI inputs/FRD preserved.
- Intel FreeCAD1.1.4:14geometric objects, native thermal/structural results imported with viewer unit conversion;21document objects verified on fresh reopen.
- SciPy: proposed TVAC hot/cold pretest prediction. No synthetic measurement or calibration claim.

## Shared inputs and model coupling

Station assumptions:600W avionics,800W payload,180W conversion,450W ECLSS,120W CMGs,100W fans,480W crew except unoccupied cold startup. Representative60min sunlight/30min eclipse, t=0sunrise,24h initial transient.9kW available solar;15kWh battery. External radiation includes constant EarthIR and assumed solar/views; albedo and propagated attitude absent. No indefinitely periodic or full mission proof.

The selected avionics subsystem is represented as a300x200x6mm Al-like spreader with600W on a150x100mm patch. Packaging PCB/device solids are context, not detailed ECAD junction analysis. Twelve identical300x8x2mm channels receive50W each. CFD is prescribed wall flux, not conjugate CHT. Waterrho1000,cp4180,k0.6,nu1e-6; constant properties andg=0. No boiling/freezing model. Manifolds, maldistribution and bends unresolved.

CFD mean wall-to-inlet resistance plus a homogenized TIM is applied over the solid bottom via an equivalent film boundary. The FEM volume-weighted mean adds spreading resistance. This bulk reduction replaces the previous avionics-to-coldplate link with an avionics-to-coolant path; heat is not double counted. CFD map limited0.5–2L/min; fault minimum approximately1L/min. Local steady full-power hotspot envelopes are distinct from transient bulk-node temperatures.

Hydraulics solves quadratic pump and loop pressure equality with CFD channel loss, then pump electrical power=delta_p*volume_flow/0.35+5W. Pump shutoff70kPa at reference speed and remaining-loop35kPa at8L/min are assumptions, not purchased pump/valve data. There is no pump-inertia/valve-actuator model.

## Results

| Case | Avionics max °C | Battery max °C | Payload max °C | Cabin max °C | Heater kWh | Pump kWh |
|---|---:|---:|---:|---:|---:|---:|
|baseline|54.810|33.875|46.809|30.347|0.0000|0.4402|
|improved|35.917|26.622|39.230|22.944|0.0000|0.7455|
|cold_fixed|23.031|23.855|25.357|21.121|17.6791|0.7455|
|cold_bypass|25.023|25.011|27.190|21.454|0.0000|0.7455|
|cold_start|23.921|19.112|25.486|15.145|0.0916|0.7455|
|flow_fault|41.696|27.836|40.652|24.382|0.0000|0.4719|
|flow_protected|41.314|26.809|39.515|23.931|0.0000|0.4719|
|power_uncertainty|38.413|27.871|42.040|23.729|0.0000|0.7455|
|refined_time|35.917|26.622|39.230|22.944|0.0000|0.7455|

Bulk study bands:avionics0–55,battery10–35,payload10–40,cabin18–27°C. An additional85°Csteady spreader-hotspot development limit is assumed, not a device junction rating. Nominal improved first-day histories meet the four bulk bands. Baseline payload/cabin fail. The+10%equipment-load case fails payload; robust margin remains unresolved.

Baseline10m²radiator/1L/minavionicsbranch/TIM0.020K/W; improved16m²/2L/min/0.005K/W plus bypass. Radiator effective thermal capacity scales70to112kJ/K. Equivalent added Al capacitance mass46.7kg atcp900is illustrative, not a selected radiator mass/BOM. Total loop approximately8to10L/min.

Cold fixed/bypass cases hold50%equipment and80%absorbed environment/PV identical. Zero heater energy applies only to that bypass case; backup heaters remain. Unoccupied5°Ccold startup removes crew heat and uses20s sensors. Cabin does not attain occupied18°Cband, so a separate crew-entry readiness/warmup gate is required. It is not an occupied cold-start pass.

50%pump-speed fault at12h approximately halves flow. Without protection payload exceeds40°C; a20s sensor reaching39.5°C latches15%payload shedding, lowering both electrical demand and payload heat. No autonomous fault detection or flight software validation is implied.

## FEM / mechanical interpretation

At20°Ccoolant, spreader peak91.2807°Cbaseline;79.1108°Cinterface-only sameflow;71.3156°Cimproved higherflow. Refined peak71.2412°C. Reaction heat approximately600W in everycase. Assumedk167,E69GPa,nu0.33,alpha23e-6/K,stressfree20°C. Both-endclamped versus kinematic support:95th-percentile extrapolated nodal stress58.34vs26.53MPa; maximum movement0.0895vs0.1642mm. Clamped maximum72.55to83.05MPa on refinement is mesh-sensitive. No pressure/launch/vibration/bolts/preload/friction/fatigue/allowables or minimum thickness claim.

## Verification

```json
{
  "time_step_max_delta_K": 4.811172635754701e-05,
  "physical_tests": 0,
  "CFD_mesh_wall_delta_K": 0.279921165,
  "CFD_mesh_pressure_change_percent": 4.483966692728791,
  "improved_quadrature_residual_kWh": 0.018486587116213826,
  "refined_time_quadrature_residual_kWh": 0.004631627998871522,
  "FEM_peak_mesh_delta_K": 0.0744,
  "high_flow_refined_wall_C": 38.51919070300005,
  "high_flow_refined_dp_Pa": 197.533323645,
  "high_flow_refined_wall_delta_K": 0.21218769800005077,
  "high_flow_refined_pressure_delta_percent": 4.999982839624817,
  "high_flow_converged": true
}
```

ODE energy ledger is an identity/integration consistency check, not physical accuracy. Independent quadrature retains both event-time rows. Small heat/mass closure does not validate materials/contacts, view factors or hardware limits. Spatial checks are initial two-grid checks, not formal asymptotic convergence.

## TVAC and hardware work remaining

See[tvac/Test_Plan.md](tvac/Test_Plan.md)for article, chamber/fixture, instrumentation, functional tests, stability and proposed correlation gates. Test temperatures/levels/cycle counts require program/facility tailoring. Calibrate bounded parameters on selected actual cases, freeze and predict held-out conditions. No test execution, actual correlation, approved drawings, vendor quotes, human-rating or flight qualification is claimed.

## Job requirement evidence

| Responsibility | Evidence | Status / decision |
|---|---|---|
|Thermal requirements|system-summary.json; assumptions in integration.json|Four bulk bands plus local hotspot development target; power uncertainty open|
|Active/passive architecture|system/source/Haven1Thermal.mo;plots/architecture.png|Pumped loop,radiation,bypass,heaters andTIM; heatpipes not separately designed|
|Thermal analysis and optimization|plots/mission.png;plots/comparison.png;fem/summary.json|Baseline and improved candidates; power/mass trade declared|
|Fluid CFD|plots/cfd.png;plots/cfd-field.png;cfd-summary.json|Coldplatechannel performance map and mesh checks|
|Multidisciplinary integration|cad/Haven1_Avionics_Cooling.FCStd;plots/stress.png|Thermal growth,motion,interfaces; real joints/flight loads unresolved|
|Drawings and manufacturing review|source/build_cad.FCMacro; interface dimensions|Review checklist prepared in notes; no approved manufacturing drawing|
|SubsystemTVAC|tvac/Test_Plan.md;tvac/predictions.json|Pretest analysis/plan prepared; no chamber run|
|Documentation and review|presentation/Speaker_Notes.md; data;verification|Reproducible source, assumptions and numerical evidence delivered|
|Cost/schedule impacts|Larger radiator, higher pump demand, TIM/preload decisions in slide8notes|Vendor quotes and production schedule unresolved; no invented costs|
|Lifecycle/operations|Coldstartup,fault,shedding cases and planned validation|Production,integration,launch,actual operations not demonstrated by simulation|
|ThermalDesktopandTVAC experience|Open-source tools and test-ready plan|Does not establish specific-tool mastery or extensive executed TVAC experience|

## Files and rerun

source/build_cooling.py builds the firstfourCFDcases;source/refine_high.py plus high/0/U copied to high_refined/0/U creates the fifth. Run blockMesh,checkMesh,buoyantBoussinesqSimpleFoam after sourcingOpenFOAM. source/post_cooling.py extracts maps. source/fem.py invokesccx;source/system.py creates nativeModelica; runomc source/run.mos in system/. source/results.py thenfinal_results.py create exports and plots. source/test_plan.py creates TVAC predictions and FreeCAD unit-viewer derivatives. Runbuild_cad.FCMacro thenverify_cad.FCMacro with FreeCAD. Native full system CSV/compiled binaries remain onIntel; selected-column CSVs are indata/.

Full accepted input/field/log archive retains reproduction evidence. Rejected pilot stays onIntel underverification/rejected-refinement-wrong-inlet and is excluded. Sources:VastpublicHaven-1andStaffThermalEngineerposting;NASAthermalcontrol/TVAC;ESAthermaltesting. This study usesno confidential Vastdata.

## Critical validity gate: freezing
The local CFD uses liquid water at20°C. Improved nominal coolant bulk remainsabove15.69°C, but radiator metal reaches−5.62°C. Cold bypass coolant remainsabove14.29°Cwhile radiator metal reaches−34.90°C; cold-start radiator metal reaches−52.29°C. A metal-node temperature is not a resolved fluid temperature, and external fluid is not modeled separately. Freeze-safe radiator plumbing/fluid selection or a separate external loop remains unresolved. Do not claim the water-containing radiator is freeze-safe. The cold-fixed bulk coolant reaches−8.97°C: this violates liquid-water assumptions, so its17.68kWhheater result is a no-phase-change mathematical sensitivity, not physical heater sizing or qualified performance. No latent heat, freeze damage or ice blockage is simulated.
