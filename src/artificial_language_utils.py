"""
artificial_language_utils.py | Author: Catherine Wong

Utility functions specifically to translate the artificial language tokens.
"""
REMOVE_TOKEN = " REMOVE "
COUNT_TOKEN = " COUNT "
COMMA_TOKEN = " , "
TRANSFORM_TOKEN = " TRANSFORM "
LESS_THAN_TOKEN = " LESS_THAN "
GREATER_THAN_TOKEN = " GREATER_THAN "
OR_TOKEN = " OR "

GET_MATERIAL_TOKEN = " GET_MATERIAL "
GET_SHAPE_TOKEN = " GET_SHAPE "
GET_SIZE_TOKEN = " GET_SIZE "
GET_COLOR_TOKEN = " GET_COLOR "

RIGHT_TOKEN = " RIGHT_OF "
LEFT_TOKEN = " LEFT_OF "
FRONT_TOKEN = " FRONT_OF "
BEHIND_TOKEN = " BEHIND_OF "

SAME_TOKEN = " SAME "

def pad_text(text):
    return f" {text} "

def remove_extraneous_spaces(text):
    return " ".join(text.split())
    
def translate_constants(text):
    """
    Replaces all instances of constants (e.g.'sphere') with their artificial language tokens. Replaces 'thing' with nothing.
    """
    constant_shape = ["cube", "sphere", "cylinder"]
    constant_color = ["gray", "red", "blue", "green", "brown", "purple", "cyan", "yellow"]
    constant_size = ["small", "large"]
    constant_material = ["rubber", "metal"]
    constant_thing = ["thing s ", "thing", "objects", "object" ]
    # Shapes can be plural; sphere s -> SPHERE
    constant_plural_shapes  = [(shape + " s ", shape) for shape in constant_shape]
    for plural_shape, shape in constant_plural_shapes:
        text = text.replace(plural_shape, f" {shape.upper()} ")
    for constant_kind in [constant_shape, constant_color, constant_size, constant_material]:
        for constant_attribute in constant_kind:
            text = text.replace(constant_attribute, f" {constant_attribute.upper()} ")
    for thing in constant_thing:
        text = text.replace(thing, " ")
    return text

def translate_localization_text(text):
    """Find the <Z> <C> <M> <S>. -> <Z> <C> <M> <S>
    """
    text = pad_text(text)
    text = text.replace("find the ", "")
    text = translate_constants(text)
    return remove_extraneous_spaces(text)

def translate_remove_text(text):
    """
    Translates four different remove templates.
    """
    text = pad_text(text)
    # What if you removed all of the <Z> <C> <M> <S>s? ->  REMOVE <Z> <C> <M> <S>
    what_if_remove = "what if you removed all of the "
    if what_if_remove in text:
        text = text.replace(what_if_remove, REMOVE_TOKEN)
        text = translate_constants(text)
    
    # If you removed the <Z> <C> <M> <S>s, how many <Z> <C> <M> <S> would be left?  REMOVE<Z> <C> <M> <S>, COUNT <Z> <C> <M> <S>
    if_remove = "if you removed the "
    how_many = "how many"
    would_be_left = "would be left"
    if if_remove in text:
        text = text.replace(if_remove, REMOVE_TOKEN)
        text = text.replace(how_many, COMMA_TOKEN + COUNT_TOKEN)
        text = text.replace(would_be_left, "")
        text = translate_constants(text)
    return remove_extraneous_spaces(text)

def translate_transform_text(text):
    # What if the <Z> <C> <M> <S> became a <Z2> <C2> <M2> <S2>?
    # What if all the <Z> <C> <M> <S>s became <Z2> <C2> <M2> <S2>s?
    text = pad_text(text)
    text = text.replace("what if the ", "")
    text = text.replace("what if all the ", "")
    text = text.replace("if all of the ", "")
    text = text.replace("would there be", "")
    
    text = text.replace("became a ", TRANSFORM_TOKEN)
    text = text.replace("became ", TRANSFORM_TOKEN)
    
    how_many = "how many"
    text = text.replace(how_many, COMMA_TOKEN + COUNT_TOKEN)
    text = translate_constants(text)
    return remove_extraneous_spaces(text)

def translate_compare_integer_text(text):
    # Are there fewer <Z> <C> <M> <S>s than <Z2> <C2> <M2> <S2>s?
    # Are there more <Z> <C> <M> <S>s than <Z2> <C2> <M2> <S2>s?
    # COUNT  <Z> <C> <M> <S> __THAN
    fewer = "fewer"
    less = "less"
    text = pad_text(text)
    text = text.replace("is the number of", "")
    text = text.replace("the number of", "")
    if fewer in text or less in text:
        text = text.replace("are there fewer", "")
        text = text.replace("less", "")
        text = text.replace("than",  LESS_THAN_TOKEN + COUNT_TOKEN )
        text = COUNT_TOKEN + text
    more = "more"
    greater = "greater"
    if greater in text or more in text:
        text = text.replace("are there more", "")
        text = text.replace(greater, "")
        text = text.replace("than",  GREATER_THAN_TOKEN + COUNT_TOKEN )
        text = COUNT_TOKEN + text
    text = translate_constants(text)
    return remove_extraneous_spaces(text)

