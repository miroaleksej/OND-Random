# OND/TDA One‑Pager (Definition + Pipeline + Claims + Non‑goals)

Preprint‑academic outline of **OND‑ART / ODD‑OBS / topology** as a single observability specification (not a “battery of tests”). See the PDF version: `docs/OND_TDA_onepager.pdf`.

---

## Definition

**Observed Nonce/Randomness Dynamics (OND)** treats protocol artifacts as a composition:

*(hidden physics / system dynamics of RNG)* → *(deterministic protocol logic)* → *(publicly observed data)*.

The goal is to detect **structural constraints** and **drift** in randomness consumption **from public artifacts only**, without assuming a model of the source.

### Observation map and observation space (ODD‑OBS)

Let $$\{\sigma_i\}_{i=1}^{N}$$ be a sequence of public artifacts (e.g., signatures).  
The **observation map** is fixed and deterministic:

$$
\pi:\ \sigma \mapsto U \in \mathcal{O}
$$

It must depend only on public data and be fixed as part of the spec: `pi_id`, `pi_version`, `pi_spec_hash`.

**Normalization/rescaling is forbidden** unless it is explicitly defined as part of π.  
Transformations “for visualization only” must be separated from metric computation.

The **observation space** $$\mathcal{O}$$ is fixed via `obs_space`, typically:

- $$\mathcal{O}=\mathbb{R}^d$$ with fixed dimension $$d$$; or
- $$\mathcal{O}=\mathbb{Z}_m$$ / $$\mathbb{Z}_m^k$$ with fixed modulus.

### Observable dynamics and OND‑profile

Define observable dynamics:

$$
\Delta_i := U_{i+1}-U_i,\quad i=1,\dots,N-1.
$$

In **Inverse OND**, this is canonical: build $$U_i=\pi(\sigma_i)$$, then $$\Delta_i$$, then compute the structural profile.

OND‑ART is a **protocol audit** of post‑protocol dynamics, returning a **structural profile + confidence intervals**, not a binary verdict.

### Algebraic orbit‑spectrum layer (ks1/ks2)

In the discrete case $$\mathcal{O}=\mathbb{Z}_n^2$$, introduce an observational parameterization via invariants:

$$
\delta:=K_2-K_1,\qquad [v]\in\mathbb{P}^1(\mathbb{Z}_n),\qquad \mathrm{type}(\mathcal{T})\in\{T0,T1,T2\}.
$$

Here $$[v]$$ is the projective direction of the step, and $$\mathcal{T}$$ fixes the dynamical class.  
Transition classes are constrained by $$\mathrm{rank}(A-I)\le 1$$ (otherwise the orbit becomes 2‑dimensional) and split into three canonical types (T0/T1/T2).

### Topological observability layer (TDA on $$\mathcal{O}$$)

The **OND/TDA channel** computes stable topological invariants from $$\{U_i\}$$ (or $$\{\Delta_i\}$$, or windowed point clouds) in a canonical space (including torus embedding for modular coordinates).  
Persistent homology and vectorized diagrams provide a robust, low‑dimensional signature of structure.

---

## Pipeline

The pipeline is modular: base OND metrics + (optional) orbit‑spectrum + (optional) topology.

### Step 0: Data and reproducibility contract (ODD‑OBS)

Fix public context (e.g., a single `pk`), π specification (`pi_id`, `pi_version`, `pi_spec_hash`), and `obs_space`.  
“No hidden normalization” is part of the reproducibility contract.

### Step 1: Observation and dynamics

Compute $$U_i=\pi(\sigma_i)$$ and $$\Delta_i=U_{i+1}-U_i$$.

### Step 2: Canonical OND metrics (structural profile)

Compute the structural vector $$(H_{\mathrm{rank}}, H_{\mathrm{sub}}, H_{\mathrm{branch}})$$ and interpret it as deviation from the null hypothesis (i.i.d. uniform on $$\mathcal{O}$$).  
Map profiles to defect/equivalence classes (model selection) via typical metric patterns.

### Step 3 (optional): Orbit‑spectrum extraction (ks1/ks2)

