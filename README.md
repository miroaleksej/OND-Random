# OND Random

OND Random is a research-grade RNG system and analysis toolkit built around **Observed Randomness Dynamics (OND)**. It provides:

- A library of RNGs, including a quantum measurement emulator
- An OND-maximal extractor (`ONDMaxRNG`) designed to remove structure
- Canonical OND metrics (`H_rank`, `H_sub`, `H_branch`)
- Benchmark suite generation and reference profiles
- A CLI to generate bytes, compute profiles, and build datasets

This project is designed for *maximum mathematical and physical fidelity* in the sense of OND: it models real-world structured randomness, and provides measurable, reproducible improvement relative to a raw QRNG emulator.

## Search Tags

Hashtags:
#OND #Random #RNG #CSPRNG #QuantumRandom #QRNG #PostQuantum #PQC #ECDSA #Schnorr #Dilithium #LatticeCryptography #Cryptography #Entropy #Randomness #Observability

Keywords:
observed randomness dynamics, ondrandom, RNG extractor, SHAKE256, structural randomness, protocol observation, nonce dynamics, signature dynamics, ECDSA ur uz, Schnorr signatures, Dilithium lattice, PQ signatures, quantum emulator, entropy whitening, OND metrics, H_rank, H_sub, H_branch, raw data analysis

## Summary

**OND Random** (Observed Randomness Dynamics) is a research-grade RNG system and analysis framework for measuring, improving, and comparing randomness quality. It is built around OND metrics (`H_rank`, `H_sub`, `H_branch`) and the SHAKE256-based `ONDMaxRNG` extractor.

**Goals**
- Improve randomness quality via strict extraction.
- Provide reproducible metrics and reports.
- Compare randomness sources (OS RNG, QRNG emulator, protocol observations).
- Support quantum emulation and test algorithms (Grover/Shor).

**Capabilities**
- Generate arbitrary bit lengths (256/512/1024 and beyond).
- OND profiling and source classification.
- Per-source auto-calibration of metrics.
- Benchmarks, reports, and an autonomous pipeline.
- Protocol observations: ECDSA/Schnorr/PQ.
- Quantum simulation: statevector/Lindblad/trajectories.
- Grover and Shor (ideal models).

## Competitive Matrix (High-Level)

Legend: `Yes` = native capability, `Partial` = limited or via integration, `No` = not a focus, `Doc/Spec` = standard document, `Tool` = reference implementation.

| System | Standard | Entropy Est. | Stat Tests | Extractor | OND Metrics | Protocol Obs | Quantum | Automation | Reproducible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **OND Random** | No | Partial | No | Yes | Yes | Yes | Yes | Yes | Yes |
| NIST SP 800-90B | Doc/Spec | Yes | No | No | No | No | No | No | Doc/Spec |
| NIST SP 800-22 | Doc/Spec | No | Yes | No | No | No | No | No | Doc/Spec |
| EntropyAssessment (NIST) | Tool | Yes | No | No | No | No | No | Partial | Partial |
| TestU01 | No | No | Yes | No | No | No | No | Partial | Partial |
| Dieharder | No | No | Yes | No | No | No | No | Partial | Partial |
| Qiskit Aer | No | No | No | No | No | No | Yes | Partial | Partial |
| QuTiP | No | No | No | No | No | No | Yes | Partial | Partial |

Notes:
- This is a **high-level, non-exhaustive** comparison focused on functional scope.
- OND Random **complements** standards (SP 800-90B / SP 800-22) rather than replaces them.

## Install (editable)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Offline / no-build-isolation (если нет доступа к PyPI):

```bash
pip install -e . --no-build-isolation
```

## CLI quickstart

Generate 64 bytes:

```bash
ond-random gen --rng ondmax --bytes 64 --hex
```

Generate exact bit lengths:

```bash
ond-random gen --rng ondmax --bits 256 --hex
ond-random gen --rng ondmax --bits 512 --hex
ond-random gen --rng ondmax --bits 1024 --hex
```

Compute OND profile from a quantum emulator:

