"""Genera datos derivados sin etiquetas para una aplicación portable."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from tws.data import CLIMATE, RAW_FEATURES
from tws.utils import RESULTS, ROOT, write_json


def main():
    dtype = {name: "float32" for name in ["lat", "lon", "TWS_t", *CLIMATE]}
    frames = [pd.read_csv(ROOT / "data/raw" / name, usecols=RAW_FEATURES, dtype=dtype, parse_dates=["time"])
              for name in ("Train.csv", "Test.csv")]
    history = pd.concat(frames, ignore_index=True)
    assert "target" not in history
    history.to_parquet(RESULTS / "historia_observable.parquet", index=False)
    test = pd.read_csv(ROOT / "data/raw/Test.csv")
    near = test[(test.lat == 14.5) & (test.lon == -90.5)]
    row = (near.iloc[-1] if len(near) else test.iloc[-1]).to_dict()
    row = {key: None if pd.isna(value) else value for key, value in row.items()}
    write_json(RESULTS / "ejemplo_entrada.json", row)
    pd.DataFrame([row])[["ID", *RAW_FEATURES]].to_csv(RESULTS / "ejemplo_nuevos_datos.csv", index=False)
    print(f"Historia observable sin target: {len(history):,} filas")


if __name__ == "__main__":
    main()
