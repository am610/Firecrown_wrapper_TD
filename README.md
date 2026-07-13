# Firecrown Wrapper (TD)

A lightweight Python wrapper for running **Firecrown** + **COSMOSIS** supernova time-domain cosmology workflows from a single command. It automates the full analysis path from Hubble diagram and covariance inputs, to SACC generation, parameter estimation, post-processing, and final summary output.

This project is designed to make Firecrown-based supernova analyses easier to reproduce, easier to run in batch or HPC environments, and easier to integrate into larger DESC / SNANA-style pipeline workflows.

## What it does

`Firecrown_wrapper.py` orchestrates a four-stage pipeline:

1. **Stage 0** — generate a SACC file from a supernova Hubble diagram and covariance matrix
2. **Stage 1** — run **COSMOSIS** parameter estimation
3. **Stage 2** — run `cosmosis-postprocess` on the resulting chains
4. **Stage 3** — extract cosmological summary values and write `SUMMARY.YAML`

The repository also includes:

- `subprocess_executor.py` for subprocess execution, logging, and timeout handling
- `test_Firecrown_wrapper.py` for unit and integration tests
- `Firecrown_wrapper.spec` for building a standalone executable with PyInstaller
- Sphinx documentation scaffolding and GitHub Actions workflows for testing/linting

## Why this repository exists

Running Firecrown for supernova cosmology involves several moving parts: input preparation, external tool execution, output organization, and post-processing. This wrapper provides a simpler and more standardized interface so analyses are easier to reproduce, maintain, and embed in larger automated workflows.
