# Study requirements and verification basis

Revision: Stage 06 / 24 October 2026. Independent public-reference portfolio study. No Sceye internal design, qualification record or employer material is represented.

## Evidence rules

- **Demonstrated in simulation:** a retained model or numerical workflow with inspectable inputs, outputs and checks. It does not establish flight performance or measured accuracy.
- **Test planned:** an executable test definition exists; the article has not been assembled or tested.
- **Physically tested:** requires raw measured data, calibrated instrumentation, configuration identity and a signed test record. There are **zero** physically tested items in this portfolio study.
- **Unresolved:** the information, equipment or independent evidence required to close the item is unavailable. A documented closure path is provided.

A job-duty row can be demonstrated in simulation while hardware selection or qualification remains unresolved. The detailed gap column controls that interpretation. The matrix assesses this independent study, not the candidate's full employment history.

## Mission basis and scope

The manufacturer reports an onboard server/mobile-core demonstration at 16.5–17 km during ST1. SceyeCELL publicly includes cellular and beamforming functions. These support a telecom-plus-edge-computing study. They do not disclose the actual board layouts, server specification, losses or installation temperatures. The new 17 km case supplements the inherited 20 km nominal; neither is an ST1 telemetry replay.

Sources: [ST1 September 2026 report](https://sceye.com/press-releases/sceye-completes-record-us-japan-stratospheric-flight/), [SceyeCELL February 2026 description](https://sceye.com/press-releases/sceye-unveils-stratospheric-telecom-antenna-sceyecell/).

The optional observation/optics payload is a separate configuration. No claim is made that all mission payloads are installed simultaneously. The underlying vehicle has 24 inherited thermal state nodes. Detailed telecom/server states extend that representative network; CAD object count is not thermal resolution.

## Selected engineering requirements

Every numerical limit below is a **study choice**, not an OEM allowable. Selected commercial components and mission requirements would replace these limits before hardware qualification. A case-temperature surrogate is not a semiconductor junction prediction.

| ID | Requirement | Verification / closure evidence |
|---|---|---|
| TH-01 | Telecom/server terminal-node operating temperature surrogates shall remain within −10 to +70 °C during enabled service. | Native time histories and time-outside-band. Package-to-junction resistance and selected-part limits remain unresolved. |
| TH-02 | When the startup gate is enabled, all five true modeled package-case states shall reach at least −5 °C before enabling variable payload workload; permitted-service reporting shall also require TH-01 and SOC >20%. | Readiness uses ideal true states, not an implemented sensor observer. Heater control uses a separate filtered plate sensor. Compare sensor bias; this gate is not production software assurance. |
| TH-03 | When thermal management is enabled, variable payload loads above standby shall start throttling at the hottest case temperature of 60 °C, reaching a 40% factor at 66 °C and retaining that floor above it. | Code factor = clip((70 − Tmax_C)/10, 0.4, 1). It affects transmitter/beamformer/baseband/server variable loads; service flag above70°C is0 but does not itself command complete shutdown. Throttling is reduced service, not full mission success. |
| TH-04 | A selected cold-start case beginning at −40 °C shall be evaluated against a chosen 6 h service-acquisition objective. | Acquisition time, true temperatures, delivered service and heater energy. Failure is retained and explained. |
| EN-01 | Nominal mission shall be assessed against an assumed minimum battery SOC of 20% in the inherited generic 60 kWh aggregate. | Minimum SOC and energy balance. Real usable energy, chemistry and age remain unresolved. |
| SV-01 | Selected nominal settled day shall be assessed for continuous permitted telecom/server service. | Availability and throttle metrics; numerical fulfillment does not prove communications throughput. |
| CT-01 | Motor heater nominal command shall preserve its selected 30 W hardware reserve (270 W ceiling, 300 W installed). | Retained Stage 05 controller histories. Reaching software ceiling is still saturation. |
| CT-02 | Inherited motor heating-floor evaluation shall use −5 ±0.5 °C, with acquisition sustained for 10 min. | Stage 05 acquisition and settled-window checks. Heating floor is not a motor operating/survival rating. |
| VM-01 | All imposed electrical input shall be accounted as thermal dissipation, exported RF/shaft/electrical work, stored energy or specified loss. | Energy audit and sign/units checks at system and subsystem boundaries. |
| VM-02 | The PCB spatial model shall show mesh sensitivity and energy closure before its effective path is used in the reduced system. | Spatial audit, material/geometry identity, transfer value and definition of the reference temperature. This is verification, not physical validation. |
| VM-03 | Correlation parameters shall be fitted on designated calibration data only; held-out conditions shall be predicted without retuning. | Synthetic workflow demonstration now; independent measured data required for physical closure. |
| VM-04 | Cases above the chosen125°C case-temperature analysis-domain guard shall be rejected as extrapolations. | Guard is a model-validity screen, not a hardware allowable. Large raw ordinary-PCB temperatures omit protection, radiation and property changes and are not credible hardware predictions. |
| TV-01 | A representative assembly shall have a documented sensor map, electrical metrology, environment record, configuration identity and abort limits before testing. | Test package supplied; physical execution not performed. |

## Margins and decisions

Report upper margin as `limit_high − Tmax` and lower margin as `Tmin − limit_low`, in kelvin. A positive margin indicates the chosen condition is inside a chosen limit. Report the minimum margin together with uncertainty; a sub-kelvin margin is not robust when input/sensor uncertainties are larger.

Separate heater hardware reserve, command-ceiling time, thermal margin, battery reserve, service availability and workload throttling. One favorable measure must not mask failure in another. Fault cases may intentionally violate a requirement; their purpose is to expose the needed detection, isolation or redesign.

Operating, survival and startup limits are different. Actual survival bounds, storage limits, thermal ramp-rate restrictions, detector stability, RF performance drift and structural allowables remain unallocated until hardware and mission definitions exist.

## Current implementation boundary

The startup gate uses all five true modeled case states. A real design would need actual sensor placement, estimation, plausibility, sample timing and an independent protective path. The filtered plate sensor (30s first-order) controls the payload heater; it is not a complete distributed temperature-monitoring implementation. The `service` output is a permissibility metric, not an independently verified shutdown command or measured communications performance.
