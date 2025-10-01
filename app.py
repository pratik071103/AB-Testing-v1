import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.power import NormalIndPower

st.set_page_config(page_title="A/B Testing v1", layout="wide")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------
# Consistent colors (use these everywhere)
# ----------------------------
CONTROL_COLOR = "#4C78A8"  # Control (gate_30)
VARIANT_COLOR = "#F58518"  # Variant (gate_40)

# ----------------------------
# Data loading (robust)
# ----------------------------
def load_first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return pd.read_csv(p), p
    return None, None

st.title("A/B Testing v1")

uploaded = st.file_uploader("Upload Cookie Cats CSV", type=["csv"])
df = None
source = "Synthetic demo"

if uploaded is not None:
    df = pd.read_csv(uploaded)
    source = "Uploaded file"
else:
    root_csv   = os.path.join("cookie_cats.csv")                # repo root
    sample_csv = os.path.join(BASE, "data", "cookie_cats_sample.csv") # optional
    df, found_path = load_first_existing([root_csv, sample_csv])
    if df is not None:
        source = f"Repo file: {os.path.relpath(found_path, BASE)}"
    else:
        # synthetic fallback so the app always runs
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
        df = pd.concat([control, variant], ignore_index=True)

st.caption(f"Dataset source: **{source}** | n={len(df)}")

# Basic checks
required_cols = {"version","retention_1","retention_7","sum_gamerounds"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

# ----------------------------
# Helpers
# ----------------------------
def rates_and_pvals(df):
    ctl7 = df.query("version=='gate_30'")["retention_7"]
    var7 = df.query("version=='gate_40'")["retention_7"]

    # D7: Variant > Control & Variant < Control (order = [variant, control])
    succ7 = [int(var7.sum()), int(ctl7.sum())]
    nobs7 = [int(var7.size), int(ctl7.size)]
    _, p_d7_variant_gt = proportions_ztest(succ7, nobs7, alternative='larger')
    _, p_d7_variant_lt = proportions_ztest(succ7, nobs7, alternative='smaller')

    r7_c = ctl7.mean()
    r7_v = var7.mean()
    lift7 = r7_v - r7_c

    # D1 guardrail (drop test: Variant < Control)
    ctl1 = df.query("version=='gate_30'")["retention_1"]
    var1 = df.query("version=='gate_40'")["retention_1"]
    succ1 = [int(var1.sum()), int(ctl1.sum())]
    nobs1 = [int(var1.size), int(ctl1.size)]
    _, p_d1_drop = proportions_ztest(succ1, nobs1, alternative='smaller')

    r1_c = ctl1.mean()
    r1_v = var1.mean()

    med_rounds_c = df.query("version=='gate_30'")["sum_gamerounds"].median()
    med_rounds_v = df.query("version=='gate_40'")["sum_gamerounds"].median()

    return (r7_c, r7_v, lift7, p_d7_variant_gt, p_d7_variant_lt,
            r1_c, r1_v, p_d1_drop, med_rounds_c, med_rounds_v)

def wilson_ci(success, n, alpha=0.05):
    low, high = proportion_confint(success, n, alpha=alpha, method='wilson')
    return low, high

def plot_rate_with_ci(label_vals, rates, cis, title):
    # label_vals: ['Control','Variant']
    # rates: [r_c, r_v] as proportions
    # cis: [(low_c, high_c), (low_v, high_v)]
    fig = go.Figure()
    xs = label_vals
    ys = [r*100 for r in rates]
    err_low  = [(r - ci[0])*100 for r, ci in zip(rates, cis)]
    err_high = [(ci[1] - r)*100 for r, ci in zip(rates, cis)]

    fig.add_trace(go.Bar(
        x=xs, y=ys, name="Rate (%)",
        marker_color=[CONTROL_COLOR, VARIANT_COLOR]  # <- consistent colors
    ))
    fig.update_traces(error_y=dict(type='data', array=err_high, arrayminus=err_low, visible=True))
    fig.update_layout(title=title, yaxis_title="Rate (%)", xaxis_title="", bargap=0.4)
    return fig

def plot_funnel(d1_c, d7_c, d1_v, d7_v):
    labels = ["Installs", "D1 retainers", "D7 retainers"]
    base = 100  # relative funnel
    c_vals = [base, d1_c*base, d7_c*base]
    v_vals = [base, d1_v*base, d7_v*base]

    fig = go.Figure()
    fig.add_trace(go.Funnel(
        name="Control", y=labels, x=c_vals, textinfo="value+percent previous",
        marker=dict(color=CONTROL_COLOR)
    ))
    fig.add_trace(go.Funnel(
        name="Variant", y=labels, x=v_vals, textinfo="value+percent previous",
        marker=dict(color=VARIANT_COLOR)
    ))
    fig.update_layout(title="Funnel (relative to installs = 100)")
    return fig

def plot_hist_rounds(df):
    ctl = df.query("version=='gate_30'")["sum_gamerounds"]
    var = df.query("version=='gate_40'")["sum_gamerounds"]
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ctl, name="Control", opacity=0.6, nbinsx=40,
        marker_color=CONTROL_COLOR
    ))
    fig.add_trace(go.Histogram(
        x=var, name="Variant", opacity=0.6, nbinsx=40,
        marker_color=VARIANT_COLOR
    ))
    fig.update_layout(barmode='overlay', title="Engagement Distribution (gamerounds)")
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(title="sum_gamerounds")
    fig.update_yaxes(title="Players")
    return fig

