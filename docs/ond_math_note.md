# OND: The Mathematics of Observed Randomness — Scientific Note

## Abstract
OND (Observed Randomness Dynamics) formalizes **observed randomness**: instead of judging an RNG by “ideal” randomness, it measures the **structure and dynamics** of a signal under a fixed observation map π. This note defines the core objects, OND metrics, regression gates, and the notion of “candidates” as detectable structural deviations.

---

## 1) Motivation
Classical batteries (NIST STS, TestU01, PractRand) test statistical properties of sequences. OND adds a layer:  
**how** an observed system structures its output and **how that structure changes** across time or versions.

This is useful when **comparability** and **regression stability** matter, not only pass/fail tests.

---

## 2) Observation map π
Observation is defined by a map:

- **π**: *input* → *observed vector*  
- π is fixed via `pi_id`, `pi_version`, `pi_spec_hash`

OND thus measures randomness **in the space induced by π**, not “randomness in general”.

This makes randomness a **geometric object** in the observation space.

---

## 3) Data and notation

- U in R^(N x d): observation matrix (N samples, dimension d)  
- D = ΔU: centered differences (dynamics)

With a modulus, differences are computed modulo m and centered into [-m/2, m/2):

$$
D_i = (U_{i+1} - U_i) \bmod m
$$

---

## 4) OND metrics
### 4.1 H_rank (rank entropy)
Compute the entropy of singular values of D.

Let s1..sr be singular values and p_i = s_i / sum(s_i). Then:

$$
H_{rank} = -\frac{1}{\log r}\sum_{i=1}^{r} p_i \log p_i
$$

Interpretation: a more uniform spectrum (richer dynamics) gives higher H_rank.

### 4.2 H_sub (subspace occupancy entropy)
1) Choose projection dimension r = min(rank(D), d_max).  
2) Project Y = D * V onto the first r singular directions.  
3) Bin Y into B bins per axis (total B^r cells).  
4) Compute entropy of the occupancy distribution.

$$
H_{sub} = -\frac{1}{\log(B^r)}\sum_{k} q_k \log q_k
$$
where \(q_k\) is the fraction of points in cell \(k\).

Interpretation: how fully the dynamic subspace is filled.

### 4.3 H_branch (trajectory branching)
Measures diversity of transitions between local states.

Modes:
- **raw**: branching on observations \(U\)  
- **delta**: branching on differences \(D\)

Process:  
1) Discretize into K bins.  
2) Build transition distributions.  
3) Normalize entropy by \(\log K\).

---

## 5) Profile and classes
An **OND profile** is:

$$
P(U) = (H_{rank}, H_{sub}, H_{branch})
$$

Profiles are compared to **reference classes** (I/II/III/IV), defined by means and standard deviations over canonical sources.

---

## 6) Regression and SLA
Define a baseline profile **B** for a given source/module.  
A regression run passes if:

- |P(U) - B| <= thresholds  
- and/or ||P(U) - B||_2 <= max_l2

This turns RNG quality into **measurable engineering tolerances**.

---

## 7) “Candidates” as a formal object
A **candidate** is any observation/module/version that:

1) violates SLA or thresholds;  
2) shows a quality regression in relative metrics;  
3) breaks invariants (e.g., Q‑ideal ≈ IID);  
4) fails execution or produces missing required artifacts.

In other words, a candidate is a **formal deviation** from expected structure.

---

## 8) New mathematics implied by OND
1. **Metricization of observed randomness** — randomness is a geometric object in π‑space.  
2. **Structural entropy of dynamics** — H_rank/H_sub/H_branch capture orthogonal structure axes.  
3. **Regression stability** — profiles are controlled with formal SLA gates.  
4. **Source typology** — quantitative class separation (I–IV).  
5. **Algorithmic candidate discovery** — deviations become objects of computation, not opinion.

---

## 9) Limitations
- Metrics depend on π.  
- OND does not replace cryptographic proofs.  
- High metric values do not imply security.  
- Candidate completeness depends on the policy of gates.

---

## 10) Practical protocol (reproducibility)
1) Fix π (`pi_id`, `pi_version`, `pi_spec_hash`).  
2) Build a baseline from a reference run.  
3) Run regression gates on each change.  
4) Record candidates and causes in reports.

---

## 11) Research directions
- Relationship between OND metrics and min‑entropy / classical tests.  
- Stability of profiles under subsampling and noise.  
- Geometric interpretation of OND classes.  
- Convergence of metrics as N and d grow.  
- Alternative normalizations and π‑invariants.

---

## Conclusion
OND turns randomness from an abstract property into a **measurable structure**, controlled by regression gates and formal policies. This creates a new applied language for audit, comparison, and stability of RNGs and related systems.
