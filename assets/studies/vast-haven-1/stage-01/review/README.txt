Haven-1 Stage-01 CAD Review R1

Serve the Stage-01-CAD-R1 parent directory using a local HTTP server, then open review/Review.html.
The viewer loads review/mesh.json, generated from the CAD geometry by the parent build workflow.
No remote JavaScript, package installation, account, or public hosting is required.

Viewer controls:
- Exterior, Side, Docking end and Cutaway camera presets.
- Drag to rotate; right-drag to pan; wheel/pinch to zoom.
- Group visibility, system focus, component search, per-component inspection.
- Internal assembly explosion uses schematic offsets for review, not actual flight placement.
- Reset restores the assembled exterior view and all groups.

Evidence boundaries:
- Public-reference exterior reconstruction; detailed dimensions and interfaces are approximate unless stated.
- Equipment is a representative internal assembly, not manufacturer CAD.
- No thermal/CFD results, qualified temperatures or pressure-drop results are included in this stage.
- Original reference imagery is credited to Vast; preserve the artwork and its attribution.

Three.js and OrbitControls are locally bundled under the included MIT license in vendor/LICENSE.txt.
