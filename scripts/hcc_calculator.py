#!/usr/bin/env python3
"""
Standalone HCC V22 Risk Score Calculator

Usage:
    python hcc_calculator.py "18,58,161"
    python hcc_calculator.py "9,40,108,169,170"

This script calculates only the HCC component of the V22 risk score
(excludes demographics) from a comma-delimited string of HCC codes.
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to the path so we can import hccinfhir modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from hccinfhir.model_hierarchies import apply_hierarchies
    from hccinfhir.model_interactions import apply_interactions
    from hccinfhir.model_coefficients import apply_coefficients
    from hccinfhir.datamodels import Demographics, ModelName
except ImportError as e:
    print(f"Error importing hccinfhir modules: {e}")
    print("\nTo fix this, run the script using one of these methods:")
    print("1. uv run python hcc_calculator.py \"18,58\"")
    print("2. uv pip install -e . && python hcc_calculator.py \"18,58\"")
    print("3. Make sure you're in the hccinfhir directory and have uv installed")
    sys.exit(1)

def calculate_hcc_component(hcc_codes_str, model_name="CMS-HCC Model V22", demographics_prefix="CNA"):
    """
    Calculate the HCC component of the V22 risk score.

    Args:
        hcc_codes_str: Comma-delimited string of HCC codes (e.g., "18,58,161")
        model_name: HCC model name (default: V22)
        demographics_prefix: Coefficient prefix to use (default: CNA for community non-dual aged)

    Returns:
        dict: Contains HCC component score and breakdown
    """

    # Parse HCC codes from string
    if not hcc_codes_str.strip():
        return {
            'hcc_component': 0.0,
            'hcc_codes_final': [],
            'hcc_codes_input': [],
            'hcc_coefficients': {},
            'interaction_coefficients': {},
            'active_interactions': {},
            'removed_by_hierarchy': [],
            'model': model_name,
            'prefix': demographics_prefix
        }

    hcc_codes = [code.strip() for code in hcc_codes_str.split(',') if code.strip()]
    hcc_set = set(hcc_codes)

    print(f"Input HCC codes: {sorted(hcc_codes)}")

    # Apply hierarchies
    hcc_set_after_hierarchies = apply_hierarchies(hcc_set, model_name)  # type: ignore
    removed_by_hierarchy = hcc_set - hcc_set_after_hierarchies

    if removed_by_hierarchy:
        print(f"HCCs removed by hierarchies: {sorted(removed_by_hierarchy)}")
        print(f"Final HCC codes: {sorted(hcc_set_after_hierarchies)}")
    else:
        print(f"No hierarchies applied - all HCCs remain: {sorted(hcc_set_after_hierarchies)}")

    # Create minimal demographics object for coefficient calculation
    # This is just used to get the right prefix - we'll zero out the demographic score
    dummy_demographics = Demographics(
        category="F65_69",  # This will be ignored since we're using custom prefix
        disabled=False,
        non_aged=False,
        fbd=demographics_prefix.startswith('CF'),
        pbd=demographics_prefix.startswith('CP'),
        lti=demographics_prefix.startswith('INS'),
        new_enrollee=demographics_prefix.startswith('NE'),
        age=65,
        sex='F',  # Required field
        orig_disabled=False,
        esrd=False,
        graft_months=None,
        dual_elgbl_cd='NA',
        orec='',
        crec='',
        snp=False,
        version='V2',
        low_income=False
    )

    # Calculate interactions
    interactions = apply_interactions(dummy_demographics, hcc_set_after_hierarchies, model_name)  # type: ignore

    # Apply coefficients with calculated interactions
    coefficients = apply_coefficients(
        demographics=dummy_demographics,
        hcc_set=hcc_set_after_hierarchies,
        interactions=interactions,
        model_name=model_name  # type: ignore
    )

    # Extract HCC and interaction coefficients (exclude demographic coefficient)
    hcc_coefficients = {}
    interaction_coefficients = {}
    hcc_component = 0.0

    # Get active interactions (value > 0)
    active_interactions = {k: v for k, v in interactions.items() if v > 0}

    # Extract HCC coefficients
    for hcc in hcc_set_after_hierarchies:
        if hcc in coefficients:
            coeff_value = coefficients[hcc]
            hcc_coefficients[hcc] = coeff_value
            hcc_component += coeff_value

    # Extract interaction coefficients
    for interaction_name in active_interactions:
        if interaction_name in coefficients:
            coeff_value = coefficients[interaction_name]
            interaction_coefficients[interaction_name] = coeff_value
            hcc_component += coeff_value

    return {
        'hcc_component': hcc_component,
        'hcc_codes_final': sorted(hcc_set_after_hierarchies),
        'hcc_codes_input': sorted(hcc_codes),
        'hcc_coefficients': hcc_coefficients,
        'interaction_coefficients': interaction_coefficients,
        'active_interactions': active_interactions,
        'removed_by_hierarchy': sorted(removed_by_hierarchy),
        'model': model_name,
        'prefix': demographics_prefix
    }

def main():
    parser = argparse.ArgumentParser(
        description='Calculate HCC component of V22 risk score',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python hcc_calculator.py "18,58,161"
  python hcc_calculator.py "9,40,108,169,170"
  python hcc_calculator.py "108,112" --prefix CFD
  python hcc_calculator.py "" --help
        '''
    )

    parser.add_argument(
        'hcc_codes',
        help='Comma-delimited string of HCC codes (e.g., "18,58,161")'
    )

    parser.add_argument(
        '--model',
        default='CMS-HCC Model V22',
        help='HCC model name (default: CMS-HCC Model V22)'
    )

    parser.add_argument(
        '--prefix',
        default='CNA',
        choices=['CNA', 'CND', 'CFA', 'CFD', 'CPA', 'CPD', 'INS'],
        help='Demographics coefficient prefix (default: CNA for Community Non-dual Aged)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed breakdown of each HCC coefficient'
    )

    args = parser.parse_args()

    try:
        result = calculate_hcc_component(args.hcc_codes, args.model, args.prefix + "_")

        print(f"\n{'='*50}")
        print(f"HCC COMPONENT CALCULATION RESULTS")
        print(f"{'='*50}")

        print(f"Model: {result['model']}")
        print(f"Coefficient Prefix: {result['prefix']}")
        print(f"Input HCCs: {result['hcc_codes_input']}")

        if result['removed_by_hierarchy']:
            print(f"Removed by hierarchies: {result['removed_by_hierarchy']}")

        print(f"Final HCCs: {result['hcc_codes_final']}")

        # Show active interactions if any
        if result['active_interactions']:
            active_list = [f"{k}={v}" for k, v in result['active_interactions'].items()]
            print(f"Active Interactions: {active_list}")
        else:
            print(f"Active Interactions: None")

        print(f"\n🎯 HCC COMPONENT: {result['hcc_component']:.3f}")

        if args.verbose and (result['hcc_coefficients'] or result['interaction_coefficients']):
            print(f"\nDetailed HCC Breakdown:")

            # Show individual HCC coefficients
            hcc_total = 0.0
            for hcc in sorted(result['hcc_codes_final']):
                if hcc in result['hcc_coefficients']:
                    coeff = result['hcc_coefficients'][hcc]
                    hcc_total += coeff
                    print(f"  HCC {hcc:>3}: {coeff:.3f}")

            # Show interaction coefficients if any
            interaction_total = 0.0
            if result['interaction_coefficients']:
                print(f"  Interactions:")
                for interaction, coeff in result['interaction_coefficients'].items():
                    interaction_total += coeff
                    print(f"    {interaction}: {coeff:.3f}")

            print(f"  {'='*20}")
            print(f"  HCCs: {hcc_total:.3f}")
            if interaction_total > 0:
                print(f"  Interactions: {interaction_total:.3f}")
            print(f"  Total: {result['hcc_component']:.3f}")

        # Output just the score for easy parsing by other scripts
        print(f"\nHCC_COMPONENT={result['hcc_component']:.3f}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()