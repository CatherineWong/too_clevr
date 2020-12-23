import gen_n_inputs
import os
import json
from types import SimpleNamespace as MockArgs

def get_default_metadata():
    mock_args = MockArgs(metadata_file=gen_n_inputs.DEFAULT_QUESTION_METADATA)
    metadata = gen_n_inputs.get_question_metadata(mock_args)
    return metadata

def get_default_scenes():
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    scene_file, all_scenes, scene_info = gen_n_inputs.get_initial_input_scenes(mock_args)
    return all_scenes

def get_default_grouping_template():
    return {"text": ["What shape is the <Z> <C> <M> <S>?"], "nodes": [{"inputs": [], "type": "scene"}, {"side_inputs": ["<Z>", "<C>", "<M>", "<S>"], "inputs": [0], "type": "filter_unique"}, {"inputs": [1], "type": "query_shape"}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}], "constraints": [{"params": ["<S>"], "type": "NULL"}]}

def get_default_all_grouping_templates():
    return {
        "unique": [get_default_grouping_template(), get_default_grouping_template()],
        "multiple": [get_default_grouping_template()]
    }

def get_default_filter_program():
    return [{'type': 'scene', 'inputs': [], '_output': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'side_inputs': []}, {'type': 'filter_color', 'inputs': [0], '_output': [0], 'side_inputs': ['red']}, {'type': 'unique', 'inputs': [1], '_output': 0}, {'type': 'query_shape', 'inputs': [2], '_output': 'sphere'}]

def test_get_input_scenes_default_train():
    """Tests that we get the default set of training scenes when no other input scenes are provided."""
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    scene_file, all_scenes, scene_info = gen_n_inputs.get_initial_input_scenes(mock_args)
    
    assert scene_file == gen_n_inputs.DEFAULT_TRAIN_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'train'
     
def test_get_input_scenes_default_val(): 
    """Tests that we get the default set of validation scenes when no other input scenes are provided."""
    mock_args = MockArgs(default_train_scenes=False,
    default_val_scenes=True)
    scene_file, all_scenes, scene_info = gen_n_inputs.get_initial_input_scenes(mock_args)
    
    assert scene_file == gen_n_inputs.DEFAULT_VAL_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'val'
    
def test_get_input_scenes_default_other(): 
    """Tests that we do use a specific set of scenes when specified."""
    mock_args = MockArgs(default_train_scenes=False,
    default_val_scenes=False, input_scene_file=gen_n_inputs.DEFAULT_VAL_SCENES)
    scene_file, all_scenes, scene_info = gen_n_inputs.get_initial_input_scenes(mock_args)
    
    assert scene_file == gen_n_inputs.DEFAULT_VAL_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'val'

def test_get_question_metadata():
    """Tests how we load the metadata file that specifies the types of the question ground truth functions."""
    mock_args = MockArgs(metadata_file=gen_n_inputs.DEFAULT_QUESTION_METADATA)
    metadata = gen_n_inputs.get_question_metadata(mock_args)
    
    assert metadata['dataset'] == 'CLEVR-v1.0'
    assert len(metadata['_functions_by_name']) == 35

def test_get_grouping_templates():
    mock_args =         MockArgs(grouping_template_file=gen_n_inputs.DEFAULT_GROUPING_TEMPLATE_FILE)
    all_grouping_templates = gen_n_inputs.get_grouping_templates(mock_args)
 
    for template_type in all_grouping_templates:
        assert template_type in gen_n_inputs.GROUPING_TEMPLATE_TYPES
        grouping_templates = all_grouping_templates[template_type]
        for grouping_template in grouping_templates:
            assert "nodes" in grouping_template
            program = grouping_template["nodes"]
            assert program[0]["type"] == "scene"
            assert (program[1]["type"] == "filter_unique") or (program[1]["type"] == "filter_count")

def test_instantiate_template_with_filter_options():
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    default_template = get_default_grouping_template()
    max_time = 100
    max_instances = 5
    n_scenes_per_question = 5
    
    instantiated_questions_with_filters = gen_n_inputs.instantiate_template_with_filter_options(all_scenes,
                                                default_template,
                                                metadata,
                                                max_time,
                                                max_instances,
                                                n_scenes_per_question)
    assert len(instantiated_questions_with_filters) == max_instances
    for question_text in instantiated_questions_with_filters:
        question_filter_tuples = instantiated_questions_with_filters[question_text]
        assert len(question_filter_tuples) == n_scenes_per_question
        for (scene, filter_options, filter_program) in question_filter_tuples:
            # Check that the scene is a scene.
            assert "image_index" in scene
            assert "objects" in scene
            
            assert type(filter_options) == type(("tuple",))
            assert type(filter_program) == type([])
    
