#!/usr/bin/env python3
"""
Risk Score Validation Script

This script validates HCC risk scores by comparing CMS scores with calculated
demographic and HCC components for each patient.

Usage:
    uv run python scripts/validate_risk_scores.py
"""

import sys
import re
import csv
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def parse_patient_data(file_path: str) -> List[Dict]:
    """
    Parse the patient data file to extract MBI, demographics, and HCC codes.

    Returns:
        List of patient dictionaries with keys: mbi, sex_age_group, hcc_codes
    """
    patients = []
    current_patient = None

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip()

        # Skip empty lines and headers
        if not line or line.startswith('1RUN DATE') or line.startswith(' PAYMENT MONTH') or 'MBI' in line and 'NAME' in line:
            continue

        # Check if this is a patient line (starts with space then MBI)
        # MBI format: space followed by 11-12 characters
        mbi_match = re.match(r'^\s([A-Z0-9]{11,12})\s+', line)
        if mbi_match:
            # Save previous patient if exists
            if current_patient:
                patients.append(current_patient)

            mbi = mbi_match.group(1)

            # Extract sex and age group from the line
            # Pattern: date (YYYYMMDD) followed by sex and age group
            demo_match = re.search(r'\d{8}\s+(Male|Female)\s+(\d+-\d+)', line)
            if demo_match:
                sex = demo_match.group(1)
                age_group = demo_match.group(2)
                sex_age_group = f"{sex} {age_group}"
            else:
                sex_age_group = None

            current_patient = {
                'mbi': mbi,
                'sex_age_group': sex_age_group,
                'hcc_codes': []
            }
            continue

        # Check for HCC codes in disease group lines (not interaction lines)
        if current_patient and 'HCC' in line and 'V22 HCC DISEASE GRP K:' in line:
            # Extract HCC numbers from lines like "HCC108 Vascular Disease"
            hcc_matches = re.findall(r'HCC(\d+)', line)
            current_patient['hcc_codes'].extend(hcc_matches)
        elif current_patient and 'HCC' in line and line.strip().startswith('HCC'):
            # Handle continuation lines with just HCC codes
            hcc_matches = re.findall(r'HCC(\d+)', line)
            current_patient['hcc_codes'].extend(hcc_matches)

    # Add the last patient
    if current_patient:
        # Remove duplicate HCC codes while preserving order
        current_patient['hcc_codes'] = list(dict.fromkeys(current_patient['hcc_codes']))
        patients.append(current_patient)

    # Remove duplicates from all patients
    for patient in patients:
        patient['hcc_codes'] = list(dict.fromkeys(patient['hcc_codes']))

    return patients

def load_cms_risk_scores(csv_path: str) -> Dict[str, float]:
    """
    Load CMS risk scores from CSV file.

    Returns:
        Dictionary mapping medicare_id -> risk_score
    """
    cms_scores = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:  # Handle BOM
        reader = csv.DictReader(f)
        for row in reader:
            medicare_id = row['medicare_id']
            risk_score_str = row['Part_AB_H1_2025_Risk_Score']

            # Skip null or empty entries
            if medicare_id and medicare_id != 'null' and risk_score_str and risk_score_str != '':
                try:
                    risk_score = float(risk_score_str)
                    cms_scores[medicare_id] = risk_score
                except ValueError:
                    continue

    return cms_scores

