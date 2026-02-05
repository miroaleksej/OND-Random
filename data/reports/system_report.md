# System Report

## Executive Summary
- Lindblad Euler max error: 1.465e-02
- Lindblad RK4 max error: 1.586e-08
- Lindblad gamma-scan max error: 6.183e-11
- Quality report status: PASS
- Online calibration key: I-ondmax
- Online calibration H_rank mean: 0.9572577450241212
- Best backend (qubits=20): numpy

## OND Differentials
- H_sub(IID) - H_sub(Q-drift): 0.0320
- H_branch(IID) - H_branch(Q-drift): 0.0413

## Shor Noise Success
- N=15: ideal=1.00, noisy=1.00
- N=21: ideal=1.00, noisy=1.00
- N=35: ideal=1.00, noisy=1.00

## Trajectories vs Lindblad
- n_qubits=1: mean_abs_err=3.336e-02, max_abs_err=3.336e-02
- n_qubits=2: mean_abs_err=2.868e-02, max_abs_err=5.736e-02

## NIST SP 800-90B Min-Entropy (EntropyAssessment)
- Not available (run scripts/nist_entropy_estimator.py)