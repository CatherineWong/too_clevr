import os
import json
import gen_questions_n_inputs 
from types import SimpleNamespace as MockArgs
def get_default_metadata():
    mock_args = MockArgs(metadata_file=gen_questions_n_inputs.DEFAULT_QUESTION_METADATA)
    metadata = gen_questions_n_inputs.get_question_metadata(mock_args)
    return metadata

def get_default_scenes():
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    scene_file, all_scenes, scene_info = gen_questions_n_inputs.get_input_scenes(mock_args)
    return all_scenes

def get_default_question_template():
    return {"text": ["How many <Z> <C> <M> <S>s are there?", "What number of <Z> <C> <M> <S>s are there?"], "nodes": [{"inputs": [], "type": "scene"}, {"side_inputs": ["<Z>", "<C>", "<M>", "<S>"], "inputs": [0], "type": "filter_count"}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}], "constraints": []}

def get_default_question_template_file(mock_filename='mock_template_fn'):
    return mock_filename, {
        (mock_filename, 0) : get_default_question_template(),
        (mock_filename, 1) : get_default_question_template(),
    }

def get_default_multiple_question_template_files():
    MOCK_FILENAME_BASE = "mock_template_fn"
    question_templates = dict()
    for filename_idx in [1,2]:
        mock_filename = f"{MOCK_FILENAME_BASE}_{filename_idx}"
        _, question_template = get_default_question_template_file(mock_filename)
        question_templates[mock_filename] = question_template
    return question_templates

def set_random_seed():
    RANDOM_SEED = 0
    mock_args = MockArgs(random_seed=RANDOM_SEED)
    gen_questions_n_inputs.set_random_seed(mock_args)

def test_get_input_scenes_default_train():
    """Tests that we get the default set of training scenes when no other input scenes are provided."""
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    scene_file, all_scenes, scene_info = gen_questions_n_inputs.get_input_scenes(mock_args)
    
    assert scene_file == gen_questions_n_inputs.DEFAULT_TRAIN_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'train'
     
def test_get_input_scenes_default_val(): 
    """Tests that we get the default set of validation scenes when no other input scenes are provided."""
    mock_args = MockArgs(default_train_scenes=False,
    default_val_scenes=True)
    scene_file, all_scenes, scene_info = gen_questions_n_inputs.get_input_scenes(mock_args)
    
    assert scene_file == gen_questions_n_inputs.DEFAULT_VAL_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'val'
    
def test_get_input_scenes_default_other(): 
    """Tests that we do use a specific set of scenes when specified."""
    mock_args = MockArgs(default_train_scenes=False,
    default_val_scenes=False, input_scene_file=gen_questions_n_inputs.DEFAULT_VAL_SCENES)
    scene_file, all_scenes, scene_info = gen_questions_n_inputs.get_input_scenes(mock_args)
    
    assert scene_file == gen_questions_n_inputs.DEFAULT_VAL_SCENES
    assert len(all_scenes) == 5000
    assert scene_info['split'] == 'val'

def test_get_question_metadata():
    """Tests how we load the metadata file that specifies the types of the question ground truth functions."""
    mock_args = MockArgs(metadata_file=gen_questions_n_inputs.DEFAULT_QUESTION_METADATA)
    metadata = gen_questions_n_inputs.get_question_metadata(mock_args)
    
    assert metadata['dataset'] == 'CLEVR-v1.0'
    assert len(metadata['_functions_by_name']) == 35
    assert len(metadata['_boolean_fns']) == 11

def test_get_question_templates_one_template():
    """Tests how we load the question templates for a single specified template file."""
    metadata = get_default_metadata()
    
    single_template = ['1_zero_hop']
    mock_args = MockArgs(no_boolean=1,
    template_dir=gen_questions_n_inputs.DEFAULT_ORIGINAL_TEMPLATES_DIR, question_templates=single_template)

    templates = gen_questions_n_inputs.get_question_templates(mock_args,metadata)
    
    assert len(templates) == len(single_template)
    for curr_template_file in single_template:
        question_templates = templates[curr_template_file]
        for (template_file, question_idx) in question_templates:
            assert curr_template_file == template_file
            assert type(question_idx) == int
    

