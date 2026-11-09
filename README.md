# ncmapss-survival-competing-risks
A survival-analysis framing of aero-engine degradation with competing risks, on NASA's N-CMAPSS run-to-failure data, compared against the standard remaining-useful-life regression approach.

## Start here

| read | for |
|---|---|
| `docs/STEPS.md` | the step-by-step path: what to do at each stage |
| `docs/learn/` | glossary, worked examples, FAQ, self-test, runnable walkthrough |
| `docs/PLAN.md` | status, decisions and findings per stage |

## Quick start and reproduce

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
Rscript -e 'install.packages(c("cmprsk","survival"))'
SKIP_STAGE1=1 ./run_all.sh
```
Stage 1 (raw HDF5 -> derived tables) and the LSTM need the 19 GB raw data;
see `data/README.md`

## Layout

```
src/            one script per step
docs/           plan, stage guides, pseudocode, checklists
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv`).

```bash
uv sync                          # creates .venv and installs the exact versions in uv.lock
uv run python src/descriptive.py # if you want to run the descriptive survival
```

Python version is pinned in `.python-version`; uv downloads it if you don't have it already.
Use `uv run <command>` for everything

## Data

Raw N-CMAPSS data (19 GB) is not included. The derived tables in `data/derived/` are,
so every stage except Stage 1 runs without it. To rebuild them, download the data and set `NCMAPSS_DIR` to the folder, then run
`uv run python src/survival_table.py --build`.