# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
hatch shell                    # Activate virtual environment
pip install -e .              # Install package in development mode
pytest tests/*                # Run all tests
pytest tests/test_filter.py   # Run specific test file
```

### Building and Publishing
```bash
hatch build                    # Build package
hatch publish                  # Publish to PyPI (maintainers only)
```

### Dependencies
- Install new dependencies by updating `pyproject.toml` dependencies
- Core dependency: `pydantic >= 2.10.3`
- Development dependency: `pytest`

## Architecture Overview

This is a Python library for extracting and processing healthcare data to calculate HCC (Hierarchical Condition Category) risk adjustment scores. The architecture follows a modular pipeline approach:

### Core Data Flow
1. **Input**: FHIR ExplanationOfBenefit resources OR X12 837 claims OR service-level data
2. **Extraction**: Convert input data to standardized Service Level Data (SLD) format
3. **Filtering**: Apply CMS filtering rules for eligible services
4. **Calculation**: Map diagnosis codes to HCCs and calculate RAF scores

### Key Components

#### Main Processor (`hccinfhir.py`)
- **HCCInFHIR class**: Main entry point integrating all components
- Three processing methods:
  - `run()`: Process FHIR EOB resources
  - `run_from_service_data()`: Process standardized service data
  - `calculate_from_diagnosis()`: Direct diagnosis code processing

#### Data Extraction
- **Extractor module** (`extractor.py`): Unified interface for data extraction
- **FHIR Extractor** (`extractor_fhir.py`): Processes FHIR resources using Pydantic models
- **837 Extractor** (`extractor_837.py`): Parses X12 837 claim data

#### Data Models (`datamodels.py`)
- **ServiceLevelData**: Standardized format for healthcare service data
- **Demographics**: Patient demographic information for risk calculation
- **RAFResult**: Complete risk score calculation results
- Uses Pydantic for validation and type safety

#### Risk Calculation Engine
- **Model modules** (`model_*.py`): Implement CMS HCC calculation logic
  - `model_calculate.py`: Main RAF calculation orchestrator
  - `model_demographics.py`: Demographics processing
  - `model_dx_to_cc.py`: Diagnosis to condition category mapping
  - `model_hierarchies.py`: HCC hierarchical rules
  - `model_interactions.py`: Interaction calculations
  - `model_coefficients.py`: Risk score coefficients

#### Filtering (`filter.py`)
- Applies CMS filtering rules based on CPT/HCPCS codes
- Separates inpatient/outpatient and professional service requirements

### Data Files
Located in `src/hccinfhir/data/`:
- **Diagnosis Mapping**: `ra_dx_to_cc_*.csv` - ICD-10 to condition category mapping
- **Hierarchies**: `ra_hierarchies_*.csv` - HCC hierarchical relationships
- **Coefficients**: `ra_coefficients_*.csv` - Risk score coefficients
- **Filtering**: `ra_eligible_cpt_hcpcs_*.csv` - Eligible procedure codes
- **Chronic Conditions**: `hcc_is_chronic.csv` - Chronic condition flags

### Sample Data System
- Comprehensive sample data in `src/hccinfhir/samples/`
- **EOB samples**: 3 individual cases + 200 sample dataset
- **837 samples**: 12 different claim scenarios
- Access via `get_eob_sample()`, `get_837_sample()`, etc.

## Model Support

### Supported HCC Models
- CMS-HCC Model V22, V24, V28
- CMS-HCC ESRD Model V21, V24
- RxHCC Model V08

### Model Years
- 2025 and 2026 model year data files included
- Default configuration uses 2026 model year

## Common Development Tasks

### Adding New HCC Models
1. Add model name to `ModelName` literal type in `datamodels.py`
2. Add corresponding data files to `src/hccinfhir/data/`
3. Update loading functions in respective model modules

### Testing New Features
- Use sample data functions: `get_eob_sample()`, `get_837_sample()`
- Test with different demographics using `Demographics` model
- Validate using `pytest tests/test_*.py` files

### Working with Data Files
- CSV files use standard format with headers
- Loading handled by utility functions in respective modules
- Files are included in package build via `pyproject.toml` configuration