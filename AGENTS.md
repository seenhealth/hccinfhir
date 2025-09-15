# Repository Guidelines

This guide streamlines contributions to the hccinfhir Python package (HCC Algorithm for FHIR Resources). Follow these conventions to keep the codebase consistent and maintainable.

## Project Structure & Module Organization
- `src/hccinfhir/` — core library
  - `data/` CSV reference tables (e.g., `ra_coefficients_2026.csv`)
  - `sample_files/` lightweight fixtures for tests/examples
  - Key modules: `extractor*.py`, `model_*.py`, `filter.py`, `utils.py`, `datamodels.py`
- `tests/` — pytest suite (`test_*.py`)
- `examples/` — runnable examples (e.g., `python examples/sample_data_usage.py`)

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install editable: `pip install -e .` (and optionally `pip install -r requirements.txt`)
- Run tests: `python -m pytest -q`
- Coverage: `coverage run -m pytest && coverage report -m`
- Build a wheel: `python -m build` (uses Hatchling via `pyproject.toml`)

## Coding Style & Naming Conventions
- Python ≥3.8; 4‑space indentation; PEP 8; use type hints for public APIs.
- Naming: modules/functions/variables `snake_case`; classes `PascalCase`; constants `UPPER_SNAKE_CASE`.
- Data files follow existing patterns (e.g., `ra_*_{year}.csv`). Keep additions small and documented.
- Keep functions focused with clear inputs/outputs; prefer pure transforms over I/O in model code.

## Testing Guidelines
- Framework: `pytest`. Place tests in `tests/` as `test_*.py`.
- Add unit tests for new logic and edge cases; parametrize where helpful.
- Use `src/hccinfhir/sample_files/` for fixture inputs; avoid external/networked data.
- Coverage config lives in `pyproject.toml` (`[tool.coverage.*]`). Example single file run: `pytest tests/test_extractor_837.py -q`.

## Commit & Pull Request Guidelines
- Commits: imperative mood and scoped. Example: `feat(extractor): add 837 segment parser`.
- PRs: include a clear description, linked issues, test coverage evidence, and notes on data/behavioral impacts.
- Avoid committing PHI/PII or large datasets; keep samples minimal and anonymized.

## Security & Configuration Tips
- No network or external services are required for tests; keep tests offline and deterministic.
- Validate any new CSV schemas and document sources in the PR description.
