"""Survival analysis: do the imaging features predict how long patients live?

Pipeline: merge features with clinical outcomes -> penalized Cox model on a
train split -> concordance index on held-out patients -> Kaplan-Meier curves
splitting patients into predicted high/low risk.

c-index: 0.5 = coin flip, 1.0 = perfect ranking. Clearly above 0.5 on unseen
patients = the scan measurements carry real survival signal.
"""
import matplotlib
matplotlib.use("Agg")  # headless: save figures without a display
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.utils import concordance_index
from sklearn.model_selection import train_test_split

from . import config


def run_survival(features_csv=config.FEATURES_CSV,
                 clinical_csv=config.RAW_DIR / "clinical.csv",
                 duration_col="REPLACE_WITH_YOUR_TIME_COLUMN",
                 event_col="REPLACE_WITH_YOUR_EVENT_COLUMN",
                 outputs_dir=config.OUTPUTS_DIR):
    outputs_dir = Path(outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    features = pd.read_csv(features_csv)
    clinical = pd.read_csv(clinical_csv)[["patient_id", duration_col, event_col]]
    df = features.merge(clinical, on="patient_id").dropna().reset_index(drop=True)

    feature_cols = [c for c in df.columns
                    if c not in ("patient_id", duration_col, event_col)]
    # Drop constant features (zero signal, break the model)
    feature_cols = [c for c in feature_cols if df[c].nunique() > 1]

    train, test = train_test_split(df, test_size=config.TEST_SIZE,
                                   random_state=config.RANDOM_STATE)

    cph = CoxPHFitter(penalizer=config.COX_PENALIZER)
    cph.fit(train[feature_cols + [duration_col, event_col]],
            duration_col=duration_col, event_col=event_col)
    print(cph.summary.sort_values("coef", ascending=False).head(10))

    risk = cph.predict_partial_hazard(test[feature_cols])
    c_index = concordance_index(test[duration_col],
                                -risk.values.ravel(),
                                test[event_col])
    print(f"concordance index on held-out patients: {c_index:.3f}")

    # Kaplan-Meier: split held-out patients at median predicted risk
    test = test.copy()
    threshold = float(risk.median().iloc[0])
    test["risk_group"] = (risk.values.ravel() > threshold).astype(int)

    kmf = KaplanMeierFitter()
    fig, ax = plt.subplots()
    for grp, label in [(0, "predicted low risk"), (1, "predicted high risk")]:
        sel = test["risk_group"] == grp
        kmf.fit(test.loc[sel, duration_col], test.loc[sel, event_col], label=label)
        kmf.plot_survival_function(ax=ax)
    ax.set_xlabel("time")
    ax.set_ylabel("survival probability")
    ax.set_title(f"Kaplan-Meier by predicted risk (c-index={c_index:.3f})")
    fig.savefig(outputs_dir / "kaplan_meier.png", dpi=150)
    print(f"saved -> {outputs_dir / 'kaplan_meier.png'}")
    return c_index
