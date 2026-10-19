"""Tres familias de regresión con el mismo contrato de predicción."""
from __future__ import annotations

import copy
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from .data import SEQ_CHANNELS, STATIC_CHANNELS, feature_names
from .utils import config, log, write_json


def metrics(observed, predicted):
    from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
    observed = np.asarray(observed, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    if not np.isfinite(observed).all() or not np.isfinite(predicted).all():
        raise ValueError("Las métricas requieren observaciones y predicciones finitas.")
    return {"n": len(observed), "rmse": float(root_mean_squared_error(observed, predicted)),
            "mae": float(mean_absolute_error(observed, predicted)),
            "r2": float(r2_score(observed, predicted)),
            "bias": float(np.mean(predicted - observed))}


def seed_everything(seed, threads, family):
    random.seed(seed)
    np.random.seed(seed)
    if family == "lstm":
        import torch
        torch.manual_seed(seed)
        torch.set_num_threads(threads)
        torch.use_deterministic_algorithms(True)


@dataclass
class ModelBundle:
    family: str
    model: object
    info: dict
    mean: np.ndarray | None = None
    scale: np.ndarray | None = None

    def predict(self, X, *, batch_size=8192):
        X = np.asarray(X, dtype=np.float32)
        if X.ndim != 2 or X.shape[1] != len(self.info["feature_names"]):
            raise ValueError("Las entradas no coinciden con las variables del modelo.")
        base_index = self.info["window"] * len(SEQ_CHANNELS) + 2
        base = X[:, base_index]
        if self.family != "lstm":
            residual = np.asarray(self.model.predict(X), dtype=np.float32)
        else:
            import torch
            self.model.eval()
            residual = np.empty(len(X), dtype=np.float32)
            with torch.inference_mode():
                for start in range(0, len(X), batch_size):
                    stop = min(start + batch_size, len(X))
                    inputs = (X[start:stop] - self.mean) / self.scale
                    residual[start:stop] = self.model(torch.from_numpy(inputs)).numpy()
        return residual + base

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        if self.family == "random_forest":
            path = directory / "model.joblib"
            joblib.dump(self.model, path, compress=3)
        elif self.family == "xgboost":
            path = directory / "model.ubj"
            self.model.save_model(path)
        else:
            import torch
            path = directory / "model.pt"
            torch.save({"state_dict": self.model.state_dict(), "mean": torch.from_numpy(self.mean),
                        "scale": torch.from_numpy(self.scale)}, path)
        self.info["model_bytes"] = path.stat().st_size
        write_json(directory / "metadata.json", self.info)


def load_bundle(directory):
    directory = Path(directory)
    info = json.loads((directory / "metadata.json").read_text())
    family = info["family"]
    if family == "random_forest":
        return ModelBundle(family, joblib.load(directory / "model.joblib"), info)
    if family == "xgboost":
        from xgboost import XGBRegressor
        model = XGBRegressor()
        model.load_model(directory / "model.ubj")
        model.set_params(n_jobs=config()["threads"])
        return ModelBundle(family, model, info)
    params = info["parameters"]
    import torch
    from .neural import WaterLSTM
    model = WaterLSTM(window=info["window"], hidden_size=params["hidden_size"],
                      head_size=params["head_size"], dropout=params["dropout"])
    checkpoint = torch.load(directory / "model.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    torch.set_num_threads(config()["threads"])
    return ModelBundle(family, model, info, checkpoint["mean"].numpy(), checkpoint["scale"].numpy())


def fit_model(family, parameters, X_train, y_train, *, X_val=None, y_val=None,
              fixed_iterations=None, fixed_epochs=None, stage="tuning"):
    cfg = config()
    seed_everything(cfg["seed"], cfg["threads"], family)
    parameters = dict(parameters)
    parameters.pop("name", None)
    start = time.perf_counter()
    base_index = cfg["window"] * len(SEQ_CHANNELS) + 2
    residual = np.asarray(y_train - X_train[:, base_index], dtype=np.float32)
    residual_val = None if X_val is None else np.asarray(y_val - X_val[:, base_index], dtype=np.float32)
    info = {"family": family, "stage": stage, "parameters": parameters,
            "seed": cfg["seed"], "threads": cfg["threads"], "device": "cpu",
            "window": cfg["window"], "feature_names": feature_names(cfg["window"]),
            "train_rows": len(y_train), "prediction": "ultimo_TWS_observable + correccion_modelada"}
    history = []
    mean = scale = None
    if family == "random_forest":
        from sklearn.ensemble import RandomForestRegressor
        parameters["max_samples"] = min(parameters["max_samples"], len(y_train))
        model = RandomForestRegressor(**parameters, random_state=cfg["seed"], n_jobs=cfg["threads"], bootstrap=True)
        model.fit(X_train, residual)
    elif family == "xgboost":
        from xgboost import XGBRegressor
        if fixed_iterations is not None:
            parameters["n_estimators"] = fixed_iterations
        extras = {"early_stopping_rounds": 70} if X_val is not None else {}
        model = XGBRegressor(**parameters, objective="reg:squarederror", tree_method="hist",
                              device="cpu", n_jobs=cfg["threads"], random_state=cfg["seed"],
                              eval_metric="rmse", **extras)
        model.fit(X_train, residual, eval_set=[(X_val, residual_val)] if X_val is not None else None, verbose=False)
        if X_val is not None:
            info["best_iterations"] = int(model.best_iteration + 1)
            history = [{"iteration": i + 1, "validation_rmse": value}
                       for i, value in enumerate(model.evals_result()["validation_0"]["rmse"])]
        else:
            info["best_iterations"] = int(parameters["n_estimators"])
    elif family == "lstm":
        import torch
        from torch import nn
        from .neural import WaterLSTM
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        for begin in range(0, len(X_train), 100000):
            scaler.partial_fit(X_train[begin:begin + 100000])
        mean, scale = scaler.mean_.astype(np.float32), scaler.scale_.astype(np.float32)
        model = WaterLSTM(window=cfg["window"], hidden_size=parameters["hidden_size"],
                          head_size=parameters["head_size"], dropout=parameters["dropout"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=parameters["learning_rate"],
                                      weight_decay=parameters["weight_decay"])
        criterion = nn.MSELoss()
        max_epochs = fixed_epochs or parameters["max_epochs"]
        best_loss, best_state, best_epoch, stale = float("inf"), None, 0, 0
        rng = np.random.default_rng(cfg["seed"])
        bundle = ModelBundle(family, model, info, mean, scale)
        for epoch in range(1, max_epochs + 1):
            epoch_start = time.perf_counter()
            model.train()
            order = rng.permutation(len(y_train))
            sum_loss = 0.0
            batch_size = parameters["batch_size"]
            for begin in range(0, len(order), batch_size):
                idx = order[begin:begin + batch_size]
                inputs = torch.from_numpy((X_train[idx] - mean) / scale)
                labels = torch.from_numpy(residual[idx])
                optimizer.zero_grad(set_to_none=True)
                output = model(inputs)
                loss = criterion(output, labels)
                if not torch.isfinite(loss):
                    raise FloatingPointError("La pérdida de LSTM dejó de ser finita.")
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                optimizer.step()
                sum_loss += loss.item() * len(idx)
            train_rmse = float(np.sqrt(sum_loss / len(order)))
            val_rmse = None
            if X_val is not None:
                prediction = bundle.predict(X_val)
                val_rmse = metrics(y_val, prediction)["rmse"]
                if val_rmse < best_loss - 1e-5:
                    best_loss, best_epoch = val_rmse, epoch
                    best_state = copy.deepcopy(model.state_dict())
                    stale = 0
                else:
                    stale += 1
            history.append({"epoch": epoch, "train_rmse": train_rmse, "validation_rmse": val_rmse,
                            "seconds": time.perf_counter() - epoch_start})
            suffix = f" validación={val_rmse:.5f}" if val_rmse is not None else ""
            log(f"LSTM {stage} época {epoch}/{max_epochs}: RMSE entrenamiento={train_rmse:.5f}{suffix} ({history[-1]['seconds']:.1f}s)")
            if X_val is not None and stale >= parameters["patience"]:
                break
        if best_state is not None:
            model.load_state_dict(best_state)
        info["best_epochs"] = best_epoch if X_val is not None else max_epochs
        info["parameter_count"] = sum(p.numel() for p in model.parameters())
    else:
        raise ValueError(f"Familia desconocida: {family}")
    info["fit_seconds"] = time.perf_counter() - start
    info["parameters"] = parameters
    info["learning_history"] = history
    log(f"Ajuste completo {family} {stage}: {info['fit_seconds']:.1f}s")
    return ModelBundle(family, model, info, mean, scale)