def test_get_question_templates_restricted_questions():
    """Tests how we load the question templates for a single specified template file where we only generate some of the questions by default."""
    metadata = get_default_metadata()
    
    single_template = ['1_single_or']
    mock_args = MockArgs(no_boolean=1,
    template_dir=gen_questions_n_inputs.DEFAULT_ORIGINAL_TEMPLATES_DIR, question_templates=single_template)

    templates = gen_questions_n_inputs.get_question_templates(mock_args,metadata)
    
    # We only read a subset of the question templates for this file.
    restricted_question_templates = gen_questions_n_inputs.TEMPLATE_RESTRICTED_QUESTIONS[single_template[0]]
    
    assert len(templates) == len(single_template)
    for curr_template_file in single_template:
        question_templates = templates[curr_template_file]
        assert len(question_templates) == len(restricted_question_templates)
        for (template_file, question_idx) in question_templates:
            assert curr_template_file == template_file
            assert type(question_idx) == int

def test_get_question_template_n_templates():
    """Tests how we load the question templates for a set of question template files."""
    metadata = get_default_metadata()
    
    single_template = ['1_zero_hop', '1_one_hop']
    mock_args = MockArgs(no_boolean=1,
    template_dir=gen_questions_n_inputs.DEFAULT_ORIGINAL_TEMPLATES_DIR, question_templates=single_template)

    templates = gen_questions_n_inputs.get_question_templates(mock_args,metadata)
    
    assert len(templates) == len(single_template)
    for curr_template_file in single_template:
        question_templates = templates[curr_template_file]
        for (template_file, question_idx) in question_templates:
            assert curr_template_file == template_file
            assert type(question_idx) == int

def test_instantiate_templates_dfs_multiple_scenes():
    set_random_seed()
    
    max_instances = 2 
    n_scenes_per_question = 5
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    max_time = 100 # Time to try finding a scene.

    TEST_QUESTION_TEMPLATE = get_default_question_template()
    
    instantiated_questions = gen_questions_n_inputs.instantiate_templates_dfs_multiple_inputs(all_scenes=all_scenes,
    template=TEST_QUESTION_TEMPLATE,
    metadata=metadata,
    max_time=max_time,
    max_instances=max_instances,
    n_scenes_per_question=n_scenes_per_question,
    answer_counts=None)
    
    assert(len(instantiated_questions) == max_instances)
    for question_text in instantiated_questions:
        assert len(instantiated_questions[question_text]) == n_scenes_per_question

def test_postprocess_instantiated_questions():
    set_random_seed()
    
    # Instantiate a set of questions.
    max_instances = 2 
    n_scenes_per_question = 5
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    max_time = 100 # Time to try finding a scene.

    TEST_QUESTION_TEMPLATE = get_default_question_template()
    
    instantiated_questions = gen_questions_n_inputs.instantiate_templates_dfs_multiple_inputs(all_scenes=all_scenes,
    template=TEST_QUESTION_TEMPLATE,
    metadata=metadata,
    max_time=max_time,
    max_instances=max_instances,
    n_scenes_per_question=n_scenes_per_question,
    answer_counts=None)
    
    SPLIT = 'split'
    TEMPLATE_FILENAME = "test_template"
    TEMPLATE_INDEX = 10
    postprocessed_questions = gen_questions_n_inputs.postprocess_instantiated_questions(instantiated_questions,
    dataset_split=SPLIT, template_filename=TEMPLATE_FILENAME,
    template_index=TEMPLATE_INDEX)
    
    assert len(postprocessed_questions) == max_instances
    for question in postprocessed_questions:
            assert question['split'] == SPLIT
            assert question['question'] in instantiated_questions
            assert question['template_filename'] == TEMPLATE_FILENAME
            assert question['template_index'] ==     TEMPLATE_INDEX
            assert len(question['answers']) == n_scenes_per_question
            assert len(question['image_filenames']) == n_scenes_per_question
            assert len(question['image_indices']) == n_scenes_per_question

