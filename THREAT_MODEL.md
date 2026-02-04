# Threat Model

## System Overview
OND Random provides:
- `ONDMaxRNG` SHAKE-based extractor
- Raw OND metrics for structural randomness analysis
- Protocol observation mappings (ECDSA/Schnorr/PQ)
- Quantum emulation modules (statevector + Lindblad)

## Assets
- Correctness and unpredictability of RNG output
- Integrity of OND metrics and reports
- Reproducibility of builds and releases

## Trust Assumptions
- Host OS entropy source (`SystemRNG`) is not adversarial
- Python runtime and dependencies are not compromised
- Users follow documented deployment procedures

## Attacker Model
- Can observe outputs (black-box)
- Can influence external environment (timing, load)
- May attempt to replace dependencies or tamper with build artifacts

## Formal Threat & Adversary Model
**System boundary:** `ONDMaxRNG` with SHAKE256 extractor; optional entropy sources include `SystemRNG`, `QuantumEmulatorRNG`, or protocol-derived observations. The adversary sees all public outputs and may control the environment but not the internal extractor state.

**Adversary capabilities (formal):**
1. **PPT attacker** with full knowledge of algorithms and parameters (Kerckhoffs).
2. **Black-box access** to the RNG output stream with adaptive queries.
3. **Partial source influence**: adversary may bias, reduce, or partially control the raw source within stated assumptions.
4. **Side-channel excluded** unless explicitly modeled; a compromised OS/hardware is out of scope.

**Security goals:**
- **Unpredictability:** for any PPT adversary, next-bit prediction advantage is negligible relative to SHAKE256 security.
- **Backtracking resistance:** past outputs remain secure if current state is exposed (subject to extractor model).
- **Structure removal:** OND metrics improve toward IID-like behavior on raw data without normalization.

**Assumptions:**
- The source has **min-entropy** `k` per input block (estimated via SP 800-90B).
- SHAKE256 behaves as a secure sponge/XOF (FIPS 202).
- Adversary cannot read or modify extractor internal state.

## Non‑Goals
- Protection against a fully compromised OS or hardware
- Side‑channel resistance in hostile execution environments
- Formal cryptographic proofs of CSPRNG security

## Threats and Mitigations
1. **Weak or biased entropy sources**
   - Mitigation: SHAKE-based extractor, periodic reseeding, OND metrics for detection

2. **Dependency supply‑chain attacks**
   - Mitigation: pinned dependencies, CI checks, signed release artifacts

3. **Build tampering / unreproducible artifacts**
   - Mitigation: reproducible build workflow, versioned releases, checksums

4. **Misuse of protocol observations**
   - Mitigation: clear documentation, no key‑recovery code, synthetic data generation with explicit bijection

5. **Measurement bias in OND metrics**
   - Mitigation: raw-data computation, documented parameters, reproducible benchmark datasets

## Residual Risk
- If the OS RNG is compromised, `ONDMaxRNG` cannot guarantee unpredictability
- Any runtime compromise invalidates results
