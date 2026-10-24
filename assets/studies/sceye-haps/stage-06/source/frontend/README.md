# Interview walkthrough frontend

The static entry page is `website/AISolutions/sceye-thermal-interview.html`.
Deploy the compact Stage 06 tree at `/assets/studies/sceye-haps/stage-06/`.
The HTML uses only the two local frontend source assets; no third-party JS or plotting libraries are required.

## Data contracts

- `inputs/requirements-matrix.json`: `requirements[]` with `id`, `category`, `title`, `jobRequirement`, `status`, `summary`, `evidenceIds`, `gaps`, `closeout`, and `relatedSteps`.
- `inputs/lifecycle-evidence-registry.json`: `evidence[]` entries carry `id`, `title`, `href`, `type`, `status`, `description`, and `boundary`; ordered `steps[]` entries carry `evidenceIds`.
- `results/engineering/explorer.json`: `default_case`, `notes`, `cases[]` with `id`, `label`, `description`, `time_h`, `temperature_C` channels, `heater_W` (payload heater), `total_heater_W` (whole vehicle), `payload_W`, `soc_pct`, `service` (thermal/SOC operability), `load_factor`, `metrics`, optional `rejected`, `validity_note`, and `csv`/`csv_href`. A nested `first_day` carries the same trace keys with its matching `metrics`; default root traces are settled day 08.
- `results/engineering/spatial-surface.json`: `cases` keyed by case id, with `surface:[{x_mm,y_mm,T_C}]`, labels, descriptions and validity notes. A common temperature scale can be applied across cases; the optional selected-case scale is explicitly labeled. Matched source powers, plate temperature and 1D/spatial package-case temperatures accompany the map.
- `results/correlation/explorer.json`: `time_s`, `runs[]` keyed by `calibration` or `held_out`, with `observed_*_C`, `predicted_*_C`, and `residual_*_K`. Observations are explicitly synthetic.
- `results/correlation/summary.json`: fit parameters, metrics, demo acceptance limits and limitations.

The browser displays saved results and computes only display reductions (saved-view ranges, explicitly labeled approximate trapezoidal electrical-energy curves and fallback service-permission duration). Scalar energy and availability cards use native counter/window metrics when available. The cumulative energy view is explicitly a two-minute-sample estimate and can differ slightly from those counters. It does not execute the engineering solvers. Source arrays retain their stored sampling interval.

## Controls and deep links

The six route tabs support click, arrow keys, Home and End. `#step-01` through `#step-06` and short aliases `#step-1` through `#step-6` select a route stop. `#requirements` aliases `#requirements-matrix`; requirement ids link to the corresponding expanded row.

The matrix supports text search, evidence-state filtering, inline detail and UTF-8 CSV export. The mission explorer supports saved case/channel/window selection, a deliberate same-window baseline overlay, temperature/power/energy/SOC/operability plots, looping playback and a time slider. Payload package-case plots show chosen −10/70°C study screens. Operability is distinguished from requested full workload. It pauses when the browser tab is hidden. The correlation viewer separates calibration and held-out prediction, with an optional signed residual plot.

No data are invented on loading failure: the affected panel shows an error and leaves the source-download path available. Rejected engineering cases are labeled as diagnostic extrapolations. Physical validation is explicitly unclaimed.

Visual browser QA and publication receipts are retained by the parent workflow under the stage/project evidence folders.