def calculate_demographic_score(sex_age_group: str) -> Optional[float]:
    """
    Calculate demographic score using the demographic_calculator.py script.
    """
    if not sex_age_group:
        return None

    try:
        # Run the demographic calculator
        result = subprocess.run([
            'uv', 'run', 'python', 'scripts/demographic_calculator.py',
            sex_age_group
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        if result.returncode != 0:
            print(f"Error calculating demographic score for {sex_age_group}: {result.stderr}")
            return None

        # Extract the score from output
        for line in result.stdout.split('\n'):
            if line.startswith('DEMOGRAPHIC_SCORE='):
                return float(line.split('=')[1])

        return None

    except Exception as e:
        print(f"Error calculating demographic score for {sex_age_group}: {e}")
        return None

def calculate_hcc_score(hcc_codes: List[str]) -> Optional[float]:
    """
    Calculate HCC component score using the hcc_calculator.py script.
    """
    if not hcc_codes:
        return 0.0  # No HCCs = 0 HCC component

    try:
        # Join HCC codes with commas
        hcc_string = ','.join(hcc_codes)

        # Run the HCC calculator
        result = subprocess.run([
            'uv', 'run', 'python', 'scripts/hcc_calculator.py',
            hcc_string
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        if result.returncode != 0:
            print(f"Error calculating HCC score for {hcc_string}: {result.stderr}")
            return None

        # Extract the score from output
        for line in result.stdout.split('\n'):
            if line.startswith('HCC_COMPONENT='):
                return float(line.split('=')[1])

        return None

    except Exception as e:
        print(f"Error calculating HCC score for {hcc_codes}: {e}")
        return None

def main():
    # File paths
    patient_data_path = "/Users/wulsin/code/hccinfhir/P.RH4538.HCCMODR.D250401.T0854070 (1).14764350.txt"
    cms_csv_path = "/Users/wulsin/code/hccinfhir/contour-export-New-Analysis---2025-09-24-17-41-07-2025-Payment-Estimate-09-24-2025.csv"
    output_csv_path = "/Users/wulsin/code/hccinfhir/risk_score_validation.csv"

    print("Starting risk score validation...")

    # Step 1: Parse patient data
    print("1. Parsing patient data...")
    patients = parse_patient_data(patient_data_path)
    print(f"   Found {len(patients)} patients")

    # Step 2: Load CMS risk scores
    print("2. Loading CMS risk scores...")
    cms_scores = load_cms_risk_scores(cms_csv_path)
    print(f"   Found {len(cms_scores)} CMS risk scores")

    # Step 3: Calculate scores for each patient
    print("3. Calculating risk scores...")
    validation_results = []

    for i, patient in enumerate(patients, 1):
        print(f"   Processing patient {i}/{len(patients)}: {patient['mbi']}")

        mbi = patient['mbi']
        sex_age_group = patient['sex_age_group']
        hcc_codes = patient['hcc_codes']

        # Get CMS risk score
        cms_risk_score = cms_scores.get(mbi)

        # Calculate demographic score
        demographic_score = calculate_demographic_score(sex_age_group)

        # Calculate HCC score
        hcc_score = calculate_hcc_score(hcc_codes)

        # Calculate total (demographic + HCC)
        total_calculated = None
        if demographic_score is not None and hcc_score is not None:
            total_calculated = demographic_score + hcc_score

        # Calculate difference
        difference = None
        if cms_risk_score is not None and total_calculated is not None:
            difference = cms_risk_score - total_calculated

        validation_results.append({
            'medicare_id': mbi,
            'cms_risk_score': cms_risk_score,
            'demographic_risk_score': demographic_score,
            'hcc_risk_score': hcc_score,
            'total_calculated_score': total_calculated,
            'difference': difference,
            'sex_age_group': sex_age_group,
            'hcc_codes': ','.join(hcc_codes) if hcc_codes else ''
        })

    # Step 4: Save results to CSV
    print("4. Saving validation results...")
    with open(output_csv_path, 'w', newline='') as f:
        fieldnames = [
            'medicare_id', 'cms_risk_score', 'demographic_risk_score',
            'hcc_risk_score', 'total_calculated_score', 'difference',
            'sex_age_group', 'hcc_codes'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validation_results)

    print(f"✅ Validation complete! Results saved to: {output_csv_path}")

    # Print summary statistics
    print("\nSummary:")
    total_patients = len(validation_results)
    patients_with_cms_scores = sum(1 for r in validation_results if r['cms_risk_score'] is not None)
    patients_with_calculated_scores = sum(1 for r in validation_results if r['total_calculated_score'] is not None)
    patients_with_both = sum(1 for r in validation_results if r['cms_risk_score'] is not None and r['total_calculated_score'] is not None)

    print(f"  Total patients: {total_patients}")
    print(f"  Patients with CMS scores: {patients_with_cms_scores}")
    print(f"  Patients with calculated scores: {patients_with_calculated_scores}")
    print(f"  Patients with both scores: {patients_with_both}")

    if patients_with_both > 0:
        differences = [r['difference'] for r in validation_results if r['difference'] is not None]
        avg_difference = sum(differences) / len(differences)
        print(f"  Average difference (CMS - Calculated): {avg_difference:.3f}")

if __name__ == "__main__":
    main()