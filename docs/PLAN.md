# Execution plan and working notes

Working roadmap for the dissertation. Four docs, four jobs:
- `CONTEXT.md` (repo root) — background and handoff: what the project is and why.
- `docs/START_HERE.md` — the step-by-step path through the project.
- `docs/PLAN.md` (this file) — status, decisions and findings per stage.
- `docs/stages.md` — plain-English explanation of how each stage works, for
  learning and review. Code files carry only short comments and point there.

**Current state in three lines.** Every stage has a first pass; the report
is at full length. Open: four figures (`figures_checklist.md`), citation
checks, and the Stage 3 decisions to settle at supervisor meeting 1 (below).

Supervisor-meeting documents: `docs/supervisor_meeting1.md` (work packages,
Gantt, literature-review plan, data summary) rendered to
`docs/Yiu_3173909Y_meeting1_planning.docx` via `pandoc`; the Gantt is generated
by `docs/gantt.py` -> `figures/gantt.png` (edit `WPS`/`MEETINGS` to replan).

Update the status line and "Findings" as stages complete.

Timeline: start 21 Sep 2026 -> submit 26 Apr 2027 (July graduation). Five
half-hour supervisor meetings; spend them at stage boundaries.

| Stage | Status | Code | Output |
|---|---|---|---|
| 0 Unblock | done | `src/load.py` | SSD symlink + loud-failure guard |
| 1 Survival table | **done 18 Sep** | `src/survival_table.py` | `data/derived/engines.csv`, `cycles.csv` |
| 2 Descriptive + gate | **done 18 Sep -- GATE PASSED** | `src/descriptive.py` | `figures/stage2_km_cif.png`, log-rank p=0.002 |
| 3 Core models | **done 18 Sep** (first pass) | `src/features.py`, `src/models.py`, `src/fine_gray.R` | `results/stage3_*.csv`, `models/*.pkl`, CIF figure |
| 4 Benchmarks | **done 18 Sep** (RSF local; LSTM on Colab) | `src/rsf_benchmark.py`, `src/lstm_benchmark.py` | `results/stage4_comparison.csv`, `stage4_lstm.csv`, `stage4_devtest_comparison.csv` |
| 5 Decision + app | **done** (first pass) | `src/predict.py`, `app/app.py` | cost-threshold decision, Streamlit app |
| 6 Writing | **full draft 18 Sep** (~8,200 body words; figures and citation checks remain) | `docs/report_draft.md` | 30-page dissertation, exec summary, code bundle |

---

## Stage 1 -- survival table (done)

**What was built.** `survival_table.py --build` reads DS01 + DS03 from the SSD
by contiguous per-unit slices (never a full-file read; ~18 s total) and writes:

- `engines.csv` -- 25 rows. `lifetime`, `event` (0 = right-censored at the
  100-cycle cap), `mode` (from file: DS01 = HPT, DS03 = HPT+LPT), `Fc`, `t_s`
  (fault onset from `hs`), `max_abs_theta` (diagnostic from `T`, **not a
  predictor**).
- `cycles.csv` -- 1,995 rows, one per engine-cycle: mean condition-normalised
  residual per sensor (`<sensor>_res`), mean flight conditions, `hs`, `Fc`.
- `normaliser_beta.npy` -- the pooled OLS coefficients (X_s on [W, 1]).

**Decisions made.**
- Normaliser fit on **healthy rows only** (`hs == 1`, subsampled every 20th),
  **pooled across both files**. A per-file normaliser would centre residuals per
  dataset and confound dataset with failure mode.
- **No dedupe needed.** The duplicated engines live in DS02 (copies of DS01/DS03
  engines). Using DS01 + DS03 without DS02 gives 25 distinct engines directly.
  (Earlier note about "dropping 3 DS03 units" was wrong -- DS03 holds the originals.)
- Linear-in-W normalisation. `corr(alt, T24_res)` per cycle = +0.03, so it
  works; upgrade to per-flight-phase terms only if Stage 3 residuals still
  track conditions.

**Checks.** `python src/survival_table.py` (no flag) is the self-check on DS01:
10 engines, units 1 & 3 censored, 894 cycle rows, all verified against raw A/Y.

