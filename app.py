import streamlit as st
import os, pandas as pd, numpy as np
from statsmodels.stats.proportion import proportions_ztest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join("cookie_cats.csv")

@st.cache_data
def load_data():
    if os.path.exists(DATA):
        df = pd.read_csv(DATA)
        return df, True
    # tiny synthetic fallback
    np.random.seed(7)
    n = 1000
    control = pd.DataFrame({
        "version":"gate_30",
        "retention_1": np.random.binomial(1, 0.42, size=n),
        "retention_7": np.random.binomial(1, 0.25, size=n),
        "sum_gamerounds": np.random.poisson(20, size=n)
    })
    variant = pd.DataFrame({
        "version":"gate_40",
        "retention_1": np.random.binomial(1, 0.41, size=n),
        "retention_7": np.random.binomial(1, 0.245, size=n),
        "sum_gamerounds": np.random.poisson(19, size=n)
    })
    return pd.concat([control, variant], ignore_index=True), False

def ab_core(df):
    ctl = df.query("version=='gate_30'")["retention_7"]
    var = df.query("version=='gate_40'")["retention_7"]
    succ = [ctl.sum(), var.sum()]
    nobs = [ctl.size, var.size]
    z, p_larger = proportions_ztest(succ, nobs, alternative='larger')
    rate_c, rate_t = ctl.mean(), var.mean()
    lift = rate_t - rate_c
    return rate_c, rate_t, lift, p_larger

st.title("A/B Test – Cookie Cats (D7 Retention)")
df, real = load_data()
st.write(f"Dataset: {'Real CSV' if real else 'Synthetic demo'} | n={len(df)}")

rate_c, rate_t, lift, p = ab_core(df)
st.metric("D7 – Control", f"{rate_c:.1%}")
st.metric("D7 – Variant", f"{rate_t:.1%}")
st.metric("Lift (pp)", f"{lift*100:.2f}")
st.write(f"p-value (Variant > Control): **{p:.4f}**")

# Guardrail: D1 drop
ctl = df.query("version=='gate_30'")["retention_1"]
var = df.query("version=='gate_40'")["retention_1"]
succ = [ctl.sum(), var.sum()]
nobs = [ctl.size, var.size]
_, p_d1_drop = proportions_ztest(succ, nobs, alternative='smaller')
st.write(f"Guardrail D1 drop p-value (Variant < Control): **{p_d1_drop:.4f}**")

# Simple segment by gamerounds
df["eng_bucket"] = pd.qcut(df["sum_gamerounds"], 3, labels=["light","medium","heavy"])
seg = st.selectbox("Segment", ["all","light","medium","heavy"])
view = df if seg=="all" else df[df["eng_bucket"]==seg]

rc = view.query("version=='gate_30'")["retention_7"].mean()
rt = view.query("version=='gate_40'")["retention_7"].mean()
succ = [int(view.query("version=='gate_30'")["retention_7"].sum()),
        int(view.query("version=='gate_40'")["retention_7"].sum())]
nobs = [int(view.query("version=='gate_30'")["retention_7"].size),
        int(view.query("version=='gate_40'")["retention_7"].size)]
_, p_seg = proportions_ztest(succ, nobs, alternative='larger')
st.subheader(f"Segment: {seg}")
st.write(f"D7 Control={rc:.1%} | Variant={rt:.1%} | Lift={(rt-rc)*100:.2f} pp | p={p_seg:.4f}")

# Decision summary
MDE = 0.015
decision = "Inconclusive"
if (lift >= MDE) and (p < 0.05) and (p_d1_drop >= 0.05):
    decision = "SHIP"
elif (lift <= -MDE):
    # check if significantly worse
    _, p_smaller = proportions_ztest(succ=[int(df.query("version=='gate_30'")["retention_7"].sum()),
                                           int(df.query("version=='gate_40'")["retention_7"].sum())],
                                     nobs=[int(df.query("version=='gate_30'")["retention_7"].size),
                                           int(df.query("version=='gate_40'")["retention_7"].size)],
                                     alternative='smaller')
    if p_smaller < 0.05:
        decision = "DON'T SHIP"

st.markdown(f"### Decision: **{decision}**")
st.caption("Rule: Ship if lift ≥ +1.5 pp and p<0.05 and no guardrail fail. Don’t ship if lift ≤ −1.5 pp and p<0.05; else inconclusive.")
