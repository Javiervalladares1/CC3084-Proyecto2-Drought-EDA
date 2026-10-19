"""Inferencia de nuevos datos con la misma preparación causal del ajuste."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .data import CLIMATE, RAW_FEATURES, build_features, validate_input
from .utils import FAMILIES, MODELS, RESULTS, ROOT, config


@lru_cache(maxsize=1)
def historical_observations():
    if (RESULTS / "historia_observable.parquet").exists():
        return pd.read_parquet(RESULTS / "historia_observable.parquet")
    dtype = {column: "float32" for column in ["lat", "lon", "TWS_t", *CLIMATE]}
    frames = [pd.read_csv(ROOT / "data/raw" / name, usecols=RAW_FEATURES,
                          dtype=dtype, parse_dates=["time"]) for name in ("Train.csv", "Test.csv")]
    return pd.concat(frames, ignore_index=True)


def predict_models_isolated(X, families, *, stage="production"):
    outputs = {}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    with tempfile.TemporaryDirectory(prefix="tws-inferencia-") as temporary:
        directory = Path(temporary)
        source = directory / "inputs.npy"
        np.save(source, X)
        for family in families:
            destination = directory / f"{family}.npy"
            try:
                process = subprocess.run([sys.executable, "-m", "tws.predict_worker", "--family", family,
                                          "--stage", stage, "--input", str(source), "--output", str(destination)],
                                         env=env, capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"La ejecución de {family} excedió el tiempo disponible. Compruebe que el entorno y los modelos estén guardados localmente.") from exc
            if process.returncode != 0:
                raise RuntimeError(f"No fue posible ejecutar el modelo {family}. Revise que sus archivos y dependencias estén completos.")
            outputs[family] = np.load(destination)
    return outputs


def parse_csv(content):
    if isinstance(content, bytes):
        content = io.BytesIO(content)
    try:
        frame = pd.read_csv(content)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        raise ValueError("No fue posible leer el CSV. Use UTF-8 y columnas separadas por comas.") from exc
    if len(frame) > 300000:
        raise ValueError("Use un máximo de 300 000 observaciones por archivo.")
    # TWS es opcional en la aplicación; los otros datos climáticos son necesarios.
    if "TWS_t" not in frame:
        frame["TWS_t"] = np.nan
    validate_input(frame)
    return frame


def predict_frame(frame, families=FAMILIES, *, history=None):
    families = tuple(families)
    if not families or any(family not in FAMILIES for family in families):
        raise ValueError("Seleccione por lo menos un modelo válido.")
    clean = validate_input(frame)
    history = historical_observations() if history is None else history
    locations = clean[["lat", "lon"]].drop_duplicates()
    history = history.merge(locations, on=["lat", "lon"], how="inner")
    history = history[history.time <= clean.time.max()]
    X, meta = build_features(clean, history=history, window=config()["window"])
    output = meta[["time", "target_time", "lat", "lon", "masked", "last_tws", "age_months", "has_history"]].copy()
    output.insert(0, "ID", frame["ID"].to_numpy() if "ID" in frame else [f"nuevo_{i+1:06d}" for i in range(len(frame))])
    predictions = predict_models_isolated(X, families)
    for family in families:
        prediction = predictions[family]
        if not np.isfinite(prediction).all():
            raise FloatingPointError("El modelo produjo una predicción no válida.")
        output[f"pred_{family}"] = prediction
    return output
