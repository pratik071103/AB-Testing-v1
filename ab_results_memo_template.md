# A/B Result – One-pager (Executive)

## Summary
Moving the first gate from level 30 → 40 reduced Day-7 retention by ~0.82 percentage points (Control 19.02% → Variant 18.20%). Day-1 retention did not show a meaningful drop, and engagement (median gamerounds) dipped slightly. Per our pre-registered rule (±1.5pp threshold), the test is Inconclusive, but the effect is directionally negative. Recommendation: do not ship this variant; explore a softer early-game change and re-test.

## Headline numbers

D7 (primary): Control = 19.02%, Variant = 18.20%, Lift = −0.82 pp

One-sided p-value (Variant < Control): ≈ 0.0008

D1 (guardrail): Control = 44.82%, Variant = 44.23%, drop test p-value = 0.9628 (no concerning drop)

Engagement (guardrail): Median gamerounds = 17 (Control) vs 16 (Variant) → small dip

## Risk & Notes

Practical impact: at 100k new players, −0.82pp ≈ ~820 fewer D7-retained players.

Direction is consistently negative; even if below our ±1.5pp decision threshold, shipping risks eroding early retention.

Data quality: dataset loaded cleanly (n ≈ 90k). CUPED not applied (no pre-period covariate).

## Decision (per rule)
Inconclusive (magnitude < 1.5pp threshold).
Recommendation: Do not ship this variant based on negative direction and engagement dip.