```bash
ond-random profile --rng quantum --samples 10000 --dimension 4 --word-bits 32 --modulus
ond-random profile --rng quantum --samples 10000 --dimension 4 --word-bits 32 --modulus --auto-calibrate
ond-random profile --rng ondmax --source system --samples 10000 --dimension 4 --word-bits 32 --modulus --auto-calibrate
```

Generate benchmark datasets and reference profiles:

```bash
ond-random benchmark --samples 10000 --dimension 4 --word-bits 32 --modulus --branch-mode delta
ond-random benchmark --samples 10000 --dimension 4 --word-bits 32 --modulus --branch-mode delta --auto-calibrate --calibration-class I
```

## Library quickstart

```python
from ond_random import ObservationMap, ONDMaxRNG, SystemRNG, compute_profile

rng = ONDMaxRNG(SystemRNG())
obs = ObservationMap(dimension=4, word_bits=32, stride=1)
U = obs.from_rng(rng, samples=10000)
profile = compute_profile(U, modulus=obs.modulus)
print(profile.as_dict())
```

## Protocol observations (ECDSA / Schnorr / PQ)

ECDSA (classical):

```python
from ond_random import ECDSAObservation, ECDSAParams, ECDSASignature

params = ECDSAParams(n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
obs = ECDSAObservation(params, mode="urz")

sig = ECDSASignature(r=123456, s=789012)
U = obs.observe(sig, message=b"hello")
```

Schnorr:

```python
from ond_random import SchnorrObservation, SchnorrParams, SchnorrSignature

params = SchnorrParams(n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
obs = SchnorrObservation(params, mode="es")

sig = SchnorrSignature(r=123456, s=789012)
U = obs.observe(sig, message=b"hello")
```

Lattice / PQ (Dilithium-style):

```python
from ond_random import dilithium_observation, LatticeSignature

obs = dilithium_observation(dimension=8, mode="z_mod_q")
sig = LatticeSignature(z=[1, 2, 3, 4, 5, 6, 7, 8])
U = obs.observe(sig)
```

## Quantum emulation (physics + math tasks)

These modules simulate simple quantum systems using **OND RNG** for measurement sampling:

```python
from ond_random import bell_state_correlations, rabi_oscillation, quantum_random_walk, monte_carlo_integral
import numpy as np

bell = bell_state_correlations(shots=1024)
print(bell.correlation, bell.counts)

rabi = rabi_oscillation(theta=0.2, steps=20, shots=512)
print(rabi[:5])

walk = quantum_random_walk(steps=8, shots=1024)
print(walk)

mc = monte_carlo_integral(lambda x: np.sin(x), 0.0, np.pi, samples=10000)
print(mc)
```

## Vectorized kernels & backend selection

The statevector engine uses vectorized gate kernels. You can select a backend:

```bash
export OND_BACKEND=numpy   # or cupy / jax if installed
export OND_BACKEND=auto    # auto-tune fastest backend on this machine
```

Benchmark and auto-select fastest backend:

```bash
PYTHONPATH=. python scripts/benchmark_kernels.py --qubits 20 --iters 5
```

Batch gates (single-qubit):

```python
from ond_random.quantum.statevector import QuantumState, H, Z

qs = QuantumState.zero(1)
qs.apply_single_qubit_batch([H, Z, H], 0)
```

Test status:

```bash
PYTHONPATH=. python -m pytest -q
```

## Lindblad (noisy two-level system)

```python
from ond_random import QubitHamiltonian, QubitNoise, LindbladQubit, simulate_relaxation

model = LindbladQubit(
    hamiltonian=QubitHamiltonian(omega_z=1.0),
    noise=QubitNoise(gamma1=0.05, gamma_phi=0.02),
)

for _ in range(10):
    model.step(dt=0.1)
    print(model.expectation_z())

relax = simulate_relaxation(t_max=5.0, steps=50, gamma1=0.05, gamma_phi=0.02)
print(relax[:5])
```

## Multi-qubit Lindblad (2+ qubits)

