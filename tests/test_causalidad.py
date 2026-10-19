import numpy as np
import pandas as pd
import pytest

from tws.data import CLIMATE, SEQ_CHANNELS, build_features, feature_names, validate_input


def observations():
    dates = pd.to_datetime(["2020-01-01", "2020-03-01", "2020-04-01"])
    frame = pd.DataFrame({"time": dates, "lat": 14.5, "lon": -90.5,
                          "TWS_t": [1.0, np.nan, 8.0], "target": [999, 999, 999]})
    for column in CLIMATE:
        frame[column] = [1.0, 3.0, 4.0]
    return frame


def test_future_and_target_cannot_change_past_features():
    frame = observations()
    X, _ = build_features(frame)
    changed = frame.copy()
    changed.loc[2, ["TWS_t", *CLIMATE]] = 12345
    changed["target"] = -99999
    X2, _ = build_features(changed)
    np.testing.assert_array_equal(X[:2], X2[:2])


def test_lags_respect_missing_calendar_months_and_masked_tws():
    X, meta = build_features(observations())
    # Marzo: febrero es un hueco real, no la fila de enero.
    previous = X[1, 4 * len(SEQ_CHANNELS):5 * len(SEQ_CHANNELS)]
    np.testing.assert_array_equal(previous, np.zeros(len(SEQ_CHANNELS)))
    assert meta.loc[1, "last_tws"] == 1
    assert meta.loc[1, "age_months"] == 2
    assert meta.loc[1, "masked"]
    assert X[1, 5 * len(SEQ_CHANNELS) + 5] == 0


def test_explicit_mask_overrides_even_a_supplied_tws_value():
    frame = observations()
    frame["TWS_t_masked"] = [False, True, True]
    X, meta = build_features(frame)
    assert meta.loc[2, "last_tws"] == 1
    assert meta.loc[2, "age_months"] == 3
    assert X[2, 5 * len(SEQ_CHANNELS) + 5] == 0


def test_input_order_does_not_change_predictions_inputs():
    frame = observations()
    X, _ = build_features(frame)
    X2, _ = build_features(frame.iloc[[2, 0, 1]])
    np.testing.assert_array_equal(X2, X[[2, 0, 1]])
    assert X.shape[1] == len(feature_names())


def test_single_observation_matches_batch_with_the_same_history():
    frame = observations()
    X, _ = build_features(frame)
    single, _ = build_features(frame.iloc[[1]], history=frame.iloc[[0, 2]])
    np.testing.assert_array_equal(single[0], X[1])


@pytest.mark.parametrize("column,value", [("lat", 91), ("lon", -181), ("SPEI_01_t", "error"), ("SOIL_MOISTURE_t", np.inf)])
def test_invalid_inputs_raise_clear_errors(column, value):
    frame = observations()
    frame[column] = value
    with pytest.raises(ValueError):
        validate_input(frame)


def test_duplicate_cell_month_is_rejected():
    frame = observations()
    with pytest.raises(ValueError, match="repetidas"):
        validate_input(pd.concat([frame, frame.iloc[[0]]]))
