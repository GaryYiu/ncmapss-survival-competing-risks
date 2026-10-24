"""converting raw N-CMAPSS HDF5 to data/derived/{engines,cycles}.csv. Run with no flags for the
DS01 self-check, with --build for the real DS01+DS03 tables.
"""

import os
import sys

import h5py
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from load import DATA_DIR, require_data_dir  # noqa: E402

# Failure mode of each file, only these two form a valid competing-risks pair.
MODES = {
    "N-CMAPSS_DS01-005.h5": "HPT",
    "N-CMAPSS_DS03-012.h5": "HPT+LPT",
}
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "derived")
CENSOR_AT = 100  # authors' observation cap, cycles
SPLITS = ("dev", "test")  # both hold different engines. both are subjects


def _cols(f, group):
    # Column names of one variable group, decoded from bytes.
    return [v.decode() for v in f[f"{group}_var"][:]]


def unit_ranges(f, split):
    #{unit: (start, stop)} row ranges. Asserts each unit is one contiguous block.
    # Find where the unit id changes; each run between changes is one engine's block.
    u = f[f"A_{split}"][:, 0].astype(int)
    starts = np.flatnonzero(np.r_[True, u[1:] != u[:-1]])
    stops = np.r_[starts[1:], len(u)]
    units = u[starts]
    assert len(units) == len(set(units)), "units not contiguous -- slicing assumption broken"
    return {int(un): (int(a), int(b)) for un, a, b in zip(units, starts, stops)}


def read_block(f, split, start, stop, groups=("A", "W", "X_s")):
    #One unit's rows as a DataFrame. Contiguous slice -> no full-file read.
    # Slice each group's array to the engine's rows and lay the columns side by side.
    data = {}
    for g in groups:
        arr = f[f"{g}_{split}"][start:stop]
        for i, c in enumerate(_cols(f, g)):
            data[c] = arr[:, i]
    df = pd.DataFrame(data)
    # odentifiers and flags are stored as floats in the file; make them integers.
    for c in ("unit", "cycle", "Fc", "hs"):
        if c in df:
            df[c] = df[c].astype(int)
    return df


def fit_normaliser(paths, step=20):
    """OLS of X_s on [W, 1], healthy rows only, pooled across files.
    Returns (beta, w_cols, s_cols, n_rows)."""
    Ws, Ss = [], []
    # collect every 20th healthy row (hs == 1) from every engine in every file.
    for p in paths:
        with h5py.File(p, "r") as f:
            w_cols, s_cols = _cols(f, "W"), _cols(f, "X_s")
            for split in SPLITS:
                for start, stop in unit_ranges(f, split).values():
                    hs = f[f"A_{split}"][start:stop, 3]
                    keep = np.flatnonzero(hs == 1)[::step] + start
                    if len(keep) == 0:
                        continue
                    Ws.append(f[f"W_{split}"][keep])
                    Ss.append(f[f"X_s_{split}"][keep])
    # one least-squares fit of all 14 sensors on the 4 flight conditions plus an intercept.
    W = np.vstack(Ws)
    S = np.vstack(Ss)
    X = np.c_[W, np.ones(len(W))]
    beta, *_ = np.linalg.lstsq(X, S, rcond=None)
    return beta, w_cols, s_cols, len(W)


def residualise(df, beta, w_cols, s_cols):
    # residual = observed sensor minus the value predicted from flight conditions.
    X = np.c_[df[w_cols].to_numpy(), np.ones(len(df))]
    res = df[s_cols].to_numpy() - X @ beta
    return pd.DataFrame(res, columns=[f"{c}_res" for c in s_cols], index=df.index)


