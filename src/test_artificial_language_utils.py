"""
test_artificial_language_utils.py | Author: Catherine Wong
"""
import artificial_language_utils as to_test

def translate_and_assert_match(input_to_gold, translation_fn):
    for input in input_to_gold:
        gold = input_to_gold[input]
        assert gold == translation_fn(input)

def test_translate_localization():
    input_to_gold = {
        "find the green rubber thing" : "GREEN RUBBER",
        "find the small rubber cube" : "SMALL RUBBER CUBE",
        "find the cyan thing s": "CYAN",
        "find the cube s": "CUBE",
    }
    translate_and_assert_match(input_to_gold, to_test.translate_localization_text)

def test_translate_remove():
    input_to_gold = {
        "what if you removed all of the small gray thing s" : "REMOVE SMALL GRAY",
        "if you removed the small brown thing s how many thing s would be left" : "REMOVE SMALL BROWN , COUNT",
        "if you removed the cyan cube s how many cube s would be left" : "REMOVE CYAN CUBE , COUNT CUBE",
        "if you removed the yellow thing s how many sphere s would be left" : "REMOVE YELLOW , COUNT SPHERE"                
    }
    translate_and_assert_match(input_to_gold, to_test.translate_remove_text)

def test_translate_transform():
    input_to_gold = {
        "what if the small sphere became a small metal thing" : "SMALL SPHERE TRANSFORM SMALL METAL",
        "what if all the green thing s became small thing s" : "GREEN TRANSFORM SMALL",
        "if all of the cyan cylinder s became brown how many brown thing s would there be" : "CYAN CYLINDER TRANSFORM BROWN , COUNT BROWN",
        "if all of the small rubber sphere s became large how many small thing s would there be" : "SMALL RUBBER SPHERE TRANSFORM LARGE , COUNT SMALL",
        "if all of the large purple thing s became red cube s how many red cube s would there be" : "LARGE PURPLE TRANSFORM RED CUBE , COUNT RED CUBE"
        
    }
    
    translate_and_assert_match(input_to_gold, to_test.translate_transform_text)

def test_translate_compare_integer():
    input_to_gold = {
        "is the number of large rubber cube s less than the number of large green rubber thing s" : "COUNT LARGE RUBBER CUBE LESS_THAN COUNT LARGE GREEN RUBBER",
        "is the number of large cylinder s greater than the number of small rubber sphere s" : "COUNT LARGE CYLINDER GREATER_THAN COUNT SMALL RUBBER SPHERE",
        "are there fewer small sphere s than cyan cube s" : "COUNT SMALL SPHERE LESS_THAN COUNT CYAN CUBE",
        "are there more metal cylinder s than blue metal thing s" : "COUNT METAL CYLINDER GREATER_THAN COUNT BLUE METAL"
    }
    
    translate_and_assert_match(input_to_gold, to_test.translate_compare_integer_text)
    
def test_translate_compare_integer():
    input_to_gold = {
        "how many objects are either large metal sphere s or large rubber thing s" : "LARGE METAL SPHERE OR LARGE RUBBER , COUNT",
        "what number of metal objects are small sphere s or purple thing s" : "SMALL SPHERE OR PURPLE , COUNT METAL",
        "how many cylinder s are either small purple thing s or small rubber thing s" : "SMALL PURPLE OR SMALL RUBBER , COUNT CYLINDER",
        "what number of rubber thing s are large sphere s or large thing s" : "LARGE SPHERE OR LARGE , COUNT RUBBER"
    }
    
    translate_and_assert_match(input_to_gold, to_test.translate_single_or_text)