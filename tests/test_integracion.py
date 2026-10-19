from pathlib import Path
import json

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tws.inference import parse_csv, predict_frame
from tws.utils import FAMILIES, MODELS, RESULTS, ROOT

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def actual_forecast():
    for family in FAMILIES:
        assert (MODELS / "production" / family / "metadata.json").exists()
    frame = parse_csv((RESULTS / "ejemplo_nuevos_datos.csv").read_bytes())
    return frame, predict_frame(frame)


def test_predictions_match_saved_test_submissions(actual_forecast):
    frame, output = actual_forecast
    for family in FAMILIES:
        submission = pd.read_csv(RESULTS / f"submission_{family}.csv")
        expected = submission.set_index("ID").loc[frame.ID.iloc[0], "Target"]
        np.testing.assert_allclose(output[f"pred_{family}"].iloc[0], expected, rtol=1e-5, atol=1e-6)
    assert output.filter(like="pred_").notna().all().all()


def test_single_model_matches_comparison(actual_forecast):
    frame, output = actual_forecast
    selected = predict_frame(frame, ("xgboost",))
    assert list(selected.filter(like="pred_").columns) == ["pred_xgboost"]
    np.testing.assert_array_equal(selected.pred_xgboost, output.pred_xgboost)


def test_application_predicts_and_hides_performance():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert len(app.exception) == 0
    app.button(key="load_example").click().run()
    next(button for button in app.button if button.label == "Predecir").click().run()
    assert len(app.exception) == 0
    assert "forecast_result" in app.session_state
    assert len(app.session_state["forecast_result"].filter(like="pred_").columns) == 3
    app.selectbox(key="model_choice").select("XGBoost").run()
    assert len(app.exception) == 0
    next(button for button in app.button if button.label == "Predecir").click().run()
    assert list(app.session_state["forecast_result"].filter(like="pred_").columns) == ["pred_xgboost"]
    app.checkbox(key="show_performance").uncheck().run()
    assert any("rendimiento está oculto" in info.value for info in app.info)
    assert len(app.exception) == 0


def test_all_submissions_are_complete_and_finite():
    audit = json.loads((RESULTS / "auditoria.json").read_text())
    for family in FAMILIES:
        frame = pd.read_csv(RESULTS / f"submission_{family}.csv")
        assert list(frame.columns) == ["ID", "Target"]
        assert len(frame) == audit["test_rows"]
        assert frame.ID.is_unique
        assert np.isfinite(frame.Target).all()