For $$\mathcal{O}=\mathbb{Z}_n^2$$:

1. compute $$\Delta_i$$;  
2. cluster $$\Delta_i$$ and classify type:  
   - 1 dominant cluster → **T0**  
   - 2 clusters → **T1**  
   - dependence of $$\Delta_i$$ on $$u_i$$ → **T2**  
3. for clusters, extract $$[\Delta]\in\mathbb{P}^1(\mathbb{Z}_n)$$ and cycle length $$L=n/\gcd(n,\Delta_r,\Delta_z)$$;  
4. build empirical distribution $$p(\Sigma)$$, entropy $$H(\Sigma)$$, and “structure bits” $$\mathcal{I}=H_0-H$$.

This pipeline is scalable (typically $$O(N\log N)$$ with standard clustering/counting).

### Step 4 (optional): Topology channel (TDA)

Build windowed point clouds over $$U$$ or $$\Delta$$, compute persistent homology (usually $$H_0/H_1$$), vectorize diagrams (landscapes/images/persistence entropy), and feed into the same baseline/regression contour as OND metrics.

### Step 5: Validation via Golden Experiment (baseline/regression)

Key validation is a **controlled** comparison of “reference RNG” vs “modified RNG” with identical public context.  
**Key recovery / state recovery is forbidden** as part of the method axioms.

Output of Inverse OND is a diagnostic report: class membership, entropy gap, and qualitative topology of constraints (cyclicity, intervals, finite‑state, etc.).

---

## Claims

1. **Structural‑failure coverage beyond bit‑tests.** Targets defects that preserve marginals and pass bit‑tests but manifest as structure after deterministic protocol processing (finite‑state, low‑rank, phase restriction, coupling, etc.).  
2. **No security leap.** Detection of structure is not cryptographic breakage; it is diagnostic evidence of deviation from idealized assumptions.  
3. **Algebraic interpretability (ks1/ks2).** The spectrum $$\Sigma=(\mathrm{type},[\Delta],L,\dots)$$ yields an interpretable decomposition of observed dynamics and a quantitative structure measure $$\mathcal{I}$$.  
4. **Information bound / effective dimension.** “OND Information Theorem” bounds extractable structure by $$\log_2 n$$, with dominant contribution from $$[\Delta]\in\mathbb{P}^1(\mathbb{Z}_n)$$.  
5. **Topology as an early diagnostic microscope.** TDA adds robust diagnostics of geometry/connectivity shifts, useful under unknown source models and drift.  
6. **Cross‑domain compatibility.** OND‑ART is consistent with Shannon, algorithmic, and physical/quantum randomness; it analyzes observable structure after computable protocol transformations.

---

## Non‑goals

1. **No cryptanalysis / no recovery.** No recovery of $$d$$, $$k$$, prediction, or security‑definition violations.  
2. **Not a pass/fail randomness test.** Produces profiles/intervals/structural interpretations, not binary decisions.  
3. **No hidden preprocessing.** Normalization not in π is a methodological error; visualization is separated from metrics.  
4. **No causal attribution by default.** Classes (A/B/C; I–IV; T0/T1/T2) are observational; causal explanations require separate investigation and/or golden experiments.  
5. **No claim that structure implies exploitability.** Structure can be diagnostically significant without a practical compromise scenario.

---

## Sources

- **OND‑ART v0.1 Specification (Draft)** — requirements for π, no hidden normalization, `obs_space`, diagnostic positioning.  
- **ks1/ks2** — T0/T1/T2 types, factor space $$\mathbb{P}^1(\mathbb{Z}_n)\times\mathbb{Z}_n\times\{T0,T1,T2\}$$, spectrum pipeline, information theorem.  
- **Inverse OND / “обратная задача”** — formalization of $$(\mathcal{O},\pi,\Delta)$$, three metrics, golden experiment, no key recovery, diagnostic report format.  
- **Связность случайных сигнатур на алгебраическом торе** — torus geometry and connection vector as base construction.  
- **Новые горизонты** — coverage claims, compatibility with randomness theories, non‑cryptanalytic positioning.
