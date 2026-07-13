# Firecrown Wrapper (TD)

A lightweight wrapper around **Firecrown** workflows for supernova time-domain cosmology analyses with **COSMOSIS**. It streamlines the end-to-end pipeline from Hubble diagram and covariance inputs to postprocessed cosmological summaries.

This repository is intended to make it easier to:
- run Firecrown/COSMOSIS analyses from a single command,
- standardize execution and output layout across environments,
- and keep the pipeline logic transparent and easier to embed in larger workflows.

---

## Why this repository exists

Running Firecrown for supernova cosmology involves multiple stages, including data preparation into **SACC** format, COSMOSIS parameter estimation, and post-processing of the resulting chains. This wrapper collects those steps into a more uniform interface that is easier to:

- **reproduce** through a consistent command-line interface,
- **maintain** through modular Python functions and structured outputs,
- **embed** in batch systems and larger pipeline tooling such as `submit_batch_jobs.sh`.

---

## What it does

The main wrapper script, `Firecrown_wrapper.py`, orchestrates four stages:

1. **Stage 0:** generate a SACC file from a supernova Hubble diagram and covariance matrix using Firecrown example tooling,
2. **Stage 1:** run **COSMOSIS** with the generated SACC file,
3. **Stage 2:** run `cosmosis-postprocess` on the output chains,
4. **Stage 3:** extract cosmological summary values and write `SUMMARY.YAML`.

The code also includes:
- a reusable subprocess execution helper in `subprocess_executor.py`,
- tests in `test_Firecrown_wrapper.py`,
- a PyInstaller spec for building a standalone executable,
- and Sphinx documentation scaffolding.

---

## Repository structure

```text
.
├── Firecrown_wrapper.py        # Main CLI wrapper for the full analysis pipeline
├── subprocess_executor.py      # Subprocess execution, logging, timeout handling
├── test_Firecrown_wrapper.py   # Unit and integration tests for the wrapper
├── CHISQ.py                    # Auxiliary χ²-related postprocessing code
├── Firecrown_wrapper.spec      # PyInstaller spec for building an executable
├── requirements.txt            # Minimal Python dependencies used directly here
├── README.md                   # Project overview and usage
├── conf.py                     # Sphinx documentation configuration
├── index.rst                   # Sphinx documentation index
├── Makefile                    # Sphinx documentation build helper
├── make.bat                    # Windows Sphinx build helper
├── .github/workflows/          # GitHub Actions workflows for linting/testing
└── _build/                     # Generated documentation artifacts
```

---

## Requirements

This wrapper assumes that **Firecrown** and **COSMOSIS** are already installed and available in the active environment.

Python packages used directly by this repository are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Current listed dependencies:
- `pandas`
- `numpy`
- `pyyaml`

You may also need environment-specific tooling such as:
- `cosmosis`
- `cosmosis-postprocess`
- Firecrown example data/scripts via `$FIRECROWN_EXAMPLES_DIR`
- `pytest` for tests
- `flake8` if you want to run the same lint checks as GitHub Actions

---

## Installation

Clone the repository:

```bash
git clone https://github.com/am610/Firecrown_wrapper_TD.git
cd Firecrown_wrapper_TD
```

To install the direct Python dependencies for local development/testing:

```bash
pip install -r requirements.txt
pip install pytest flake8
```

To build a standalone executable version of the wrapper:

```bash
pyinstaller Firecrown_wrapper.spec
```

This creates an executable named `Firecrown_wrapper` based on `Firecrown_wrapper.py`.

---

## How to run

The main entry point is the wrapper script itself:

```bash
python Firecrown_wrapper.py <path> <hd> <cov> <ini> [-O <outdir>] [-p <param>] [-s <summary>]
```

Where:
- `<path>` is the directory containing the Hubble diagram and covariance files,
- `<hd>` is the Hubble diagram filename,
- `<cov>` is the covariance filename,
- `<ini>` is the COSMOSIS `.ini` input file,
- `-O/--outdir` optionally sets the output directory,
- `-p/--param` optionally overrides COSMOSIS parameter values,
- `-s/--summary` optionally sets the output `SUMMARY.YAML` path.

Example:

```bash
python Firecrown_wrapper.py /path/to/input HD.txt cov.txt sn_only.ini -O /path/to/output
```

The script will create the following output subdirectories under the selected output path:
- `ERROR_LOGS`
- `COSMOSIS-CHAINS`
- `PLOTS`

It also writes a `SUMMARY.YAML` file with stage status and extracted cosmological summary values.

---

## Batch usage

This wrapper was designed to work well in HPC and pipeline environments.

Two supported usage patterns documented in the original project are:
- use through `submit_batch_jobs.sh` in SNANA / DESC TD workflows,
- or submit directly as a batch job in NERSC Perlmutter via `sbatch`.

The repository does not include the external pipeline utilities themselves, but the wrapper is structured to integrate with them.

---

## Testing

The repository includes a pytest suite in `test_Firecrown_wrapper.py` covering:
- argument parsing and validation,
- output directory setup,
- file/path validation,
- subprocess execution behavior,
- burn-in calculation,
- figure-of-merit calculation,
- and some end-to-end integration-style checks.

Run tests with:

```bash
pytest -q
```

GitHub Actions workflows are also present for automated linting and testing on `main`.

---

## Notes and current limitations

- The wrapper expects external Firecrown/COSMOSIS tooling to already be installed and configured.
- Stage 0 depends on `$FIRECROWN_EXAMPLES_DIR/srd_sn/generate_sn_data.py`.
- The `CHISQ.py` module exists, but `chi2` is currently left as a placeholder in `Firecrown_wrapper.py`.
- The repository includes generated/documentation helper files such as `_build/`, `conf.py`, `index.rst`, and Sphinx makefiles.

---

## Contact

Maintainer: **Ayan Mitra** (GitHub: [@am610](https://github.com/am610))
