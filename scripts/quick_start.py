from __future__ import annotations

from typing import List

from hccinfhir import HCCInFHIR, Demographics


def main() -> None:
    # Initialize processor with defaults matching the README Quick Start
    processor = HCCInFHIR(model_name="CMS-HCC Model V28")

    # Minimal demographics for a beneficiary
    demographics = Demographics(age=67, sex="F")

    # Example diagnosis codes (ICD-10-CM)
    diagnosis_codes: List[str] = ["E11.9", "I10", "N18.3"]

    # Calculate RAF from diagnosis list
    result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)

    # Display results
    print("=== HCCInFHIR Quick Start ===")
    print(f"Input demographics: age={demographics.age}, sex={demographics.sex}")
    print(f"Diagnosis codes: {diagnosis_codes}")
    print(f"Risk Score: {result.risk_score}")
    print(f"HCCs: {sorted(result.hcc_list)}")


if __name__ == "__main__":
    main()

