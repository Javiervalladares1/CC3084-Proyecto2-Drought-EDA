"""Tablas, figuras estáticas y síntesis calculadas de resultados reales."""
from __future__ import annotations

import itertools
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import feature_names, load_prepared
from .models import load_bundle, metrics
from .utils import FAMILIES, FIGURES, LABELS, MODELS, RESULTS, config, log, update_status, write_json

SHADES = ["#111111", "#666666", "#AAAAAA"]
STYLES = ["-", "--", ":"]
MARKERS = ["o", "s", "^"]
HATCHES = ["", "///", "..."]


def save_figure(name):
    plt.tight_layout()
    plt.savefig(FIGURES / name, dpi=210, bbox_inches="tight", facecolor="white")
    plt.close()


def grouped_metrics(wide, column):
    records = []
    for group, part in wide.groupby(column, observed=True, sort=True):
        for family in FAMILIES:
            records.append({column: group, "algorithm": LABELS[family], "family": family,
                            **metrics(part.target, part[f"pred_{family}"])})
    return pd.DataFrame(records)


def block_bootstrap(wide, repetitions=2000, block_length=3):
    """Remuestreo circular de bloques de meses observados, con errores pareados."""
    dates = sorted(wide.target_time.unique())
    counts = np.array([(wide.target_time == date).sum() for date in dates])
    squared = {family: np.array([np.square(part.target.to_numpy(dtype=float) - part[f"pred_{family}"].to_numpy(dtype=float)).sum()
                                 for _, part in wide.groupby("target_time", sort=True)]) for family in FAMILIES}
    rng = np.random.default_rng(config()["seed"])
    starts = rng.integers(0, len(dates), size=(repetitions, int(np.ceil(len(dates) / block_length))))
    indices = ((starts[:, :, None] + np.arange(block_length)) % len(dates)).reshape(repetitions, -1)[:, :len(dates)]
    denominators = counts[indices].sum(axis=1)
    distribution = {family: np.sqrt(sums[indices].sum(axis=1) / denominators) for family, sums in squared.items()}
    intervals = []
    for family in FAMILIES:
        lo, hi = np.quantile(distribution[family], [.025, .975])
        intervals.append({"family": family, "algorithm": LABELS[family], "rmse_low": lo, "rmse_high": hi})
    differences = []
    for first, second in itertools.combinations(FAMILIES, 2):
        diff = distribution[first] - distribution[second]
        lo, hi = np.quantile(diff, [.025, .975])
        differences.append({"first": first, "second": second, "difference_rmse": metrics(wide.target, wide[f"pred_{first}"])["rmse"] - metrics(wide.target, wide[f"pred_{second}"])["rmse"],
                            "ci_low": lo, "ci_high": hi, "includes_zero": bool(lo <= 0 <= hi)})
    return {"repetitions": repetitions, "block_length_observed_months": block_length,
            "observed_months": len(dates), "method": "Bootstrap circular de bloques temporales de meses observados; celdas del mismo mes se mantienen juntas",
            "intervals": intervals, "paired_differences": differences}


def _feature_group(name):
    if name.startswith("SPEI_"):
        return "SPEI " + name.split("_")[1] + " meses"
    if name.startswith("SOIL_MOISTURE"):
        return "Humedad del suelo"
    if name.startswith(("TWS_observable", "ultimo_TWS", "antiguedad_TWS")):
        return "TWS e historia"
    if name.startswith(("latitud", "longitud")):
        return "Ubicación"
    if name.startswith("month_"):
        return "Estacionalidad"
    if name.startswith("tiempo_"):
        return "Tiempo transcurrido"
    return "Disponibilidad"


