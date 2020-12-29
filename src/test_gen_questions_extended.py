import gen_questions_extended as to_test

import os
from types import SimpleNamespace as MockArgs

def set_random_seed():
    RANDOM_SEED = 0
    mock_args = MockArgs(random_seed=RANDOM_SEED)
    gen_questions_n_inputs.set_random_seed(mock_args)

def get_default_metadata():
    mock_args = MockArgs(metadata_file=to_test.DEFAULT_EXTENDED_QUESTION_METADATA)
    metadata = to_test.get_question_metadata(mock_args)
    return metadata

def get_default_grouped_scenes():
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    scenes_file, all_scenes, scene_info, grouped_scenes_file, grouped_scenes = to_test.get_input_scenes_and_grouped_scenes(mock_args)
    return grouped_scenes

def get_default_localization_question_template():
    return {"text": ["Find the <Z> <C> <M> <S>."], "nodes": [{"inputs": [], "type": "scene"}, {"side_inputs": ["<Z>", "<C>", "<M>", "<S>"], "inputs": [0], "type": "filter"}], "constraints": {}, "group": "unique", "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}]}

def get_default_transformation_question_template_choose_some():
    return {"text": ["What if the <Z> <C> <M> <S> became a <Z2> <C2> <M2> <S2>?"], "nodes": [{"inputs": [], "type": "scene"}, {"side_inputs": ["<Z>", "<C>", "<M>", "<S>"], "inputs": [0], "type": "filter"}, {"side_inputs": ["<Z2>", "<C2>", "<M2>", "<S2>"], "inputs": [0, 1], "type": "transform"}], "constraints": [], "group": "unique", "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}]}

def get_default_transformation_question_template_choose_all():
    return {"text": ["If all of the <Z> <C> <M> <S>s became <Z2>, how many <Z> things would there be?"], "nodes": [{"inputs": [], "type": "scene"}, {"side_inputs": ["<Z>", "<C>", "<M>", "<S>"], "inputs": [0], "type": "filter"}, {"side_inputs": ["<Z2>"], "inputs": [0, 1], "type": "transform"}, {"side_inputs": ["<Z>"], "inputs": [2], "type": "filter_size"}, {"inputs": [3], "type": "count"}], "constraints": {"transform": "choose_all", "<Z>": "instantiated"}, "group": "multiple", "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}]}

def get_default_remove_question_template():
    return {"text": ["If you removed the <C> things, how many <S>s would be left?"], "nodes": [{"inputs": [], "type": "scene"}, {"side_inputs": ["<C>"], "inputs": [0], "type": "filter"}, {"inputs": [0, 1], "type": "remove"}, {"side_inputs": ["<S>"], "inputs": [2], "type": "filter_shape"}, {"inputs": [3], "type": "count"}], "constraints": {"filter": "choose_exactly"}, "group": "multiple", "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}]}
    
def test_get_input_scenes_and_grouped_scenes_default_train():
    """Tests that we get the default set of training and grouped scenes when no other input scenes are provided."""
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    scenes_file, all_scenes, scene_info, grouped_scenes_file, grouped_scenes = to_test.get_input_scenes_and_grouped_scenes(mock_args)
    
    assert scenes_file == to_test.DEFAULT_TRAIN_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'train'
    
    assert grouped_scenes_file == to_test.DEFAULT_GROUPED_TRAIN_SCENES
    assert to_test.UNIQUE in grouped_scenes
    assert to_test.MULTIPLE in grouped_scenes
    
def test_get_input_scenes_and_grouped_scenes_default_val(): 
    mock_args = MockArgs(default_train_scenes=False,
    default_val_scenes=True)
    scenes_file, all_scenes, scene_info, grouped_scenes_file, grouped_scenes = to_test.get_input_scenes_and_grouped_scenes(mock_args)
    
    assert scenes_file == to_test.DEFAULT_VAL_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'val'
    
    assert grouped_scenes_file == to_test.DEFAULT_GROUPED_VAL_SCENES
    assert to_test.UNIQUE in grouped_scenes
    assert to_test.MULTIPLE in grouped_scenes
    
def test_get_input_scenes_and_grouped_scenes_other_file_success():
    mock_args = MockArgs(default_train_scenes=False,
    default_val_scenes=False,
    input_scene_file=to_test.DEFAULT_VAL_SCENES,
    input_grouped_scene_file=to_test.DEFAULT_GROUPED_VAL_SCENES)
    scenes_file, all_scenes, scene_info, grouped_scenes_file, grouped_scenes = to_test.get_input_scenes_and_grouped_scenes(mock_args)
    
    assert scenes_file == to_test.DEFAULT_VAL_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'val'
    
    assert grouped_scenes_file == to_test.DEFAULT_GROUPED_VAL_SCENES
    assert to_test.UNIQUE in grouped_scenes
    assert to_test.MULTIPLE in grouped_scenes
    
def test_get_input_scenes_and_grouped_scenes_other_file_failure():
    threw_error = False
    try:
        mock_args = MockArgs(default_train_scenes=False,
        default_val_scenes=False,
        input_scene_file=to_test.DEFAULT_TRAIN_SCENES,
        input_grouped_scene_file=to_test.DEFAULT_GROUPED_VAL_SCENES)
        scenes_file, all_scenes, scene_info, grouped_scenes_file, grouped_scenes = to_test.get_input_scenes_and_grouped_scenes(mock_args)
    except:
        threw_error = True
    assert threw_error
        
def test_get_question_metadata():
    """Tests how we load the metadata file that specifies the types of the question ground truth functions, which are extended for these templates."""
    mock_args = MockArgs(metadata_file=to_test.DEFAULT_EXTENDED_QUESTION_METADATA)
    metadata = to_test.get_question_metadata(mock_args)
    
    assert metadata['dataset'] == 'CLEVR-extended-v1.0'
    assert to_test.PRIMITIVE_REMOVE in metadata['_functions_by_name']
    assert to_test.PRIMITIVE_TRANSFORM in metadata['_functions_by_name']
    
def test_get_question_templates_one_template():
    """Tests how we load the question templates for a single specified template file."""
    metadata = get_default_metadata()
    
    single_template = ['2_remove']
    mock_args = MockArgs(template_dir=to_test.DEFAULT_EXTENDED_TEMPLATES_DIR, question_templates=single_template)

    templates = to_test.get_question_templates(mock_args,metadata)
    
    assert len(templates) == len(single_template)
    for curr_template_file in single_template:
        question_templates = templates[curr_template_file]
        for (template_file, question_idx) in question_templates:
            assert curr_template_file == template_file
            assert type(question_idx) == int
    
def test_get_question_template_all_templates():
    metadata = get_default_metadata()
    
    all_template_files = os.listdir(to_test.DEFAULT_EXTENDED_TEMPLATES_DIR)
    all_templates = [candidate_template_file.split('.json')[0] for candidate_template_file in all_template_files]
    
    mock_args = MockArgs(template_dir=to_test.DEFAULT_EXTENDED_TEMPLATES_DIR, question_templates=[to_test.GENERATE_ALL_FLAG])

    templates = to_test.get_question_templates(mock_args,metadata)
    
    assert len(templates) == len(all_templates)
    for curr_template_file in all_templates:
        question_templates = templates[curr_template_file]
        for (template_file, question_idx) in question_templates:
            assert curr_template_file == template_file
            assert type(question_idx) == int

def test_build_filter_option():
    grouped_input_scenes = get_default_grouped_scenes()
    template = get_default_localization_question_template()
    
    # Extract the filter node
    filter_node_object = [(node_index, node) for (node_index, node) in enumerate(template['nodes']) if node['type'] == to_test.PRIMITIVE_FILTER]
    original_idx, filter_node = filter_node_object[0]
    new_node_idxs = {i : i for i in range(len(template['nodes']))}
    current_node_index = 10 # Artificially extend to test that we can modify this accordingly.
    
    filter_program, input_scenes = to_test.build_filter_option(grouped_input_scenes=grouped_input_scenes, filter_node=filter_node, constraints=template["constraints"], group=template['group'], params=template['params'], original_idx=original_idx, curr_node_idx=current_node_index, new_node_idxs=new_node_idxs)

    filter_options = input_scenes["filter_options"]
    assert len(filter_program) == len(filter_options)
    possible_filter_types = [f"filter_{attr_type.lower()}" for (attr_type, attr_value) in filter_options]
    possible_filter_values = [attr_value for (attr_type, attr_value) in filter_options]
    for index, filter_program_node in enumerate(filter_program):
        if index == 0:
            assert filter_program_node['inputs'] == [0] # Directly from the scene
        else:
            assert filter_program_node['inputs'] == [current_node_index + index - 1]
        assert filter_program_node['type'] in possible_filter_types
        assert len(filter_program_node['side_inputs']) == 1
        assert filter_program_node['side_inputs'][0] in possible_filter_values
        
    # Make sure we changed the node indices
    assert new_node_idxs[original_idx] == current_node_index + len(filter_options) - 1

def test_build_transform_option_choose_some():
    """Test the transformations for a question where we also randomly sample a subset of possible attributes to transform."""
    metadata = get_default_metadata()
    template = get_default_transformation_question_template_choose_some()
    
    # Extract the transform node
    transform_node_object = [(node_index, node) for (node_index, node) in enumerate(template['nodes']) if node['type'] == to_test.PRIMITIVE_TRANSFORM]
    original_idx, transform_node = transform_node_object[0]
    new_node_idxs = {i : i for i in range(len(template['nodes']))}
    current_node_index = 10 # Artificially extend to test that we can modify this accordingly.
    
    transform_program = to_test.build_transform_option(transform_node=transform_node, constraints=template["constraints"], metadata=metadata, params=template['params'], original_idx=original_idx, curr_node_idx=current_node_index, new_node_idxs=new_node_idxs)

    assert len(transform_program) > 0
    candidate_params = [param for param in template['params'] if param['name'] in transform_node['side_inputs']]
    instantiated_params = [param for param in candidate_params if "value" in param]
    assert len(transform_program) == len(instantiated_params)
    
    possible_transform_types = [f"transform_{param['type'].lower()}" for param in instantiated_params]
    possible_transform_values = [param['value'] for param in instantiated_params]
    
    for index, transform_program_node in enumerate(transform_program):
        assert len(transform_program_node['inputs']) == 2
        if index == 0:
            assert transform_program_node['inputs'][0] == 0 # Directly from the scene
        else:
            assert transform_program_node['inputs'][0] == current_node_index + index - 1
        assert transform_program_node['type'] in possible_transform_types
        assert len(transform_program_node['side_inputs']) == 1
        assert transform_program_node['side_inputs'][0] in possible_transform_values
        
    # Make sure we changed the node indices
    assert new_node_idxs[original_idx] == current_node_index + len(transform_program) - 1


def test_build_transform_option_choose_all():
    """Test the transformations for a question where we must transform a given number of parameters."""
    """Test the transformations for a question where we also randomly sample a subset of possible attributes to transform."""
    metadata = get_default_metadata()
    template = get_default_transformation_question_template_choose_all()
    
    # Extract the transform node
    transform_node_object = [(node_index, node) for (node_index, node) in enumerate(template['nodes']) if node['type'] == to_test.PRIMITIVE_TRANSFORM]
    original_idx, transform_node = transform_node_object[0]
    new_node_idxs = {i : i for i in range(len(template['nodes']))}
    current_node_index = 10 # Artificially extend to test that we can modify this accordingly.
    
    transform_program = to_test.build_transform_option(transform_node=transform_node, constraints=template["constraints"], metadata=metadata, params=template['params'], original_idx=original_idx, curr_node_idx=current_node_index, new_node_idxs=new_node_idxs)

    assert len(transform_program) == 1
    candidate_params = [param for param in template['params'] if param['name'] in transform_node['side_inputs']]
    instantiated_params = [param for param in candidate_params if "value" in param]
    assert len(transform_program) == len(instantiated_params)
    
    possible_transform_types = [f"transform_{param['type'].lower()}" for param in instantiated_params]
    possible_transform_values = [param['value'] for param in instantiated_params]
    
    for index, transform_program_node in enumerate(transform_program):
        assert len(transform_program_node['inputs']) == 2
        if index == 0:
            assert transform_program_node['inputs'][0] == 0 # Directly from the scene
        else:
            assert transform_program_node['inputs'][0] == current_node_index + index - 1
        assert transform_program_node['type'] in possible_transform_types
        assert len(transform_program_node['side_inputs']) == 1
        assert transform_program_node['side_inputs'][0] in possible_transform_values
        
    # Make sure we changed the node indices
    assert new_node_idxs[original_idx] == current_node_index + len(transform_program) - 1

def test_build_other_instantiated_program_node_remove():
    metadata = get_default_metadata()
    template = get_default_remove_question_template()
    
    # Extract the filter shape node that determines what we will remove
    remove_node_object = [(node_index, node) for (node_index, node) in enumerate(template['nodes']) if node['type'] == "filter_shape"]
    original_idx, remove_node = remove_node_object[0]
    num_params_to_instantiate = len(remove_node['side_inputs'])
    new_node_idxs = {i : i for i in range(len(template['nodes']))}
    current_node_index = 10 # Artificially extend to test that we can modify this accordingly.
    
    remove_program = to_test.build_other_instantiated_program_node(other_node=remove_node, metadata=metadata, params=template['params'], original_idx=original_idx, curr_node_idx=current_node_index, new_node_idxs=new_node_idxs)
    
    instantiated_params = [param for param in template['params'] if "value" in param]
    instantiated_param_values = [param['value'] for param in instantiated_params]
    assert len(instantiated_params) == num_params_to_instantiate
    
    assert len(remove_program) == 1
    instantiated_node = remove_program[0]
    assert instantiated_node['type'] == "filter_shape"
    for param in instantiated_node['side_inputs']:
        assert param in instantiated_param_values
    
    # Make sure we changed the node indices
    assert new_node_idxs[original_idx] == current_node_index + len(remove_program) - 1


def test_instantiate_extended_template_from_grouped_scenes_localization():
    """Test the instantiation of a template that requires localization: filtering down a set of initial objects to a set that satisfies one or more attributes."""
    pass

def test_instantiate_extended_template_from_grouped_scenes_remove():
    """Test the instantiation of a template that requires remove: filtering down a set of initial objects to a set that satisfies one or more attributes, then removing them."""
    
def test_instantiate_extended_template_from_grouped_scenes_transform():
    """Test the instantiation of a template that requires transform: filtering down a set of initial objects to a set that satisfies one or more attributes, then removing them."""
    pass


def test_instantiate_templates_extended():
    pass
def test_generate_questions_for_template_file():
    pass
def test_generate_questions_for_all_template_files():
    pass 
def test_integration_main(tmpdir):
    pass