def power_curve(baseline, alphas=[0.05], powers=[0.8], lifts_pp=np.linspace(0.005, 0.03, 11)):
    # plot MDE (pp) vs required n per group for chosen alpha/power
    dfp = []
    for lift in lifts_pp:
        p1 = baseline + lift
        h = 2*np.arcsin(np.sqrt(p1)) - 2*np.arcsin(np.sqrt(baseline))  # Cohen's h
        n = NormalIndPower().solve_power(effect_size=h, power=powers[0], alpha=alphas[0],
                                         ratio=1.0, alternative='larger')
        dfp.append((lift*100, np.ceil(n)))
    d = pd.DataFrame(dfp, columns=["Lift (pp)", "N per group"])
    fig = go.Figure(go.Scatter(x=d["Lift (pp)"], y=d["N per group"], mode="lines+markers"))
    fig.update_layout(
        title=f"Sample Size vs MDE (baseline D7={baseline*100:.2f}%, α={alphas[0]}, power={powers[0]})",
        xaxis_title="Minimum Detectable Effect (pp)",
        yaxis_title="Required sample per group"
    )
    return fig

# ----------------------------
# Overview cards
# ----------------------------
(r7_c, r7_v, lift7, p7_gt, p7_lt,
 r1_c, r1_v, p1_drop, med_c, med_v) = rates_and_pvals(df)

colA, colB, colC, colD = st.columns(4)
colA.metric("D7 – Control", f"{r7_c:.1%}")
colB.metric("D7 – Variant", f"{r7_v:.1%}")
colC.metric("Lift (pp)", f"{(r7_v - r7_c)*100:.2f}")
colD.metric("p-value (Variant > Control)", f"{p7_gt:.4f}")

# ----------------------------
# D7 & D1 charts with 95% CIs
# ----------------------------
st.markdown("### Outcomes with Confidence Intervals")

succ_c7 = int(df.query("version=='gate_30'")["retention_7"].sum()); n_c7 = int(df.query("version=='gate_30'").shape[0])
succ_v7 = int(df.query("version=='gate_40'")["retention_7"].sum()); n_v7 = int(df.query("version=='gate_40'").shape[0])
ci_c7 = wilson_ci(succ_c7, n_c7); ci_v7 = wilson_ci(succ_v7, n_v7)

succ_c1 = int(df.query("version=='gate_30'")["retention_1"].sum()); n_c1 = n_c7
succ_v1 = int(df.query("version=='gate_40'")["retention_1"].sum()); n_v1 = n_v7
ci_c1 = wilson_ci(succ_c1, n_c1); ci_v1 = wilson_ci(succ_v1, n_v1)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        plot_rate_with_ci(["Control","Variant"], [r7_c, r7_v], [ci_c7, ci_v7], "D7 Retention (95% CI)"),
        use_container_width=True
    )
with c2:
    st.plotly_chart(
        plot_rate_with_ci(["Control","Variant"], [r1_c, r1_v], [ci_c1, ci_v1], "D1 Retention (95% CI, Guardrail)"),
        use_container_width=True
    )

# ----------------------------
# Funnel + Engagement distribution
# ----------------------------
st.markdown("### Funnel & Engagement")
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(plot_funnel(r1_c, r7_c, r1_v, r7_v), use_container_width=True)
with c4:
    st.plotly_chart(plot_hist_rounds(df), use_container_width=True)

# ----------------------------
# Segments (safe bucketing)
# ----------------------------
st.markdown("### Segments (by gamerounds)")
sr = df["sum_gamerounds"].astype("float64")
try:
    df["_eng_bucket"] = pd.qcut(sr, 3, labels=["light","medium","heavy"], duplicates="drop")
    if df["_eng_bucket"].nunique() < 3:
        raise ValueError("not enough unique bins")
except Exception:
    q33, q66 = sr.quantile([0.33, 0.66]).values
    def bucket(x):
        if x <= q33: return "light"
        if x <= q66: return "medium"
        return "heavy"
    df["_eng_bucket"] = sr.apply(bucket)

seg = st.selectbox("Choose a segment", ["all","light","medium","heavy"])
view = df if seg=="all" else df[df["_eng_bucket"]==seg]

# recompute for segment
(r7_c_s, r7_v_s, lift7_s, p7_gt_s, p7_lt_s,
 r1_c_s, r1_v_s, p1_drop_s, med_c_s, med_v_s) = rates_and_pvals(view)

st.write(f"**Segment:** {seg} | D7 Control={r7_c_s:.1%} | Variant={r7_v_s:.1%} | Lift={(r7_v_s-r7_c_s)*100:.2f} pp | p(Variant>Control)={p7_gt_s:.4f}")

# Segment bar with consistent colors
seg_fig = go.Figure()
seg_fig.add_trace(go.Bar(
    x=["Control","Variant"],
    y=[r7_c_s*100, r7_v_s*100],
    marker_color=[CONTROL_COLOR, VARIANT_COLOR]  # <-- consistent colors
))
seg_fig.update_layout(title=f"D7 by Segment: {seg}", yaxis_title="Rate (%)", xaxis_title="")
st.plotly_chart(seg_fig, use_container_width=True)

# ----------------------------
# Decision badge
# ----------------------------
MDE = 0.015
decision = "Inconclusive"
if (lift7 >= MDE) and (p7_gt < 0.05) and (p1_drop >= 0.05):
    decision = "SHIP"
elif (lift7 <= -MDE) and (p7_lt < 0.05):
    decision = "DON'T SHIP"
st.markdown(f"### Decision: **{decision}**")
st.caption("Rule: Ship if lift ≥ +1.5 pp and p<0.05 and no guardrail fail. Don’t ship if lift ≤ −1.5 pp and p<0.05; else inconclusive.")

# ----------------------------
# Power curve (MDE intuition)
# ----------------------------
st.markdown("### Sample Size vs MDE (for planning)")
baseline = r7_c
st.plotly_chart(power_curve(baseline), use_container_width=True)
