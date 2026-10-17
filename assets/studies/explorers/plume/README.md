# Midnight center-section thermal plume — completed R5 case

2026-10-11. The user approved the R5 center section. A new OpenFOAM mesh and 0–15 s external-flow calculation are complete. The three new 10-second videos use only this run's temperature and velocity fields. The task-owned solver container is stopped. R2 results and the rejected R4 side-silhouette proposal are preserved separately.

## Videos

All three videos are 1600 × 900, 30 fps, 300 frames, exactly 10 seconds, H.264/yuv420p. They show one fixed near-aircraft view with a white background, Turbo temperature colors, instantaneous streamlines and only a temperature colorbar. No title, time counter, captions, axes text or overview inset is shown. The fifteen physical seconds play at 1.5× speed.

- [Plain approved CFD section](results/white-turbo-r5/midnight_plume_plain_white_turbo_10s.mp4)
- [Pencil aircraft overlay](results/white-turbo-r5/midnight_plume_pencil_white_turbo_10s.mp4)
- [Photo-based aircraft overlay](results/white-turbo-r5/midnight_plume_photo_white_turbo_10s.mp4)

The viewport is x = −3 to 14 m and height = −0.1 to 8 m; it crops plume beyond that view. Display orientation keeps the reference aircraft's nose pointing right. CFD coordinates retain positive x from nose to tail. The color range is 30–600 °C, with gas below 30 °C white and 30–40 °C blended into white; the same mapping is on the colorbar. Spatial and temporal interpolation is for display. Quantitative metrics use native finite-volume fields.

## Geometry and assumptions

The wall comes from a true native CAD intersection at y = 0 of the estimated 3D fuselage envelope and an assumed centered nose fairing. It is a vertical nose-to-tail center section. Main landing-gear fairings, outboard wing/rotor booms and V-tail arms are outside this plane. The center wing attachment is blended into the estimated roof. This remains an approximate reconstruction from oblique public images, not authenticated manufacturer geometry. Source traces and envelope stations are in `geometry.json`; the original approval state is preserved in `geometry_review_approved.json` and `README_geometry_review.md`.

The estimated fuselage length is 7.2 m, using the prior assumed 8.2 m projected whole-aircraft extent for scale. Widths, hidden contours, nose-fairing dimensions, pack location and vent layout are not manufacturer measurements. The approved 25 mm nose-fairing gap is retained and resolved by the mesh; exact tire contact is not claimed. Native CAD/STEP uses millimetres with X longitudinal, Y lateral, Z vertical. The solver rotates that plane into XY, with solver Y representing height and a single 0.1 m empty span cell.

The assumed flush belly slot is 100 mm high at (x,height) ≈ (4.9000,0.7004) m. Hot, air-like gas enters at 873.15 K (600 °C), 40 m/s, directed aft/down 35°, for 10 s. Ambient air is still, 298.15 K, with a hydrostatic pressure profile referenced to 101325 Pa at ground level. Gravity is (0,−9.81,0) in solver coordinates; rotors are stopped. Ground and aircraft are stationary no-slip adiabatic boundaries. At 10 s the mouth becomes a closed, no-slip adiabatic wall for 5 s of dispersion.

The external domain is x [−16.4,32.8] m and height [0,24.6] m. There is no battery/internal fluid region, combustion, multi-species chemistry, toxicity, rotor forcing, solid heating or ground conduction. The gas and release are concept inputs, not measured Archer thermal-runaway data. Slot flow is per unit span, not a 100 mm round nozzle. The new flush slot has a different normal from R2's protruding nozzle, so matching speed, direction, temperature and duration does not make this a mass-flow-controlled geometry comparison.

## Numerical checks

OpenCFD OpenFOAM v2506 `buoyantPimpleFoam` uses nonreacting perfect-gas air, Cp = 1005 J/(kg K), Sutherland transport, k–omega SST, Euler time integration and first-order upwind convection. The independent mesh has 13,472 cells and eight vent faces. `checkMesh -allTopology -allGeometry` returned `Mesh OK`; maximum non-orthogonality is about 44.54° and maximum skewness about 1.57. Mesh-wall simplification differs from the approved CAD boundary by less than 1 mm while retaining the exact vent endpoints. Near the vent the target size is 12.5 mm, with 6 mm refinement around the nose gap.