def make_figures(wide, overall, grouped, sample, importance):
    import matplotlib.dates as mdates
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14, "axes.titlesize": 14,
                         "axes.labelsize": 13, "legend.fontsize": 12, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False, "text.color": "black", "axes.labelcolor": "black"})
    audit = json.loads((RESULTS / "auditoria.json").read_text())
    dates = pd.date_range(audit["train_start"], audit["train_end"], freq="MS")
    missing = pd.to_datetime(audit["train_missing_months"])
    observed = ~dates.isin(missing)
    fig, ax = plt.subplots(figsize=(9, 2.7))
    ax.bar(dates, observed.astype(int), width=26, color="#333333")
    ax.set(ylim=(0, 1.15), yticks=[0, 1], yticklabels=["Ausente", "Observado"],
           xlabel="Mes calendario", title="Cobertura de los registros de entrenamiento")
    save_figure("00_cobertura_calendario.png")
    regional = pd.read_csv(RESULTS / "series_regionales_eda.csv", parse_dates=["time"])
    global_ts = pd.read_csv(RESULTS / "serie_global_eda.csv", parse_dates=["time"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(global_ts.time, global_ts.mean_target, color="black")
    axes[0].set(title="Promedio global del objetivo", xlabel="Mes de entrada", ylabel="TWS estandarizado")
    axes[0].xaxis.set_major_locator(mdates.YearLocator(3))
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for i, (region, part) in enumerate(regional.groupby("region", sort=True)):
        temp = part.assign(month=part.time.dt.month, weighted=part.mean_target * part.rows)
        prof = temp.groupby("month").agg(weighted=("weighted", "sum"), rows=("rows", "sum"))
        axes[1].plot(prof.index, prof.weighted / prof.rows, label=region,
                     color=["#111111", "#555555", "#888888", "#BBBBBB"][i], linestyle=["-", "--", ":", "-."][i])
    axes[1].set(title="Ciclo mensual por región", xlabel="Mes de entrada", ylabel="TWS del siguiente mes", xticks=range(1, 13))
    axes[1].legend(fontsize=11)
    save_figure("01_eda_temporal_estacional.png")
    geo = pd.read_parquet(RESULTS / "mapa_eda.parquet")
    fig, ax = plt.subplots(figsize=(9, 4))
    points = ax.scatter(geo.lon, geo.lat, c=geo.mean_target, s=3, cmap="Greys", rasterized=True)
    fig.colorbar(points, ax=ax, label="TWS promedio estandarizado", pad=.02)
    ax.set(xlabel="Longitud", ylabel="Latitud", title="Cobertura terrestre y promedio del objetivo por celda")
    save_figure("02_eda_espacial.png")
    heldout = overall[overall.stage == "holdout"]
    baseline = pd.read_csv(RESULTS / "metricas_referencias.csv")
    base = baseline[baseline.stage == "holdout"]
    comparison = pd.concat([heldout[["algorithm", "rmse"]], base[["algorithm", "rmse"]]], ignore_index=True)
    fig, ax = plt.subplots(figsize=(9, 4))
    chart_labels = comparison.algorithm.replace({"Persistencia causal": "Persistencia\ncausal", "Climatología mensual": "Climatología\nmensual"})
    bars = ax.bar(chart_labels, comparison.rmse, color=SHADES + ["#D0D0D0", "#EEEEEE"], edgecolor="black", linewidth=.7)
    for bar, value in zip(bars, comparison.rmse):
        ax.text(bar.get_x() + bar.get_width() / 2, value + .01, f"{value:.4f}", ha="center", fontsize=13)
    ax.set(ylabel="RMSE (menor es mejor)", title="Prueba temporal reservada: comparación con referencias")
    ax.tick_params(axis="x", labelsize=11)
    ax.set_ylim(0, comparison.rmse.max() * 1.18)
    save_figure("03_comparacion_rmse.png")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4))
    for ax, column, scale, title, ylabel in [(axes[0], "fit_seconds", 60, "Tiempo de ajuste", "Minutos"),
                                            (axes[1], "inference_ms_per_1000", 1, "Tiempo de inferencia", "Milisegundos por 1 000 filas")]:
        bars = ax.bar(heldout.algorithm, heldout[column] / scale, color=SHADES, edgecolor="black", linewidth=.7)
        for bar, hatch, value in zip(bars, HATCHES, heldout[column] / scale):
            bar.set_hatch(hatch)
            ax.text(bar.get_x() + bar.get_width()/2, value * 1.03, f"{value:.2f}", ha="center", fontsize=12)
        ax.set(title=title, ylabel=ylabel)
        ax.margins(y=.17)
    save_figure("04_eficiencia.png")
    monthly = grouped["target_time"]
    fig, ax = plt.subplots(figsize=(10.5, 4))
    for i, family in enumerate(FAMILIES):
        part = monthly[monthly.family == family]
        ax.plot(pd.to_datetime(part.target_time), part.rmse, label=LABELS[family], color=SHADES[i], linestyle=STYLES[i], marker=MARKERS[i], markersize=4)
    ax.set(xlabel="Mes objetivo", ylabel="RMSE", title="Variación temporal del error en la prueba reservada")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(ncol=3)
    save_figure("05_error_temporal.png")
    for column, filename, title, label in [("region", "06_error_regional.png", "El desempeño depende de la región", "Región"),
                                          ("availability", "07_error_disponibilidad.png", "Efecto de la disponibilidad del TWS actual", "TWS actual")]:
        data = grouped[column]
        groups = list(data[column].unique())
        x = np.arange(len(groups))
        fig, ax = plt.subplots(figsize=(10.5, 4))
        for i, family in enumerate(FAMILIES):
            part = data[data.family == family].set_index(column).reindex(groups)
            ax.bar(x + (i - 1) * .23, part.rmse, width=.23, label=LABELS[family], color=SHADES[i], hatch=HATCHES[i], edgecolor="black", linewidth=.6)
        ax.set(xticks=x, xticklabels=groups, ylabel="RMSE", xlabel=label, title=title)
        ax.set_ylim(0, data.rmse.max() * 1.23)
        ax.legend(ncol=3, loc="upper center")
        save_figure(filename)
    age = grouped["age_group"]
    order = [group for group in ["0", "1", "2", "3", "4 a 6", "7 o más", "Sin historia"] if group in age.age_group.unique()]
    fig, ax = plt.subplots(figsize=(10.5, 4))
    for i, family in enumerate(FAMILIES):
        part = age[age.family == family].set_index("age_group").reindex(order)
        ax.plot(order, part.rmse, label=LABELS[family], color=SHADES[i], linestyle=STYLES[i], marker=MARKERS[i])
    ax.set(xlabel="Antigüedad del último TWS observable (meses)", ylabel="RMSE", title="Error según la historia de TWS disponible")
    ax.legend(ncol=3)
    save_figure("08_error_antiguedad.png")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharex=True, sharey=True)
    limit = max(float(sample.target.abs().quantile(.998)), 3)
    for i, family in enumerate(FAMILIES):
        axes[i].scatter(sample.target, sample[f"pred_{family}"], s=3, alpha=.15, color="black", rasterized=True)
        axes[i].plot([-limit, limit], [-limit, limit], color="#777777", linestyle="--")
        axes[i].set(title=LABELS[family], xlabel="Observado", xlim=(-limit, limit), ylim=(-limit, limit))
    axes[0].set_ylabel("Predicho")
    save_figure("09_observado_predicho.png")
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    for i, family in enumerate(FAMILIES):
        errors = wide[f"pred_{family}"] - wide.target
        ax.hist(errors, bins=90, range=(-2.5, 2.5), histtype="step", density=True, color=SHADES[i], linestyle=STYLES[i], label=LABELS[family])
    ax.axvline(0, color="black", linewidth=.7)
    ax.set(xlabel="Predicho - observado", ylabel="Densidad", title="Distribución de errores de predicción")
    ax.legend(ncol=3)
    save_figure("10_residuos.png")
    fig, ax = plt.subplots(figsize=(10.5, 4))
    for i, params in enumerate(config()["lstm"]):
        info = json.loads((MODELS / "tuning/lstm" / params["name"] / "metadata.json").read_text())
        learning = pd.DataFrame(info["learning_history"])
        ax.plot(learning.epoch, learning.validation_rmse, label=params["name"], color=SHADES[i], linestyle=STYLES[i])
        best = info["best_epochs"]
        row = learning[learning.epoch == best].iloc[0]
        ax.scatter([best], [row.validation_rmse], marker=MARKERS[i], s=35, color=SHADES[i])
    ax.set(xlabel="Época", ylabel="RMSE de validación 2011-2012", title="LSTM: aprendizaje y selección de la mejor época")
    ax.legend(ncol=3)
    save_figure("11_aprendizaje_lstm.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for i, family in enumerate(FAMILIES[:2]):
        part = importance[importance.family == family].sort_values("importance")
        axes[i].barh(part.group, part.importance, color=SHADES[i])
        axes[i].set(title=LABELS[family], xlabel="Importancia interna agrupada")
        axes[i].tick_params(axis="y", labelsize=12)
    save_figure("12_importancias.png")


def main():
    records = []
    for stage in ("confirmation", "holdout"):
        for family in FAMILIES:
            result = json.loads((MODELS / stage / family / "complete.json").read_text())
            records.append({"stage": stage, "family": family, "algorithm": LABELS[family], **result["validation"],
                            "fit_seconds": result["fit_seconds"], "predict_seconds": result["predict_seconds"],
                            "inference_ms_per_1000": result["inference_ms_per_1000"],
                            "peak_rss_mb": result["peak_rss_mb"], "model_size_mb": result["model_bytes"] / 1024 ** 2,
                            "configuration": result["name"]})
    overall = pd.DataFrame(records)
    overall.to_csv(RESULTS / "metricas_modelos.csv", index=False)
    wide = None
    for family in FAMILIES:
        pred = pd.read_parquet(RESULTS / f"predicciones_holdout_{family}.parquet")
        if wide is None:
            wide = pred.drop(columns=["prediction", "error"]).copy()
        assert np.array_equal(wide.ID.to_numpy(), pred.ID.to_numpy())
        assert np.allclose(wide.target, pred.target)
        wide[f"pred_{family}"] = pred.prediction.to_numpy()
        recalculated = metrics(wide.target, wide[f"pred_{family}"])
        reported = overall[(overall.stage == "holdout") & (overall.family == family)].iloc[0]
        assert abs(recalculated["rmse"] - reported.rmse) < 1e-9
    wide["availability"] = np.where(wide.masked, "Oculto", "Observado")
    wide["age_group"] = pd.cut(wide.age_months, [-1, .5, 1.5, 2.5, 3.5, 6.5, np.inf],
                                labels=["0", "1", "2", "3", "4 a 6", "7 o más"]).astype(str)
    wide.loc[~wide.has_history, "age_group"] = "Sin historia"
    grouped = {column: grouped_metrics(wide, column) for column in ["target_time", "region", "availability", "age_group"]}
    for column, name in [("target_time", "mes"), ("region", "region"), ("availability", "disponibilidad"), ("age_group", "antiguedad")]:
        grouped[column].to_csv(RESULTS / f"metricas_por_{name}.csv", index=False)
    series = wide.groupby("target_time").agg(observed=("target", "mean"), **{f"pred_{family}": (f"pred_{family}", "mean") for family in FAMILIES}).reset_index()
    series.to_csv(RESULTS / "series_predicciones.csv", index=False)
    sample = wide.sample(n=min(12000, len(wide)), random_state=config()["seed"])
    sample.to_parquet(RESULTS / "predicciones_visualizacion.parquet", index=False)
    wide.to_parquet(RESULTS / "predicciones_prueba_completas.parquet", index=False)
    _, meta = load_prepared()
    training = meta[meta.target_time < config()["holdout_start"]]
    lower, upper = training.target.quantile([.1, .9])
    wide["extreme_group"] = np.select([wide.target < lower, wide.target > upper], ["Bajo percentil 10", "Sobre percentil 90"], default="Intervalo central")
    extremes = grouped_metrics(wide, "extreme_group")
    extremes.to_csv(RESULTS / "metricas_extremos.csv", index=False)
    uncertainty = block_bootstrap(wide)
    write_json(RESULTS / "incertidumbre_bloques.json", uncertainty)
    importance_records = []
    for family in FAMILIES[:2]:
        model = load_bundle(MODELS / "holdout" / family)
        for name, value in zip(feature_names(), model.model.feature_importances_):
            importance_records.append({"family": family, "group": _feature_group(name), "importance": float(value)})
    importance = pd.DataFrame(importance_records).groupby(["family", "group"], as_index=False).importance.sum()
    importance.to_csv(RESULTS / "importancias_agrupadas.csv", index=False)
    baseline = pd.read_csv(RESULTS / "metricas_referencias.csv")
    heldout = overall[overall.stage == "holdout"].copy()
    persistence = float(baseline[(baseline.stage == "holdout") & (baseline.algorithm == "Persistencia causal")].rmse.iloc[0])
    heldout["improvement_vs_persistence_pct"] = (1 - heldout.rmse / persistence) * 100
    frozen = json.loads((RESULTS / "seleccion_fijada.json").read_text())
    summary = {"recommended_family": frozen["recommended_family"],
               "best_holdout_family_descriptive": str(heldout.loc[heldout.rmse.idxmin(), "family"]),
               "holdout_rows": len(wide), "holdout_observed_months": wide.target_time.nunique(),
               "holdout_mask_rate": float(wide.masked.mean()), "holdout_results": heldout.to_dict("records"),
               "baselines_holdout": baseline[baseline.stage == "holdout"].to_dict("records"),
               "extreme_thresholds_training": {"p10": lower, "p90": upper},
               "extreme_results": extremes.to_dict("records"), "uncertainty": uncertainty,
               "by_availability": grouped["availability"].to_dict("records"),
               "by_region": grouped["region"].to_dict("records"),
               "worst_months": grouped["target_time"].sort_values("rmse", ascending=False).head(6).assign(target_time=lambda x: x.target_time.astype(str)).to_dict("records"),
               "selection_criterion": frozen["criterion"]}
    write_json(RESULTS / "resumen_resultados.json", summary)
    log("Generación de figuras de resultados y EDA")
    make_figures(wide, overall, grouped, sample, importance)
    update_status("analisis", status="complete", figures=len(list(FIGURES.glob("*.png"))))
    log("Análisis y visualizaciones completos")


if __name__ == "__main__":
    main()
