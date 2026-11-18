#!/usr/bin/env python3
"""Export the frozen geometry U-Net and verify float32 native/ONNX parity.

Run with the native study's Python environment plus separately installed onnx
and onnxruntime packages.  The source study and its runtime are read-only inputs.
Output and verification directories must be outside the source study.

The ONNX graph accepts NCHW float32 geometry [1,4,128,256] and returns RAW
normalized network response [1,3,128,256].  Inlet/gauge/scaling/mask recovery is
intentionally performed by the client, not by this graph.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True


EXPECTED_WEIGHT_SHA256 = "cd47ac8670f7265d46ded7ca787a6a861f360d4fd92a486a8c58536f556da6c9"
EXPECTED_METADATA_SHA256 = "e6688d121ba71a962e53ee11d188fab3804242cbcd694a8d3b1d7d5f9d37e6e8"
FILM_SHAPES = (("airfoil", "Airfoil", 0), ("car", "Car", 7101),
               ("plane", "Plane", 7201), ("human", "Human", 7301))
ALTERED_POSES = {
    "airfoil": {"center": [3.8, 0.25], "size": 1.65, "angle_deg": 12.0},
    "car": {"center": [3.0, -0.2], "size": 1.55, "angle_deg": -9.0},
    "plane": {"center": [4.1, 0.3], "size": 1.85, "angle_deg": 14.0},
    "human": {"center": [3.6, -0.25], "size": 1.65, "angle_deg": -8.0},
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_external(path, source):
    try:
        path.relative_to(source)
    except ValueError:
        return
    raise ValueError("Export and verification outputs must be outside source study")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-model-directory", type=Path, required=True)
    parser.add_argument("--verification-directory", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    destination = args.output_model_directory.resolve()
    verification = args.verification_directory.resolve()
    require_external(destination, source)
    require_external(verification, source)

    import numpy as np
    import onnx
    import onnxruntime as ort
    import torch

    study = source / "work/geometry_flow"
    model_directory = source / "outputs/geometry_flow/model"
    weights = model_directory / "weights.pt"
    native_metadata = model_directory / "model.json"
    if sha256(weights) != EXPECTED_WEIGHT_SHA256:
        raise ValueError("Native model weights differ from the approved frozen model")
    if sha256(native_metadata) != EXPECTED_METADATA_SHA256:
        raise ValueError("Native model metadata differs from the approved frozen model")

    sys.path.insert(0, str(study))
    sys.path.insert(0, str(study / "ml"))
    from geometry import build_geometry, canonical_polygons
    from model import GeometrySurrogate, input_array

    surrogate = GeometrySurrogate.load(model_directory, threads=4)
    metadata = surrogate.metadata
    if metadata["architecture"]["parameters"] != 124411:
        raise ValueError("Unexpected network architecture")
    if len(surrogate.x) != 256 or len(surrogate.y) != 128:
        raise ValueError("Unexpected fixed native grid")

    destination.mkdir(parents=True, exist_ok=True)
    verification.mkdir(parents=True, exist_ok=True)
    onnx_path = destination / "geometry-unet.onnx"
    example = torch.zeros((1, 4, 128, 256), dtype=torch.float32)
    with torch.inference_mode():
        torch.onnx.export(
            surrogate.network, example, onnx_path,
            export_params=True, opset_version=17,
            input_names=["geometry"], output_names=["response"],
            do_constant_folding=True, dynamo=False,
        )
    graph = onnx.load(onnx_path)
    onnx.checker.check_model(graph, full_check=True)
    if any(t.data_type in {onnx.TensorProto.FLOAT16, onnx.TensorProto.DOUBLE,
                          onnx.TensorProto.BFLOAT16} for t in graph.graph.initializer):
        raise ValueError("Export unexpectedly contains non-float32 floating weights")
    for tensor, expected_name, expected_shape in [
        (graph.graph.input[0], "geometry", [1, 4, 128, 256]),
        (graph.graph.output[0], "response", [1, 3, 128, 256]),
    ]:
        shape = [d.dim_value for d in tensor.type.tensor_type.shape.dim]
        if (tensor.name != expected_name or shape != expected_shape or
                tensor.type.tensor_type.elem_type != onnx.TensorProto.FLOAT):
            raise ValueError("ONNX input/output contract differs from requested schema")

    domain = metadata["input_domain"]
    physics = metadata["physics"]
    config = {
        "nx": 256, "ny": 128, "dx": float(physics["dx"]),
        "xmin": float(physics["domain_x"][0]),
        "ymin": float(physics["domain_y"][0]),
        "xmax": float(physics["domain_x"][1]),
        "ymax": float(physics["domain_y"][1]),
        "sdfScale": float(metadata["normalization"]["sdf_scale"]),
        "outputScales": metadata["normalization"]["output_scales"],
        "centerX": domain["center_x"], "centerY": domain["center_y"],
        "size": domain["size"], "shapeBounds": [0.75, 6.5, -1.65, 1.65],
        "shapes": [
            {"id": family, "label": label,
             "angle": domain["angle_limits_deg"][family],
             "polygons": [p.tolist() for p in canonical_polygons(family, seed)]}
            for family, label, seed in FILM_SHAPES
        ],
        "weightSha256": EXPECTED_WEIGHT_SHA256,
        "onnxSha256": sha256(onnx_path),
    }
    (destination / "config.json").write_text(json.dumps(config, indent=2) + "\n")

    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(onnx_path), sess_options=options,
                                   providers=["CPUExecutionProvider"])
    if [i.name for i in session.get_inputs()] != ["geometry"]:
        raise ValueError("Unexpected ONNX input name")
    if [o.name for o in session.get_outputs()] != ["response"]:
        raise ValueError("Unexpected ONNX output name")

    def metrics(reference, candidate):
        difference = candidate.astype(np.float64) - reference.astype(np.float64)
        return {
            "maximum_absolute_error": float(np.max(np.abs(difference))),
            "mean_absolute_error": float(np.mean(np.abs(difference))),
            "relative_L2": float(np.linalg.norm(difference.ravel()) /
                                 max(np.linalg.norm(reference.astype(np.float64).ravel()), 1e-30)),
            "allclose": bool(np.allclose(reference, candidate, rtol=1e-4, atol=1e-5)),
        }

    def recover(raw, mask):
        response = raw[0].astype(np.float32, copy=True)
        response[:2, :, 0] = 0
        response[2] -= response[2, :, -1].mean(dtype=np.float32)
        response *= surrogate.output_scales[:, None, None]
        fields = {"u_star": 1 + response[0], "v_star": response[1], "Cp": response[2]}
        for value in fields.values():
            value[mask] = 0
        return fields

    records = []
    for family, _, seed in FILM_SHAPES:
        spec = {"shape_id": "onnx_parity_" + family, "family": family,
                "shape_seed": seed, "pose": ALTERED_POSES[family]}
        geometry = build_geometry(spec)
        inputs = input_array(geometry["mask"], geometry["sdf"], surrogate.x,
                             surrogate.y, surrogate.sdf_scale)[None]
        with torch.inference_mode():
            native_raw = surrogate.network(torch.from_numpy(inputs)).numpy()
        onnx_raw = session.run(["response"], {"geometry": inputs})[0]
        native_fields, details = surrogate.predict(geometry["mask"], geometry["sdf"], spec)
        recovered = recover(onnx_raw, geometry["mask"])
        checks = {"raw_response": metrics(native_raw, onnx_raw)}
        for name in ("u_star", "v_star", "Cp"):
            checks[name] = metrics(native_fields[name], recovered[name])
        if not all(v["allclose"] for v in checks.values()):
            raise ValueError("Native/ONNX float32 parity failed: " + json.dumps({"family": family, "checks": checks}))
        fixture = verification / (family + "_altered_pose.npz")
        arrays = {
            "solidmask": geometry["mask"].astype(np.uint8),
            "input_geometry": inputs.astype(np.float32),
            "response_native": native_raw, "response_onnx": onnx_raw,
            "x": surrogate.x, "y": surrogate.y,
        }
        for name in ("u_star", "v_star", "Cp"):
            arrays[name + "_native"] = native_fields[name]
            arrays[name + "_onnx"] = recovered[name]
        np.savez_compressed(fixture, **arrays)
        record = {"query": spec, "fixture": fixture.name,
                  "fixture_sha256": sha256(fixture),
                  "mask_shape": list(geometry["mask"].shape),
                  "input_shape": list(inputs.shape), "input_dtype": str(inputs.dtype),
                  "native_support": details["support"], "checks": checks,
                  "passed": True}
        (verification / (family + "_altered_pose.json")).write_text(json.dumps(record, indent=2) + "\n")
        records.append(record)

    if sha256(weights) != EXPECTED_WEIGHT_SHA256 or sha256(native_metadata) != EXPECTED_METADATA_SHA256:
        raise ValueError("Native model inputs changed during export")
    report = {
        "schema": "GEOMETRY_FLOW_ONNX_PARITY_V1", "passed": True,
        "createdUTC": datetime.now(timezone.utc).isoformat(),
        "sourceRoot": str(source), "nativeWeightsSha256": EXPECTED_WEIGHT_SHA256,
        "nativeMetadataSha256": EXPECTED_METADATA_SHA256,
        "onnxSha256": sha256(onnx_path), "onnxBytes": onnx_path.stat().st_size,
        "onnxOpset": 17, "networkParameters": 124411,
        "input": {"name": "geometry", "shape": [1, 4, 128, 256], "dtype": "float32"},
        "output": {"name": "response", "shape": [1, 3, 128, 256], "dtype": "float32",
                   "meaning": "raw normalized du/Uinf, v/Uinf, Cp; no recovery inside graph"},
        "tolerance": {"rtol": 1e-4, "atol": 1e-5},
        "versions": {name: importlib.metadata.version(name) for name in ("torch", "onnx", "onnxruntime", "numpy")},
        "sourceUnchanged": True, "fixtures": records,
        "clientPreprocessing": [
            "Occupancy=1 inside solid; row0 is domain bottom; NCHW float32.",
            "Recompute periodic-y SDF from occupancy: tile vertically three times, EDT(fluid)-EDT(solid), retain central rows, multiply dx.",
            "Stack occupancy, clip(SDF/sdfScale,-4,4), xNormalized, yNormalized.",
            "Coordinate channels span [-1,1] over the minimum/maximum CELL CENTERS, not the domain edges.",
        ],
        "clientRecovery": [
            "Set first-column raw du and dv to zero.",
            "Subtract the mean of the raw Cp outlet column (mean over y) from all raw Cp.",
            "Multiply raw channels by outputScales, then u_star=1+du, v_star=dv, Cp=scaled_Cp.",
            "Set u_star, v_star and Cp to zero inside the supplied solid mask.",
        ],
    }
    (verification / "onnx-parity-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "onnx": str(onnx_path), "onnxSha256": report["onnxSha256"],
                      "onnxBytes": report["onnxBytes"], "config": str(destination / "config.json"),
                      "report": str(verification / "onnx-parity-report.json"),
                      "maximumRawAbsoluteError": max(x["checks"]["raw_response"]["maximum_absolute_error"] for x in records),
                      "maximumRecoveredAbsoluteError": max(x["checks"][name]["maximum_absolute_error"] for x in records for name in ("u_star", "v_star", "Cp"))}, indent=2))


if __name__ == "__main__":
    main()
