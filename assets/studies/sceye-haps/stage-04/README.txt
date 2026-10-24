STAGE04 / MOTOR HEATER CONTROL

Read inputs/controller-design.json and docs/Results-Walkthrough.txt first.

Native tools used:OpenModelica1.27.1, Modelica4.1.0, Python3/NumPy/SciPy/Matplotlib on Intel. From verification/native:omc ../../source/compile.mos. From project root:python3 source/run_cases.py then python3 source/audit_and_export.py. The reproduction check expects the immutable sibling folder stage-03-night-control-spatial-r1, including its results/combined_native.csv; download Stage03 combined full-native archive and extract there if reproducing elsewhere. inspect.mos produces native graph data for render_and_archive.py, which makes figures and archives.

Open source/HAPSDiurnal.mo in OMEdit, then IntegratedMission; open only one stage version at a time because the package name is shared.

All final-day CSVs and website JSONs are included. Separate full-native archives provide the main comparison and selected refinement; other complete8day CSVs remain on Intel, with hashes and runtime settings in verification/run-manifest.json. No compiled runtime binaries are distributed.

Portable viewer:python3 -m http.server8894 --bind127.0.0.1, then open Review.html. The viewer inspects saved data and does not solve in-browser.
