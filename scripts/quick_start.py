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
import json
import subprocess
from typing import Dict, List, get_args

from hccinfhir import HCCInFHIR, Demographics, ModelName

try:
    from google.cloud import bigquery
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False


def write_to_bigquery(results_data: List[Dict], verbose: bool = False) -> None:
    """Write risk scores to BigQuery table sgv_reporting.risk_scores."""
    if not BIGQUERY_AVAILABLE:
        print("Error: google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery")
        return

    if not results_data:
        print("No results to write to BigQuery")
        return

    if verbose:
        print(f"DEBUG: Preparing {len(results_data)} records for BigQuery")

    rows = []
    for result in results_data:
        v22_data = result.get("v22_result", {})
        v28_data = result.get("v28_result", {})

        # Helper function to convert set to list for JSON serialization
        def serialize_cc_to_dx(cc_to_dx):
            if not cc_to_dx:
                return {}
            return {k: list(v) for k, v in cc_to_dx.items()}

        # Get demographics from either model (they should be the same)
        demographics = v22_data.get("demographics", {}) or v28_data.get("demographics", {})

        row = {
            # Identifiers
            "mrn": str(result["mrn"]),

            # V22 Model Results
            "v22_risk_score": float(v22_data.get("risk_score", 0.0)),
            "v22_risk_score_demographics": float(v22_data.get("risk_score_demographics", 0.0)),
            "v22_risk_score_chronic_only": float(v22_data.get("risk_score_chronic_only", 0.0)),
            "v22_risk_score_hcc": float(v22_data.get("risk_score_hcc", 0.0)),
            "v22_hcc_list": [str(hcc) for hcc in v22_data.get("hcc_list", [])],
            "v22_diagnosis_codes": v22_data.get("diagnosis_codes", []),
            "v22_coefficients": v22_data.get("coefficients", {}),
            "v22_interactions": v22_data.get("interactions", {}),
            "v22_cc_to_dx": serialize_cc_to_dx(v22_data.get("cc_to_dx", {})),
            "v22_model_name": v22_data.get("model_name", ""),

            # V28 Model Results
            "v28_risk_score": float(v28_data.get("risk_score", 0.0)),
            "v28_risk_score_demographics": float(v28_data.get("risk_score_demographics", 0.0)),
            "v28_risk_score_chronic_only": float(v28_data.get("risk_score_chronic_only", 0.0)),
            "v28_risk_score_hcc": float(v28_data.get("risk_score_hcc", 0.0)),
            "v28_hcc_list": [str(hcc) for hcc in v28_data.get("hcc_list", [])],
            "v28_diagnosis_codes": v28_data.get("diagnosis_codes", []),
            "v28_coefficients": v28_data.get("coefficients", {}),
            "v28_interactions": v28_data.get("interactions", {}),
            "v28_cc_to_dx": serialize_cc_to_dx(v28_data.get("cc_to_dx", {})),
            "v28_model_name": v28_data.get("model_name", ""),

            # Demographics (shared across models)
            "age": int(demographics.get("age", 0)),
            "sex": str(demographics.get("sex", "")),
            "dual_elgbl_cd": str(demographics.get("dual_elgbl_cd", "")),
            "orec": str(demographics.get("orec", "")),
            "crec": str(demographics.get("crec", "")),
            "new_enrollee": bool(demographics.get("new_enrollee", False)),
            "snp": bool(demographics.get("snp", False)),
            "demographic_version": str(demographics.get("version", "")),
            "low_income": bool(demographics.get("low_income", False)),
            "graft_months": demographics.get("graft_months"),
            "category": str(demographics.get("category", "")),
            "non_aged": bool(demographics.get("non_aged", False)),
            "orig_disabled": bool(demographics.get("orig_disabled", False)),
            "disabled": bool(demographics.get("disabled", False)),
            "esrd": bool(demographics.get("esrd", False)),
            "lti": bool(demographics.get("lti", False)),
            "fbd": bool(demographics.get("fbd", False)),
            "pbd": bool(demographics.get("pbd", False)),
        }

        rows.append(row)

    if verbose:
        print("DEBUG: Sample row for BigQuery:")
        print(f"  {rows[0] if rows else 'No rows'}")

    try:
        client = bigquery.Client()
        table_id = "sgv_reporting.risk_scores"

        schema = [
            # Identifiers
            bigquery.SchemaField("mrn", "STRING"),

            # V22 Model Results
            bigquery.SchemaField("v22_risk_score", "FLOAT"),
            bigquery.SchemaField("v22_risk_score_demographics", "FLOAT"),
            bigquery.SchemaField("v22_risk_score_chronic_only", "FLOAT"),
            bigquery.SchemaField("v22_risk_score_hcc", "FLOAT"),
            bigquery.SchemaField("v22_hcc_list", "STRING", mode="REPEATED"),
            bigquery.SchemaField("v22_diagnosis_codes", "STRING", mode="REPEATED"),
            bigquery.SchemaField("v22_coefficients", "JSON"),
            bigquery.SchemaField("v22_interactions", "JSON"),
            bigquery.SchemaField("v22_cc_to_dx", "JSON"),
            bigquery.SchemaField("v22_model_name", "STRING"),

            # V28 Model Results
            bigquery.SchemaField("v28_risk_score", "FLOAT"),
            bigquery.SchemaField("v28_risk_score_demographics", "FLOAT"),
            bigquery.SchemaField("v28_risk_score_chronic_only", "FLOAT"),
            bigquery.SchemaField("v28_risk_score_hcc", "FLOAT"),
            bigquery.SchemaField("v28_hcc_list", "STRING", mode="REPEATED"),
            bigquery.SchemaField("v28_diagnosis_codes", "STRING", mode="REPEATED"),
            bigquery.SchemaField("v28_coefficients", "JSON"),
            bigquery.SchemaField("v28_interactions", "JSON"),
            bigquery.SchemaField("v28_cc_to_dx", "JSON"),
            bigquery.SchemaField("v28_model_name", "STRING"),

            # Demographics (shared across models)
            bigquery.SchemaField("age", "INTEGER"),
            bigquery.SchemaField("sex", "STRING"),
            bigquery.SchemaField("dual_elgbl_cd", "STRING"),
            bigquery.SchemaField("orec", "STRING"),
            bigquery.SchemaField("crec", "STRING"),
            bigquery.SchemaField("new_enrollee", "BOOLEAN"),
            bigquery.SchemaField("snp", "BOOLEAN"),
            bigquery.SchemaField("demographic_version", "STRING"),
            bigquery.SchemaField("low_income", "BOOLEAN"),
            bigquery.SchemaField("graft_months", "INTEGER"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("non_aged", "BOOLEAN"),
            bigquery.SchemaField("orig_disabled", "BOOLEAN"),
            bigquery.SchemaField("disabled", "BOOLEAN"),
            bigquery.SchemaField("esrd", "BOOLEAN"),
            bigquery.SchemaField("lti", "BOOLEAN"),
            bigquery.SchemaField("fbd", "BOOLEAN"),
            bigquery.SchemaField("pbd", "BOOLEAN"),
        ]

        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=schema
        )

        if verbose:
            print(f"DEBUG: Writing to BigQuery table: {table_id}")

        job = client.load_table_from_json(rows, table_id, job_config=job_config)
        job.result()

        dest = client.get_table(table_id)
        print(f"Successfully wrote {dest.num_rows} rows to {table_id}")

    except Exception as e:
        print(f"Error writing to BigQuery: {e}")