**Findings (observations, not yet tested).**
- Censoring diagnostic reproduces the CONTEXT analysis exactly: every failed
  engine has `max_abs_theta` ~ 0.018-0.025; DS01 u3 = 0.0075 (clearly still
  healthy at 100 -> censored); DS01 u1 = 0.0172 (at failure level -> the
  ambiguous case for the sensitivity flip). Only 2/25 censored, both HPT.
- **HPT+LPT engines fail earlier**: lifetimes mostly 59-77 (median ~72) vs
  HPT-only 75-100 (median ~89). Suggests the modes separate -> good sign for
  the Stage 2 gate.
- **Fault onset `t_s` tracks flight class almost deterministically**: Fc=1 ->
  ~36-38, Fc=2 -> ~24-26, Fc=3 -> ~18-19, in both files. Usage severity
  governs when degradation starts. `Fc` is a legitimate predictor; expect it to
  carry a lot of the signal. (`t_s` itself is derived from `hs` -> descriptive
  only, never a predictor.)

## Stage 2 -- descriptive + go/no-go gate

Run `python src/descriptive.py`. Produces KM by mode (+ log-rank) and
Aalen-Johansen CIF per cause. **Gate:** do the two modes' curves separate?
Given the Stage 1 lifetimes they should. If log-rank p is not convincing at
n = 10 vs 15, that is a power statement, not evidence of no difference -- record
it honestly and keep competing risks as the primary framing *only if* the
descriptive separation is visually clear; otherwise single-event primary,
by-cause exploratory.

**Result (18 Sep): GATE PASSED -- competing risks is the primary framing.**
- Median survival: HPT-only **89** cycles vs HPT+LPT **72** cycles.
- Log-rank HPT vs HPT+LPT: stat = 9.60, **p = 0.0019** (n = 10 vs 15).
- Aalen-Johansen CIFs: HPT+LPT failures accumulate first (from ~59 cycles),
  HPT-only failures later (from ~75). Curves are well separated.
- Risk #3 from the proposal ("competing-risks signal too weak") is retired.
  Caveat for the write-up: the modes are labelled by *file*, so "mode" and
  "dataset" are the same variable here. DS02 (re-simulations of these very
  engines with reassigned flight profiles) is the argument that the two pools
  are the same engine population -- use it explicitly in the dissertation.
- Figure: `figures/stage2_km_cif.png` (candidate Figure 1 of the results).

## Stage 3 -- core models (first pass done 18 Sep)

**Design decision made: landmark analysis at L = 50, window 10.** The
"early-window features" idea in the original skeleton was wrong: before fault
onset engines differ only by tiny initial wear, so such features carry no
signal by construction. Verified: corr(PC2, lifetime) = -0.20 on pre-onset
flights vs **-0.82** at the landmark. One row per engine, no outcome leakage.
Time-varying Cox remains the alternative to raise at meeting 1.

**Results** (`results/stage3_cox.csv`, penalised Cox, ridge 0.1, covariates
Fc + PC1 + PC2; PCA explains 45% + 26%):
- **HPT+LPT, 15 events: strong signal.** PC2 HR 2.42, engine-bootstrap 95%
  [1.97, 3.06], p < 0.001. C-index 0.906 -> **0.892 optimism-corrected**.
  PH test passes for all covariates.
- **HPT, 8 events: underpowered.** No significant covariate; C-index 0.69 ->
  0.62 corrected (large optimism = over-fitting 8 events). Physical reason:
  HPT-only engines fail late (median 89), so at flight 50 the Fc=1 ones are
  ~12 flights past onset with little degradation to see. **Fix to try:** a
  later landmark (60-70) or the time-varying model for this cause.
- **Sensitivity** (`stage3_sensitivity_u1.csv`): flipping ambiguous DS01 u1 to
  "failed" moves log-HRs by <= 0.044. Robust.
