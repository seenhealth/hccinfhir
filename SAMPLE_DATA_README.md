# Sample Data Module for HCCInFHIR

The HCCInFHIR package includes a comprehensive sample data module that provides easy access to pre-prepared sample data for testing, development, and demonstration purposes.

## Overview

The sample data module provides access to two types of sample data:

1. **EOB (Explanation of Benefits) Samples**: FHIR resources for testing HCC calculations
2. **837 Claim Samples**: X12 837 claim data for testing claim processing

## Quick Start

### Import the Module

```python
from hccinfhir import (
    get_eob_sample,
    get_eob_sample_list,
    get_837_sample,
    get_837_sample_list,
    list_available_samples
)
```

### Get EOB Samples

```python
# Get a specific EOB sample (case 1, 2, or 3)
eob_data = get_eob_sample(1)
print(f"Resource Type: {eob_data['resourceType']}")

# Get a list of EOB samples (limited to first 10)
eob_list = get_eob_sample_list(limit=10)
print(f"Retrieved {len(eob_list)} EOB samples")

# Get all 200 EOB samples
all_eob_samples = get_eob_sample_list()
print(f"Total EOB samples: {len(all_eob_samples)}")
```

### Get 837 Claim Samples

```python
# Get a specific 837 sample (case 0 through 11)
claim_data = get_837_sample(0)
print(f"Claim data length: {len(claim_data)} characters")
print(f"Starts with ISA: {'ISA' in claim_data}")

# Get multiple 837 samples
claims = get_837_sample_list([0, 1, 2])
print(f"Retrieved {len(claims)} claim samples")

# Get all 12 837 samples
all_claims = get_837_sample_list()
print(f"Total claim samples: {len(all_claims)}")
```

### Get Sample Information

```python
# Get information about available samples
info = list_available_samples()
print(f"Available EOB samples: {info['eob_samples']}")
print(f"Available 837 samples: {info['837_samples']}")
print(f"EOB case numbers: {info['eob_case_numbers']}")
print(f"837 case numbers: {info['837_case_numbers']}")
```

## Detailed Usage

### Using the SampleData Class

You can also use the `SampleData` class directly:

```python
from hccinfhir import SampleData

# Class methods provide the same functionality
eob = SampleData.get_eob_sample(1)
claims = SampleData.get_837_sample_list([0, 1, 2])
info = SampleData.list_available_samples()
```

### Error Handling

The module includes proper error handling:

```python
try:
    # Try to get a non-existent case
    eob = get_eob_sample(99)
except ValueError as e:
    print(f"Invalid case number: {e}")

try:
    # Try to get a non-existent file
    claim = get_837_sample(99)
except ValueError as e:
    print(f"Invalid case number: {e}")
except FileNotFoundError as e:
    print(f"Sample file not found: {e}")
```

## Available Samples

### EOB Samples

| Case | File | Description |
|------|------|-------------|
| 1 | `sample_eob_1.json` | Basic EOB with single diagnosis |
| 2 | `sample_eob_2.json` | EOB with multiple service lines |
| 3 | `sample_eob_3.json` | EOB with complex diagnosis mapping |
| - | `sample_eob_200.ndjson` | Large dataset with 200 EOB samples |

### 837 Claim Samples

| Case | File | Description |
|------|------|-------------|
| 0 | `sample_837_0.txt` | Comprehensive professional claim |
| 1 | `sample_837_1.txt` | Basic professional claim |
| 2 | `sample_837_2.txt` | Institutional claim |
| 3-11 | `sample_837_3.txt` - `sample_837_11.txt` | Various claim scenarios |

## Integration Examples

### Testing HCC Calculations

```python
from hccinfhir import HCCInFHIR, get_eob_sample, Demographics

# Get sample EOB data
eob_data = get_eob_sample(1)

# Create sample demographics
demographics = Demographics(
    age=65,
    sex="F",
    dual_elgbl_cd="0",
    orec="0",
    crec="0",
    new_enrollee=False,
    snp="0",
    low_income=False
)

# Process the sample data
processor = HCCInFHIR()
result = processor.run([eob_data], demographics)
print(f"HCC Score: {result.raf_score}")
```

### Testing Claim Processing

```python
from hccinfhir import extract_sld, get_837_sample

# Get sample 837 claim data
claim_data = get_837_sample(0)

# Process the claim
service_data = extract_sld(claim_data, format="837")
print(f"Extracted {len(service_data)} service lines")

for service in service_data:
    print(f"Procedure: {service.procedure_code}")
    print(f"Diagnosis: {service.linked_diagnosis_codes}")
```

## Use Cases

1. **Development and Testing**: Use sample data to test your HCC calculation logic
2. **Demonstrations**: Show how the library works with real-world data
3. **Documentation**: Provide examples in your documentation
4. **Training**: Use samples to train users on the library
5. **Integration Testing**: Test integration with other systems

## File Locations

The sample data files are located in the package's `samples` directory and are automatically included when the package is installed. The module uses Python's `importlib.resources` to access these files reliably across different installation methods.

## Performance Notes

- **EOB samples**: Individual JSON files are small and load quickly
- **EOB list**: The 200-sample file is larger (~1.8MB) but loads incrementally
- **837 samples**: Text files are small and load very quickly
- **Memory usage**: The module loads files on-demand to minimize memory usage

## Troubleshooting

### Common Issues

1. **File not found errors**: Ensure the package is properly installed
2. **Import errors**: Check that you're importing from the correct package
3. **Memory issues**: Use `limit` parameter when loading large sample lists

### Getting Help

If you encounter issues with the sample data module:

1. Check that the package is properly installed
2. Verify the import statements are correct
3. Use the `list_available_samples()` function to verify available files
4. Check the package documentation for updates

## Contributing

To add new sample data:

1. Place new sample files in the `src/hccinfhir/samples/` directory
2. Update the `list_available_samples()` method in `sample_utils.py`
3. Add appropriate tests
4. Update this documentation

## License

The sample data is included with the HCCInFHIR package under the same license terms.
