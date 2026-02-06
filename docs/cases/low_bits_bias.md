# Case: Low‑bits coupling passes simple bit‑tests, OND/ks1‑ks2 sees structure

This case demonstrates a **subtle low‑bits structural defect** where basic bit‑tests look normal, but OND/ks1‑ks2 detects a strong deviation in the dynamics.

## Setup (what we injected)

- **Observation space:** `Z_mod_m` with `m = 2^32`, 2D observations `(u_r, u_z)` from `ObservationMap(d=2, word_bits=32)`.
- **Baseline:** `ONDMaxRNG` seeded by deterministic `LCG` (reproducible).
- **Structured variant:** keep `u_r` unchanged but **force a low‑bits offset relation**:

$$
u_z = (u_r + 2^{k}) \bmod 2^{32},\quad k=2
$$

This preserves **marginal distributions** of bits (so simple bit‑tests stay “OK”), but introduces **deterministic coupling** that collapses the Δ‑dynamics into a few projective classes.

## Reproduce

```bash
PYTHONPATH=. python scripts/low_bits_case.py
```

Outputs are written to:

```
data/reports/cases/low_bits_bias/
```

## Results (from generated artifacts)

### Simple bit‑tests (monobit + runs)

From `data/reports/cases/low_bits_bias/bit_tests.json`:

| Variant | p‑monobit | p‑runs |
| --- | --- | --- |
| baseline | **0.0288** | **0.4014** |
| low_bits_offset | **0.0336** | **0.1890** |

Threshold used: **p ≥ 0.01** → **both pass**.

### OND/ks1‑ks2 orbit‑spectrum (Δ‑structure)

From `data/reports/cases/low_bits_bias/ond_art_report.json`:

- **Orbit baseline classification:** **Strong Deviation**
- **Baseline:** `unique_classes ≈ 4999`, `structure_bits ≈ 0`
- **Structured:** `unique_classes = 12`, `structure_bits ≈ 1.57`
- **Dominant class share:** ~0.49 (structured)

This is exactly the “looks fine at the bit level → OND/ks1‑ks2 detects structure in Δ” behavior.

## Notes / non‑claims

- These are **simple SP800‑22‑style checks**, not full test batteries.
- This is **diagnostic**, not cryptanalysis: no key recovery, no security claim.

## Files

- Observations (baseline/structured):
  - `data/reports/cases/low_bits_bias/observations_baseline.jsonl`
  - `data/reports/cases/low_bits_bias/observations_low_bits.jsonl`
- Reports:
  - `data/reports/cases/low_bits_bias/baseline_report.json`
  - `data/reports/cases/low_bits_bias/ond_art_report.json`
- Bit‑tests:
  - `data/reports/cases/low_bits_bias/bit_tests.json`