def build(paths, out_dir=OUT_DIR):
    require_data_dir()
    # fit the shared normaliser first, so every engine is residualised the same way.
    beta, w_cols, s_cols, n_fit = fit_normaliser(paths)
    print(f"normaliser fit on {n_fit:,} healthy rows (subsampled)")

    engines, cycles = [], []
    for p in paths:
        name = os.path.basename(p)
        mode = MODES[name]
        ds = name.split("_")[1].split("-")[0]
        with h5py.File(p, "r") as f:
            for split in SPLITS:
                for unit, (start, stop) in unit_ranges(f, split).items():
                    # read this engine's rows, its health parameters (diagnostic only), and residualise.
                    df = read_block(f, split, start, stop)
                    theta = f[f"T_{split}"][start:stop]  # diagnostic ONLY, never a predictor
                    res = residualise(df, beta, w_cols, s_cols)

                    # average residuals and flight conditions per cycle: one flight becomes one row.
                    per_cycle = pd.concat([df[["cycle", "Fc", "hs"] + w_cols], res], axis=1)
                    g = per_cycle.groupby("cycle")
                    ct = g.mean(numeric_only=True)
                    ct["hs"] = g["hs"].min()  # constant within a cycle; min is safe
                    ct["n_rows"] = g.size()
                    ct.insert(0, "unit", unit)
                    ct.insert(0, "dataset", ds)
                    cycles.append(ct.reset_index())

                    # engine-level labels: lifetime, censoring by the 100-cycle cap, mode, fault onset.
                    life = int(df["cycle"].max())
                    fc_vals = df["Fc"].unique()
                    assert len(fc_vals) == 1, f"{ds} u{unit}: Fc varies within engine"
                    onset = df.loc[df["hs"] == 0, "cycle"]
                    engines.append({
                        "dataset": ds, "unit": unit, "split": split,
                        "Fc": int(fc_vals[0]), "mode": mode,
                        "lifetime": life,
                        "event": int(life < CENSOR_AT),  # 0 = right-censored by protocol
                        "t_s": int(onset.min()) if len(onset) else None,
                        "max_abs_theta": float(np.abs(theta).max()),  # diagnostic only
                    })
                    print(f"  {ds} u{unit:2d} {split:4s} life={life:3d} event={int(life < CENSOR_AT)} "
                          f"mode={mode} t_s={engines[-1]['t_s']}")

    # Write the two tables and the normaliser coefficients (reused by the app)
    eng = pd.DataFrame(engines)
    cyc = pd.concat(cycles, ignore_index=True)
    os.makedirs(out_dir, exist_ok=True)
    eng.to_csv(os.path.join(out_dir, "engines.csv"), index=False)
    cyc.to_csv(os.path.join(out_dir, "cycles.csv"), index=False)
    np.save(os.path.join(out_dir, "normaliser_beta.npy"), beta)
    return eng, cyc, beta


if __name__ == "__main__":
    if "--build" in sys.argv:
        # real analysis set: DS01 + DS03, 25 distinct engines (no dedupe needed, DS02 not used)
        eng, cyc, beta = build([os.path.join(DATA_DIR, n) for n in MODES])
        print(eng.groupby("mode").agg(n=("unit", "size"), censored=("event", lambda e: int((e == 0).sum()))))
        print("\nOK: engines", eng.shape, "cycles", cyc.shape, "-> data/derived/")
        sys.exit()

    # check on DS01 in a scratch dir, expected values verified against the raw A/Y arrays
    import tempfile
    paths = [os.path.join(DATA_DIR, "N-CMAPSS_DS01-005.h5")]
    eng, cyc, beta = build(paths, out_dir=tempfile.mkdtemp())

    #testing output
    assert len(eng) == 10, len(eng)
    assert set(eng.loc[eng.event == 0, "unit"]) == {1, 3}, eng[eng.event == 0]
    assert eng.lifetime.sum() == 894 == len(cyc), (eng.lifetime.sum(), len(cyc))
    assert (eng["mode"] == "HPT").all()
    assert cyc.groupby(["dataset", "unit"]).cycle.max().equals(
        eng.set_index(["dataset", "unit"]).lifetime.rename("cycle")
    )

    # normalisation check, the per-cycle residual should no longer track altitude
    raw_corr = np.corrcoef(cyc["alt"], cyc["T24_res"])[0, 1]
    print(f"\ncorr(alt, T24_res) per cycle = {raw_corr:+.3f}  (want ~0)")
    assert abs(raw_corr) < 0.3, raw_corr
    print(eng.to_string(index=False))
    print("\nOK: engines", eng.shape, "cycles", cyc.shape)