```python
from ond_random import MultiQubitHamiltonian, MultiQubitNoise, LindbladSystem

system = LindbladSystem(
    n_qubits=2,
    hamiltonian=MultiQubitHamiltonian(n_qubits=2, omega_z=[1.0, 1.0], couplings_zz={(0, 1): 0.2}),
    noise=MultiQubitNoise(gamma1=[0.05, 0.05], gamma_phi=[0.02, 0.02]),
)

system.step(dt=0.1)
print(system.expectation_z(0), system.expectation_z(1))
```

## Quantum trajectories (Monte Carlo wavefunction)

For larger systems, trajectories scale better than full density matrices:

```python
from ond_random import MultiQubitHamiltonian, MultiQubitNoise, simulate_trajectories

result = simulate_trajectories(
    n_qubits=2,
    steps=40,
    dt=0.05,
    hamiltonian=MultiQubitHamiltonian(n_qubits=2, omega_z=[1.0, 1.0]),
    noise=MultiQubitNoise(gamma1=[0.05, 0.05], gamma_phi=[0.02, 0.02]),
    trajectories=200,
)
print(result.expectations_z)
```

## Grover search (quantum‑identical statevector)

Example: search a 5‑digit space (`00000–99999`). This uses 17 qubits (2^17 = 131072).

```python
from ond_random import grover_search

result = grover_search(target=42424, n_items=100000, shots=100)
print(result.success_prob, result.measured_success, result.theta, result.theoretical_amplitude, result.counts)
```

CLI:

```bash
ond-random grover --items 100000 --target 42424 --shots 100
ond-random grover --items 100000 --targets 123,456,789 --shots 200
ond-random grover --items 100000 --n-solutions 5 --shots 200
ond-random grover --items 100000 --targets-random 5 --shots 200
```

## Shor factorization (ideal period finding)

```bash
ond-random shor --N 15 --a 2 --shots 200
ond-random shor --N 21 --a 2 --shots 200
```

Noise mode (effective depolarizing on measurement distribution):

```bash
ond-random shor --N 15 --a 2 --shots 200 --gamma1 0.05 --gamma-phi 0.02
```

Batch test (N=15,21,35):

```bash
ond-random shor-batch --a 2 --shots 200 --out data/reports/shor_batch.json
```

Noise success report (ideal vs noisy):

```bash
PYTHONPATH=. python scripts/shor_noise_report.py --shots 50 --trials 50 --gamma1 0.05 --gamma-phi 0.02
```

## Auto-calibration (online)

Online calibration updates target statistics as new profiles arrive:

```python
from ond_random import OnlineCalibrator

cal = OnlineCalibrator()
cal.update({"H_rank": 0.99, "H_sub": 0.81, "H_branch": 0.22})
target = cal.target()
print(target.mean, target.std)
```

Calibration is stored **per source** in a calibration bank (`online_calibration_state.json`, mapping keys -> stats). You can override the key:

```bash
ond-random profile --rng quantum --auto-calibrate --calibration-key my-quantum-source
```

Generate a calibration report from benchmarks:

```bash
PYTHONPATH=. python scripts/auto_calibrate.py --ond-class I
```

## Formal security bounds (conditional)

Formal statements and bounds are in `docs/SECURITY_PROOFS.md`.

Compute conditional bounds:

```bash
PYTHONPATH=. python scripts/security_bounds.py --min-entropy 512 --output-bits 256 --queries 2^32
```

## NIST SP 800-90B min-entropy estimation

Run the official EntropyAssessment tool (ea_iid / ea_non_iid) from NIST:

```bash
PYTHONPATH=. python scripts/nist_entropy_estimator.py --rng system --symbols 1000000 --bits-per-symbol 8 --track non-iid
```

Note: install the NIST EntropyAssessment tool and ensure `ea_iid` / `ea_non_iid` are on PATH.

## Academic security report (PDF)

Generate `docs/SECURITY_REPORT.pdf`:

```bash
PYTHONPATH=. python scripts/build_security_report.py
```

Add compliance excerpts (verbatim, short quotes) in:

`docs/COMPLIANCE_EXCERPTS.md`

## Autonomous benchmarking pipeline

