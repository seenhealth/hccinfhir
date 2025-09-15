from __future__ import annotations

from typing import List, get_args

from hccinfhir import HCCInFHIR, Demographics, ModelName


def main() -> None:
    # Initialize processor with defaults matching the README Quick Start


    # Minimal demographics for a beneficiary
    demographics = Demographics(age=67, sex="F")

    # Example diagnosis codes (ICD-10-CM)
    diagnosis_codes: List[str] = ["E11.9", "I10", "N18.3"]

    # Calculate RAF from diagnosis list

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


if __name__ == "__main__":
    main()

