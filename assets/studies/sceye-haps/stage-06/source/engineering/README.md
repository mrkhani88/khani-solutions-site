# Representative HAPS telecom / edge-server thermal engineering

This is independent public-reference portfolio work. SceyeCELL telecom functions and an onboard server/mobile core have public mission evidence. Five internal equipment blocks, geometry, materials, capacities, efficiencies, dissipation schedules, limits and interfaces are study assumptions. They are not recovered Sceye hardware or supplier qualification data.

## What is integrated

The native OpenModelica mission contains 28 thermal states. It preserves the Stage05 Avionics, Battery, Propulsion, HullSolar, Structure and PowerManager class equations. It replaces the original three-node generic payload with RF TX, beamforming, baseband, edge server, DC supply, plate and radiator. Full power input includes emitted RF energy, retained device heat and conversion losses. Heat through the mount and reciprocal hull-radiation port remains in the first-law balance.

RF electrical power before mode factors is 300+200*day+200*midday_window W. Beamforming is50+30*day+20*window W; baseband60+40*day W; server120+100*day+80*window W. Standby loads are5/5/5/10 W. Payload supply efficiency is94%; RF export is35% of transmitter input above5 W. These are illustrative functional budgets, not telecom performance predictions.

Full-load duty profiles are prescribed. There is no link-budget/throughput/RF propagation calculation. "Full workload available" requires a workload fraction of1 plus selected temperature/SOC conditions; it does not prove measured communication availability.

## Spatial model and reduction

`conduction.py` solves an orthogonal 3D finite-volume conduction network, not the earlier Stage03 brick FEM and not CFD. A240x180x2mm homogeneous PCB has kx=ky20W/mK. Five package-case terminals are isothermal over footprints. A distributed bottom pad terminates at prescribed plate temperature. Other spatial faces are adiabatic. There is no junction-to-case or actual ECAD trace model.

Ordinary board kz=.69W/mK /0.5mm k3 pad is compared with a target effective kz10 /0.25mm k6 interface. Effective kz10 represents a proposed via/thermal-path architecture, not a measured bulk FR4 property. Actual via layout, electrical clearances and manufacturing feasibility are not designed here. A rough copper-volume estimate and panel/pad mass changes are reported separately from the thermal solution.

Five independent unit loads generate the terminal resistance matrix. Its inverse provides conservative terminal-to-plate and inter-terminal conductances. Fine-grid conductances return to the mission model. Package capacities and partitioned board capacity produce an approximate dynamic network. `transient_reduction.py` compares that approximation with the full4800-cell transient network under matched sources, capacities and plate boundary: maximum terminal difference is about0.43K. This is reduction verification, not physical correlation and not a bound on omitted pad/via heat capacities.

Spatial grids are600,4800 and38400 cells. The selected improved path changes maximum resistance by about1.62% from4800 to38400 cells; the ordinary-board failure screen changes about4.10% and does not meet the3% refinement screen. The ordinary-board large raw temperature is outside a chosen125°C linear-property-domain guard and must not be treated as credible hardware temperature. The operating screen−10..70°C is independently selected and is not an OEM limit.

## Selected trade and boundaries

The inherited15W/K radiator link bottlenecks the more detailed payload. Improving the PCB alone is inadequate. The selected candidate uses a short/direct effective60W/K radiator attachment, a4.5m² panel and continuously modulated radiator isolation. This is a thermal design target; the attachment mechanism and panel construction are not selected/qualified production hardware. A4m² compact design is retained as a trade.

Radiator capacity scales from8000J/K at3.12m². At assumed cp900J/kgK, increasing to4.5m² adds approximately3.93kg of panel. This excludes unspecified attachment changes and is not total airship mass. Changes in effective board/pad heat capacity are omitted in this controlled path comparison; their actual values require hardware design/data. Buoyancy, full mass closure and aerodynamics are not solved.

The nominal20km environment, radiative properties, weather and mission profiles are inherited assumptions. The17km case changes pressure to8790Pa while holding temperature/radiation/wind fixed, isolating density/convection sensitivity; it is not a replay of ST1. Hot/cold equilibrium cases use a separately powered payload-only harness with prescribed mount/hull temperatures. They are not indefinitely powered full flights.

## Controls and faults

Payload heater sensing is a30s first-order response, delivered heater power a5s response, and hardware capacity240W. The selected cold-start case starts only the new payload cases/plate at−40°C; the radiator and rest of vehicle keep their declared initial states. It is not an all-vehicle equilibrium soak.

Readiness requires all five **true simulated case temperatures** to exceed−5°C. This ideal truth-state gate would require validated distributed sensors or an observer in hardware; a biased single heater sensor is not proven fault tolerant. Service flag requires true cases within−10..70°C and SOC>20%. It flags unavailability without imposing a high-temperature power trip.

Optional thermal derating starts at60°C and reaches40% variable workload at66°C. It scales all variable payload loads above standby, not just the server. A separate reserve demonstration reduces workload when SOC<65%; this is an illustrative policy, not required mission behavior. Sensor+10K bias, failed-open heater, heater stuck on and damaged thermal interface are deliberately retained failure/degraded examples.

## Reproduction on Intel

Engineering runs used the existing OpenModelica1.27.1 / Modelica4.1.0 installation, Python3.14.4, NumPy2.3.5, SciPy1.16.3 and FreeCAD1.1.4. No installation or existing solver interruption is required. Use one numerical thread; native compiler uses two compilation processes.

From the downloaded Stage06 root on a suitable engineering machine:

```sh
mkdir -p results/engineering verification/engineering/native cad
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 source/engineering/conduction.py
python3 source/engineering/build_model.py
cd verification/engineering/native
omc ../../../source/engineering/compile.mos
cd ../../..
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 source/engineering/run_cases.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 source/engineering/equilibrium.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 source/engineering/transient_reduction.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 source/engineering/reference_check.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 source/engineering/audit_export.py
```

`Stage05-reference.mo` and `results/engineering/stage05-prior-reference.csv` are frozen reproduction inputs included with the compact package. Prior extraction provenance preserves the original native CSV hash. Each complete native result archive supplements the compact source/results package; download both for an auditable historical record.

Run `build_assembly.FCMacro` in an existing FreeCAD installation (GUI or xvfb wrapper) for the17-solid representative assembly and STEP/STL exports. The CAD omits the full separate radiator. Effective thermal capacities include attached structure not fully drawn, and no structural sizing/clearance/production integration is claimed.

No physical measurements, environmental qualification, airship validation or operational readiness is claimed. Physical test methods and the separately labeled synthetic correlation exercise are in the study evidence package.