def load_demographics(verbose: bool = False) -> Dict[str, Demographics]:
    """Load demographics from BigQuery table sgv_reporting.participants."""
    demographics_dict = {}

    query = "SELECT mrn, gender, age, coverage_type FROM sgv_reporting.participants"
    cmd = ['bq', 'query', '--use_legacy_sql=false', query]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        lines = result.stdout.strip().split('\n')

        # Skip header and separator lines
        # BigQuery output format is typically:
        # +-----+--------+-----+---------------+
        # | mrn | gender | age | coverage_type |
        # +-----+--------+-----+---------------+
        # | ... | ...    | ... | ...           |
        # +-----+--------+-----+---------------+

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

            # Parse data rows (format: | mrn | gender | age | coverage_type |)
            if line.startswith('|') and line.endswith('|'):
                parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first/last elements
                if len(parts) == 4:
                    mrn, gender, age, coverage_type = parts
                    if verbose:
                        print(f"DEBUG: Parsing row for MRN {mrn} sex={gender} age={age} coverage_type={coverage_type}")
                    try:
                        age_int = int(age)
                        # Convert gender to HCC format
                        sex = 'M' if gender.lower() == 'male' else 'F'
                        # Set dual eligibility code based on coverage type
                        dual_elgbl_cd = '02' if coverage_type == 'DUAL' else '00'
                        demographics_dict[mrn] = Demographics(age=age_int, sex=sex, dual_elgbl_cd=dual_elgbl_cd)  # type: ignore
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
                sex = 'M' if row['gender'].lower() == 'male' else 'F'
                # For CSV fallback, default to non-dual eligible unless coverage_type column exists
                coverage_type = row.get('coverage_type', '')
                dual_elgbl_cd = '02' if coverage_type == 'DUAL' else '00'
                demographics_dict[mrn] = Demographics(age=age, sex=sex, dual_elgbl_cd=dual_elgbl_cd)  # type: ignore
        print(f"Loaded {len(demographics_dict)} demographics records from CSV")
    except FileNotFoundError:
        print("Error: demographics.csv not found")
    except Exception as e:
        print(f"Error loading CSV: {e}")

    return demographics_dict