def test_extract_filter_options():
    test_program = get_default_filter_program()
    filter_options, filter_program = gen_n_inputs.extract_filter_options(test_program)
    
    assert type(filter_options) == type(('tuple',))
    assert filter_options == (('Color', 'red'),)
    assert filter_program[0]['type'] == "scene"
    assert filter_program[1]['type'] == 'filter_color'
    
def test_generate_grouped_scenes_for_question_template():
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    default_template = get_default_grouping_template()
    max_time = 100
    max_instances = 5
    n_scenes_per_question = 5
    current_grouped_scene_index = 10 # Start at not 0 so we can check the indexing.
    updated_grouped_scene_index, grouped_scenes = gen_n_inputs.generate_grouped_scenes_for_question_template(
        all_scenes,
        default_template,
        metadata,
        max_time,
        max_instances,
        n_scenes_per_question,
        current_grouped_scene_index)
    
    assert updated_grouped_scene_index == current_grouped_scene_index + max_instances
    
    for grouped_scene_index in range(current_grouped_scene_index, current_grouped_scene_index + max_instances):
        grouped_scene_object = grouped_scenes[grouped_scene_index]
        assert len(grouped_scene_object['input_image_filenames']) == n_scenes_per_question
        assert len(grouped_scene_object['input_image_indexes']) == n_scenes_per_question
        filter_programs = grouped_scene_object['filter_programs']
        assert len(filter_programs) == n_scenes_per_question
        for filter_program in filter_programs:
            assert len(filter_program) >= 2
            assert filter_program[1]['type'].startswith('filter')
        assert len(grouped_scene_object['filter_options']) > 0

def test_generate_grouped_scenes_for_all_question_templates():
    max_time = 100
    max_instances = 5
    n_scenes_per_question = 5
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    default_all_grouping_templates = get_default_all_grouping_templates()
    
    mock_args = MockArgs(
        instances_per_template = max_instances,
        max_time_to_instantiate = max_time,
        n_scenes_per_question = n_scenes_per_question
    )
    
    all_grouped_scenes = gen_n_inputs.generate_grouped_scenes_for_all_question_templates(mock_args, default_all_grouping_templates, all_scenes, metadata)
    
    for grouping_template_type in gen_n_inputs.GROUPING_TEMPLATE_TYPES:
        assert grouping_template_type in all_grouped_scenes
    unique_grouped_scenes = all_grouped_scenes[gen_n_inputs.UNIQUE]
    multiple_grouped_scenes = all_grouped_scenes[gen_n_inputs.MULTIPLE]
    assert len(unique_grouped_scenes) == len(multiple_grouped_scenes)
    assert len(unique_grouped_scenes) > 0
    
    # Check one of them.
    for scene_index, grouped_scene_object in unique_grouped_scenes.items():
        assert scene_index >= 0
        assert len(grouped_scene_object['filter_options']) > 0
        assert len(grouped_scene_object['input_image_filenames']) == n_scenes_per_question
        
def test_integration_main(tmpdir):
    TEST_PREFIX = "TEST"
    GOLD_FILE_NAMES = [f"{TEST_PREFIX}_CLEVR_train_scenes_5000.json"] # From the basename of the input file.
    mock_args = MockArgs(
        random_seed=0,
        default_train_scenes=True,
        default_val_scenes=False,
        input_scene_file=None,
        metadata_file=gen_n_inputs.DEFAULT_QUESTION_METADATA,
        grouping_template_file=gen_n_inputs.DEFAULT_GROUPING_TEMPLATE_FILE,
        instances_per_template=5,
        n_scenes_per_question=5,
        max_time_to_instantiate=100,
        output_scenes_directory=tmpdir,
        output_scenes_prefix=TEST_PREFIX,
    )
    gen_n_inputs.main(mock_args)
    
    files_in_dir = os.listdir(tmpdir)
    assert len(files_in_dir) == len(GOLD_FILE_NAMES)
    for filename in GOLD_FILE_NAMES:
        assert filename in files_in_dir
    
    for filename in GOLD_FILE_NAMES:
        with open(os.path.join(tmpdir, filename), 'r') as f:
            grouped_scenes = json.load(f)['grouped_scenes']
            
            assert gen_n_inputs.UNIQUE in grouped_scenes
            assert gen_n_inputs.MULTIPLE in grouped_scenes
            