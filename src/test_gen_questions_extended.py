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
def test_instantiate_templates_extended():
    pass
def test_generate_questions_for_template_file():
    pass
def test_generate_questions_for_all_template_files():
    pass 
def test_integration_main(tmpdir):
    pass