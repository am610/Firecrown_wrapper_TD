# Firecrown Wrapper (TD)

A lightweight wrapper around **Firecrown** workflows for time-delay (TD) cosmology analyses, focused on reproducible execution, configuration management, and cleaner interfaces for iterative scientific work.

This repository is intended to make it easier to:
- define and run TD analysis configurations,
- standardize execution across environments,
- and keep scientific pipeline logic transparent and auditable.

---

## Why this repository exists

Running cosmology workflows often involves repeated setup, parameter editing, and orchestration around core analysis tools.  
This wrapper provides a structured layer around Firecrown so that analyses are easier to:

- **reproduce** (explicit environment + configuration),
- **maintain** (modular code + clear entry points),
- **extend** (new models/data choices without rewriting everything).

---

## Features

- Wrapper utilities for Firecrown-based TD workflows.
- Config-driven execution for analysis runs.
- Web/UI-related components (JavaScript/CSS/HTML) for interaction or result presentation.
- Python-first scientific logic and pipeline orchestration.

> Language composition (GitHub): Python 35.2%, JavaScript 29.6%, CSS 26.5%, HTML 7.5%.

---

## Repository structure

> Update this tree to exactly match your repo before sharing.

```text
.
├── src/                    # Core Python wrapper code (recommended)
├── scripts/                # Runnable helper scripts / CLI entrypoints
├── config/                 # Example configuration files
├── web/                    # Front-end assets (JS/CSS/HTML), if applicable
├── tests/                  # Unit/integration tests
├── examples/               # Minimal runnable examples
├── requirements.txt        # Python dependencies (or environment.yml)
└── README.md
```

If your current layout differs, keep this section truthful and concise.

---

## Requirements

- Python **3.10+** (recommended: 3.11)
- `pip` or `conda/mamba`
- (Optional) Node.js if front-end build steps are required

---

## Installation

### Option A: pip + virtualenv

```bash
git clone https://github.com/am610/Firecrown_wrapper_TD.git
cd Firecrown_wrapper_TD

python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows PowerShell

pip install -U pip
pip install -r requirements.txt
```

### Option B: conda/mamba (if `environment.yml` is present)

```bash
git clone https://github.com/am610/Firecrown_wrapper_TD.git
cd Firecrown_wrapper_TD
mamba env create -f environment.yml
mamba activate firecrown-wrapper-td
```

---

## Quickstart

> Replace the commands below with your actual entry point(s).

```bash
# Example: run a baseline configuration
python scripts/run_analysis.py --config config/baseline.yaml
```

Expected outcome:
- analysis runs successfully,
- output artifacts are written to the configured output directory,
- logs summarize the selected model/settings.

---

## Minimal example workflow

1. Choose/edit a config file in `config/`.
2. Run the analysis entrypoint script.
3. Inspect output summaries/plots/tables.
4. (Optional) use web components for visualization or interaction.

If helpful, include a concrete command+output snippet from one real run.

---

## Testing

> Keep this section aligned with what currently exists.

Run tests with:

```bash
pytest -q
```

If you have only a small test suite, that is still valuable—keep tests focused on core logic and expected behavior.

---

## Reproducibility notes

- Pin dependencies in `requirements.txt` (or lock file / environment file).
- Keep configuration files under version control.
- Avoid hard-coded local paths; use config/env variables instead.
- Record software versions in output metadata when possible.

---

## Scientific/software context

This repository reflects practical research software engineering in cosmology workflows:
- balancing scientific flexibility with maintainable code,
- preserving transparent assumptions through config-first design,
- and enabling repeatable analyses across collaborators and environments.

---

## Limitations and future improvements

Current limitations may include:
- incomplete test coverage,
- evolving configuration schema,
- workflow assumptions specific to current TD use cases.

Planned improvements:
- expanded test suite and CI checks,
- clearer typed interfaces and docs,
- additional example configs and benchmark runs.

---

## Contributing

Contributions, issues, and suggestions are welcome.  
For substantial changes, please open an issue first to discuss scope and design.

---

## License

Add a license file (recommended: MIT, BSD-3-Clause, or Apache-2.0), then reference it here.

Example:

`This project is licensed under the MIT License - see the LICENSE file for details.`

---

## Citation

If this repository supports published or publishable scientific work, add `CITATION.cff` so others can cite it properly.

---

## Contact

Maintainer: **Ayan** (GitHub: [@am610](https://github.com/am610))
