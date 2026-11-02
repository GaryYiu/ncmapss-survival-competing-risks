# START HERE: the step-by-step path through the project

This is the one document to follow. Every other file is referenced from here
at the point you need it. Work top to bottom; tick boxes as you go.

## Where everything lives (so nothing feels scattered)

| you want | open |
|---|---|
| the plan and where things stand | `docs/PLAN.md` |
| why the project is shaped this way | `CONTEXT.md` |
| how a stage works + what to read first | `docs/stages/stageN_*.md` |
| a language-neutral sketch of a script | `docs/pseudocode.md` |
| what each stage checks, and what to do when a check fails | `docs/verification_flowcharts.md` |
| the dissertation text | `docs/report_draft.md` |
| which figures/tables are missing | `docs/figures_checklist.md` |
| graphics to help you understand a concept | `docs/concept_graphics_prompts.md` |
| learn the concepts: glossary, worked examples by hand, FAQ, self-test, runnable walkthrough | `docs/learn/` |
| supervisor meeting 1 upload | `docs/Yiu_3173909Y_meeting1_planning.docx` |
| slides and viva questions | `docs/presentation_outline.md` |
| what to hand in | `docs/submission_checklist.md` |
| run everything again | `./run_all.sh` |

Weekly rhythm that fits the Gantt: two evenings on the current stage's
reading, one longer session running and checking code, one hour updating
`PLAN.md` and the report section for that stage. Never let the report lag
more than one stage behind the code.

---

## Phase 0: setup (one evening, once)

