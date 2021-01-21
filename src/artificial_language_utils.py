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