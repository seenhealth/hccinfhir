#!/usr/bin/env python3
"""
Debug Risk Score Calculation

This script helps debug risk score discrepancies by providing detailed output
for the calculation process with specific HCC codes.
"""

from hccinfhir.model_calculate import calculate_raf_from_hcc
from hccinfhir.datamodels import Demographics
from hccinfhir.model_demographics import categorize_demographics
from hccinfhir.model_hierarchies import apply_hierarchies
from hccinfhir.model_interactions import apply_interactions
from hccinfhir.model_coefficients import apply_coefficients, get_coefficent_prefix

def debug_hcc_calculation(hcc_list, model_name="CMS-HCC Model V22", **demographic_kwargs):
    """
    Debug HCC calculation with detailed output at each step.
    """
    print(f"=== Debugging HCC Calculation ===")
    print(f"Model: {model_name}")
    print(f"Input HCCs: {hcc_list}")
    print(f"Demographics: {demographic_kwargs}")
    print()

    # Step 1: Create demographics
    print("Step 1: Demographics Processing")
    version = 'V2'
    if 'RxHCC' in model_name:
        version = 'V4'
    elif 'HHS-HCC' in model_name:
        version = 'V6'

    demographics = categorize_demographics(
        age=demographic_kwargs.get('age', 65),
        sex=demographic_kwargs.get('sex', 'F'),
        dual_elgbl_cd=demographic_kwargs.get('dual_elgbl_cd', 'NA'),
        orec=demographic_kwargs.get('orec', '0'),
        crec=demographic_kwargs.get('crec', '0'),
        version=version,
        new_enrollee=demographic_kwargs.get('new_enrollee', False),
        snp=demographic_kwargs.get('snp', False),
        low_income=demographic_kwargs.get('low_income', False),
        graft_months=demographic_kwargs.get('graft_months', None)
    )

    print(f"  Demographics category: {demographics.category}")
    print(f"  Disabled: {demographics.disabled}")
    print(f"  Non-aged: {demographics.non_aged}")
    print(f"  FBD: {demographics.fbd}")
    print(f"  PBD: {demographics.pbd}")
    print(f"  LTI: {demographics.lti}")
    print(f"  New enrollee: {demographics.new_enrollee}")
    print()

    # Step 2: Apply hierarchies
    print("Step 2: Apply Hierarchies")
    hcc_set = set(hcc_list)
    print(f"  Before hierarchies: {sorted(hcc_set)}")
    hcc_set_after = apply_hierarchies(hcc_set, model_name)
    print(f"  After hierarchies: {sorted(hcc_set_after)}")
    if hcc_set != hcc_set_after:
        removed = hcc_set - hcc_set_after
        print(f"  HCCs removed by hierarchies: {sorted(removed)}")
    print()

    # Step 3: Calculate interactions
    print("Step 3: Calculate Interactions")
    interactions = apply_interactions(demographics, hcc_set_after, model_name)
    active_interactions = {k: v for k, v in interactions.items() if v > 0}
    print(f"  Total interactions calculated: {len(interactions)}")
    print(f"  Active interactions (value > 0): {len(active_interactions)}")
    for k, v in active_interactions.items():
        print(f"    {k}: {v}")
    print()

    # Step 4: Get coefficient prefix
    print("Step 4: Coefficient Prefix")
    prefix = get_coefficent_prefix(demographics, model_name)
    print(f"  Coefficient prefix: {prefix}")
    print()

    # Step 5: Apply coefficients
    print("Step 5: Apply Coefficients")
    coefficients = apply_coefficients(demographics, hcc_set_after, interactions, model_name)
    print(f"  Total coefficients applied: {len(coefficients)}")

    demographic_coeff = 0
    hcc_coeffs = {}
    interaction_coeffs = {}

    for key, value in coefficients.items():
        if key == demographics.category:
            demographic_coeff = value
            print(f"  Demographics ({key}): {value}")
        elif key in hcc_set_after:
            hcc_coeffs[key] = value
            print(f"  HCC {key}: {value}")
        else:
            interaction_coeffs[key] = value
            print(f"  Interaction {key}: {value}")

    print()

    # Step 6: Calculate final risk score
    print("Step 6: Calculate Risk Score")
    total_risk_score = sum(coefficients.values())
    hcc_contribution = sum(hcc_coeffs.values())
    interaction_contribution = sum(interaction_coeffs.values())

    print(f"  Demographics contribution: {demographic_coeff:.3f}")
    print(f"  HCC contribution: {hcc_contribution:.3f}")
    print(f"  Interaction contribution: {interaction_contribution:.3f}")
    print(f"  Total risk score: {total_risk_score:.3f}")
    print()

    # Compare with actual function result
    print("Step 7: Verification")
    result = calculate_raf_from_hcc(hcc_list, model_name, **demographic_kwargs)
    print(f"  Function result: {result.risk_score:.3f}")
    print(f"  Manual calculation: {total_risk_score:.3f}")
    print(f"  Match: {abs(result.risk_score - total_risk_score) < 0.001}")

    return result, {
        'demographics': demographics,
        'hcc_set_after_hierarchies': hcc_set_after,
        'interactions': active_interactions,
        'coefficients': coefficients,
        'breakdown': {
            'demographic': demographic_coeff,
            'hcc': hcc_contribution,
            'interactions': interaction_contribution,
            'total': total_risk_score
        }
    }