def translate_single_or_text(text):
    text = pad_text(text)
    if "either" in text:
        either_delimiter = "are either"
    else:
        either_delimiter = "are"
    split_question = text.split(either_delimiter)
    text = split_question[1] + " " + split_question[0]
    text = text.replace("or", OR_TOKEN)
    how_many = "how many"
    what_number = "what number of"
    text = text.replace(how_many, COMMA_TOKEN + COUNT_TOKEN)
    text = text.replace(what_number, COMMA_TOKEN + COUNT_TOKEN)
    text = translate_constants(text)
    return remove_extraneous_spaces(text)

def translate_and_remove_count_queries(text):
    how_many = "how many"
    what_number = "what number of"
    if how_many in text or what_number in text:
        text = text.replace("are there", "")
        text = text.replace(how_many, COUNT_TOKEN)
        text = text.replace(what_number, COUNT_TOKEN)
    return text

def translate_and_remove_material_queries(text):
    made_of = "made of"
    material = "material of the"
    material_short = "material"
    if not(made_of in text or material in text or material_short in text):
        return text
    # Counterintuitive, but always places the query in the front of the filters.
    text = text.replace(made_of, "")
    text = text.replace(material, "")
    text = text.replace(material_short, "")
    text = remove_extraneous_spaces(text)
    text = text.replace("what is the", GET_MATERIAL_TOKEN)
    return text

def translate_and_remove_shape_queries(text):
    shape_prefix = "what shape is the "
    shape_prefix_long = "what is the shape of the "
    shape_postfix = "what shape is it" 
    shape_postfix_long = "has what shape"
    if shape_prefix in text or shape_prefix_long in text:
        text = text.replace(shape_prefix_long, GET_SHAPE_TOKEN)
        text = text.replace(shape_prefix, GET_SHAPE_TOKEN)
    elif shape_postfix in text or shape_postfix_long in text:
        text = text.replace(shape_postfix, "")
        text = text.replace(shape_postfix_long, "")
        text = text.replace("there is a", "")
        text = text.replace("the", "")
        text = GET_SHAPE_TOKEN + text
    return text

def translate_and_remove_color_queries(text):
    color_prefix = "what color is the"
    color_prefix_long = 'what is the color of the'
    color_postfix = "is what color"
    color_postfix_2 = "has what color"
    
    if color_prefix in text or color_prefix_long in text:
        text = text.replace(color_prefix_long, GET_COLOR_TOKEN)
        text = text.replace(color_prefix, GET_COLOR_TOKEN)
    elif color_postfix in text or color_postfix_2 in text:
        text = text.replace("the", "")
        text = text.replace(color_postfix, "")
        text = text.replace(color_postfix_2, "")
        text = GET_COLOR_TOKEN + text
    return text

def translate_and_remove_size_queries(text):
    size_prefix = "how big is the"
    size_prefix_long = 'what size is the'
    size_prefix_long_2 = "what is the size of the"
    size_postfix = "is what size"
    size_postfix_2 = "has what size"
    size_postfix_long = "what is its size"
    if size_prefix in text or size_prefix_long in text or size_prefix_long_2 in text:
        text = text.replace(size_prefix_long_2, GET_SIZE_TOKEN)
        text = text.replace(size_prefix_long, GET_SIZE_TOKEN)
        text = text.replace(size_prefix, GET_SIZE_TOKEN)
        
    elif size_postfix in text or size_postfix_long in text or size_postfix_2 in text:
        text = text.replace("there is a", "")
        text = text.replace("the", "")
        text = text.replace(size_postfix, "")
        text = text.replace(size_postfix_2, "")
        text = text.replace(size_postfix_long, "")
        text = GET_SIZE_TOKEN + text
    return text

def translate_and_remove_relation_queries(text):
    for relation in ["behind", "left", "front", "right"]:
        for context in ["that is {} the", "that are {} the", "are {} the", "is {} the", "{} the"]:
            relation_context = context.format(relation)
            if relation_context in text:
                text = text.replace(relation_context, f"{relation.upper()}_OF ")
    return text

def translate_zero_hop_text(text):
    # There are two forms for each question.
    text = pad_text(text)
    # Count questions.
    text = translate_and_remove_count_queries(text)
    text = translate_and_remove_shape_queries(text)
    text = translate_and_remove_material_queries(text)
    text = translate_and_remove_size_queries(text)
    text = translate_and_remove_color_queries(text)
    text = translate_constants(text)
    return remove_extraneous_spaces(text)
    
def translate_one_hop_text(text):
    # There are two forms for each question.
    text = pad_text(text)
    text = translate_and_remove_relation_queries(text)
    return translate_zero_hop_text(text) 

def translate_same_relate_restricted_text(text):
    text = pad_text(text)
    # Break the text around the word "same"
    split_on_same = text.split(" same ")
    assert len(split_on_same) == 2
    same_query = split_on_same[1]
    same_query = "_" + same_query
    for attribute in ["_color", "_size", "_shape", "_material"]:
        same_query = same_query.replace(attribute, f" GET{attribute.upper()} SAME ")
    text = same_query + split_on_same[0]
    
    for count in ["how many", "what number"]:
        text = text.replace(count, COMMA_TOKEN + COUNT_TOKEN)
    for get_shape in ["shape"]:
        text = text.replace(get_shape, COMMA_TOKEN +  GET_SHAPE_TOKEN)
    
    text = text.replace("made of the", "")
    for get_material in ["material", "made of"]:
        text = text.replace(get_material,COMMA_TOKEN +  GET_MATERIAL_TOKEN)
    
    text = translate_constants(text)
    text = " ".join([token for token in text.split() if token.isupper() or token == ","])
    return remove_extraneous_spaces(text)
    