import os
import h5py
import numpy as np
import pandas as pd

#variable groups in the HDF5 file
GROUPS = ["A", "W", "X_s", "X_v", "T"] # X_v is simulator only, consider dropping it

#symlink to raw data in external disc
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ncmapss")

def require_data_dir(path=DATA_DIR) #fail handling if data not found
    if not os.path.isdir(path):
        raise FileNotFoundError(
            f"{path} is not accessible."
        )

def load(path, split="dev", groups=GROUPS, units=None):
    require_data_dir()
    with h5py.File(path, "r") as f:
        # decode the column names stored as bytes in each group's *_var array.
        cols = {g: [v.decode() for v in f[f"{g}_var"][:]] for g in groups}
        # Read the auxiliary array (unit, cycle, Fc, hs) and build a row mask for the requested units.
        a = f[f"A{split}"][:]
        keep = np.isin(a[:, 0], units) if units is not None else slice(None)
        # Read each group's array and place its columns side by side (arrays are row-aligned).
        data = {}
        for g in groups:
            arr = a if g == "A" else f[f"{g}_{split}"][:]
            for i, c in enumerate(cols[g]):
                data[c] = arr [keep, i]
        #add the remaining useful life target columns
        data["RUL"] = f[f"Y_{split}"][keep, 0]
    #assemble the datafram and make identifiers integers
    df = pd.DataFrame(data)
    df["unit"] = df["unit"].astype(int)
    df["cycle"] = df["cycle"].astype(int)
    return df

if __name__ == "__main__":
    # testing the data load: load one engine from DS02 and confirm shape, columns and lifetime.
    p = os.path.join(DATA_DIR, "N-CMAPSS_DS02-006.h5")
    df = load(p, units=[2])
    assert {"unit", "cycle", "T24", "HPT_eff_mod", "alt", "RUL"} <= set(df.columns)
    assert df["unit"].nunique() == 1
    assert df["cycle"].max() == 75, df["cycle"].max()
    assert df["RUL"].iloc[-1] == 0
    print(df.shape, "OK")
    print(df[["unit", "cycle", "T24", "HPT_eff_mod", "RUL"]].head())