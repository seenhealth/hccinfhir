import pytest
from hccinfhir.extractor_837 import extract_sld_837
from hccinfhir.samples import get_837_sample

def test_malformed_segments_no_exceptions():
    """Test that malformed segments don't cause exceptions"""
    # Test with incomplete segments
    malformed = 'ISA*00*~GS*HC*SUBMITTER*RECEIVER*20230415*1430*1*X*005010X222A1~ST*837*0001~NM1~CLM*12345~HI~SV1~'
    
    # Should not raise exceptions
    result = extract_sld_837(malformed)
    assert isinstance(result, list)
    assert len(result) == 0  # No valid service lines extracted


def test_empty_segment_elements():
    """Test segments with empty elements"""
    # Test with empty NM1 elements
    test_data = """ISA*00*          *00*          *ZZ*SUBMITTER*ZZ*RECEIVER*230415*1430*^*00501*000000001*0*P*:~
                   GS*HC*SUBMITTER*RECEIVER*20230415*1430*1*X*005010X222A1~
                   ST*837*0001*005010X222A1~
                   NM1**~
                   NM1*IL~
                   CLM*12345*500~
                   HI*ABK:F1120~
                   SV1**50*UN*1~
                   SE*8*0001~
                   GE*1*1~
                   IEA*1*000000001~"""
    
    # Should not raise exceptions
    result = extract_sld_837(test_data)
    assert isinstance(result, list)


def test_short_segments():
    """Test segments that are shorter than expected"""
    test_data = """ISA*00*          *00*          *ZZ*SUBMITTER*ZZ*RECEIVER*230415*1430*^*00501*000000001*0*P*:~
                   GS*HC*SUBMITTER*RECEIVER*20230415*1430*1*X*005010X222A1~
                   ST*837*0001*005010X222A1~
                   NM1*IL*1~
                   CLM~
                   PRV~
                   HI~
                   SV1*HC:99213~
                   SE*8*0001~
                   GE*1*1~
                   IEA*1*000000001~"""
    
    # Should not raise exceptions
    result = extract_sld_837(test_data)
    assert isinstance(result, list)


def test_none_values_in_date_processing():
    """Test DTP segments with None or short date values"""
    test_data = """ISA*00*          *00*          *ZZ*SUBMITTER*ZZ*RECEIVER*230415*1430*^*00501*000000001*0*P*:~
                   GS*HC*SUBMITTER*RECEIVER*20230415*1430*1*X*005010X222A1~
                   ST*837*0001*005010X222A1~
                   NM1*IL*1*DOE*JOHN****MI*12345~
                   CLM*12345*500~
                   HI*ABK:F1120~
                   SV1*HC:99213*50*UN*1~~~1~
                   DTP*472*D8*~
                   DTP*472*D8*123~
                   DTP*472*D8*20230415~
                   SE*11*0001~
                   GE*1*1~
                   IEA*1*000000001~"""
    
    # Should not raise exceptions
    result = extract_sld_837(test_data)
    assert isinstance(result, list)


def test_institutional_clm_with_empty_elements():
    """Test institutional CLM segment with empty facility/service type"""
    test_data = """ISA*00*          *00*          *ZZ*SUBMITTER*ZZ*RECEIVER*240209*1230*^*00501*000000001*0*P*:~
                   GS*HC*SUBMITTER*RECEIVER*20240209*1230*1*X*005010X223A2~
                   ST*837*0001*005010X223A2~
                   NM1*IL*1*DOE*JOHN****MI*123456789A~
                   CLM*12345*500***~
                   CLM*12346*500***:**1~
                   HI*ABK:R69.0~
                   SV2*0450*HC:99284*500*UN*1~
                   SE*7*0001~
                   GE*1*1~
                   IEA*1*000000001~"""
    
    # Should not raise exceptions
    result = extract_sld_837(test_data)
    assert isinstance(result, list)

def test_multiple_claims_in_one_file():

    # use the sample data function to get the sample data
    sample_data = get_837_sample(12)
    result = extract_sld_837(sample_data)
    assert isinstance(result, list)
    assert len(result) == 8