Run the full benchmark + validation + report pipeline:

```bash
PYTHONPATH=. python scripts/run_pipeline.py --samples 10000 --dimension 4 --word-bits 32 --branch-mode delta
```

Trajectory vs Lindblad comparison report (with plots in `data/reports/plots/`):

```bash
PYTHONPATH=. python scripts/trajectories_report.py
```

## Synthetic ECDSA signatures (valid, non-public)

For synthetic OND datasets, `r, s, z` must be **valid** and consistent. You can generate them from random `(u_r, u_z)` using the ECDSA table bijection:

```
R = u_r * Q + u_z * G
r = x(R) mod n
s = r / u_r mod n
z = u_z * s mod n
```

This is implemented in `synthetic_ecdsa_signature`:

```python
from ond_random import (
    SECP256K1,
    public_key_from_private,
    synthetic_ecdsa_signature,
    ECDSAObservation,
    ECDSAParams,
)
from ond_random.rng import ONDMaxRNG, SystemRNG

Q = public_key_from_private(3, SECP256K1)
sig, z, _ = synthetic_ecdsa_signature(ur=12345, uz=67890, Q=Q, curve=SECP256K1)

obs = ECDSAObservation(ECDSAParams(n=SECP256K1.n), mode="urz")
U = obs.observe(sig, message=z)  # message can be pre-hashed int
```

## OND-maximality

OND-maximality here means that the extracted output is as close as possible to the IID null model *in the OND sense*. This is measured by the three canonical metrics, computed **on raw observations (no normalization)**:

- `H_rank` (effective dimensionality)
- `H_sub` (uniformity of phase-space occupancy)
- `H_branch` (branching/automaton structure)

## Formal Criteria (Fixed)

1. **OND‑Maximality**: `H_rank`, `H_sub`, `H_branch` максимально близки к IID‑null на сырых данных.
2. **Устойчивость**: стабильность профиля при смене источника (QRNG, OS RNG, эмулятор) и при разных режимах.
3. **Проверяемость**: воспроизводимый отчёт и методика, проверяемая без доступа к внутреннему состоянию.
4. **Безопасность**: строгая экстракция (SHAKE‑based), отсутствие скрытых параметров, прозрачный код.

## Production Readiness

- Threat model: `THREAT_MODEL.md`
- Security checklist: `SECURITY_CHECKLIST.md`
- API stability: `docs/API.md`, `docs/STABILITY.md`
- Release process: `RELEASE.md`
- CI: `.github/workflows/ci.yml`
- Contributor guide: `CONTRIBUTING.md`
- Code owners: `.github/CODEOWNERS`

## OND scoring and calibration

You can convert a profile into a single OND score and calibrate against a benchmark class:

```python
from ond_random import score_profile, calibrate_from_benchmark_dir

target = calibrate_from_benchmark_dir("data/benchmarks")
score = score_profile(profile, target=target)
print(score.score, score.distance)
```

You can also optimize `ONDMaxRNG` parameters with a simple grid search:

```bash
PYTHONPATH=. python scripts/optimize_ondmax.py --samples 10000 --dimension 4 --word-bits 32 --stride 1 --modulus
```

Auto-weights and reference updates:

```bash
PYTHONPATH=. python scripts/optimize_ondmax.py --auto-weights --update-references
```

## Quality report

After running benchmarks, generate a sanity report:

```bash
PYTHONPATH=. python scripts/quality_report.py
```

## Numeric validation (RK4 + analytic checks + plots)

```bash
PYTHONPATH=. python scripts/numeric_validation.py
```

Outputs:
- `data/reports/numeric_validation.json`
- `data/reports/plots/dt_scan.png`
- `data/reports/plots/gamma_scan.png`

## Benchmarks

Generated datasets are stored under `data/benchmarks/` as:

- `*.npz` (compressed observation arrays)
- `*.json` (OND profile + metadata)
- `reference_profiles.json` (class references)

## Notes

This toolkit is diagnostic. It does **not** attempt key recovery or cryptanalysis. It is a structural randomness evaluation system compatible with cryptographic safety principles.
