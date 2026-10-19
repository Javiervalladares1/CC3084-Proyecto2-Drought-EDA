import io
import numpy as np
import pandas as pd
import pytest

from tws.data import CLIMATE, build_features
from tws.inference import parse_csv


def row():
    return {"time": "2018-12-01", "lat": 14.5, "lon": -90.5, **{col: 0.1 for col in CLIMATE}}


def test_csv_accepts_missing_tws_and_ignores_targets():
    frame = pd.DataFrame([{**row(), "target": 12345}])
    parsed = parse_csv(frame.to_csv(index=False).encode())
    assert parsed.TWS_t.isna().all()
    x, _ = build_features(parsed)
    changed = parsed.copy()
    changed.target = -999999
    x2, _ = build_features(changed)
    np.testing.assert_array_equal(x, x2)


def test_csv_reports_missing_covariates():
    frame = pd.DataFrame([row()]).drop(columns=[CLIMATE[0]])
    with pytest.raises(ValueError, match="Faltan columnas"):
        parse_csv(frame.to_csv(index=False).encode())


def test_empty_csv_is_rejected():
    with pytest.raises(ValueError, match="CSV"):
        parse_csv(b"")


def test_csv_rejects_repeated_month_cell():
    frame = pd.DataFrame([row(), row()])
    with pytest.raises(ValueError, match="repetidas"):
        parse_csv(frame.to_csv(index=False).encode())
