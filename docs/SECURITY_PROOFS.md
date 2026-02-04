# Formal Security Claims and Bounds (Conditional)

This document provides the **strongest formal statements currently possible** for the OND Random system, under explicit assumptions. These are **conditional proofs**. They do **not** substitute for empirical entropy estimation, hardware source certification, or external audits.

## Scope

The security-relevant component is the extractor `ONDMaxRNG`, which applies SHAKE256 to the raw source stream and outputs fixed-length or variable-length bits.

We formalize:
1. **Information-theoretic (IT) bounds** if the extractor were a 2‑universal hash (reference bound).
2. **Computational bounds** when SHAKE256 is modeled as a random oracle / sponge.
3. **Limits of OND metrics** (they are structure detectors, not proofs of unpredictability).

## Definitions

Let:
- `S` be the raw source RNG stream.
- `H∞(S)` be the min-entropy of the source over the extractor input.
- `k = H∞(S)` in bits.
- `m` be the number of output bits produced by the extractor.

We distinguish:
- **IT security**: statistical distance to uniform.
- **Computational security**: indistinguishability by efficient adversaries.

## Claim A (Information-Theoretic bound, reference)

If the extractor were a **2‑universal hash** `Ext` (not SHAKE), the **Leftover Hash Lemma** gives:

```
Δ(Ext(S), U_m) ≤ 1/2 * sqrt(2^(m - k))
```

This implies:
```
log2 Δ ≤ -1 + (m - k)/2
```

Example:
- If `k = 512` and `m = 256`, then `Δ ≤ 2^(-129)`.

**Important:** This is a reference bound. SHAKE256 is not a 2‑universal hash, so this is not a direct proof for the current implementation.

## Claim B (Computational bound, SHAKE256 in Random Oracle / Sponge Model)

Model SHAKE256 as a random oracle or a sponge with capacity `c = 512`.

A standard indistinguishability bound for a sponge-based PRG/PRF is:

```
Adv ≤ q^2 / 2^(c+1)
```

Where `q` is the number of adversarial queries (or effective blocks). This gives a concrete **computational** security bound under the ROM/Spongy assumptions.

Example:
- With `c = 512` and `q = 2^32`, `Adv ≤ 2^(-449)` (extremely small).

**Important:** This is a computational bound under the idealized sponge/RO model.

## Claim C (What OND Metrics Prove and Do Not Prove)

OND metrics (`H_rank`, `H_sub`, `H_branch`) detect **structure**, not min-entropy or unpredictability. Even perfect OND scores do **not** imply cryptographic security.

OND metrics can:
- Detect non-IID artifacts
- Compare sources and extractors
- Provide reproducible, empirical evidence of structure removal

OND metrics cannot:
- Prove min-entropy
- Prove resistance to adaptive adversaries
- Replace formal cryptographic reductions

## What Is Still Required for a Full Proof

To upgrade from conditional proofs to rigorous security statements, you need:
1. A **precise source model** with measured or bounded min-entropy.
2. A formal **adversary model** and attack surface.
3. If you want IT security, a **provable extractor** (e.g., 2‑universal hashing).
4. If you accept computational security, a full **cryptographic reduction** to SHAKE256 under the sponge/RO model.
5. External validation: min-entropy estimation, FIPS/NIST battery, independent audit.

## Practical Bound Calculator

Use `scripts/security_bounds.py` to compute:
- Leftover Hash Lemma bound (IT reference).
- Sponge/RO bound (computational).

Example:

```bash
PYTHONPATH=. python scripts/security_bounds.py --min-entropy 512 --output-bits 256 --queries 2^32
```

The script prints JSON with `epsilon` and `log2_epsilon`.
