"""
test_gen_distractor_output_scenes.py | Author: Catherine Wong
"""
import gen_distractor_output_scenes as to_test
import os
import json
from types import SimpleNamespace as MockArgs

TEST_DEFAULT_INPUT_QUESTIONS_DIR = "../data/clevr_icml_2021_no_string/questions"
def set_random_seed():
    RANDOM_SEED = 0
    mock_args = MockArgs(random_seed=RANDOM_SEED)
    to_test.set_random_seed(mock_args)

def get_default_all_scenes():
    mock_args = MockArgs(default_train_scenes=True,
    default_val_scenes=False)
    all_scenes = to_test.get_input_scenes(mock_args)
    return all_scenes

def get_default_localization_object():
    mock_args = MockArgs(question_classes=["2_localization"],
    input_questions_dir=TEST_DEFAULT_INPUT_QUESTIONS_DIR)
    for question_file in  to_test.get_question_files_and_metadata(mock_args):
        full_question_filepath = os.path.join(mock_args.input_questions_dir, question_file)
        with open(full_question_filepath, 'r') as f:
            input_questions_file_object = json.load(f)
            return input_questions_file_object

def get_default_single_input_answer_scene():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    default_question = default_question_file_object['questions'][0]
    assert type(default_question['answers'][0]) == type(dict())
    input_scene_idx = default_question['image_indices'][0]
    input_scene = default_all_scenes[input_scene_idx]
    true_answer = default_question['answers'][0]
    input_scene = to_test.add_object_ids_to_input(input_scene)
    return input_scene, true_answer
    
def test_check_differing_scenes():
    input_scene, true_answer = get_default_single_input_answer_scene()
    assert not to_test.check_differing_scenes(input_scene, input_scene)

def test_check_differing_scenes():
    input_scene, true_answer = get_default_single_input_answer_scene()
    assert to_test.check_differing_scenes(input_scene, true_answer)

def test_remove_some_random_objects_if_possible():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()
    removed_scene = to_test.remove_some_random_objects_if_possible(input_scene, true_answer)
    assert len(input_scene['objects']) > len(removed_scene['objects'])

def test_remove_some_random_objects_if_not_possible():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()
    input_scene['objects'] = input_scene['objects'][:2]
    removed_scene = to_test.remove_some_random_objects_if_possible(input_scene, true_answer)
    assert removed_scene is None

def test_transform_some_random_attribute():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()
    transformed_scene = to_test.transform_some_random_attribute(input_scene, true_answer)
    assert to_test.check_differing_scenes(transformed_scene, true_answer)

def test_gen_distractor_random_filter_input_scene():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()
    filtered_scene, attributes_to_keep = to_test.gen_distractor_random_filter_input_scene(input_scene, true_answer)
    assert len(filtered_scene['objects']) > 0
    assert to_test.check_differing_scenes(filtered_scene, input_scene)
    for obj in filtered_scene['objects']:
        for attribute, value in attributes_to_keep.items():
            assert obj[attribute] == value

def test_gen_distractor_random_remove_input_scene():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()
    filtered_scene, attributes_to_remove = to_test.gen_distractor_random_filter_input_scene(input_scene, true_answer)
    assert len(filtered_scene['objects']) > 0
    assert to_test.check_differing_scenes(filtered_scene, input_scene)
    for obj in filtered_scene['objects']:
        all_same = True
        for attribute, value in attributes_to_remove.items():
            all_same = False
        assert not all_same


def test_gen_distractor_random_transform_input_scene():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()
    filtered_scene, transform_info = to_test.gen_distractor_random_transform_input_scene(input_scene, true_answer)
    assert len(filtered_scene['objects']) == len(input_scene['objects'])

    (attribute_to_transform, transformed_value) = transform_info['transformed_to']
    assert to_test.check_differing_scenes(filtered_scene, input_scene)
    for obj in filtered_scene['objects']:
        all_same = True
        for attribute, value in transform_info['filter_on'].items():
            all_same = False
        if all_same:
            assert obj[attribute_to_transform] == transformed_value

def test_generate_distractor_and_check_not_same_for_max_tries():
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    input_scene, true_answer = get_default_single_input_answer_scene()

    distractor_fn = to_test.gen_distractor_random_filter_input_scene
    new_distractor = to_test.generate_distractor_and_check_not_same_for_max_tries(to_test.MAX_TRIES, distractor_fn, input_scene, true_answer)
    assert to_test.check_differing_scenes(new_distractor, true_answer)

def test_add_distractors_for_question():
    set_random_seed()
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    default_question = default_question_file_object['questions'][0]

    mock_args = MockArgs(num_answers_per_question=2,
    num_distractors_per_answer=4)
    transformed_question = to_test.add_distractors_for_question(mock_args, default_question, default_all_scenes)
    assert to_test.DISTRACTOR_TAG in transformed_question
    assert len(transformed_question[to_test.DISTRACTOR_TAG]) == mock_args.num_answers_per_question
    for distractor_set in transformed_question[to_test.DISTRACTOR_TAG]:
        assert len(distractor_set) == mock_args.num_distractors_per_answer
        for distractor in distractor_set:
            assert type(distractor) == type(dict())    
            assert len(distractor['objects']) > 0
    
def test_add_distractors_for_question_file_object():
    set_random_seed()
    mock_args = MockArgs(num_answers_per_question=2,
    num_distractors_per_answer=4)
    default_question_file_object =  get_default_localization_object()
    default_all_scenes = get_default_all_scenes()
    distractor_augmented_questions = to_test.add_distractors_for_question_file_object(mock_args, default_question_file_object, default_all_scenes)
    for question in distractor_augmented_questions['questions']:
        if type(question['answers'][0]) == type(dict()):
            assert to_test.DISTRACTOR_TAG in question
    
    