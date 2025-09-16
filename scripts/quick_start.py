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
import subprocess
from typing import Dict, List, get_args

from hccinfhir import HCCInFHIR, Demographics, ModelName


def load_demographics() -> Dict[str, Demographics]:
    """Load demographics from BigQuery table sgv_reporting.participants."""
    demographics_dict = {}

    # Execute BigQuery query
    query = "SELECT mrn, gender, age FROM sgv_reporting.participants"
    cmd = ['bq', 'query', '--use_legacy_sql=false', query]

    try:
        # Run BigQuery command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the BigQuery output
        lines = result.stdout.strip().split('\n')

        # Skip header and separator lines
        # BigQuery output format is typically:
        # +-----+--------+-----+
        # | mrn | gender | age |
        # +-----+--------+-----+
        # | ... | ...    | ... |
        # +-----+--------+-----+

        data_started = False
        for line in lines:
            line = line.strip()
            # Skip empty lines, separator lines (starting with +), and header
            if not line or line.startswith('+') or 'mrn' in line.lower() and 'gender' in line.lower():
                if 'mrn' in line.lower() and 'gender' in line.lower():
                    data_started = True
                continue

            if not data_started:
                continue

            # Parse data rows (format: | mrn | gender | age |)
            if line.startswith('|') and line.endswith('|'):
                parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first/last elements
                if len(parts) == 3:
                    mrn, gender, age = parts
                    try:
                        age_int = int(age)
                        # Convert gender to HCC format
                        sex = 'M' if gender.lower() == 'male' else 'F'
                        demographics_dict[mrn] = Demographics(age=age_int, sex=sex)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Could not parse demographics for MRN {mrn}: {e}")
                        continue

        print(f"Loaded {len(demographics_dict)} demographics records from BigQuery")
        return demographics_dict

    except subprocess.CalledProcessError as e:
        print(f"Error executing BigQuery command: {e}")
        print(f"stderr: {e.stderr}")
        print("Falling back to CSV file...")

        # Fallback to CSV file
        return load_demographics_from_csv()

    except Exception as e:
        print(f"Unexpected error loading from BigQuery: {e}")
        print("Falling back to CSV file...")
        return load_demographics_from_csv()


