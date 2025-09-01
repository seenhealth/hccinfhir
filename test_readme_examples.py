#!/usr/bin/env python3
"""
Test script to validate all README examples work correctly.
This ensures the documentation examples are accurate and functional.
"""

import sys
import traceback
from typing import Dict, Any

def test_quick_start():
    """Test the Quick Start example from README"""
    print("\n=== Testing Quick Start Example ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics

        # Initialize processor
        processor = HCCInFHIR(model_name="CMS-HCC Model V28")

        # Calculate from diagnosis codes
        demographics = Demographics(age=67, sex="F")
        diagnosis_codes = ["E11.9", "I10", "N18.3"]

        result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)
        print(f"Risk Score: {result.risk_score}")
        print(f"HCCs: {result.hcc_list}")
        
        # Validate result structure
        assert hasattr(result, 'risk_score'), "Result missing risk_score"
        assert hasattr(result, 'hcc_list'), "Result missing hcc_list"
        assert isinstance(result.risk_score, float), "risk_score should be float"
        assert isinstance(result.hcc_list, list), "hcc_list should be list"
        assert result.risk_score > 0, "Risk score should be positive"
        assert len(result.hcc_list) > 0, "Should have some HCCs"
        
        print("✅ Quick Start example passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick Start example failed: {e}")
        traceback.print_exc()
        return False

