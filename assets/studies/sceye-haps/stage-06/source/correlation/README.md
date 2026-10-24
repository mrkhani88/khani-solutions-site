# Synthetic correlation workflow

This is a standalone demonstration, not measured Sceye hardware data or physical validation of the integrated payload. The two-node example is independent of the five-terminal spatial model.

Run `python3 synthetic_correlation.py` with NumPy and SciPy installed. Execute from the retained stage layout; the script locates the stage relative to its own file and writes `results/correlation/` and `verification/correlation/`.

The calibration sequence alone fits two conductances and two heat capacities. A different power/ambient sequence is predicted without retuning. The nonlinear synthetic generator has temperature-dependent conductance; the fitted model has constant conductance. Generated sensor noise and fixed biases are explicitly assumed. The seed is fixed for reproducibility.

Read `results/correlation/summary.json` for all fit inputs, metrics, selected demonstration thresholds and limitations. The CSVs contain generated observations, predictions and residuals; they must never be relabeled as measurements. `verification/correlation/audit.json` records energy closure, generator refinement, independent optimizer start and source hash. The physical test plan uses separate, explicitly proposed acceptance objectives.
