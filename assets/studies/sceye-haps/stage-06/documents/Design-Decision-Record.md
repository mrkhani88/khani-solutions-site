# Design decisions and evidence boundaries

Decision record, Stage 06. Numerical case outcomes are reported in the retained engineering results; this document records why a comparison is informative and what evidence would change the decision.

| ID | Decision / rationale | Evidence | Remaining condition |
|---|---|---|---|
| D-01 | Retain an integrated thermal-energy model so heater, RF/server and propulsion demand compete for the same energy reserve. | Stage 02 mission model, Stage 05 startup comparisons, Stage 06 detailed payload. | Actual power maps, battery chemistry and mission telemetry unavailable. |
| D-02 | Reduce avoidable nighttime radiator heat leakage before simply increasing installed heater capacity. | Stage 03 fixed-path, switch, insulation and larger-heater cases. | Effective variable conductance is a design hypothesis; actuator mass/power, life and failure behavior need selection/testing. |
| D-03 | Use limited PI with anti-windup and explicit sensor/command/output response for motor heating. | Stages 04–05 native histories and analytical delay probes. | Selected motor temperature limits and measured mounted-sensor dynamics unavailable. |
| D-04 | Reserve 30 W of a 300 W heater through a 270 W software ceiling where warm-up duration permits. | Stage 05 longer acquisition versus installed-power headroom. | The software ceiling is still active; reserve is not proof of redundancy or an independent safety function. |
| D-05 | Resolve the telecom/server heat path spatially and return its effective thermal path to the system. | Stage 03 spatial PCB baseline and Stage 06 mesh/path audit. | A representative block case temperature is not actual device junction temperature. Real ECAD and independent measurements required. |
| D-06 | Compare board/interface improvement separately from nighttime thermal-path changes. | Stage 06 baseline → improved interface → selected insulated cases. | The chosen candidate must satisfy both thermal/service and energy criteria; inspect fault cases and uncertainty before selection. |
| D-07 | Treat startup permission and workload throttling as explicit outputs. | Stage 06 enabled-service, temperature and workload histories. | Communications throughput and production software assurance are outside this thermal study. |
| D-08 | Use generated data only to demonstrate calibration/held-out prediction mechanics. | Stage 06 synthetic correlation source and residual plots. | Physical correlation remains unresolved until independently measured data are acquired. |
| D-09 | Keep observation optics as an alternative mission configuration. | Public announced sensing program; optional CAD envelope. | Detector/optics hardware, accuracy limits and actual installation are not disclosed. |

The ordinary-board and severe degraded-path raw extrapolations exceed a chosen125°C analysis-domain guard. They are **rejected numerical extrapolations**, not credible hardware-temperature predictions. Rejection shows the assumed ordinary heat path is inadequate; it does not quantify how an actual protected device would fail.

Selection gate: prefer the candidate that meets the chosen nominal temperature/service/SOC objectives with documented margins and the simplest credible heat paths. Do not call it an optimized flight design. A fault-case failure is retained evidence of a needed mitigation, not removed to make the dashboard look complete.