- **Penalty, not method, drives the magnitudes.** Unpenalised Cox gives
  HPT+LPT Fc HR 0.04 / PC2 HR 17.4; Fine-Gray (`cmprsk::crr`, unpenalised)
  gives 0.04 / 16.9 -- the same. With ridge 0.01: 0.12 / 7.6; ridge 0.1:
  0.57 / 2.42. Bootstrap intervals for the unpenalised fits span orders of
  magnitude (Fc upper bound ~1e17). Directions agree across every method;
  magnitudes are only estimable with regularisation at n = 25. **Write-up:**
  penalised cause-specific Cox is primary; report the penalty as a
  sensitivity table; present Fine-Gray as direction-confirming, with the
  instability explained (this is proposal risk #1, observed).
- Reduced Fine-Gray spec (Fc + PC2) is still unstable, so the issue is
  quasi-separation (PC2 nearly separates the two modes, and mode = file), not
  covariate count.
- **Figure caveat:** `figures/stage3_cif_by_fc.png` shows the AFT model
  extrapolating the non-significant Fc effect to extremes at Fc = 1 and 3.
  Illustrative only; the dissertation figure should show CIF for an average
  engine with bootstrap bands.

**Open items for meeting 1:** landmark choice (50 vs later, or multi-landmark);
penalty selection (fixed vs CV -- CV is noisy at n=25); whether to try a
penalised Fine-Gray implementation (`fastcmprsk`) or keep Fine-Gray as
confirmatory only; Fc as numeric (1-3) vs categorical (costs 1 more df).

## Stage 4 -- benchmarks (done 18 Sep)

`results/stage4_comparison.csv`, same features and same engine-bootstrap
optimism recipe as Cox:

| cause | events | Cox C (app -> corr) | RSF C (app -> corr) |
|---|---|---|---|
| HPT | 8 | 0.694 -> 0.624 | 0.855 -> 0.709 |
| HPT+LPT | 15 | 0.906 -> **0.892** | 0.872 -> 0.803 |

Penalised Cox beats the forest where there is signal; the forest edges the
underpowered cause but with a large optimism gap. C-index only; time-dependent
AUC adds noise, not information, at n = 25.

**LSTM (run on Colab 18 Sep, `results/stage4_lstm.csv`).** Windows exported
locally (`--export`, 0.91 GB npz, 37 s): 349,252 training windows from the
15 dev engines, 232,885 test windows from the 10 test engines. **Test RMSE
9.58 flights**; **C-index of implied failure time at flight 50 on the test
engines 0.844.**

**Like-for-like finding (`results/stage4_devtest_comparison.csv`).** All-cause
Cox and RSF fitted on the same 15 dev engines and scored on the same 10 test
engines give **0.844 too**: 38 of 45 pairs, all three models. A 3-coefficient
penalised Cox, a forest, and an LSTM on 349k windows rank unseen engines
identically. Ranking at flight 50 is limited by the data, not the model.
This is the strongest form of the engines-not-rows argument and now anchors
report sections 5.4 (Table 5.7), 6.2 and the conclusion. Caveat: with 10 test
engines the C-index moves in steps of 1/45, so "identical value" is certain
but "identical ranking" is likely, not verified (the LSTM's per-engine
predictions were not saved; add that if a re-run happens).

## Stage 5 -- decision layer + Streamlit (first pass done)

`src/predict.py`: raw recent sensor means + flight conditions + Fc -> Stage 1
normaliser -> Stage 3 scaler/PCA -> two Weibull AFTs -> CIF -> service when
P(any failure) >= cost_planned / cost_unplanned. Self-test reproduces Stage 3's
PC scores for a real engine to 1e-6. `app/app.py` is a thin UI over it; runs
with `.venv/bin/streamlit run app/app.py`. Limitation: trained at landmark 50,
so predictions are for an engine at about that point in life.

## Stage 6 -- writing

Start the literature review in **October**, in parallel with Stages 2-3. Do not
leave all writing to February.

---

## Environment notes
- Internal disk ~1.6 GB free. Installed: `lifelines`, `scipy`, `scikit-survival`,
  `scikit-learn`, `streamlit`; R with `cmprsk`, `survival`. **TensorFlow not
  installed** (Colab for the LSTM). Raw data on the external SSD (`CONTEXT.md`
  > Files on disk).
- After Stage 1 the SSD is only needed for `lstm_benchmark.py` (raw windows).
  All survival modelling runs from `data/derived/*.csv`, which are committed.
