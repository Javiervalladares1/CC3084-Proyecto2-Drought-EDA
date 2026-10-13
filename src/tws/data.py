"""Preparación causal compartida por entrenamiento e inferencia.

Nunca utiliza target para construir entradas ni interpola con datos futuros.
La ventana contiene seis meses calendario, incluso cuando faltan registros.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .utils import CACHE, RESULTS, ROOT, config, log, sha256, update_status, write_json

CLIMATE = ["SPEI_01_t", "SPEI_03_t", "SPEI_06_t", "SPEI_12_t", "SOIL_MOISTURE_t"]
RAW_FEATURES = ["time", "lat", "lon", "TWS_t", *CLIMATE]
SEQ_CHANNELS = [*CLIMATE, "TWS_observable", "TWS_disponible", "registro_disponible"]
STATIC_CHANNELS = ["month_sin", "month_cos", "ultimo_TWS", "antiguedad_TWS_6m",
                   "historia_TWS_disponible", "latitud_90", "longitud_sin", "longitud_cos", "tiempo_120m"]


def feature_names(window=6):
    return [f"{column}_rezago_{lag}" for lag in range(window - 1, -1, -1)
            for column in SEQ_CHANNELS] + STATIC_CHANNELS


def _bool_values(series):
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.to_numpy()
    mapped = series.astype(str).str.strip().str.lower().map(
        {"true": True, "false": False, "1": True, "0": False})
    if mapped.isna().any():
        raise ValueError("TWS_t_masked solo acepta True o False.")
    return mapped.to_numpy(dtype=bool)


def validate_input(frame):
    missing = sorted(set(RAW_FEATURES) - set(frame.columns))
    if missing:
        raise ValueError("Faltan columnas: " + ", ".join(missing))
    if len(frame) == 0:
        raise ValueError("El archivo no contiene observaciones.")
    out = frame.loc[:, RAW_FEATURES].copy()
    dates = pd.to_datetime(out["time"], errors="coerce")
    if dates.isna().any():
        raise ValueError("time contiene fechas inválidas.")
    out["time"] = dates.dt.to_period("M").dt.to_timestamp()
    for col in ["lat", "lon", "TWS_t", *CLIMATE]:
        numeric = pd.to_numeric(out[col], errors="coerce")
        nonempty = out[col].notna() & out[col].astype(str).str.strip().ne("")
        if (nonempty & numeric.isna()).any():
            raise ValueError(f"{col} contiene valores no numéricos.")
        if np.isinf(numeric.to_numpy(dtype=np.float64)).any():
            raise ValueError(f"{col} contiene valores infinitos.")
        if col != "TWS_t" and numeric.isna().any():
            raise ValueError(f"{col} no puede estar vacío.")
        out[col] = numeric.astype(np.float32)
    if not out["lat"].between(-90, 90).all() or not out["lon"].between(-180, 180).all():
        raise ValueError("Las coordenadas están fuera de rango.")
    if "TWS_t_masked" in frame:
        out.loc[_bool_values(frame["TWS_t_masked"]), "TWS_t"] = np.nan
    if out.duplicated(["time", "lat", "lon"]).any():
        raise ValueError("Hay observaciones repetidas para la misma celda y mes.")
    return out.reset_index(drop=True)


def synthetic_visibility(dates, seed):
    """Bloques globales de faltantes; el calendario es independiente de target."""
    dates = pd.DatetimeIndex(dates)
    calendar = pd.date_range(dates.min(), dates.max(), freq="MS")
    rng = np.random.default_rng(seed)
    visible = np.zeros(len(calendar), dtype=bool)
    pos = 0
    while pos < len(calendar):
        visible[pos] = True
        hidden = int(rng.choice(np.arange(7), p=[.10, .20, .40, .20, .07, .02, .01]))
        pos += 1 + hidden
    return pd.Series(visible, index=calendar)


def build_features(frame, *, history=None, window=6, synthetic=False,
                   mask_seed=2026, output_path=None):
    requested = validate_input(frame)
    source = requested.copy()
    if history is not None and len(history):
        historical = validate_input(history)
        historical = historical[historical.time <= requested.time.max()]
        source = pd.concat([historical, source], ignore_index=True)
        source = source.drop_duplicates(["time", "lat", "lon"], keep="last")
    source = source.sort_values(["time", "lat", "lon"]).reset_index(drop=True)
    if synthetic:
        schedule = synthetic_visibility(source.time.unique(), mask_seed)
        visible = source.time.map(schedule).to_numpy(dtype=bool)
        # Las escasas excepciones por celda imitan la estructura del Test real.
        rng = np.random.default_rng(mask_seed + 1)
        visible |= rng.random(len(source)) < .0025
        source.loc[~visible, "TWS_t"] = np.nan
    calendar = pd.date_range(source.time.min(), source.time.max(), freq="MS")
    cells = source[["lat", "lon"]].drop_duplicates().sort_values(["lat", "lon"])
    cell_keys = pd.MultiIndex.from_frame(cells)
    src_cells = cell_keys.get_indexer(pd.MultiIndex.from_frame(source[["lat", "lon"]]))
    req_cells = cell_keys.get_indexer(pd.MultiIndex.from_frame(requested[["lat", "lon"]]))
    src_months = calendar.get_indexer(source.time)
    req_months = calendar.get_indexer(requested.time)
    n_months, n_cells = len(calendar), len(cells)
    # La rejilla densa ocupa decenas de MB, no una secuencia duplicada por fila.
    values = np.full((n_months, n_cells, 6), np.nan, dtype=np.float32)
    values[src_months, src_cells, :5] = source[CLIMATE].to_numpy(dtype=np.float32)
    values[src_months, src_cells, 5] = source.TWS_t.to_numpy(dtype=np.float32)
    record = np.zeros((n_months, n_cells), dtype=bool)
    record[src_months, src_cells] = True
    available = np.isfinite(values[:, :, 5])
    last = np.zeros((n_months, n_cells), dtype=np.float32)
    age = np.zeros((n_months, n_cells), dtype=np.int16)
    known = np.zeros((n_months, n_cells), dtype=bool)
    last_value = np.zeros(n_cells, dtype=np.float32)
    last_date = np.full(n_cells, -1, dtype=np.int16)
    for t in range(n_months):
        fresh = available[t]
        last_value[fresh] = values[t, fresh, 5]
        last_date[fresh] = t
        last[t] = last_value
        known[t] = last_date >= 0
        age[t] = np.where(last_date >= 0, t - last_date, 0)
    values = np.nan_to_num(values, nan=0.0)
    n_features = window * len(SEQ_CHANNELS) + len(STATIC_CHANNELS)
    shape = (len(requested), n_features)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        X = np.lib.format.open_memmap(output_path, mode="w+", dtype=np.float32, shape=shape)
    else:
        X = np.zeros(shape, dtype=np.float32)
    for start in range(0, len(requested), 100000):
        stop = min(start + 100000, len(requested))
        tm, cm = req_months[start:stop], req_cells[start:stop]
        for step, lag in enumerate(range(window - 1, -1, -1)):
            hist_t = tm - lag
            valid = hist_t >= 0
            hist_t = np.maximum(hist_t, 0)
            offset = step * len(SEQ_CHANNELS)
            X[start:stop, offset:offset + 6] = values[hist_t, cm] * valid[:, None]
            X[start:stop, offset + 6] = available[hist_t, cm] & valid
            X[start:stop, offset + 7] = record[hist_t, cm] & valid
        date = requested.time.iloc[start:stop]
        month = date.dt.month.to_numpy()
        lat = requested.lat.iloc[start:stop].to_numpy()
        lon = np.deg2rad(requested.lon.iloc[start:stop].to_numpy())
        elapsed = ((date.dt.year.to_numpy() - 2002) * 12 + month - 5) / 120
        static = np.column_stack([
            np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12),
            last[tm, cm], np.minimum(age[tm, cm], 24) / 6, known[tm, cm],
            lat / 90, np.sin(lon), np.cos(lon), elapsed,
        ])
        X[start:stop, window * len(SEQ_CHANNELS):] = static
    if isinstance(X, np.memmap):
        X.flush()
    meta = requested[["time", "lat", "lon"]].copy()
    meta["target_time"] = meta.time + pd.offsets.MonthBegin(1)
    meta["masked"] = ~available[req_months, req_cells]
    meta["last_tws"] = last[req_months, req_cells]
    meta["age_months"] = age[req_months, req_cells]
    meta["has_history"] = known[req_months, req_cells]
    meta["cell_id"] = req_cells.astype(np.int32)
    return X, meta


def latitude_band(latitude):
    return pd.cut(latitude, [-90, -30, 0, 30, 90],
                  labels=["Sur extratropical", "Trópico sur", "Trópico norte", "Norte extratropical"],
                  include_lowest=True, right=False).astype(str)


def prepare(force=False):
    cfg = config()
    if (CACHE / "preparacion.json").exists() and not force:
        prepared = json.loads((CACHE / "preparacion.json").read_text())
        for key in ("window", "mask_seed"):
            if prepared["config"][key] != cfg[key]:
                raise ValueError("Cambió la preparación de entradas. Regenere la caché y los modelos antes de continuar.")
        current_stats = {name: {"bytes": (ROOT / "data/raw" / name).stat().st_size,
                               "mtime_ns": (ROOT / "data/raw" / name).stat().st_mtime_ns}
                         for name in ("Train.csv", "Test.csv")}
        if current_stats != prepared.get("source_stats"):
            current_hashes = {name: sha256(ROOT / "data/raw" / name) for name in current_stats}
            if current_hashes != prepared["source_sha256"]:
                raise ValueError("Los archivos crudos cambiaron. No se reutilizarán matrices o modelos de otros datos.")
            prepared["source_stats"] = current_stats
            write_json(CACHE / "preparacion.json", prepared)
        log("Preparación existente. Se reutilizan matrices y máscaras.")
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    dtype = {column: "float32" for column in ["lat", "lon", "TWS_t", *CLIMATE,
                                              "month_sin", "month_cos", "target"]}
    log("Lectura y auditoría de Train.csv y Test.csv")
    train = pd.read_csv(ROOT / "data/raw/Train.csv", dtype=dtype, parse_dates=["time"])
    test = pd.read_csv(ROOT / "data/raw/Test.csv", dtype={k: v for k, v in dtype.items() if k != "target"}, parse_dates=["time"])
    assert train.sample_id.is_unique and test.ID.is_unique
    assert not train.duplicated(["time", "lat", "lon"]).any()
    assert not test.duplicated(["time", "lat", "lon"]).any()
    assert np.array_equal(test.TWS_t_masked.to_numpy(), test.TWS_t.isna().to_numpy())
    assert np.isfinite(train.target).all()
    assert train.target.notna().all()
    target_time = train.time + pd.offsets.MonthBegin(1)
    # Comprobación del significado del objetivo, nunca imputación de entradas.
    keys = pd.MultiIndex.from_frame(train[["time", "lat", "lon"]])
    future_keys = pd.MultiIndex.from_arrays([target_time, train.lat, train.lon])
    linked = keys.get_indexer(future_keys)
    present = linked >= 0
    max_difference = float(np.max(np.abs(train.target.to_numpy()[present] - train.TWS_t.to_numpy()[linked[present]])))
    assert max_difference < 1e-5, max_difference
    summary = {
        "train_rows": len(train), "test_rows": len(test), "train_columns": list(train.columns),
        "test_columns": list(test.columns), "train_start": str(train.time.min().date()),
        "train_end": str(train.time.max().date()), "test_start": str(test.time.min().date()),
        "test_end": str(test.time.max().date()), "train_observed_months": train.time.nunique(),
        "test_observed_months": test.time.nunique(), "cells": len(train[["lat", "lon"]].drop_duplicates()),
        "train_missing_months": [str(x.date()) for x in pd.date_range(train.time.min(), train.time.max(), freq="MS").difference(train.time.unique())],
        "train_nulls": train.isna().sum().to_dict(), "test_nulls": test.isna().sum().to_dict(),
        "train_duplicates": 0, "test_duplicates": 0,
        "test_mask_rate": float(test.TWS_t_masked.mean()), "target_linked_rows": int(present.sum()),
        "target_link_max_absolute_difference": max_difference,
        "north_fraction": float((train.lat >= 0).mean()),
        "raw_sha256": {name: sha256(ROOT / "data/raw" / name) for name in ["Train.csv", "Test.csv"]},
        "config": cfg,
    }
    train.select_dtypes("number").describe(percentiles=[.01, .25, .5, .75, .99]).T.to_csv(RESULTS / "estadisticas_originales.csv")
    test.groupby("time").agg(rows=("ID", "size"), masked_rate=("TWS_t_masked", "mean")).to_csv(RESULTS / "mascara_test_por_mes.csv")
    log("Construcción de entradas con enmascaramiento temporal sintético")
    X, meta = build_features(train, window=cfg["window"], synthetic=True,
                             mask_seed=cfg["mask_seed"], output_path=CACHE / "X.npy")
    meta["ID"] = train.sample_id.to_numpy()
    meta["target"] = train.target.to_numpy()
    meta["region"] = latitude_band(meta.lat)
    meta.to_parquet(CACHE / "metadata.parquet", index=False)
    summary["synthetic_mask_rate"] = float(meta.masked.mean())
    summary["feature_count"] = X.shape[1]
    summary["feature_names"] = feature_names(cfg["window"])
    summary["window"] = cfg["window"]
    log("Construcción causal de entradas para Test.csv, usando historia observable")
    Xt, mt = build_features(test, history=train, window=cfg["window"], output_path=CACHE / "X_test.npy")
    mt["ID"] = test.ID.to_numpy()
    mt["region"] = latitude_band(mt.lat)
    mt.to_parquet(CACHE / "test_metadata.parquet", index=False)
    # Muestra determinista solo para exploración interactiva, nunca para métricas.
    sample = train.sample(n=min(40000, len(train)), random_state=cfg["seed"])
    sample.to_parquet(RESULTS / "muestra_exploracion.parquet", index=False)
    train.groupby("time").agg(mean_target=("target", "mean"), mean_tws=("TWS_t", "mean"),
                              rows=("target", "size")).to_csv(RESULTS / "serie_global_eda.csv")
    train.assign(region=latitude_band(train.lat)).groupby(["time", "region"], observed=True).agg(
        mean_target=("target", "mean"), mean_spei12=("SPEI_12_t", "mean"), rows=("target", "size")
    ).to_csv(RESULTS / "series_regionales_eda.csv")
    train.groupby(["lat", "lon"]).agg(mean_target=("target", "mean"), std_target=("target", "std"),
                                       rows=("target", "size")).reset_index().to_parquet(RESULTS / "mapa_eda.parquet", index=False)
    partitions = {
        "ajuste_entrenamiento": meta.target_time <= cfg["train_end"],
        "ajuste_validacion": meta.target_time.between(cfg["tuning_start"], cfg["tuning_end"]),
        "confirmacion_entrenamiento": meta.target_time < cfg["confirmation_start"],
        "confirmacion_validacion": meta.target_time.between(cfg["confirmation_start"], cfg["confirmation_end"]),
        "prueba_entrenamiento": meta.target_time < cfg["holdout_start"],
        "prueba_reservada": meta.target_time.between(cfg["holdout_start"], cfg["holdout_end"]),
    }
    summary["partitions"] = {key: {"rows": int(mask.sum()), "target_start": str(meta.loc[mask, "target_time"].min().date()),
                                 "target_end": str(meta.loc[mask, "target_time"].max().date()),
                                 "masked_rate": float(meta.loc[mask, "masked"].mean())}
                             for key, mask in partitions.items()}
    write_json(RESULTS / "auditoria.json", summary)
    write_json(CACHE / "preparacion.json", {"source_sha256": summary["raw_sha256"], "feature_names": summary["feature_names"], "config": cfg})
    update_status("preparacion", status="complete", rows=len(meta), features=X.shape[1])
    log(f"Preparación completa: {X.shape}; máscara sintética {meta.masked.mean():.2%}")


def load_prepared():
    return np.load(CACHE / "X.npy", mmap_mode="r"), pd.read_parquet(CACHE / "metadata.parquet")


if __name__ == "__main__":
    prepare()
