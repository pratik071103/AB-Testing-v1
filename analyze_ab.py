#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = r"C:\Users\hpvic\Documents\A B testing\cookie_cats.csv"  # Update with your path or leave as is to use synthetic data

def load_data():
    if os.path.exists(DATA):
        df = pd.read_csv(DATA)
        print(f"[info] Loaded real dataset: {DATA} (n={len(df)})")
        # Minimal column checks
        required = {"version","retention_1","retention_7","sum_gamerounds"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in CSV: {missing}")
        return df
    else:
        print("[warn] No dataset found. Using a tiny synthetic sample (demo only).")
        # Make a tiny synthetic dataset (control slightly better than variant)
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
        return pd.concat([control, variant], ignore_index=True)

def prop_test(success_a, size_a, success_b, size_b, alt="larger"):
    z, p = proportions_ztest([success_a, success_b], [size_a, size_b], alternative=alt)
    rate_a = success_a/size_a
    rate_b = success_b/size_b
    lift = rate_b - rate_a
    return rate_a, rate_b, lift, p

def main():
    df = load_data()
    ctl = df.query("version=='gate_30'")
    var = df.query("version=='gate_40'")

    # --- D7 main metric ---
    r7_a, r7_b, lift7, p7_larger = prop_test(ctl["retention_7"].sum(), len(ctl),
                                             var["retention_7"].sum(), len(var),
                                             alt="larger")  # tests Variant > Control
    p7_smaller = proportions_ztest([ctl["retention_7"].sum(), var["retention_7"].sum()],
                                   [len(ctl), len(var)], alternative="smaller")[1]

    # --- D1 guardrail (we only worry if Variant is worse) ---
    r1_a, r1_b, lift1, p1_smaller = prop_test(ctl["retention_1"].sum(), len(ctl),
                                              var["retention_1"].sum(), len(var),
                                              alt="smaller")  # tests Variant < Control

    # --- Simple engagement guardrail (gamerounds median) ---
    med_rounds_a = ctl["sum_gamerounds"].median()
    med_rounds_b = var["sum_gamerounds"].median()

    print("\n=== A/B Results ===")
    print(f"D7 Control (A): {r7_a:.3%}")
    print(f"D7 Variant (B): {r7_b:.3%}")
    print(f"D7 Lift (B-A):  {lift7*100:.2f} pp")
    print(f"p-value (B>A):  {p7_larger:.4f}")
    print(f"p-value (B<A):  {p7_smaller:.4f}")

    print("\n[Guardrail] D1")
    print(f"D1 Control (A): {r1_a:.3%}")
    print(f"D1 Variant (B): {r1_b:.3%}")
    print(f"D1 drop p-value (B<A): {p1_smaller:.4f}")

    print("\n[Guardrail] Engagement proxy (median gamerounds)")
    print(f"Control median: {med_rounds_a} | Variant median: {med_rounds_b}")

    # --- Decision rule ---
    MDE = 0.015  # 1.5 percentage points
    decision = "Inconclusive"
    if (lift7 >= MDE) and (p7_larger < 0.05) and (p1_smaller >= 0.05):
        decision = "SHIP"
    elif (lift7 <= -MDE) and (p7_smaller < 0.05):
        decision = "DON'T SHIP"

    print("\n=== Decision ===")
    print(f"Rule: Ship if lift ≥ +1.5 pp AND p<0.05 AND no guardrail fail.")
    print(f"Outcome: {decision}")
    if decision == "SHIP":
        print("Rationale: D7 improved meaningfully, result looks real, and D1 guardrail did not fail.")
    elif decision == "DON'T SHIP":
        print("Rationale: D7 worsened meaningfully and the result looks real.")
    else:
        print("Rationale: Effect too small/uncertain or guardrail issue. Run longer or redesign.")

if __name__ == "__main__":
    main()
