# OND Random Security Report (Academic Summary)

Date: 2026-02-04

## Abstract

This report provides formal, conditional security statements for OND Random. The core security claim is derived from the SHAKE256-based extractor (ONDMaxRNG) and is framed under explicit assumptions about the source min-entropy and the cryptographic model of SHAKE256. We include a formal threat and adversary model, summarize entropy estimation using NIST SP 800-90B, and present the strongest bounds currently justifiable without external audit.

## System Overview

OND Random combines:
1. A raw source RNG (OS RNG or emulator).
2. A SHAKE256-based extractor (ONDMaxRNG).
3. OND structure metrics (H_rank, H_sub, H_branch) for empirical validation.

## Threat Model

**Assets:** unpredictability of output bits, integrity of reports, reproducibility of releases.  
**Scope:** software implementation; no hardware security guarantees.  
**Assumptions:** source has min-entropy k per input block, SHAKE256 is secure (FIPS 202).

### Formal Adversary Model

Let A be a probabilistic polynomial-time adversary with:
- Full knowledge of algorithms and parameters (Kerckhoffs).
- Adaptive access to output stream.
- Ability to bias the raw source within stated assumptions.

Goals:
- Predict next output bits with non-negligible advantage.
- Distinguish extracted output from uniform.

We exclude:
- Fully compromised OS/hardware.
- Side-channel attacks unless explicitly modeled.

## Formal Security Claims (Conditional)

### Claim 1: Information-Theoretic Reference Bound

If the extractor were a 2-universal hash Ext, the Leftover Hash Lemma gives:

  Delta(Ext(S), U_m) <= 1/2 * sqrt(2^(m - k))

This is a reference bound. SHAKE256 is not a 2-universal hash; therefore this bound is not directly applicable to the implementation but provides a conservative target when k is known.

### Claim 2: Computational Bound (SHAKE256 as Random Oracle / Sponge)

Model SHAKE256 as an ideal sponge with capacity c = 512. The standard indistinguishability advantage satisfies:

  Adv <= q^2 / 2^(c+1)

where q is the number of oracle queries. This yields negligible advantage for practical q.

### Claim 3: OND Metrics

OND metrics detect structure but do not prove min-entropy or unpredictability. They are supporting evidence only.

## Entropy Estimation (NIST SP 800-90B)

We rely on NIST SP 800-90B for min-entropy assessment of raw sources. The repository includes a script to run the official EntropyAssessment tool (ea_iid / ea_non_iid). The tool implements the IID and non-IID estimators defined by SP 800-90B and outputs the conservative min-entropy estimate. (See References.)

## Limitations

- These proofs are conditional and depend on assumptions about the source and SHAKE256.
- There is no external audit or certification included here.
- Hardware entropy sources are not validated in this report.

## References

1. NIST SP 800-90B, Recommendation for the Entropy Sources Used for Random Bit Generation.
2. NIST FIPS 202, SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions.
3. NIST EntropyAssessment Tool (SP 800-90B reference implementation).

## Compliance Appendix (Excerpts)

Verbatim excerpts must be inserted into `docs/COMPLIANCE_EXCERPTS.md` from the official sources.
The PDF builder will append those excerpts to the report.