A no-release check at 0.25 s held maximum cell speed to 0.00022128 m/s. Startup and six-rank continuation checks passed; the main release and dispersion ended normally at 10 and 15 s. All 61 saved T/U/p/rho fields are finite with positive pressure/density and accepted temperature bounds. Startup used maximum Courant 0.6; continuation used 0.8. A full mesh/time/domain independence study has not been performed.

Patch flux and total fluid mass were recorded at every solver timestep: 124,652 samples. Euler end-step integration gives a maximum inventory residual of 0.00019114 kg for the 0.1 m span, or 0.01636% of injected mass. A separate check using saved native rho fields gives 0.00533%. Saved-field and function-object inventory differences are reported explicitly in `run_summary.json`; the exact update-order cause has not been traced. The injected mass is 1.168359 kg for the 0.1 m span, corresponding to mean release flow 1.168359 kg/s per metre of slot span.

The largest saved external-cell temperature is 598.61 °C. Maximum monitored gas temperature adjacent to the adiabatic ground is 222.67 °C; this is not solid ground temperature. These are results of a preliminary 2D screening model, not aircraft safety or exposure validation.

## Overlay assets and provenance

The photo-based and pencil cutouts were created with the built-in image-generation tool from the matching official side reference. They have genuine alpha transparency and uniform landmark registration. Image editing can reconstruct details; the photographic cutout is not promised to be a pixel-exact unmodified photo. Their main gear, wing/rotor and V-tail details are visual context only and do not become CFD obstacles. A faint section boundary remains visible where the center cut and exterior image do not coincide.

Saved assets:

- `/Users/reza/Documents/ChatGPT/Job/output/midnight-ground-tr-r5/results/white-turbo-r5/aircraft_photo_transparent.png`
- `/Users/reza/Documents/ChatGPT/Job/output/midnight-ground-tr-r5/results/white-turbo-r5/aircraft_pencil_transparent.png`
- Exact tool prompts: `/Users/reza/Documents/ChatGPT/Job/output/midnight-ground-tr-r5/results/white-turbo-r5/overlay_prompts.json`
- `overlay_alignment.json` and `asset_manifest.json` record scale, orientation, transparency and hashes.

Primary references: [Stellantis, Preparing for Takeoff](https://www.stellantis.com/en/news/insights/preparing-for-takeoff), May 16, 2023, and [January 4, 2023 press release](https://www.stellantis.com/en/news/press-releases/2023/january/stellantis-to-build-electric-aircraft-with-archer-and-provide-strategic-funding-for-growth). Exact image URLs and retained originals are in `geometry.json`. Generated overlays played no role in constructing the approved CAD or solving the flow.

## Files and reproducibility

- `cfd/`: native mesh, dictionaries, serial/reconstructed time fields, complete solver logs, every-step monitors and independent quiet-air diagnostic case.
- `results/mesh_review.png`: native mesh around body, vent and nose gap.
- `results/run_summary.json`, `cell_metrics.json`, `mass_balance.csv`: native metrics and full-run flux audit.
- `results/completion_evidence.json`: phase completion, field checks, case hashes, stopped-container evidence and video verification.
- `results/white-turbo-r5/video_quality_check.json` and decode logs: all three MP4s fully decoded, with frame count, duration, codec, size and SHA-256 verified.
- `midnight_center_section.FCStd` and STEP exports: approved reconstructed envelope and section.
- `prepare_cfd.py`, `initialize_hydrostatic.py`, `close_vent.py`, `finish_r5.py`, `analyze_r5.py`, `render_white_turbo.py`: workflow source. Use a new, empty `MIDNIGHT_R5_CASE_DIR` for a replay; the builder refuses to overwrite solved time fields.

No LinkedIn post has been published.
