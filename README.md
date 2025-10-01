# AB Testing v1

Goal: Evaluate whether moving an early gate (Control: gate_30) to a new placement (Variant: gate_40) improves Day-7 retention (D7).

Primary KPI: Day-7 retention (D7)
Guardrails: Day-1 retention (D1) and engagement (sum of game rounds)
Decision rule:

Ship if D7 lift ≥ +1.5pp, p < 0.05 (one-sided), and no guardrail fails.

Don’t ship if D7 lift ≤ −1.5pp and p < 0.05.

Otherwise Inconclusive → collect more data or redesign.
Notes: No peeking mid-test; CUPED skipped (no clean pre-period covariate in this dataset).

TL;DR (Results)

D7: Control 19.02% vs Variant 18.20% → −0.82pp (Variant is lower)

Significance: One-sided p (Variant > Control) = 0.0008 → strong evidence Variant is not better

Guardrail (D1): 44.82% vs 44.23%, no significant drop (p = 0.9628)

Engagement snapshot: median gamerounds = 17 (Control) vs 16 (Variant)

Decision (by our pre-set rule): Inconclusive (magnitude smaller than ±1.5pp threshold).
Recommendation: Direction is negative; do not ship as-is. Propose a softer early-game tweak (e.g., gate at 35 or tutorial assist) and re-test.

How to Run Locally
### 1) create & activate a virtual env (Windows PowerShell shown)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

### 2) install deps
pip install -r requirements.txt

### 3) put the CSV data at: cookie_cats.csv
   required columns:
  version ∈ {'gate_30','gate_40'}, retention_1 ∈ {0,1}, retention_7 ∈ {0,1}, sum_gamerounds (int)

### 4) run the analysis (prints D7/D1, lift, p-values, decision)
python analyze_ab.py

### 5) (optional) launch the dashboard
streamlit run app.py


If cookie_cats.csv is missing, analyze_ab.py runs on a tiny synthetic demo so you can see the flow. Replace with the real CSV for the actual results.

## What This Project Demonstrates

Proper pre-registration (success metric, guardrails, decision rule, no peeking).

Correct one-sided proportion tests for binary outcomes (D7, D1).

Clear guardrail logic (don’t win D7 by breaking D1/engagement).

Executive-friendly reporting (1-page memo) + Streamlit dashboard for fast reads.

Honest tradeoffs (we skip CUPED because there’s no pre-period covariate).

Method (Short)

Define metrics & rule (see 02_preregistration.md).

Load & split cohorts: gate_30 (Control) vs gate_40 (Variant).

Test D7 with a one-sided z-test (Variant > Control) and compute lift (pp).

Guardrails: test D1 for a drop (Variant < Control); sanity-check engagement (median rounds).

Decide using the pre-written rule; translate to business terms (retain/lose per 100k installs).

Communicate: Streamlit + 1-page memo.

Data Dictionary (Columns Used)
Column	Type	Description
version	str	gate_30 (Control) or gate_40 (Variant)
retention_1	int	1 if user returned on Day-1, else 0
retention_7	int	1 if user returned on Day-7, else 0
sum_gamerounds	int	Total rounds played in the observed window
Interpreting the Output

Lift (pp) = Variant − Control in percentage points.

p-value (Variant > Control) small (<0.05) → evidence Variant beats Control.

D1 drop p-value (Variant < Control) small (<0.05) → Variant hurts Day-1 retention (guardrail fail).

Decision applies the rule exactly (≥ +1.5pp / ≤ −1.5pp with significance and guardrails).

Limitations & Next Steps

No true pre-period features → CUPED omitted.

Magnitude of effect (~0.82pp drop) is below the reject threshold but directionally negative.

## Dataset: Cookie Cats A/B testing dataset (public mirrors on Kaggle; include link in your repo if allowed).
## Libraries: pandas, numpy, statsmodels, streamlit.

Live Demo & Contact

## Live app: add your Streamlit URL here

## Say hi: https://www.linkedin.com/in/pratik-kumar-jha-5509742b0/
