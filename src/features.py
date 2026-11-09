"""Stage 3 features: one row per engine at a landmark flight L.

Why a landmark and not early-flight features: docs/stages/stage3_models.md.
"""
import os

import pandas as pd

HERE = os.path.dirname(__file__)
DERIVED = os.path.join(HERE, "..", "data", "derived")
CAUSE = {"HPT": 1, "HPT+LPT": 2}  # 0 = censored


def load_tables(derived=DERIVED):
    # Read both Stage 1 tables and add the 0/1/2 cause code to the engine table.
    eng = pd.read_csv(os.path.join(derived, "engines.csv"))
    cyc = pd.read_csv(os.path.join(derived, "cycles.csv"))
    eng["cause"] = eng["mode"].map(CAUSE) * eng["event"]
    return eng, cyc


def res_cols(cyc):
    # The 14 condition-normalised sensor columns.
    return [c for c in cyc.columns if c.endswith("_res")]


def landmark_features(eng, cyc, L=50, window=10):
    """Engines alive after L, with mean residuals over cycles (L-window, L]."""
    # Keep engines still running after the landmark (time since landmark must be positive).
    alive = eng[eng["lifetime"] > L].copy()
    # Average each engine's residuals over the last `window` flights up to the landmark.
    w = cyc[(cyc["cycle"] > L - window) & (cyc["cycle"] <= L)]
    feat = w.groupby(["dataset", "unit"])[res_cols(cyc)].mean().reset_index()
    # Join labels and features; the survival time is measured from the landmark.
    df = alive.merge(feat, on=["dataset", "unit"], how="inner")
    df["time"] = df["lifetime"] - L  # time since landmark; > 0 by construction
    df.attrs["L"], df.attrs["window"] = L, window
    return df


if __name__ == "__main__":
    # Self-check: all 25 engines are alive at 50 and every feature is present.
    eng, cyc = load_tables()
    df = landmark_features(eng, cyc)
    assert len(df) == 25 and (df["time"] > 0).all()
    assert df[res_cols(cyc)].notna().all().all()
    print(df[["dataset", "unit", "Fc", "mode", "lifetime", "event", "time"]].head(8).to_string(index=False))
    print("OK", df.shape)