- [ ] Clone the repo; `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- [ ] `Rscript -e 'install.packages(c("cmprsk","survival"))'`
- [ ] Mount the SSD; run `.venv/bin/python src/load.py` (prints `OK`)
- [ ] `SKIP_STAGE1=1 ./run_all.sh` ends with `ALL OK` (about 3 minutes)
- [ ] Read `CONTEXT.md` once, then `docs/PLAN.md` once
- [ ] Skim `docs/learn/glossary.md`; work through `docs/learn/worked_examples.md` with a pencil (an evening)
- [ ] Run `.venv/bin/python docs/learn/concepts_walkthrough.py` and read the code next to the printed numbers
- [ ] Generate the concept graphics you want from `docs/concept_graphics_prompts.md`
      (start with G1 censoring, G4 landmark, G6 engines-vs-rows) and keep them in `figures/concepts/`
- [ ] Before each supervisor meeting: `docs/learn/self_test.md` (the (viva) questions) and `docs/learn/faq.md`

## Phase 1: Stage 1, the survival table (already built; your job is to understand it)

Read: `docs/stages/stage1_survival_table.md`, section "Before you start" (2-3 h).
- [ ] ISLR chapter 11.1-11.2; the data paper sections 2-3 and Table 2
- [ ] Explain to yourself, in writing, why an engine that reaches 100 flights is censored and why the RUL column cannot tell you that
- [ ] Explain why the normaliser is fitted on healthy rows only and pooled across files

Run and check:
- [ ] `.venv/bin/python src/survival_table.py` (self-check) and read the printed table against the guide's "What to look at"
- [ ] Open `data/derived/engines.csv`; find the two censored engines and the ambiguous one

Produce for the report:
- [ ] Table 3.1 (paste `engines.csv`), Table 3.2 (variable roles), and write section 3 of `report_draft.md` in your own words from the guide
- [ ] Write `src/fig_normalisation.py` (spec in `figures_checklist.md`, D1) and insert Figure 3.1

## Phase 2: Stage 2, descriptive survival (already run; understand and write up)

Read: `docs/stages/stage2_descriptive.md` "Before you start" (3-4 h).
- [ ] ISLR 11.3-11.4; Kleinbaum & Klein chapter 2; Austin, Lee & Fine (2016)
- [ ] Write one paragraph: why 1 minus Kaplan-Meier is wrong when another cause exists

Run and check:
- [ ] `.venv/bin/python src/descriptive.py`; confirm medians 89 / 72 and p = 0.0019
- [ ] Look at `figures/stage2_km_cif.png` and check every curve against the guide

Produce:
- [ ] Report section 5.1 (two paragraphs) and Figure 5.1 caption
- [ ] Literature review section 2.1-2.2 drafts (two pages) while this reading is fresh

## Supervisor meeting 1 (early October)

- [ ] Upload `docs/Yiu_3173909Y_meeting1_planning.docx` (update meeting dates in `docs/gantt.py` first, re-run it, re-render with the pandoc command in `PLAN.md`)
- [ ] Bring the five open decisions from `docs/stages/stage3_models.md` and get a steer on each
- [ ] Record the decisions in `docs/PLAN.md` under Stage 3

## Phase 3: Stage 3, the core models (first pass exists; refine after meeting 1)

Read: `docs/stages/stage3_models.md` "Before you start" (a week of evenings).
- [ ] ISLR 11.5; Kleinbaum & Klein chapters 3, 4, 7; lifelines "Survival Regression" and PH-test pages
- [ ] Austin, Lee & Fine (2016) competing-risks regression sections; skim Fine & Gray (1999)
- [ ] van Houwelingen (2007) sections 1-2 (landmarking)
- [ ] Peduzzi (1996); Harrell RMS chapter 5 (bootstrap validation)
- [ ] Write one paragraph each: what a hazard ratio means; what optimism is; why engines are resampled, not rows

Run and check:
- [ ] `.venv/bin/python src/models.py`; match the printed hazard ratios and C-indexes to `docs/PLAN.md`
- [ ] `Rscript src/fine_gray.R`; see the instability and re-read the "Penalty, not method" finding
- [ ] `.venv/bin/python src/penalty_sensitivity.py`; look at the figure

Apply the meeting-1 decisions (edit, re-run, record in `PLAN.md`):
- [ ] Landmark: if changing L or adding landmarks, edit `run(L=...)` in `models.py` and repeat the runs; keep a table of results per L
- [ ] Penalty: if selecting differently, document the choice; the sensitivity table stays
- [ ] Fine-Gray: confirmatory only, or try `fastcmprsk` in R
- [ ] Optional extension: time-varying Cox (`CoxTimeVaryingFitter` on `cycles.csv`)

Produce:
- [ ] Report sections 4.1-4.7 and 5.2-5.3 (the draft has the first-pass numbers; replace with final ones)
- [ ] Tables 5.1-5.4; Figure 5.2; write `src/fig_cif_bands.py` (spec R2) for Figure 5.4; Schoenfeld plots (R3b)
- [ ] Literature review 2.3 draft

## Supervisor meeting 2 (early November): first models

- [ ] Show Table 5.1 and the penalty figure; agree the final Stage 3 specification

## Phase 4: Stage 4, benchmarks

Read: `docs/stages/stage4_benchmarks.md` "Before you start" (one weekend).
- [ ] Ishwaran (2008) sections 1-3; Harrell C-index; one C-MAPSS LSTM paper; Keras RNN guide

Run and check:
- [ ] `.venv/bin/python src/rsf_benchmark.py`; compare with `PLAN.md`
- [x] Run the LSTM on Colab following `docs/colab_lstm.md`; commit `results/stage4_lstm.csv` (done 18 Sep: RMSE 9.58, C 0.844)
- [ ] Optional: predicted-vs-true scatter (R4) needs a re-run with predictions saved

Produce:
- [ ] Report section 4.8 and 5.4 with the LSTM row filled; section 6.2 tied to the actual window counts
- [ ] Literature review 2.4 draft

## Phase 5: code organisation and the sample chapter (November-December)

- [ ] Walk through `docs/stages.md` and each guide; fix anything a marker would not follow
- [ ] `./run_all.sh` from a fresh clone of the repo passes
- [ ] Sample chapter = report sections 3 and 4, polished, with all Data/Method tables and figures

## Supervisor meeting 3 (mid December): code walk-through + sample chapter

## Phase 6: Stage 5, the decision app (January, stretch: drop first if behind)

Read: `docs/stages/stage5_decision_app.md` (an afternoon).
- [ ] `.venv/bin/python src/predict.py`; `.venv/bin/streamlit run app/app.py`; screenshot for Figure 5.3
- [ ] Report sections 4.9 and 5.6, half a page each

## Phase 7: full draft (January-March)

- [ ] Resolve every `[TODO]` in `report_draft.md`; expand the literature review to about five pages
- [ ] Every figure in `figures_checklist.md` exists at 200 dpi with a caption
- [ ] Discussion and conclusion; abstract last
- [ ] Check length against the targets in `docs/stages/stage6_writing.md`

## Supervisor meeting 4 (mid February): results and draft

## Phase 8: final draft, slides, submission (March-April)

- [ ] Apply meeting-4 feedback; references verified one by one
- [ ] Slides from `docs/presentation_outline.md`; rehearse the viva answers
- [ ] Executive summary from `docs/executive_summary_template.md`
- [ ] `docs/submission_checklist.md` fully ticked

## Supervisor meeting 5 (late March): final draft

## Submit 26 April 2027
