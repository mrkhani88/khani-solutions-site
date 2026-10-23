DATA-CENTER HYDRAULICS - DESIGN R1 - 23 OCTOBER 2026

Prepared on Intel using QElectroTech 0.9 and official FreeCAD 1.1.4.

REVIEW
Open Review.html directly in a browser, or serve this folder with:
  python3 -m http.server 8891 --bind 127.0.0.1
Then visit http://127.0.0.1:8891/Review.html
This review needs no external web assets. Component buttons explain the system.

NATIVE FILES
- diagram/DataCenter_Piping_R1.qet: two editable QElectroTech folios.
- cad/DataCenter_Layout_R1.FCStd: native FreeCAD layout with 285 valid solids.
- cad/DataCenter_Layout_R1.step: STEP assembly, 281 solids (floor/service zones excluded).
- cad/pipe-route-schedule.csv: centerline routes, IDs, illustrative wall and bends.
- review/: SVG-derived piping previews and native FreeCAD camera exports.
- verification/: native reopen and geometry checks.

REPRODUCE
1. Run source/build_diagram.py with Python 3. Open the QET file in QElectroTech.
   The diagram uses native editable lines, shapes and rich text; it is not an electrical netlist.
2. Run source/build_layout.FCMacro inside FreeCAD GUI. It creates the layout, STEP and route schedule.
3. Run source/render_verify.FCMacro inside FreeCAD GUI. It checks saved geometry and STEP,
   then exports three views using delayed GUI redraws. Keep the application running until CAD_COMPLETE.
4. Run source/build_review.py with Python 3 to rebuild the local review page.
The macro parameters use millimetres. Rerun to regenerate geometry after changing routing parameters.
No custom Python proxy modules or external FreeCAD workbenches are needed to reopen the model.

DESIGN BASIS
Ten racks, 100 kW/rack liquid load, total 1 MW. Nominal TCS 35/45 C.
Illustrative FWS boundary 25/35 C. Three 50% pumps: two duty, one standby.
Header clear ID 125 mm; branch clear ID 40 mm. Header elevation 2.70 m.
20 x 8 m planning envelope; rack 0.8 x 1.2 x 2.2 m, pitch 1.2 m.
Measured external main headers total 24.40 m plus listed CDU links/internal routes.
Each routed rack branch pair totals 4.746992 m, excluding rack internals/connection envelopes.
Stage 01 40/20 m lengths were placeholders. Head and power have NOT been recalculated.

LIMITS
This is a concept routing layout, not construction documentation, a solved network,
pressure qualification, structural/support design, complete clash review or CFD fluid CAD.
Valve, pump, filter and heat-exchanger bodies are packaging envelopes; equipment curves,
ports, valve positions, pressure ratings, relief/fill settings and coolant chemistry remain pending.
Illustrative 4/3 mm pipe walls are not selected/rated pipe schedules.
Tee bores are not booleaned into one continuous fluid domain.
Service-zone colors are planning reservations, not an accessibility/fire/electrical code check.
Screenshots are CAD geometry and diagrams, not simulation contours or measured data.

NEXT
Review arrangement -> freeze tagged route schedule -> build segmented OpenModelica network ->
check conservation/pressure balance and rack distribution -> compare direct/reverse return ->
select supplier curves -> targeted manifold CFD where it changes the design decision.

OFFICIAL SOFTWARE
https://qelectrotech.org/
https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4
FreeCAD AppImage SHA256 verified on Intel:
f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434
