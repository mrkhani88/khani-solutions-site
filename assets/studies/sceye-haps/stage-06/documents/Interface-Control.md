# Representative thermal/electrical interface-control record

Status: design definition for this portfolio; interface hardware not assembled. Values belong to simulation assumptions, not a released installation drawing.

| Interface | Definition to control | Analysis and verification |
|---|---|---|
| Equipment → board | Heat-source footprint, power definition, package/case reference, anisotropic board properties | Match CAD material regions and power units. A bulk block is not a junction model. |
| Board → pad → plate | Product/lot, compressed thickness, area, contact pressure/torque, flatness, surface finish | Track bulk and contact resistance separately; test multiple assemblies. |
| Plate → strap/radiator | Conductance definition, endpoints, open/minimum states, contact terms | Compare fixed and controlled paths; include failure low/high and actuator energy/mass when selected. |
| Equipment → mounting structure | Fastener material, washer/bushing stack, torque and bypass paths | Account for parasitic conduction and mechanical constraints; thermal improvement may change structural load path. |
| Harness crossing insulation | Wire metal/gauge, count, length, routing, connectors and strain relief | Add conduction/I²R losses; avoid hiding harness heat leakage inside an unexplained insulation value. |
| Enclosure → atmosphere | Vented or sealed decision, pressure equalization, leakage, gas composition and local velocity | Do not assume sea-level free convection or vacuum; test chosen pressure and identify internal gas state. |
| Surface → radiative environment | Area, coating/finish, solar absorptance, IR emissivity, view factors, shading and aging | Direct solar, Earth/sky IR and hull exchange have different boundaries; preserve optical-property provenance. |
| Power → thermal network | Input electrical power, exported RF, converter loss, server workload and heaters | Account for each watt once; no duplicate input between aggregate RF and detailed server modules. |
| Sensors → controller | Sensor location, bias, lag, sample/filter delay, command transport and power response | Heater controller reads filtered plate surrogate; startup gate and service metrics use ideal true modeled terminal states. A real sensor observer/distributed protective function is not implemented. |
| Subsystem → mission energy | Requested service, allowed service, throttling, heater demand and SOC | Report service loss rather than silently assuming full payload performance under thermal shutdown. |

Cross-functional review questions: mechanical owns contact/torque/clearance; electrical owns power maps and bus limits; controls owns startup/fault actions; manufacturing owns repeatability and work instructions; test owns instrumentation and environment fidelity; systems owns mission and allocated margins. These are proposed responsibilities, not claims that a production team reviewed this work.

Change control: any changed material, pad thickness, mounting pattern, power schedule, software interlock or boundary condition creates a dated configuration change. Preserve the prior source and results; rerun affected verification and requirement rows. Sign-off fields in Design-Review-Checklist.csv remain unapproved until an actual review.
