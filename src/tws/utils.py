"""Rutas, registro y escritura segura de resultados."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/processed/modelado"
RESULTS = ROOT / "outputs/modelado"
MODELS = ROOT / "models"
FIGURES = ROOT / "figures/resultados"
FAMILIES = ("random_forest", "xgboost", "lstm")
LABELS = {"random_forest": "Random Forest", "xgboost": "XGBoost", "lstm": "LSTM"}


def config():
    return json.loads((ROOT / "config/modelado.json").read_text())


def json_default(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(type(obj).__name__)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    os.replace(temp, path)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def log(message):
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {message}", flush=True)


def update_status(stage, **info):
    path = RESULTS / "estado.json"
    state = json.loads(path.read_text()) if path.exists() else {}
    state[stage] = {"updated_utc": datetime.now(timezone.utc).isoformat(), **info}
    write_json(path, state)
