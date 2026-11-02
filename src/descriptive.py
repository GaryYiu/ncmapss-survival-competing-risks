"""Kaplan-Meier by failure mode + log-rank, Aalen-Johansen CIF per cause. Reads data/derived/engines.csv, 
writes figures/stage2_km_cif.png. This is the competing-risks go/no-go check. 
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from lifelines import AalenJohansenFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test

HERE = os.path.dirname(__file__)
ENGINES = os.path.join(HERE, "..", "data", "derived", "engines.csv")
FIG_DIR = os.path.join(HERE, "..", "figures")
CAUSE = {"HPT": 1, "HPT+LPT": 2}  # 0 = censored


def load_engines(path=ENGINES):
    # Read the engine table and code the cause as 1/2 for failures, 0 for censored.
    eng = pd.read_csv(path)
    eng["cause"] = eng["mode"].map(CAUSE) * eng["event"]  # 0 when censored
    return eng


def run(eng, out=os.path.join(FIG_DIR, "km_cif.png")):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    # (a) Kaplan-Meier, one curve per failure mode, with confidence bands and the median.
    medians = {}
    for mode, g in eng.groupby("mode"):
        km = KaplanMeierFitter(label=f"{mode} (n={len(g)})")
        km.fit(g["lifetime"], g["event"])
        km.plot_survival_function(ax=ax1, ci_show=True)
        medians[mode] = km.median_survival_time_
    # Log-rank test of the two modes' survival curves.
    a, b = (eng[eng["mode"] == m] for m in ("HPT", "HPT+LPT"))
    lr = logrank_test(a["lifetime"], b["lifetime"], a["event"], b["event"])
    ax1.set(title=f"Kaplan-Meier by failure mode  (log-rank p={lr.p_value:.3f})",
            xlabel="cycles", ylabel="P(still running)")
    ax1.set_ylim(0, 1.02)

    # (b) Aalen-Johansen cumulative incidence per cause on the pooled engines.
    for mode, k in CAUSE.items():
        aj = AalenJohansenFitter(calculate_variance=False, seed=0)
        aj.fit(eng["lifetime"], eng["cause"], event_of_interest=k)
        # Rename the column, otherwise lifelines' internal name ("CIF_k") becomes the legend label.
        aj.cumulative_density_.rename(columns=lambda _: f"failed from {mode}").plot(ax=ax2)
    ax2.set(title="Aalen-Johansen cumulative incidence (pooled, n=25)",
            xlabel="cycles", ylabel="P(failed from cause by t)")
    ax2.set_ylim(0, 1.02)
    ax2.legend()

    # Save the two-panel figure.
    fig.tight_layout()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=130)
    return medians, lr


if __name__ == "__main__":
    # Self-check on the committed engine table, then print the gate decision.
    eng = load_engines()
    assert len(eng) == 25 and (eng["event"] == 0).sum() == 2, eng[["mode", "event"]].value_counts()
    medians, lr = run(eng)
    print("median survival (cycles):", {k: float(v) for k, v in medians.items()})
    print(f"log-rank HPT vs HPT+LPT: stat={lr.test_statistic:.2f}  p={lr.p_value:.4f}")
    print("figure -> figures/km_cif.png")
    # The gate is a decision, not an assert; outcome recorded in docs/PLAN.md.
    print("GATE:", "modes separate" if lr.p_value < 0.10 else "modes NOT clearly separated -> consider single-event fallback")
