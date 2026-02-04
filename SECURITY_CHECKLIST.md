# Security Audit Checklist

## Design
- [ ] Threat model reviewed and updated
- [ ] RNG source assumptions documented
- [ ] Extraction parameters justified and reviewed

## Implementation
- [ ] No hidden parameters or secret defaults
- [ ] All RNG outputs generated via `ONDMaxRNG`
- [ ] Raw OND metrics (no normalization)
- [ ] Synthetic signature generation uses valid bijection

## Dependencies
- [ ] `requirements.txt` pinned
- [ ] `requirements-dev.txt` pinned
- [ ] Dependencies reviewed for CVEs

## Testing
- [ ] Unit tests cover RNG core and protocol mappings
- [ ] Metrics validated on benchmark datasets
- [ ] Reproducibility checks (same seed, same output)

## Build & Release
- [ ] CI passes on supported Python versions
- [ ] Reproducible build verified
- [ ] Artifacts signed and checksums published

## Documentation
- [ ] API stability policy documented
- [ ] Release process documented
- [ ] Security contact configured
