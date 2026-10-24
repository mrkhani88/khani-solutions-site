Stage05 / Cold-soaked motor startup and delayed heating control
Independent public-reference HAPS thermal study; no selected hardware qualification.

PUBLIC: https://khanisolutions.com/AISolutions/sceye-haps-thermal.html#cold-startup

REPRODUCE (Linux, OpenModelica1.27.1, Modelica4.1.0, Python3 + NumPy/SciPy):
1. Create verification/native and results/viewer. In verification/native run:
   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 omc ../../source/compile.mos
2. From the project root run python3 source/run_cases.py
   This runs9 mission cases and1 refinement for8continuous days each.
3. Run python3 source/audit_and_export.py
   Checks initial states, independent energy balance, PI/output limits, SOC,
   final-cycle repeatability, refinement and frozen Stage04 reproduction.
4. In verification/native run omc ../../source/probes.mos
   Then from root run python3 source/check_probes.py
5. Optional: python3 source/archive_native.py creates full native ZIPs.
   It deliberately refuses to replace existing archives.
6. Serve this directory with a static HTTP server; open Review.html.
   Downloaded JSON/CSV is a postprocessed native solver history, not a browser solver.

The compact bundle includes all9 cases first24h and day08 exports. Full8-day
native CSV/log/model/run-record archives are separate public downloads.
Stage04-reference.mo.txt and inputs/stage04-pi-day08.csv preserve the frozen
baseline; no external private files are required for the audit.
See inputs/startup-design.json and docs/Results-Walkthrough.txt for assumptions,
metrics, power-limit distinctions, limitations and results.

Initial-power prose correction: see docs/Initial-Power-Clarification.txt.
Original native CSVs, archives and model parameters remain unchanged.
