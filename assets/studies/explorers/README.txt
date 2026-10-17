Khani Solutions — interactive result library, 2026-10-17

These viewers inspect saved numerical results; changing a time, quantity or
material does not run a solver or change the modeled inputs.

plume: 61 native OpenFOAM 2D states, 13,472 gas cells, 0–15 s.
battery: 121 Elmer states, 0–3,600 s. The displayed Y=0 FE slice has 44,437
triangles. The underlying model has 2,084,927 tetrahedra and 372,971 nodes.
The map is triangle-mean FE interpolation, not a full-volume peak or a 30-cell
resolved battery. Full-volume quantities come from the separate history CSV.
lunar: 221 exact native states selected from 3,022 snapshots in 35 windows;
2,118 planar cells. Original fields and 0D pressure remain distinct. CFD window
time excludes long mission coasts. Phase 29 onward leaves the tank in lunar
orbit; Orion return graphics are contextual.
wake: 75 fixed-camera native-field renders, 0.502–1.982 s, synchronized to
retained load/circulation records. The 3D volume cannot be rotated or probed
from these images. Force chart downsampling preserves min/max in 400 bins for
each force; the unmodified high-rate CSV remains available. No mean or RMS is
recalculated from the decimated display series.

Binary files: little-endian float32 [state, stored quantity, displayed cell].
Battery stores one temperature quantity; two display ranges share it. Other
cell viewers store two quantities. Geometry, units, times and ranges are in
viewer.json. Constant per-cell colors and fixed ranges permit comparisons.
Values outside each display range saturate; the count is reported. Float32
rounding is a display export, not a fresh numerical solve. Local profiles
sample the same displayed cell across the retained states.

Every study manifest records byte sizes and SHA-256 hashes. The source ZIP
contains web source, preparation/export scripts and checks. Export scripts
require the original source cases at the documented paths and scientific
Python dependencies (NumPy, Matplotlib, PyVista, SciPy, Pillow as applicable).
The ZIP is not a self-contained solver rerun archive. The source cases remain
in their original project/compute locations and have not been modified.

Model validation: all four studies remain exploratory and lack experimental
validation and complete grid/time-step independence. Execution checks, data
integrity checks and usable web controls do not establish physical validity.
Existing PCB stages and angle-sweep control modules were preserved.
