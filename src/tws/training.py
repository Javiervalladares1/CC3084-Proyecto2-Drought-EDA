"""Experimentos manuales y evaluación temporal reservada, con reanudación."""
from __future__ import annotations

import argparse
import gc
import json
import platform
import shutil
import statistics
import subprocess
import sys
import threading
import time
from importlib.metadata import version

import numpy as np
import pandas as pd
import psutil

from .data import load_prepared, prepare
from .models import fit_model, load_bundle, metrics
from .utils import CACHE, FAMILIES, LABELS, MODELS, RESULTS, ROOT, config, log, sha256, update_status, write_json


class MemoryMonitor:
    def __enter__(self):
        self.peak = psutil.Process().memory_info().rss
        self.done = threading.Event()
        def sample():
            while not self.done.wait(.5):
                self.peak = max(self.peak, psutil.Process().memory_info().rss)
        self.worker = threading.Thread(target=sample, daemon=True)
        self.worker.start()
        return self

    def __exit__(self, *args):
        self.done.set()
        self.worker.join()


def _indices(meta, stage):
    cfg = config()
    date = meta.target_time
    if stage == "tuning":
        train = date <= cfg["train_end"]
        valid = date.between(cfg["tuning_start"], cfg["tuning_end"])
    elif stage == "confirmation":
        train = date < cfg["confirmation_start"]
        valid = date.between(cfg["confirmation_start"], cfg["confirmation_end"])
    elif stage == "holdout":
        train = date < cfg["holdout_start"]
        valid = date.between(cfg["holdout_start"], cfg["holdout_end"])
    else:
        return np.arange(len(meta)), np.array([], dtype=int)
    assert not (train & valid).any()
    assert date[train].max() < date[valid].min()
    return np.flatnonzero(train), np.flatnonzero(valid)


def _experiment_rows():
    records = []
    for path in MODELS.glob("tuning/*/*/complete.json"):
        data = json.loads(path.read_text())
        records.append({"algorithm": LABELS[data["family"]], "family": data["family"],
                        "configuration": data["name"], **data["validation"],
                        "fit_seconds": data["fit_seconds"], "peak_rss_mb": data["peak_rss_mb"],
                        "best_iterations": data.get("best_iterations"), "best_epochs": data.get("best_epochs"),
                        "parameters": json.dumps(data["parameters"], ensure_ascii=False)})
    if records:
        pd.DataFrame(records).to_csv(RESULTS / "experimentos.csv", index=False)


def _benchmark(bundle, X):
    sample = X[:min(10000, len(X))]
    bundle.predict(sample[:32])
    times = []
    for _ in range(3):
        start = time.perf_counter()
        bundle.predict(sample)
        times.append(time.perf_counter() - start)
    return statistics.median(times) * 1000 * 1000 / len(sample)


