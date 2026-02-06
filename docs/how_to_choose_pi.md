# How to choose π (observation map)

Your observation map `π` defines what is “visible” to ODD. Good `π` should be:

1. **Deterministic** (same input → same output).
2. **Public‑only** (no hidden state, no secret fields).
3. **Fixed shape** (consistent dimension across runs).
4. **Documented** (pi_id, pi_version, pi_spec_hash).
5. **Raw‑policy explicit** (any normalization/rescaling must be part of π and documented; otherwise ODD/TDA uses raw data).

## Practical patterns

### Scalar series
- Example: `energy` over time.
- Use delay embedding: `U_i = [x_i, x_{i+1}, ..., x_{i+k}]`.

### Vector observations
- Example: `(lat, lon, temp, humidity)` per sample.
- Use direct vector with `obs_space = R^d`.

### Modular observations
- Example: signature‑derived `u_r, u_z` (mod n).
- Use `obs_space = Z_mod_m` and torus embedding for large moduli.

## Versioning rule
- If you change the math of `π`, bump `pi_version`.
- Keep `pi_id` stable for the conceptual map.

## Registry (anti‑drift)
Maintain a shared `pi_registry.json` that maps `pi_id`/`pi_version` to `pi_spec_hash`.
Use `ond-random pi-registry add/check` or `ond-random obs-export --pi-registry ...` to enforce it.
