"""
test_artificial_language_utils.py | Author: Catherine Wong
Usage: 
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
    
def test_translate_single_or():
    input_to_gold = {
        "how many objects are either large metal sphere s or large rubber thing s" : "LARGE METAL SPHERE OR LARGE RUBBER , COUNT",
        "what number of metal objects are small sphere s or purple thing s" : "SMALL SPHERE OR PURPLE , COUNT METAL",
        "how many cylinder s are either small purple thing s or small rubber thing s" : "SMALL PURPLE OR SMALL RUBBER , COUNT CYLINDER",
        "what number of rubber thing s are large sphere s or large thing s" : "LARGE SPHERE OR LARGE , COUNT RUBBER"
    }
    
    translate_and_assert_match(input_to_gold, to_test.translate_single_or_text)

def test_translate_zero_hop():
    input_to_gold = {
        "what number of large thing s are there" : "COUNT LARGE",
        "how many rubber cylinder s are there" : "COUNT RUBBER CYLINDER",
        "there is a yellow thing what shape is it" : "GET_SHAPE YELLOW",
        "what is the shape of the small yellow thing" : "GET_SHAPE SMALL YELLOW",
        "what is the small blue cube made of" : "GET_MATERIAL SMALL BLUE CUBE",
        "what is the material of the gray sphere" : "GET_MATERIAL GRAY SPHERE",
        "what color is the metal cylinder" : "GET_COLOR METAL CYLINDER",
        "the small metal sphere is what color" : "GET_COLOR SMALL METAL SPHERE",
        "the metal sphere is what size" : "GET_SIZE METAL SPHERE",
        "how big is the purple thing" : "GET_SIZE PURPLE"
    }
    translate_and_assert_match(input_to_gold, to_test.translate_zero_hop_text)

def test_translate_one_hop():
    input_to_gold = {
        "what number of metal cube s are behind the rubber cylinder" : "COUNT METAL CUBE BEHIND_OF RUBBER CYLINDER",
        "how many metal thing s are behind the rubber cylinder" : "COUNT METAL BEHIND_OF RUBBER CYLINDER",
        "there is a cylinder front the small blue rubber cylinder what is its size" : "GET_SIZE CYLINDER FRONT_OF SMALL BLUE RUBBER CYLINDER",
        "what size is the rubber thing that is right the purple thing" : "GET_SIZE RUBBER RIGHT_OF PURPLE",
        "what color is the thing that is behind the sphere" : "GET_COLOR BEHIND_OF SPHERE",
        "the small metal thing that is right the small metal sphere is what color" : "GET_COLOR SMALL METAL RIGHT_OF SMALL METAL SPHERE",
        
        "what is the material of the large thing right the large purple metal thing" : "GET_MATERIAL LARGE RIGHT_OF LARGE PURPLE METAL",
        "what is the small cylinder front the small brown cylinder made of" : "GET_MATERIAL SMALL CYLINDER FRONT_OF SMALL BROWN CYLINDER", 
        
        "the small metal thing right the small metal sphere has what shape" : "GET_SHAPE SMALL METAL RIGHT_OF SMALL METAL SPHERE",
        "what is the shape of the large rubber thing that is left the small red metal thing" : "GET_SHAPE LARGE RUBBER LEFT_OF SMALL RED METAL",
    }
    
    translate_and_assert_match(input_to_gold, to_test.translate_one_hop_text)

def test_translate_same_related_restricted():
    input_to_gold = {
        "how many other thing s are there of the same size as the cyan thing" : "GET_SIZE SAME CYAN , COUNT",
        "what number of other thing s are there of the same size as the metal sphere" : "GET_SIZE SAME METAL SPHERE , COUNT",
        
        "what number of other objects are the same color as the small cylinder" : "GET_COLOR SAME SMALL CYLINDER , COUNT",
        "what number of other objects are there of the same color as the metal sphere" : "GET_COLOR SAME METAL SPHERE , COUNT",
        "what number of other objects are there of the same color as the metal sphere" : "GET_COLOR SAME METAL SPHERE , COUNT",
        
        "what number of large cube s have the same material as the cylinder" : "GET_MATERIAL SAME CYLINDER , COUNT LARGE CUBE",
        "what number of thing s are made of the same material as the cyan sphere" : "GET_MATERIAL SAME CYAN SPHERE , COUNT",
        "how many other blue thing s have the same material as the large blue thing" : "GET_MATERIAL SAME LARGE BLUE , COUNT BLUE",
        
        "what number of large metal thing s have the same shape as the small red metal thing" : "GET_SHAPE SAME SMALL RED METAL , COUNT LARGE METAL",
        "how many metal thing s have the same shape as the green rubber thing" : "GET_SHAPE SAME GREEN RUBBER , COUNT METAL",
        "how many other rubber thing s are the same shape as the small yellow thing" : "GET_SHAPE SAME SMALL YELLOW , COUNT RUBBER",
        
        "the green metal thing that is the same size as the rubber cylinder is what shape" : "GET_SIZE SAME RUBBER CYLINDER , GET_SHAPE GREEN METAL",
        "what shape is the brown thing that is the same size as the gray rubber thing" : "GET_SIZE SAME GRAY RUBBER , GET_SHAPE BROWN",
        
        "what is the material of the small cylinder that is the same color as the metal cube" : "GET_COLOR SAME METAL CUBE , GET_MATERIAL SMALL CYLINDER",
        "there is another thing that is the same color as the large rubber thing what is it made of" : "GET_COLOR SAME LARGE RUBBER , GET_MATERIAL",
        "there is a thing that is the same color as the small cylinder what material is it" : "GET_COLOR SAME SMALL CYLINDER , GET_MATERIAL"
    }
    
    translate_and_assert_match(input_to_gold, to_test.translate_same_relate_restricted_text)