def _run_fit(family, params, X, meta, stage, directory, selected=None):
    completed = directory / "complete.json"
    if completed.exists():
        log(f"Se reutiliza {family} {stage} {params['name']}")
        return json.loads(completed.read_text())
    train_idx, valid_idx = _indices(meta, stage)
    X_train = np.asarray(X[train_idx], dtype=np.float32)
    y_train = meta.target.to_numpy(dtype=np.float32)[train_idx]
    # La prueba reservada nunca se pasa a fit_model ni a la parada temprana.
    use_early_stopping = stage == "tuning"
    X_valid = np.asarray(X[valid_idx], dtype=np.float32) if len(valid_idx) else None
    y_valid = meta.target.to_numpy(dtype=np.float32)[valid_idx] if len(valid_idx) else None
    log(f"INICIO {LABELS[family]} {stage} {params['name']}: {len(train_idx):,} entrenamiento / {len(valid_idx):,} evaluación")
    update_status(f"{family}_{stage}", status="running", configuration=params["name"], train_rows=len(train_idx))
    with MemoryMonitor() as memory:
        bundle = fit_model(family, params, X_train, y_train,
                           X_val=X_valid if use_early_stopping else None,
                           y_val=y_valid if use_early_stopping else None,
                           fixed_iterations=(selected or {}).get("best_iterations"),
                           fixed_epochs=(selected or {}).get("best_epochs"), stage=stage)
    bundle.info.update({"name": params["name"], "peak_rss_mb": memory.peak / 1024 ** 2,
                        "train_target_start": str(meta.target_time.iloc[train_idx].min().date()),
                        "train_target_end": str(meta.target_time.iloc[train_idx].max().date()),
                        "raw_sha256": json.loads((RESULTS / "auditoria.json").read_text())["raw_sha256"]})
    rng = np.random.default_rng(config()["seed"])
    sample_idx = rng.choice(len(train_idx), size=min(20000, len(train_idx)), replace=False)
    bundle.info["training_diagnostic_sample"] = metrics(y_train[sample_idx], bundle.predict(X_train[sample_idx]))
    result = {"family": family, "name": params["name"], "stage": stage,
              "parameters": bundle.info["parameters"], "fit_seconds": bundle.info["fit_seconds"],
              "peak_rss_mb": bundle.info["peak_rss_mb"], "train_rows": len(train_idx),
              "train_target_end": bundle.info["train_target_end"],
              "training_diagnostic_sample": bundle.info["training_diagnostic_sample"]}
    for key in ("best_iterations", "best_epochs", "parameter_count"):
        if key in bundle.info:
            result[key] = bundle.info[key]
    if len(valid_idx):
        start = time.perf_counter()
        prediction = bundle.predict(X_valid)
        result["predict_seconds"] = time.perf_counter() - start
        result["validation"] = metrics(y_valid, prediction)
        vm = meta.iloc[valid_idx]
        result["groups"] = {str(flag): metrics(y_valid[vm.masked.to_numpy() == flag], prediction[vm.masked.to_numpy() == flag])
                            for flag in (False, True)}
        result["inference_ms_per_1000"] = _benchmark(bundle, X_valid)
        if stage != "tuning":
            predictions = vm.copy()
            predictions["prediction"] = prediction
            predictions["error"] = prediction - y_valid
            predictions.to_parquet(RESULTS / f"predicciones_{stage}_{family}.parquet", index=False)
        bundle.info["evaluation"] = result["validation"]
        bundle.info["evaluation_target_start"] = str(vm.target_time.min().date())
        bundle.info["evaluation_target_end"] = str(vm.target_time.max().date())
        log(f"RESULTADO {LABELS[family]} {stage}: RMSE={result['validation']['rmse']:.6f} MAE={result['validation']['mae']:.6f}")
    bundle.save(directory)
    result["model_bytes"] = bundle.info["model_bytes"]
    # Comprobar la portabilidad del artefacto real, sin volver a entrenarlo.
    expected = bundle.predict(X_train[:64])
    del bundle
    gc.collect()
    reloaded = load_bundle(directory)
    np.testing.assert_allclose(reloaded.predict(X_train[:64]), expected, rtol=1e-5, atol=1e-6)
    del reloaded, X_train, X_valid
    gc.collect()
    write_json(completed, result)
    update_status(f"{family}_{stage}", status="complete", configuration=params["name"], result=result)
    return result


def development(family, X, meta):
    cfg = config()
    records = []
    for params in cfg[family]:
        directory = MODELS / "tuning" / family / params["name"]
        records.append(_run_fit(family, params, X, meta, "tuning", directory))
        _experiment_rows()
    best = min(records, key=lambda result: result["validation"]["rmse"])
    selected = next(p for p in cfg[family] if p["name"] == best["name"])
    write_json(RESULTS / f"seleccion_{family}.json", {"configuration": selected, "tuning": best})
    _run_fit(family, selected, X, meta, "confirmation", MODELS / "confirmation" / family, selected=best)


def freeze_selection():
    results = {family: json.loads((MODELS / "confirmation" / family / "complete.json").read_text()) for family in FAMILIES}
    winner = min(results, key=lambda family: results[family]["validation"]["rmse"])
    destination = RESULTS / "seleccion_fijada.json"
    if not destination.exists():
        write_json(destination, {"criterion": "Menor RMSE de confirmación temporal 2013, antes de abrir la prueba final",
                                 "recommended_family": winner, "confirmation": results,
                                 "config_sha256": sha256(ROOT / "config/modelado.json")})
    log(f"Selección fijada antes de evaluar 2014-2015: {LABELS[winner]}")


def final_stage(family, stage, X, meta):
    selection = json.loads((RESULTS / "seleccion_fijada.json").read_text())
    assert selection["config_sha256"] == sha256(ROOT / "config/modelado.json"), "La configuración cambió después de fijar la selección."
    chosen = json.loads((RESULTS / f"seleccion_{family}.json").read_text())
    directory = MODELS / stage / family
    result = _run_fit(family, chosen["configuration"], X, meta, stage, directory, selected=chosen["tuning"])
    if stage == "production":
        output = RESULTS / f"submission_{family}.csv"
        if not output.exists():
            X_test = np.load(CACHE / "X_test.npy", mmap_mode="r")
            test_meta = pd.read_parquet(CACHE / "test_metadata.parquet")
            model = load_bundle(directory)
            start = time.perf_counter()
            predictions = model.predict(X_test)
            result["test_predict_seconds"] = time.perf_counter() - start
            assert np.isfinite(predictions).all()
            pd.DataFrame({"ID": test_meta.ID, "Target": predictions}).to_csv(output, index=False)
            write_json(directory / "complete.json", result)
            if family == selection["recommended_family"]:
                shutil.copy2(output, RESULTS / "submission_recomendado.csv")
            log(f"Predicciones Test completas: {LABELS[family]}, {len(predictions):,} filas")


