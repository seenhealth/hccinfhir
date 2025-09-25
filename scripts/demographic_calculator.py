#!/usr/bin/env python3
"""
Standalone V22 Demographic Score Calculator

Usage:
    python demographic_calculator.py "Male 55-59"
    python demographic_calculator.py "Female 75-79"
    python demographic_calculator.py "Male 65-69"

This script calculates the demographic component of the V22 risk score
from a sex and age band string.
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to the path so we can import hccinfhir modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from hccinfhir.model_demographics import categorize_demographics
    from hccinfhir.model_coefficients import apply_coefficients, get_coefficent_prefix
except ImportError as e:
    print(f"Error importing hccinfhir modules: {e}")
    print("\nTo fix this, run the script using one of these methods:")
    print("1. uv run python demographic_calculator.py \"Male 55-59\"")
    print("2. uv pip install -e . && python demographic_calculator.py \"Male 55-59\"")
    print("3. Make sure you're in the hccinfhir directory and have uv installed")
    sys.exit(1)

def parse_demographic_string(demo_str):
    """
    Parse demographic string like "Male 55-59" or "Female 75-79".

    Args:
        demo_str: String like "Male 55-59" or "Female 75-79"

    Returns:
        tuple: (sex, age) where sex is 'M' or 'F' and age is int
    """
    parts = demo_str.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Invalid format. Expected 'Sex Age-Range' but got: '{demo_str}'")

    sex_str, age_range = parts

    # Parse sex
    sex_str = sex_str.lower()
    if sex_str in ['male', 'm']:
        sex = 'M'
    elif sex_str in ['female', 'f']:
        sex = 'F'
    else:
        raise ValueError(f"Invalid sex: {sex_str}. Expected 'Male', 'Female', 'M', or 'F'")

    # Parse age range - take the lower bound
    if '-' not in age_range:
        raise ValueError(f"Invalid age range: {age_range}. Expected format like '55-59'")

    try:
        age_start, _ = age_range.split('-')
        age = int(age_start)
    except ValueError:
        raise ValueError(f"Invalid age range: {age_range}. Expected format like '55-59'")

    return sex, age

def calculate_demographic_score(demo_str, model_name="CMS-HCC Model V22", dual_elgbl_cd="02", orec="0", crec="0"):
    """
    Calculate the demographic component of the V22 risk score.

    Args:
        demo_str: String like "Male 55-59" or "Female 75-79"
        model_name: HCC model name (default: V22)
        dual_elgbl_cd: Dual eligibility code (default: "02")
        orec: Original enrollment code (default: "0")
        crec: Current enrollment code (default: "0")

    Returns:
        dict: Contains demographic score and breakdown
    """

    # Parse the demographic string
    sex, age = parse_demographic_string(demo_str)

    print(f"Parsed demographics: Sex={sex}, Age={age}")

    # Determine version based on model
    version = 'V2'
    if 'RxHCC' in model_name:
        version = 'V4'
    elif 'HHS-HCC' in model_name:
        version = 'V6'

    # Create demographics object
    demographics = categorize_demographics(
        age=age,
        sex=sex,
        dual_elgbl_cd=dual_elgbl_cd,
        orec=orec,
        crec=crec,
        version=version,
        new_enrollee=False,
        snp=False,
        low_income=False,
        graft_months=0
    )

    print(f"Demographics category: {demographics.category}")
    print(f"Disabled: {demographics.disabled}")
    print(f"Non-aged: {demographics.non_aged}")

    # Get coefficient prefix
    prefix = get_coefficent_prefix(demographics, model_name)  # type: ignore
    print(f"Coefficient prefix: {prefix}")

    # Apply coefficients with empty HCC set to get just demographic score
    coefficients = apply_coefficients(
        demographics=demographics,
        hcc_set=set(),  # Empty HCC set
        interactions={},  # No interactions
        model_name=model_name  # type: ignore
    )

    # Extract demographic coefficient
    demographic_score = 0.0
    demographic_coeff_key = None

    for key, value in coefficients.items():
        if key == demographics.category:
            demographic_score = value
            demographic_coeff_key = key
            break

    return {
        'demographic_score': demographic_score,
        'demographic_category': demographics.category,
        'coefficient_key': demographic_coeff_key,
        'coefficient_prefix': prefix,
        'sex': sex,
        'age': age,
        'disabled': demographics.disabled,
        'non_aged': demographics.non_aged,
        'model': model_name,
        'dual_elgbl_cd': dual_elgbl_cd
    }

def main():
    parser = argparse.ArgumentParser(
        description='Calculate demographic component of V22 risk score',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python demographic_calculator.py "Male 55-59"
  python demographic_calculator.py "Female 75-79"
  python demographic_calculator.py "Male 65-69" --dual 03
  python demographic_calculator.py "Female 85-89" --dual 02
        '''
    )

    parser.add_argument(
        'demographics',
        help='Sex and age range (e.g., "Male 55-59", "Female 75-79")'
    )

    parser.add_argument(
        '--model',
        default='CMS-HCC Model V22',
        help='HCC model name (default: CMS-HCC Model V22)'
    )

    parser.add_argument(
        '--dual',
        dest='dual_elgbl_cd',
        default='02',
        choices=['NA', '00', '01', '02', '03', '04', '05', '06', '08', '09'],
        help='Dual eligibility code (default: 02 for full benefit dual)'
    )

    parser.add_argument(
        '--orec',
        default='0',
        help='Original enrollment code (default: 0)'
    )

    parser.add_argument(
        '--crec',
        default='0',
        help='Current enrollment code (default: 0)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed breakdown'
    )

    args = parser.parse_args()

    try:
        result = calculate_demographic_score(
            args.demographics,
            args.model,
            args.dual_elgbl_cd,
            args.orec,
            args.crec
        )

        print(f"\n{'='*50}")
        print(f"DEMOGRAPHIC SCORE CALCULATION RESULTS")
        print(f"{'='*50}")

        print(f"Model: {result['model']}")
        print(f"Input: {args.demographics}")
        print(f"Sex: {result['sex']}, Age: {result['age']}")
        print(f"Category: {result['demographic_category']}")
        print(f"Coefficient Prefix: {result['coefficient_prefix']}")
        print(f"Dual Eligibility: {result['dual_elgbl_cd']}")

        if result['disabled']:
            print(f"Status: Disabled")
        elif result['non_aged']:
            print(f"Status: Non-aged")
        else:
            print(f"Status: Aged")

        print(f"\n🎯 DEMOGRAPHIC SCORE: {result['demographic_score']:.3f}")

        if args.verbose:
            print(f"\nDetailed Breakdown:")
            print(f"  Coefficient Key: {result['coefficient_key']}")
            print(f"  Coefficient Value: {result['demographic_score']:.3f}")

        # Output just the score for easy parsing by other scripts
        print(f"\nDEMOGRAPHIC_SCORE={result['demographic_score']:.3f}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()