def test_generate_questions_for_template_file():
    set_random_seed()
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    
    mock_filename, mock_templates = get_default_question_template_file()
    SPLIT = 'split'
    INSTANCES_PER_TEMPLATE = 2 
    N_SCENES_PER_QUESTION = 5
    mock_args = MockArgs(
        max_generation_tries_per_instantiation=2,
        max_time_to_instantiate=100,
        instances_per_template=INSTANCES_PER_TEMPLATE,
        n_scenes_per_question=N_SCENES_PER_QUESTION,
    )
    training_text_questions = {mock_filename : []}
    
    generated_questions = gen_questions_n_inputs.generate_questions_for_template_file(args=mock_args,
        templates_for_file=mock_templates,
        dataset_split=SPLIT,
        metadata=metadata,
        all_scenes=all_scenes,
        training_text_questions=training_text_questions)
    
    assert len(generated_questions) == INSTANCES_PER_TEMPLATE * len(mock_templates)
    
    for question_index, question in enumerate(generated_questions):
        assert question['question_index'] == question_index
    
    
def test_generate_questions_for_all_template_files():
    set_random_seed()
    all_scenes = get_default_scenes()
    metadata = get_default_metadata()
    
    mock_templates = get_default_multiple_question_template_files()
    SPLIT = 'split'
    INSTANCES_PER_TEMPLATE = 2 
    N_SCENES_PER_QUESTION = 5
    mock_args = MockArgs(
        max_generation_tries_per_instantiation=2,
        max_time_to_instantiate=100,
        instances_per_template=INSTANCES_PER_TEMPLATE,
        n_scenes_per_question=N_SCENES_PER_QUESTION,
    )
    
    # Generate mock training test questions
    training_text_questions = {template_filename : [] for template_filename in mock_templates}
    
    generated_questions_dict = gen_questions_n_inputs.generate_questions_for_all_template_files(mock_args,mock_templates,SPLIT, metadata, all_scenes, training_text_questions)
    
    for template_fn in generated_questions_dict:
        assert template_fn in mock_templates
        generated_questions = generated_questions_dict[template_fn]
        
        for question_index, question in enumerate(generated_questions):
            assert question['question_index'] == question_index
            assert question['template_filename'] == template_fn

def test_integration_main(tmpdir):
    INSTANCES_PER_TEMPLATE = 2
    N_SCENES_PER_QUESTION = 2
    OUTPUT_QUESTIONS_PREFIX = "TEST"
    QUESTION_TEMPLATES = ["1_zero_hop", "1_one_hop"]
    GOLD_FILE_NAMES = [f"{OUTPUT_QUESTIONS_PREFIX}_train_{template_fn}.json" for template_fn in QUESTION_TEMPLATES]
    mock_args = MockArgs(
        random_seed=0,
        default_train_scenes=True,
        default_val_scenes=False,
        input_scene_file=None,
        metadata_file=gen_questions_n_inputs.DEFAULT_QUESTION_METADATA,
        template_dir=gen_questions_n_inputs.DEFAULT_ORIGINAL_TEMPLATES_DIR,
        question_templates=QUESTION_TEMPLATES,
        max_generation_tries_per_instantiation=2,
        max_time_to_instantiate=100,
        instances_per_template=INSTANCES_PER_TEMPLATE,
        n_scenes_per_question=N_SCENES_PER_QUESTION,
        no_boolean=0,
        output_questions_prefix=OUTPUT_QUESTIONS_PREFIX,
        output_questions_directory=tmpdir
    )
    gen_questions_n_inputs.main(mock_args)
    
    files_in_dir = os.listdir(tmpdir)
    assert len(files_in_dir) == len(GOLD_FILE_NAMES)
    for filename in GOLD_FILE_NAMES:
        assert filename in files_in_dir
    
    for filename in GOLD_FILE_NAMES:
        with open(os.path.join(tmpdir, filename), 'r') as f:
            questions = json.load(f)['questions']
            assert type(questions) == type([])
            assert len(questions) == 9
            test_question = questions[0]
            assert test_question['split'] == 'train'
            assert test_question['template_filename'] in QUESTION_TEMPLATES
            assert len(test_question['answers']) == N_SCENES_PER_QUESTION