def baselines(meta, stage):
    train_idx, valid_idx = _indices(meta, stage)
    train, valid = meta.iloc[train_idx].copy(), meta.iloc[valid_idx].copy()
    train["month"] = train.target_time.dt.month
    valid["month"] = valid.target_time.dt.month
    climatology = train.groupby(["lat", "lon", "month"], observed=True).target.mean()
    keys = pd.MultiIndex.from_frame(valid[["lat", "lon", "month"]])
    climatology_pred = climatology.reindex(keys).to_numpy()
    fallback = valid.month.map(train.groupby("month").target.mean()).to_numpy()
    climatology_pred = np.where(np.isfinite(climatology_pred), climatology_pred, fallback)
    climatology_pred = np.nan_to_num(climatology_pred, nan=float(train.target.mean()))
    output = valid.copy()
    output["persistence"] = valid.last_tws
    output["climatology"] = climatology_pred
    output.to_parquet(RESULTS / f"referencias_{stage}.parquet", index=False)
    return [{"stage": stage, "algorithm": name, **metrics(valid.target, prediction)}
            for name, prediction in [("Persistencia causal", output.persistence), ("Climatología mensual", output.climatology)]]


def save_environment():
    packages = ["numpy", "pandas", "scipy", "scikit-learn", "xgboost", "torch", "streamlit", "plotly",
                "matplotlib", "seaborn", "joblib", "pyarrow", "nbformat", "nbclient", "ipykernel", "pytest", "psutil"]
    versions = {name: version(name) for name in packages}
    write_json(RESULTS / "entorno.json", {"python": platform.python_version(), "platform": platform.platform(),
                                         "processor": "Apple M1 Pro", "logical_cpus": psutil.cpu_count(),
                                         "total_memory_gb": psutil.virtual_memory().total / 1024 ** 3,
                                         "versions": versions})
    (ROOT / "requirements-modelado.lock.txt").write_text("# Versiones exactas utilizadas en la ejecución local\n" +
                                                       "\n".join(f"{name}=={number}" for name, number in versions.items()) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all", "development", "freeze", "holdout", "production"], default="all")
    parser.add_argument("--family", choices=["all", *FAMILIES], default="all")
    args = parser.parse_args()
    prepare()
    save_environment()
    if args.stage == "all" and args.family == "all":
        # PyTorch y XGBoost pueden cargar runtimes OpenMP diferentes en macOS.
        # Aislar cada familia conserva paralelismo y evita mezclar esas bibliotecas.
        script = ROOT / "scripts/entrenar_modelos.py"
        for family in FAMILIES:
            subprocess.run([sys.executable, "-X", "faulthandler", "-u", str(script),
                            "--stage", "development", "--family", family], check=True)
        freeze_selection()
        for stage in ("holdout", "production"):
            for family in FAMILIES:
                subprocess.run([sys.executable, "-X", "faulthandler", "-u", str(script),
                                "--stage", stage, "--family", family], check=True)
        _, meta = load_prepared()
        baseline_records = []
        for stage in ("tuning", "confirmation", "holdout"):
            baseline_records.extend(baselines(meta, stage))
        pd.DataFrame(baseline_records).to_csv(RESULTS / "metricas_referencias.csv", index=False)
        update_status("entrenamiento_completo", status="complete")
        log("Entrenamiento, prueba reservada y producción completos.")
        return
    X, meta = load_prepared()
    families = FAMILIES if args.family == "all" else (args.family,)
    if args.stage in ("all", "development"):
        for family in families:
            development(family, X, meta)
    if args.stage in ("all", "freeze"):
        freeze_selection()
    if args.stage in ("all", "holdout"):
        for family in families:
            final_stage(family, "holdout", X, meta)
    if args.stage in ("all", "production"):
        for family in families:
            final_stage(family, "production", X, meta)
    if args.stage == "all":
        baseline_records = []
        for stage in ("tuning", "confirmation", "holdout"):
            baseline_records.extend(baselines(meta, stage))
        pd.DataFrame(baseline_records).to_csv(RESULTS / "metricas_referencias.csv", index=False)
        update_status("entrenamiento_completo", status="complete")
    log("Etapa solicitada terminada.")


if __name__ == "__main__":
    main()
