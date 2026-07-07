"""Model ladder on the signal-return panel: predict next-month signal return from
trailing momentum/vol. Expanding window, strictly out-of-sample."""
import pandas as pd
from tracks.gkx.cz_data import validate_panel


def _features(panel: pd.DataFrame) -> pd.DataFrame:
    df = validate_panel(panel).sort_values(["signalname", "date"])
    g = df.groupby("signalname")["ret"]
    df["mom12"] = g.transform(lambda s: s.rolling(12).mean())
    df["vol12"] = g.transform(lambda s: s.rolling(12).std())
    df["y"] = g.shift(-1)  # next-month return
    return df.dropna(subset=["mom12", "vol12", "y"])


def _make_model(name: str):
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    return {
        "ols": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "gbrt": GradientBoostingRegressor(random_state=0, n_estimators=100, max_depth=2),
    }[name]


def expanding_window_predict(panel: pd.DataFrame, model: str = "ridge",
                             min_train_months: int = 24, refit_every: int = 12) -> pd.DataFrame:
    """Predict each month's cross-section of signal returns out-of-sample.

    Follows Gu-Kelly-Xiu: the model is retrained on an EXPANDING window every
    `refit_every` months (default 12 = annual) and reused for the intervening
    monthly predictions. Annual refit is both faithful to the paper and keeps the
    tree model tractable (monthly GBRT refit is ~12x slower for no methodological gain).
    """
    df = _features(panel)
    months = sorted(df["date"].unique())
    out = []
    fitted = None
    for i in range(min_train_months, len(months)):
        test = df[df["date"] == months[i]]
        if test.empty:
            continue
        if fitted is None or (i - min_train_months) % refit_every == 0:
            train = df[df["date"] < months[i]]
            if train.empty:
                continue
            fitted = _make_model(model)
            fitted.fit(train[["mom12", "vol12"]], train["y"])
        out.append(pd.DataFrame({
            "date": test["date"].values,
            "signal": test["signalname"].values,
            "y_true": test["y"].values,
            "y_pred": fitted.predict(test[["mom12", "vol12"]]),
        }))
    if not out:
        raise ValueError("not enough months for expanding window")
    return pd.concat(out, ignore_index=True)