def test_example_case():
    """Test the specific example case."""
    print("=" * 60)
    print("TESTING EXAMPLE CASE")
    print("=" * 60)

    # Test with different demographic scenarios to see which matches
    scenarios = [
        {
            'name': 'Community Female Aged (CFA)',
            'age': 65, 'sex': 'F', 'dual_elgbl_cd': 'NA'
        },
        {
            'name': 'Community Female Disabled (CFD)',
            'age': 55, 'sex': 'F', 'dual_elgbl_cd': 'NA'
        },
        {
            'name': 'Community Non-dual Aged (CNA)',
            'age': 65, 'sex': 'F', 'dual_elgbl_cd': '00'
        },
        {
            'name': 'Community Non-dual Disabled (CND)',
            'age': 55, 'sex': 'F', 'dual_elgbl_cd': '00'
        },
        {
            'name': 'Community Partial Dual Aged (CPA)',
            'age': 65, 'sex': 'F', 'dual_elgbl_cd': '03'
        },
        {
            'name': 'Community Partial Dual Disabled (CPD)',
            'age': 55, 'sex': 'F', 'dual_elgbl_cd': '03'
        },
        {
            'name': 'Full Benefit Dual Aged (CFA)',
            'age': 75, 'sex': 'F', 'dual_elgbl_cd': '02'
        },
        {
            'name': 'Full Benefit Dual Disabled (CFD)',
            'age': 45, 'sex': 'F', 'dual_elgbl_cd': '02'
        },
        {
            'name': 'Male scenarios - CNA',
            'age': 70, 'sex': 'M', 'dual_elgbl_cd': '00'
        },
        {
            'name': 'Different age - F70_74',
            'age': 72, 'sex': 'F', 'dual_elgbl_cd': '00'
        }
    ]

    target_risk_score = 1.32  # Government risk score
    target_demographic_score = 0.61

    best_match = None
    best_diff = float('inf')

    for scenario in scenarios:
        print(f"\n--- Testing {scenario['name']} ---")
        result, debug_info = debug_hcc_calculation(
            hcc_list=['161', '18', '58'],
            model_name="CMS-HCC Model V22",
            **{k: v for k, v in scenario.items() if k != 'name'}
        )

        print(f"Risk Score: {result.risk_score:.3f} (Target: {target_risk_score})")
        print(f"Demographics Score: {result.risk_score_demographics:.3f} (Target: {target_demographic_score})")

        demographic_diff = abs(result.risk_score_demographics - target_demographic_score)
        total_diff = abs(result.risk_score - target_risk_score)

        print(f"Demographics diff: {demographic_diff:.3f}")
        print(f"Total diff: {total_diff:.3f}")

        if total_diff < best_diff:
            best_diff = total_diff
            best_match = scenario['name']

    print(f"\n\nBest match: {best_match} (diff: {best_diff:.3f})")

    # Let's also try some other model versions
    print("\n" + "=" * 60)
    print("TESTING OTHER MODEL VERSIONS")
    print("=" * 60)

    models_to_test = ["CMS-HCC Model V24", "CMS-HCC Model V28"]
    for model in models_to_test:
        print(f"\n--- Testing {model} with CNA demographics ---")
        result, debug_info = debug_hcc_calculation(
            hcc_list=['161', '18', '58'],
            model_name=model,
            age=65, sex='F', dual_elgbl_cd='00'
        )
        print(f"Risk Score: {result.risk_score:.3f} (Target: {target_risk_score})")
        print(f"Demographics Score: {result.risk_score_demographics:.3f} (Target: {target_demographic_score})")
        print(f"Total diff: {abs(result.risk_score - target_risk_score):.3f}")
        print(f"Demo diff: {abs(result.risk_score_demographics - target_demographic_score):.3f}")

if __name__ == "__main__":
    test_example_case()