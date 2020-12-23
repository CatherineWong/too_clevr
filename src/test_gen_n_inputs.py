import gen_n_inputs
from types import SimpleNamespace as MockArgs

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

# def test_generate_grouped_scenes_for_question_template():
# 
# def test_generate_grouped_scenes_for_all_question_templates():
# 
# def test_integration_main():
    
    