def load_demographics_from_csv() -> Dict[str, Demographics]:
    """Fallback: Load demographics from CSV file into dict keyed by MRN."""
    demographics_dict = {}
    try:
        with open('demographics.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mrn = row['mrn']
                age = int(row['age'])
                # Convert gender to HCC format
                sex = 'M' if row['gender'].lower() == 'male' else 'F'
                demographics_dict[mrn] = Demographics(age=age, sex=sex)
        print(f"Loaded {len(demographics_dict)} demographics records from CSV")
    except FileNotFoundError:
        print("Error: demographics.csv not found")
    except Exception as e:
        print(f"Error loading CSV: {e}")

    return demographics_dict


def load_icd10_codes(verbose: bool = False) -> Dict[str, List[str]]:
    """Load ICD-10 codes from BigQuery table sgv_reporting.participant_diagnosis_codes."""
    codes_dict = {}

    # Execute BigQuery query
    query = "SELECT mrn, icd10_codes FROM sgv_reporting.participant_diagnosis_codes"
    cmd = ['bq', 'query', '--use_legacy_sql=false', query]

    try:
        # Run BigQuery command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the BigQuery output
        lines = result.stdout.strip().split('\n')

        # DEBUG: Show first few lines of BigQuery output
        if verbose:
            print("DEBUG: First 10 lines of BigQuery ICD-10 output:")
            for i, line in enumerate(lines[:10]):
                print(f"  {i}: {repr(line)}")
            print()

        # Skip header and separator lines
        # BigQuery output format is typically:
        # +-----+-------------+
        # | mrn | icd10_codes |
        # +-----+-------------+
        # | ... | ...         |
        # +-----+-------------+

        data_started = False
        for line in lines:
            line = line.strip()
            # Skip empty lines, separator lines (starting with +), and header
            if not line or line.startswith('+') or ('mrn' in line.lower() and 'icd10_codes' in line.lower()):
                if 'mrn' in line.lower() and 'icd10_codes' in line.lower():
                    data_started = True
                continue

            if not data_started:
                continue

            # Parse data rows (format: | mrn | icd10_codes |)
            if line.startswith('|') and line.endswith('|'):
                parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first/last elements
                if len(parts) == 2:
                    mrn, icd10_codes = parts

                    # DEBUG: Show first few parsed rows
                    if verbose and len(codes_dict) < 3:
                        print(f"DEBUG: Parsing row for MRN {mrn}")
                        print(f"  Raw icd10_codes: {repr(icd10_codes)}")

                    try:
                        # Parse the ICD-10 codes - expecting comma-separated values
                        if icd10_codes and icd10_codes != 'NULL':
                            # Handle potential list format [code1, code2, ...] or comma-separated
                            if icd10_codes.startswith('[') and icd10_codes.endswith(']'):
                                icd10_codes = icd10_codes[1:-1]  # Remove brackets

                            codes_list = [code.strip() for code in icd10_codes.split(',')]
                            # Filter out empty strings and remove quotes
                            codes_list = [code.strip('"') for code in codes_list if code]
                            codes_dict[mrn] = codes_list

                            # DEBUG: Show parsed codes for first few MRNs
                            if verbose and len(codes_dict) <= 3:
                                print(f"  Parsed codes ({len(codes_list)}): {codes_list}")
                        else:
                            codes_dict[mrn] = []
                            if verbose and len(codes_dict) <= 3:
                                print(f"  No codes (NULL or empty)")
                    except Exception as e:
                        print(f"Warning: Could not parse ICD-10 codes for MRN {mrn}: {e}")
                        codes_dict[mrn] = []

        print(f"Loaded ICD-10 codes for {len(codes_dict)} patients from BigQuery")
        return codes_dict

    except subprocess.CalledProcessError as e:
        print(f"Error executing BigQuery command: {e}")
        print(f"stderr: {e.stderr}")
        print("Falling back to CSV file...")

        # Fallback to CSV file
        return load_icd10_codes_from_csv()

    except Exception as e:
        print(f"Unexpected error loading ICD-10 codes from BigQuery: {e}")
        print("Falling back to CSV file...")
        return load_icd10_codes_from_csv()


def load_icd10_codes_from_csv() -> Dict[str, List[str]]:
    """Fallback: Load ICD-10 codes from CSV file into dict keyed by MRN."""
    codes_dict = {}
    try:
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
        print(f"Loaded ICD-10 codes for {len(codes_dict)} patients from CSV")
    except FileNotFoundError:
        print("Error: icd10_codes.csv not found")
    except Exception as e:
        print(f"Error loading CSV: {e}")

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


def process_input_data(verbose: bool = False) -> None:
    """Process input data (BigQuery or CSV fallback) and display compact risk scores for each MRN."""
    print("=== Processing Input Data ===")

    # Load data
    demographics_dict = load_demographics()
    codes_dict = load_icd10_codes(verbose)

    # Get all MRNs that have both demographics and ICD codes
    all_mrns = set(demographics_dict.keys()) & set(codes_dict.keys())

    if not all_mrns:
        print("No MRNs found with both demographics and ICD-10 codes")
        return

    # DEBUG: Show diagnostic summary
    if verbose:
        print(f"DEBUG: Demographics loaded for {len(demographics_dict)} MRNs")
        print(f"DEBUG: ICD-10 codes loaded for {len(codes_dict)} MRNs")
        print(f"DEBUG: MRNs with both demographics and codes: {len(all_mrns)}")

        # DEBUG: Show sample of diagnosis codes
        sample_mrns = list(all_mrns)[:3]
        print(f"DEBUG: Sample diagnosis codes:")
        for mrn in sample_mrns:
            codes = codes_dict.get(mrn, [])
            print(f"  MRN {mrn}: {len(codes)} codes = {codes[:5]}{'...' if len(codes) > 5 else ''}")
        print()

    print(f"Processing {len(all_mrns)} MRNs...\n")

    # Process each MRN
    processed_count = 0
    for mrn in sorted(all_mrns):
        demographics = demographics_dict[mrn]
        diagnosis_codes = codes_dict[mrn]

        # Skip if no diagnosis codes
        if not diagnosis_codes:
            print(f"{mrn}: No diagnosis codes found")
            continue

        # DEBUG: Show diagnosis codes being processed for first few MRNs
        if verbose and processed_count < 2:
            print(f"DEBUG: Processing MRN {mrn}")
            print(f"  Demographics: age={demographics.age}, sex={demographics.sex}")
            print(f"  Diagnosis codes ({len(diagnosis_codes)}): {diagnosis_codes}")

        results = []
        for model_name in get_args(ModelName):
            processor = HCCInFHIR(model_name=model_name)
            result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)

            # DEBUG: Show HCC result for first MRN, first model
            if verbose and processed_count == 0 and model_name == get_args(ModelName)[0]:
                print(f"  First model result: risk_score={result.risk_score}, hccs={result.hcc_list}")
                print(f"  CC to DX mapping: {dict(result.cc_to_dx)}")
                print()

            # Create abbreviated model name (e.g., "CMS-HCC Model V28" -> "V28")
            # short_name = model_name.split()[-1]  # Get last part (V28, V24, etc.)
            short_name = model_name
            results.append(f"{short_name}={result.risk_score:.3f} (HCCs: {sorted(result.hcc_list)})")

        # Print compact one-line format
        print(f"{mrn}: {', '.join(results)}")

        processed_count += 1


def main() -> None:
    parser = argparse.ArgumentParser(description='HCCInFHIR Quick Start Script')
    parser.add_argument('-q', '--quick', action='store_true',
                        help='Run quick demo mode with hardcoded data')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show debug information during processing')

    args = parser.parse_args()

    if args.quick:
        run_quick_demo()
    else:
        process_input_data(args.verbose)


if __name__ == "__main__":
    main()