def load_icd10_codes(verbose: bool = False) -> Dict[str, List[str]]:
    """Load ICD-10 codes from BigQuery table sgv_reporting.participant_diagnosis_codes."""
    codes_dict = {}

    query = "SELECT mrn, icd10_codes FROM sgv_reporting.participant_diagnosis_codes"
    cmd = ['bq', 'query', '--use_legacy_sql=false', query]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        lines = result.stdout.strip().split('\n')

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
    demographics = Demographics(age=67, sex="F")  # type: ignore

    diagnosis_codes: List[str] = ["E11.9", "I10", "N18.3"]

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

    demographics_dict = load_demographics(verbose)
    codes_dict = load_icd10_codes(verbose)

    all_mrns = set(demographics_dict.keys()) & set(codes_dict.keys())

    if not all_mrns:
        print("No MRNs found with both demographics and ICD-10 codes")
        return

    if verbose:
        print(f"DEBUG: Demographics loaded for {len(demographics_dict)} MRNs")
        print(f"DEBUG: ICD-10 codes loaded for {len(codes_dict)} MRNs")
        print(f"DEBUG: MRNs with both demographics and codes: {len(all_mrns)}")

        sample_mrns = list(all_mrns)[:3]
        print(f"DEBUG: Sample diagnosis codes:")
        for mrn in sample_mrns:
            codes = codes_dict.get(mrn, [])
            print(f"  MRN {mrn}: {len(codes)} codes = {codes[:5]}{'...' if len(codes) > 5 else ''} coverage_type={demographics_dict[mrn].dual_elgbl_cd}")
        print()

    print(f"Processing {len(all_mrns)} MRNs...\n")

    bq_results = []

    processed_count = 0
    for mrn in sorted(all_mrns):
        demographics = demographics_dict[mrn]
        diagnosis_codes = codes_dict[mrn]

        if not diagnosis_codes:
            print(f"{mrn}: No diagnosis codes found")
            continue

        if verbose and processed_count < 2:
            print(f"DEBUG: Processing MRN {mrn}")
            print(f"  Demographics: age={demographics.age}, sex={demographics.sex}")
            print(f"  Diagnosis codes ({len(diagnosis_codes)}): {diagnosis_codes}")

        results = []
        v22_result, v28_result = None, None

        for model_name in get_args(ModelName):
            processor = HCCInFHIR(model_name=model_name)
            result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)

            if verbose and processed_count == 0 and model_name == get_args(ModelName)[0]:
                print(f"  First model result: risk_score={result.risk_score}, hccs={result.hcc_list}")
                print(f"  CC to DX mapping: {dict(result.cc_to_dx)}")
                print()

            # Capture full model dumps for V22 and V28
            if "V22" in model_name:
                v22_result = result.model_dump()
            elif "V28" in model_name:
                v28_result = result.model_dump()

            # Create abbreviated model name (e.g., "CMS-HCC Model V28" -> "V28")
            # short_name = model_name.split()[-1]  # Get last part (V28, V24, etc.)
            short_name = model_name
            results.append(f"{short_name}={result.risk_score:.3f} (HCCs: {sorted(result.hcc_list)})")

        print(f"{mrn}: {', '.join(results)}")

        bq_results.append({
            "mrn": mrn,
            "v22_result": v22_result,
            "v28_result": v28_result
        })

        processed_count += 1

    if bq_results:
        print(f"\nWriting {len(bq_results)} results to BigQuery...")
        write_to_bigquery(bq_results, verbose)


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