def test_cms_encounter_data():
    """Test the CMS Encounter Data (EDRs) example"""
    print("\n=== Testing CMS Encounter Data (EDRs) Example ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics, get_837_sample
        from hccinfhir.extractor import extract_sld

        # Step 1: Configure processor for your model year and version
        processor = HCCInFHIR(
            model_name="CMS-HCC Model V28",           # CMS model version
            filter_claims=True,                       # Apply CMS filtering rules
            dx_cc_mapping_filename="ra_dx_to_cc_2026.csv",
            proc_filtering_filename="ra_eligible_cpt_hcpcs_2026.csv"
        )

        # Step 2: Load 837 data (using sample data 12 as suggested)
        raw_837_data = get_837_sample(12)

        # Step 3: Extract service-level data
        service_data = extract_sld(raw_837_data, format="837")

        # Step 4: Define beneficiary demographics
        demographics = Demographics(
            age=72,
            sex="M",
            dual_elgbl_cd="00",     # Dual eligibility status
            orig_disabled=False,     # Original disability status
            new_enrollee=False,      # New enrollee flag
            esrd=False              # ESRD status
        )

        # Step 5: Calculate risk score
        result = processor.run_from_service_data(service_data, demographics)

        # Step 6: Review results
        print(f"Beneficiary Risk Score: {result.risk_score}")
        print(f"Active HCCs: {result.hcc_list}")
        print(f"Disease Interactions: {result.interactions}")

        # Export results for CMS submission
        encounter_summary = {
            "beneficiary_id": "example_id",
            "risk_score": result.risk_score,
            "hcc_list": result.hcc_list,
            "model_version": "V28",
            "payment_year": 2026
        }
        print(f"Encounter Summary: {encounter_summary}")
        
        # Validate results
        assert isinstance(result.risk_score, float), "risk_score should be float"
        assert isinstance(result.hcc_list, list), "hcc_list should be list"
        assert isinstance(result.interactions, dict), "interactions should be dict"
        assert isinstance(service_data, list), "service_data should be list"
        assert len(service_data) > 0, "Should have extracted some service data"
        
        print("✅ CMS Encounter Data example passed!")
        return True
        
    except Exception as e:
        print(f"❌ CMS Encounter Data example failed: {e}")
        traceback.print_exc()
        return False

def test_clearinghouse_837():
    """Test the Clearinghouse 837 Claims example"""
    print("\n=== Testing Clearinghouse 837 Claims Example ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics
        from hccinfhir.extractor import extract_sld_list

        # Configure for institutional and professional claims
        processor = HCCInFHIR(
            model_name="CMS-HCC Model V28",
            filter_claims=True,    # Enable CMS filtering
            dx_cc_mapping_filename="ra_dx_to_cc_2026.csv"
        )

        # Process multiple 837 files (using sample data)
        from hccinfhir import get_837_sample
        claim_files = [get_837_sample(0), get_837_sample(1)]  # Simulate multiple files
        all_service_data = []

        for claims_data in claim_files:
            # Extract service data from each file
            service_data = extract_sld_list([claims_data], format="837")
            all_service_data.extend(service_data)

        # Member demographics (typically from your enrollment system)
        member_demographics = Demographics(
            age=45,
            sex="F",
            dual_elgbl_cd="02",    # Partial dual eligible
            orig_disabled=True,     # Originally disabled
            new_enrollee=False
        )

        # Calculate comprehensive risk score
        result = processor.run_from_service_data(all_service_data, member_demographics)

        # Analyze by service type
        professional_services = [svc for svc in result.service_level_data if svc.claim_type == "71"]
        institutional_services = [svc for svc in result.service_level_data if svc.claim_type == "72"]

        print(f"Member Risk Score: {result.risk_score}")
        print(f"Professional Claims: {len(professional_services)}")
        print(f"Institutional Claims: {len(institutional_services)}")
        
        # Validate results
        assert isinstance(result.risk_score, float), "risk_score should be float"
        assert isinstance(all_service_data, list), "service_data should be list"
        assert len(all_service_data) > 0, "Should have extracted some service data"
        
        print("✅ Clearinghouse 837 Claims example passed!")
        return True
        
    except Exception as e:
        print(f"❌ Clearinghouse 837 Claims example failed: {e}")
        traceback.print_exc()
        return False

def test_bcda_api_data():
    """Test the CMS BCDA API Data example"""
    print("\n=== Testing CMS BCDA API Data Example ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics, get_eob_sample_list
        from hccinfhir.extractor import extract_sld_list

        # Configure processor for BCDA data
        processor = HCCInFHIR(
            model_name="CMS-HCC Model V24",    # BCDA typically uses V24
            filter_claims=True,
            dx_cc_mapping_filename="ra_dx_to_cc_2025.csv"
        )

        # Fetch EOB data from BCDA (example using sample data)
        eob_resources = get_eob_sample_list(limit=5)  # Smaller limit for testing

        # Extract service-level data from FHIR resources
        service_data = extract_sld_list(eob_resources, format="fhir")

        # BCDA provides beneficiary demographics in the EOB
        # Extract demographics from the first EOB resource
        first_eob = eob_resources[0]
        beneficiary_ref = first_eob.get("patient", {}).get("reference", "")

        # You would typically look up demographics from your system
        demographics = Demographics(
            age=68,
            sex="M",
            dual_elgbl_cd="00",
            new_enrollee=False,
            esrd=False
        )

        # Process FHIR data
        result = processor.run(eob_resources, demographics)

        # BCDA-specific analysis
        print(f"Beneficiary: {beneficiary_ref}")
        print(f"Risk Score: {result.risk_score}")
        print(f"Data Source: BCDA API")
        print(f"HCC Categories: {', '.join(map(str, result.hcc_list))}")

        # Examine service utilization patterns
        service_dates = [svc.service_date for svc in result.service_level_data if svc.service_date]
        if service_dates:
            print(f"Service Period: {min(service_dates)} to {max(service_dates)}")
        
        # Validate results
        assert isinstance(result.risk_score, float), "risk_score should be float"
        assert isinstance(result.hcc_list, list), "hcc_list should be list"
        assert isinstance(service_data, list), "service_data should be list"
        assert len(eob_resources) > 0, "Should have EOB resources"
        
        print("✅ BCDA API Data example passed!")
        return True
        
    except Exception as e:
        print(f"❌ BCDA API Data example failed: {e}")
        traceback.print_exc()
        return False

def test_direct_diagnosis_processing():
    """Test the Direct Diagnosis Code Processing example"""
    print("\n=== Testing Direct Diagnosis Code Processing Example ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics

        # Simple setup for diagnosis-only processing
        processor = HCCInFHIR(model_name="CMS-HCC Model V28")

        # Define patient population
        demographics = Demographics(
            age=75,
            sex="F",
            dual_elgbl_cd="02",  # Dual eligible
            orig_disabled=False,
            new_enrollee=False,
            esrd=False
        )

        # Diagnosis codes from clinical encounter
        diagnosis_codes = [
            "E11.9",   # Type 2 diabetes without complications
            "I10",     # Essential hypertension  
            "N18.3",   # Chronic kidney disease, stage 3
            "F32.9",   # Major depressive disorder
            "M79.3"    # Panniculitis
        ]

        # Calculate risk score
        result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)

        # Detailed analysis
        print("=== HCC Risk Analysis ===")
        print(f"Risk Score: {result.risk_score:.3f}")
        print(f"HCC Categories: {result.hcc_list}")

        # Show diagnosis to HCC mappings
        print("\nDiagnosis Mappings:")
        for cc, dx_list in result.cc_to_dx.items():
            print(f"  CC {cc}: {', '.join(dx_list)}")

        # Show applied coefficients
        print(f"\nApplied Coefficients: {len(result.coefficients)}")
        for coeff_name, value in result.coefficients.items():
            print(f"  {coeff_name}: {value}")

        # Check for interactions
        if result.interactions:
            print(f"\nDisease Interactions: {len(result.interactions)}")
            for interaction, value in result.interactions.items():
                print(f"  {interaction}: {value}")
        else:
            print("\nNo Disease Interactions found")
        
        # Validate results
        assert isinstance(result.risk_score, float), "risk_score should be float"
        assert isinstance(result.hcc_list, list), "hcc_list should be list"
        assert isinstance(result.cc_to_dx, dict), "cc_to_dx should be dict"
        assert isinstance(result.coefficients, dict), "coefficients should be dict"
        assert isinstance(result.interactions, dict), "interactions should be dict"
        assert result.risk_score > 0, "Risk score should be positive"
        assert len(result.hcc_list) > 0, "Should have some HCCs"
        
        print("✅ Direct Diagnosis Processing example passed!")
        return True
        
    except Exception as e:
        print(f"❌ Direct Diagnosis Processing example failed: {e}")
        traceback.print_exc()
        return False

def test_sample_data_usage():
    """Test sample data functions from the README"""
    print("\n=== Testing Sample Data Usage ===")
    
    try:
        from hccinfhir import get_eob_sample, get_837_sample, list_available_samples

        # FHIR ExplanationOfBenefit samples
        eob_data = get_eob_sample(1)                    # Individual EOB (cases 1, 2, 3)
        from hccinfhir import get_eob_sample_list
        eob_list = get_eob_sample_list(limit=3)        # Up to 200 EOB resources

        # X12 837 claim samples  
        claim_data = get_837_sample(0)                  # Individual 837 claim (cases 0-12)
        from hccinfhir import get_837_sample_list
        claim_list = get_837_sample_list([0, 1, 2])    # Multiple 837 claims

        # Sample information
        sample_info = list_available_samples()
        print(f"Available EOB samples: {len(sample_info['eob_case_numbers'])}")
        print(f"Available 837 samples: {len(sample_info['837_case_numbers'])}")
        
        # Validate samples
        assert isinstance(eob_data, dict), "EOB sample should be dict"
        assert isinstance(eob_list, list), "EOB list should be list"
        assert isinstance(claim_data, str), "837 sample should be string"
        assert isinstance(claim_list, list), "837 list should be list"
        assert len(eob_list) == 3, "Should have 3 EOB samples"
        assert len(claim_list) == 3, "Should have 3 837 samples"
        assert len(sample_info['eob_case_numbers']) > 0, "Should have EOB cases"
        assert len(sample_info['837_case_numbers']) > 0, "Should have 837 cases"
        
        print("✅ Sample Data Usage example passed!")
        return True
        
    except Exception as e:
        print(f"❌ Sample Data Usage example failed: {e}")
        traceback.print_exc()
        return False

def test_configuration_examples():
    """Test configuration examples from the README"""
    print("\n=== Testing Configuration Examples ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics

        # Test comprehensive configuration
        processor = HCCInFHIR(
            # Core model settings
            model_name="CMS-HCC Model V28",              # Required: HCC model version
            
            # Filtering options
            filter_claims=True,                          # Apply CMS filtering rules
            
            # Custom data files (using defaults)
            dx_cc_mapping_filename="ra_dx_to_cc_2026.csv",           # Diagnosis to CC mapping
            proc_filtering_filename="ra_eligible_cpt_hcpcs_2026.csv", # Procedure code filtering
        )

        # Test demographics configuration
        demographics = Demographics(
            # Required fields
            age=67,                    # Age in years
            sex="F",                   # "M" or "F"
            
            # CMS-specific fields
            dual_elgbl_cd="00",        # Dual eligibility: "00"=Non-dual, "01"=Partial, "02"=Full
            orig_disabled=False,        # Original reason for Medicare entitlement was disability
            new_enrollee=False,        # New Medicare enrollee (< 12 months)
            esrd=False,                # End-Stage Renal Disease status
            
            # Optional fields
            snp=False,                 # Special Needs Plan member
            low_income=False,          # Low-income subsidy
            graft_months=None,         # Months since kidney transplant (for ESRD models)
            category="CNA"             # Beneficiary category (auto-calculated if not provided)
        )
        
        # Test basic calculation to ensure configuration works
        result = processor.calculate_from_diagnosis(["E11.9"], demographics)
        
        assert isinstance(processor, HCCInFHIR), "Processor should be HCCInFHIR instance"
        assert isinstance(demographics, Demographics), "Demographics should be Demographics instance"
        assert isinstance(result.risk_score, float), "Should calculate risk score"
        
        print("✅ Configuration examples passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration examples failed: {e}")
        traceback.print_exc()
        return False

def test_dictionary_conversion():
    """Test dictionary conversion examples from the README"""
    print("\n=== Testing Dictionary Conversion Examples ===")
    
    try:
        from hccinfhir import HCCInFHIR, Demographics

        processor = HCCInFHIR(model_name="CMS-HCC Model V28")
        demographics = Demographics(age=67, sex="F")
        diagnosis_codes = ["E11.9", "I10"]

        # Get Pydantic model result
        result = processor.calculate_from_diagnosis(diagnosis_codes, demographics)
        print(f"Risk Score (Pydantic): {result.risk_score}")

        # Convert to dictionary
        result_dict = result.model_dump()
        print(f"Risk Score (Dict): {result_dict['risk_score']}")

        # Convert with different modes
        result_json_compatible = result.model_dump(mode='json')
        result_python_types = result.model_dump(mode='python')

        # Convert only specific fields
        partial_dict = result.model_dump(include={'risk_score', 'hcc_list', 'demographics'})

        # Convert excluding certain fields
        summary_dict = result.model_dump(exclude={'service_level_data', 'interactions'})

        # Convert to JSON string directly
        json_string = result.model_dump_json()

        # Demographics conversion
        demographics_dict = result.demographics.model_dump()
        print(f"Demographics dict keys: {list(demographics_dict.keys())}")

        # Validate conversions
        assert isinstance(result_dict, dict), "model_dump should return dict"
        assert result_dict['risk_score'] == result.risk_score, "Values should match"
        assert 'risk_score' in partial_dict, "Should include specified fields"
        assert 'hcc_list' in partial_dict, "Should include specified fields"
        assert 'service_level_data' not in summary_dict, "Should exclude specified fields"
        assert isinstance(json_string, str), "model_dump_json should return string"
        assert isinstance(demographics_dict, dict), "Demographics should convert to dict"
        assert demographics_dict['age'] == 67, "Values should be preserved"
        
        print("✅ Dictionary conversion examples passed!")
        return True
        
    except Exception as e:
        print(f"❌ Dictionary conversion examples failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all README example tests"""
    print("🧪 Testing all README examples...")
    print("=" * 60)
    
    test_functions = [
        test_quick_start,
        test_cms_encounter_data,
        test_clearinghouse_837,
        test_bcda_api_data,
        test_direct_diagnosis_processing,
        test_sample_data_usage,
        test_configuration_examples,
        test_dictionary_conversion
    ]
    
    results = []
    for test_func in test_functions:
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ {test_func.__name__} crashed: {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All README examples are working correctly!")
        sys.exit(0)
    else:
        print("⚠️  Some README examples need fixes.")
        sys.exit(1)

if __name__ == "__main__":
    main()