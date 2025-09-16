#!/usr/bin/env python3
"""
HCCInFHIR Quick Start Script

Run with:
  uv run scripts/quick_start.py          # Process CSV files (demographics.csv, icd10_codes.csv)
  uv run scripts/quick_start.py -q       # Quick demo mode
"""

from __future__ import annotations

import argparse
import ast
import csv
from typing import Dict, List, get_args

from hccinfhir import HCCInFHIR, Demographics, ModelName


def load_demographics() -> Dict[str, Demographics]:
    """Load demographics from CSV file into dict keyed by MRN."""
    demographics_dict = {}
    with open('demographics.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mrn = row['mrn']
            age = int(row['age'])
            # Convert gender to HCC format
            sex = 'M' if row['gender'].lower() == 'male' else 'F'
            demographics_dict[mrn] = Demographics(age=age, sex=sex)
    return demographics_dict


def load_icd10_codes() -> Dict[str, List[str]]:
    """Load ICD-10 codes from CSV file into dict keyed by MRN."""
    codes_dict = {}
    with open('icd10_codes.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential BOM in column name
            mrn_key = next(key for key in row.keys() if 'mrn' in key.lower())
            mrn = row[mrn_key]
            # Parse the string representation of the list
            codes_str = row['icd10_codes_all']
            try:
                # Remove brackets and split by comma, then strip whitespace
                if codes_str.startswith('[') and codes_str.endswith(']'):
                    codes_str = codes_str[1:-1]  # Remove brackets
                    codes_list = [code.strip() for code in codes_str.split(',')]
                    # Filter out empty strings
                    codes_list = [code for code in codes_list if code]
                    codes_dict[mrn] = codes_list
                else:
                    print(f"Warning: Invalid format for ICD-10 codes for MRN {mrn}")
                    codes_dict[mrn] = []
            except Exception as e:
                print(f"Warning: Could not parse ICD-10 codes for MRN {mrn}: {e}")
                codes_dict[mrn] = []
    return codes_dict


def run_quick_demo() -> None:
    """Run the original quick demo with hardcoded data."""
    # Minimal demographics for a beneficiary
    demographics = Demographics(age=67, sex="F")

    # Example diagnosis codes (ICD-10-CM)
    diagnosis_codes: List[str] = ["E11.9", "I10", "N18.3"]

    # Display results
    print("=== HCCInFHIR Quick Start ===")
    print(f"Input demographics: age={demographics.age}, sex={demographics.sex}")
    print(f"Diagnosis codes: {diagnosis_codes}")
    for model_name in get_args(ModelName):
        processor = HCCInFHIR(model_name=model_name)
        result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)
        print(f"Model: {model_name}")
        print(f"Risk Score: {result.risk_score}")
        print(f"HCCs: {sorted(result.hcc_list)}")
        print("")


def process_csv_data() -> None:
    """Process CSV files and display compact risk scores for each MRN."""
    print("=== Processing CSV Data ===")

    # Load data
    demographics_dict = load_demographics()
    codes_dict = load_icd10_codes()

    # Get all MRNs that have both demographics and ICD codes
    all_mrns = set(demographics_dict.keys()) & set(codes_dict.keys())

    if not all_mrns:
        print("No MRNs found with both demographics and ICD-10 codes")
        return

    print(f"Processing {len(all_mrns)} MRNs...\n")

    # Process each MRN
    for mrn in sorted(all_mrns):
        demographics = demographics_dict[mrn]
        diagnosis_codes = codes_dict[mrn]

        # Skip if no diagnosis codes
        if not diagnosis_codes:
            print(f"{mrn}: No diagnosis codes found")
            continue

        results = []
        for model_name in get_args(ModelName):
            processor = HCCInFHIR(model_name=model_name)
            result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)

            # Create abbreviated model name (e.g., "CMS-HCC Model V28" -> "V28")
            # short_name = model_name.split()[-1]  # Get last part (V28, V24, etc.)
            short_name = model_name
            results.append(f"{short_name}={result.risk_score:.3f} (HCCs: {sorted(result.hcc_list)})")

        # Print compact one-line format
        print(f"{mrn}: {', '.join(results)}")


def main() -> None:
    parser = argparse.ArgumentParser(description='HCCInFHIR Quick Start Script')
    parser.add_argument('-q', '--quick', action='store_true',
                        help='Run quick demo mode with hardcoded data')

    args = parser.parse_args()

    if args.quick:
        run_quick_demo()
    else:
        process_csv_data()


if __name__ == "__main__":
    main()

