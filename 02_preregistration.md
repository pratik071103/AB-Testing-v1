# Pre-registration (simple plan)

- **Objective:** Evaluate moving the first gate from level 30 (Control) to 40 (Variant).
- **Primary metric:** Day-7 retention (D7).
- **Guardrails:** Day-1 retention (D1) and gamerounds (engagement).
- **Alpha (false alarm tolerance):** 0.05.
- **Power target:** 0.80 (sample-size discussion kept simple for capstone).
- **Decision rule:**
  - Ship if **D7 lift ≥ +1.5 percentage points**, **p < 0.05 (one-sided)** and **no guardrail fails**.
  - Don’t ship if **D7 ≤ −1.5 pp** and **p < 0.05**.
  - Otherwise, **Inconclusive**.
- **Peeking:** We will **not** make a decision mid-way. We will evaluate **once** at the end.
- **CUPED:** Skipped (no clean pre-period covariates in this dataset).
