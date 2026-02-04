# API Reference (Stable Surface)

This document defines the **stable public API**. Anything not listed here is internal and may change.

## RNG Core
- `ond_random.ONDMaxRNG`
- `ond_random.SystemRNG`
- `ond_random.rng.base.RNG` methods: `random_bytes`, `random_bits`, `random_uint`, `random_vector`

## OND Metrics
- `ond_random.compute_profile(U, modulus=None, bins=16, max_subspace_dim=6, branch_bins=16)`
- `ond_random.ond.ONDProfile`

## Scoring & Calibration
- `ond_random.score_profile(profile, target, weights=None)`
- `ond_random.calibrate_from_benchmark_dir(path, target_class=ONDClass.I)`
- `ond_random.OnlineCalibrator`
- `ond_random.auto_weights_from_profiles(profiles)`
- `ond_random.objective_from_profiles(profiles, target, weights=None)`

## Protocol Observations
- ECDSA: `ECDSAObservation`, `ECDSAParams`, `ECDSASignature`, `synthetic_ecdsa_signature`, `synthetic_ecdsa_batch`
- Schnorr: `SchnorrObservation`, `SchnorrParams`, `SchnorrSignature`
- PQ/Lattice: `LatticeObservation`, `LatticeParams`, `LatticeSignature`, `dilithium_observation`

## Quantum Emulation
- Statevector: `QuantumState`, `H`, `X`, `Y`, `Z`, `rotation_x`, `rotation_y`, `rotation_z`
- Tasks: `bell_state_correlations`, `rabi_oscillation`, `quantum_random_walk`, `monte_carlo_integral`
- Lindblad: `QubitHamiltonian`, `QubitNoise`, `LindbladQubit`, `simulate_relaxation`
- Lindblad (multi-qubit): `MultiQubitHamiltonian`, `MultiQubitNoise`, `LindbladSystem`
- Quantum trajectories: `simulate_trajectories`, `TrajectoryResult`
- Grover/Shor: `grover_search`, `GroverResult`, `shor_factor`, `ShorResult`
- Backend selection: `select_backend`, `available_backends`, `benchmark_backend`, `auto_select_backend`

## Stability Policy
See `docs/STABILITY.md`.
