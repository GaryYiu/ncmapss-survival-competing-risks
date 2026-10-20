# Data (not committed)

## N-CMAPSS (headline dataset in HDF5, ~19 GB, DS01–DS07)

**Lives on the external SSD** (not enough free space locally). `data/ncmapss` is a symlink to:
```
/Volumes/Extreme SSD/N-CMAPSS data/data_set
```
Mount the SSD before running any code in `src/` that loads raw HDF5 — `load.py`
fails loudly if it isn't mounted.

Only DS01 + DS03 (competing-risks pool, 25 engines) and DS02 (comparability
check) are actually used; DS04–DS07 are unused. After initial load and aggregation(raw HDF5 →
tidy survival-table CSV, committed to the repo), the SSD is no longer needed for the rest of the project.

```bash
curl -L -o ncmapss.zip "https://phm-datasets.s3.amazonaws.com/NASA/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip"
unzip ncmapss.zip -d ncmapss/
```
Citation: M. Arias Chao, C. Kulkarni, K. Goebel, O. Fink (2021), "Aircraft Engine Run-to-Failure Dataset under Real Flight Conditions", NASA Prognostics Data Repository, NASA Ames Research Center. Companion paper: Arias Chao et al. (2021), Data 6(1):5.
