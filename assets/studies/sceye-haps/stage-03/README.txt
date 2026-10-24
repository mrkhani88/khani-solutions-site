INDEPENDENT HAPS THERMAL STUDY / STAGE03

Start with docs/Design-Basis-and-Assumptions.txt, then docs/Results-Walkthrough.txt.

Run on Linux with OpenModelica1.27.1, Modelica4.1.0, Python3/NumPy/SciPy/Matplotlib. From verification/native execute omc ../../source/compile.mos; then from project root python3 source/run_cases.py; python3 source/audit_and_export.py. verify_additional.py also expects the immutable Stage02 sibling for baseline reproduction. Run source/pcb_fem.py then source/verify_spatial.py for the independent open-source3D finite-element model; source/render_assets.py makes figures. Run source/build_pcb.FCMacro in FreeCAD1.1.4 to regenerate native geometry. OMEdit opens source/HAPSDiurnal.mo and IntegratedMission.

VTK: mesh in metres; scalar rise_K_per_W. T_C(x)=Ttray_C+Ptotal_W*rise(x). Coupling is one-way steady/frozen-boundary, not a transientPCB or physical validation.3D device bulk temperatures are not junction temperatures.

The main ZIP contains all final-day outputs and spatial meshes/fields. Five separate full native archives contain complete8-day primary trajectories plus combined refinement. Full native sensitivity and reference-refinement CSVs remain on Intel with recorded hashes; they are reproducible from the supplied scripts. No private employer/recruiter materials are included.

For portable viewer: python3 -m http.server8893 --bind127.0.0.1 then open Review.html.
