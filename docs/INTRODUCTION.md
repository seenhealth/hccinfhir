# Introduction to HCC Risk Adjustment

Welcome to HCC risk adjustment! If you're new to healthcare analytics or wondering what this library does, this guide will help you understand the fundamentals.

## 🏥 The Big Picture: What is HCC Risk Adjustment?

**HCC** stands for **Hierarchical Condition Categories** - it's a sophisticated payment system that Medicare uses to fairly pay health plans based on how sick their patients are.

**The Problem**: Not all patients cost the same to treat. A healthy 65-year-old might cost $3,000/year, while someone with diabetes, heart disease, and kidney failure might cost $30,000/year.

**The Solution**: HCC risk adjustment calculates a "risk score" that predicts how expensive a patient will be, so Medicare can pay plans appropriately.

## 🔢 How Risk Scores Work

- **Risk Score of 1.0** = Average Medicare beneficiary
- **Risk Score of 2.5** = Expected to cost 2.5x more than average
- **Risk Score of 0.7** = Expected to cost 30% less than average

Medicare multiplies your plan's payment by these risk scores!

## 🛠️ What This Library Does

This `hccinfhir` library takes healthcare data and calculates these risk scores automatically. It's like a specialized calculator that:

1. **Reads** medical claims data (diagnoses, procedures, patient info)
2. **Applies** complex CMS rules and mappings
3. **Calculates** precise risk scores used for payments

## 📊 The Data Flow

```
Input Data → Extract → Filter → Map → Calculate → Risk Score
```

Let's walk through each step:

### 1. Input Data Sources
The library accepts three types of healthcare data:

- **FHIR Resources** (modern healthcare API format)
- **X12 837 Claims** (traditional claims format)
- **Diagnosis Codes** (simple list of medical conditions)

### 2. Extract & Standardize
Different formats get converted into a standard `ServiceLevelData` format containing:
- Patient demographics (age, sex, eligibility status)
- Diagnosis codes (like "E11.9" for diabetes)
- Service information (dates, providers, procedures)

### 3. Apply CMS Rules
The library implements hundreds of CMS rules:
- Which services count for risk adjustment?
- How do you handle duplicate diagnoses?
- What eligibility criteria matter?

### 4. Map Diagnoses to HCC Categories
This is where it gets interesting! The library contains CSV files with official CMS mappings:

```
ICD-10 Code → Condition Category → HCC Category
E11.9 (Diabetes) → CC 19 → HCC 19 (Diabetes without complications)
I50.9 (Heart failure) → CC 85 → HCC 85 (Congestive Heart Failure)
```

### 5. Apply Hierarchies
Here's the "Hierarchical" part - if you have both mild and severe diabetes, only the severe one counts (it "trumps" the mild one).

### 6. Calculate Interactions
Some disease combinations are especially expensive. The library calculates bonus points for interactions like:
- Diabetes + Heart Failure = Extra risk points
- Multiple chronic conditions = Interaction bonuses

### 7. Apply Coefficients & Sum
Each factor gets multiplied by a coefficient from CMS tables:
- Female, age 70-74: 0.323 points
- HCC 19 (Diabetes): 0.318 points
- HCC 85 (Heart Failure): 0.368 points
- Diabetes-Heart Failure interaction: 0.154 points

**Total Risk Score = 0.323 + 0.318 + 0.368 + 0.154 = 1.163**

## 🏗️ The Code Architecture

The library is beautifully organized:

### Core Processing (`hccinfhir.py`)
The main `HCCInFHIR` class orchestrates everything:
```python
processor = HCCInFHIR(model_name="CMS-HCC Model V28")
result = processor.calculate_from_diagnosis(["E11.9", "I50.9"], demographics)
print(f"Risk Score: {result.risk_score}")  # Outputs: 1.163
```

### Data Extractors
- `extractor_fhir.py` - Reads modern FHIR resources
- `extractor_837.py` - Parses traditional X12 claims files

### Model Components
Each implements a specific piece of the CMS methodology:
- `model_demographics.py` - Age/sex categories, eligibility
- `model_dx_to_cc.py` - Diagnosis code mappings
- `model_hierarchies.py` - Applies hierarchy rules
- `model_interactions.py` - Disease interaction bonuses
- `model_coefficients.py` - Final coefficient application

### Reference Data (`data/` folder)
Contains official CMS tables in CSV format:
- Diagnosis-to-HCC mappings (40,000+ codes!)
- Risk adjustment coefficients
- Hierarchy relationships
- Interaction definitions

## 💰 Real-World Impact

This isn't just academic - it directly affects billions in Medicare payments:

- **Medicare Advantage plans** use this for risk adjustment submissions
- **Healthcare providers** use it to understand their patient populations
- **Researchers** use it to risk-adjust outcomes in studies
- **Government actuaries** use it to set Medicare rates

The calculations must be **perfect** because they determine actual money flowing through the healthcare system.

## 🎯 Why This Library is Valuable

Before this library, organizations had to:
- Build their own HCC calculators (expensive, error-prone)
- Manually implement hundreds of CMS rules
- Keep up with annual updates to coefficients and mappings

This library provides a **production-ready, validated implementation** that handles all the complexity, supports multiple data formats, and stays current with CMS updates.

It's essentially taking a 200-page CMS technical manual and turning it into clean, tested Python code that anyone can use!

## 📚 Next Steps

Ready to start using the library? Check out:

- [Quick Start Guide](../README.md#-quick-start) - Get up and running in 5 minutes
- [How-To Guides](../README.md#-how-to-guides) - Practical examples for different use cases
- [API Reference](../README.md#-api-reference) - Detailed documentation of all classes and methods

Have questions about HCC concepts? The [CMS Risk Adjustment documentation](https://www.cms.gov/Medicare/Health-Plans/MedicareAdvtgSpecRateStats/Risk-Adjustors) provides the official technical specifications.