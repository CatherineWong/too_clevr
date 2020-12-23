import generate_language_datasets as to_test
import os
import json
from types import SimpleNamespace as MockArgs

DEFAULT_QUESTIONS_DIR = '../metadata/clevr_test_metadata/questions'

def get_default_question_classes_in_dir():
    return ['1_one_hop', '2_transform']
    
def get_default_questions_and_ground_truth_processed():
    question = [{"split": "train", "question": "There is a metal sphere; what number of spheres are right it?", "template_filename": "1_one_hop.json", "template_index": 0, "question_index": 0, "image_filenames": ["CLEVR_train_000889.png", "CLEVR_train_000234.png", "CLEVR_train_004001.png", "CLEVR_train_000112.png", "CLEVR_train_001604.png", "CLEVR_train_003401.png", "CLEVR_train_003964.png", "CLEVR_train_002631.png", "CLEVR_train_002757.png", "CLEVR_train_004472.png", "CLEVR_train_000708.png", "CLEVR_train_004504.png", "CLEVR_train_002045.png", "CLEVR_train_002092.png", "CLEVR_train_002993.png"], "image_indices": [889, 234, 4001, 112, 1604, 3401, 3964, 2631, 2757, 4472, 708, 4504, 2045, 2092, 2993], "answers": [0, 2, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0]}]
    processed ="there is a metal sphere what number of sphere s are right it"
    return question, processed
    
def test_get_metadata_from_question_file():
    TEST_PREFIX="TEST"
    TEST_DATASET_NAME = "1_question_class"
    SPLIT = "train"
    
    mock_args = MockArgs(question_files_prefix=TEST_PREFIX)
    
    TEST_FILENAME = f"{TEST_PREFIX}_{SPLIT}_{TEST_DATASET_NAME}.json"
    (filename, split, dataset_name) = to_test.get_metadata_from_question_file(TEST_FILENAME, mock_args)
    
    assert filename == TEST_FILENAME
    assert split == SPLIT
    assert dataset_name == TEST_DATASET_NAME

def test_get_question_files_and_metadata_all():
    TEST_PREFIX="CLEVR"
    mock_args = MockArgs(question_files_prefix=TEST_PREFIX,
                        question_classes_to_generate=[to_test.GENERATE_ALL_FLAG],
                        questions_dir=DEFAULT_QUESTIONS_DIR)
    
    valid_question_files = to_test.get_question_files_and_metadata(mock_args)
    
    possible_question_files = os.listdir(DEFAULT_QUESTIONS_DIR)
    assert len(valid_question_files) == len(possible_question_files)
    for valid_filename in valid_question_files:
        assert valid_filename in possible_question_files
        (split, dataset_name) = valid_question_files[valid_filename]
        assert split in to_test.DATASET_SPLIT_NAMES
        assert dataset_name in valid_filename

def test_get_question_files_and_metadata_specific():
    TEST_PREFIX="CLEVR"
    VALID_FILE = '2_transform'
    mock_args = MockArgs(question_files_prefix=TEST_PREFIX,
                        question_classes_to_generate=[VALID_FILE],
                        questions_dir=DEFAULT_QUESTIONS_DIR)
    
    valid_question_files = to_test.get_question_files_and_metadata(mock_args)
    
    possible_question_files = [f for f in os.listdir(DEFAULT_QUESTIONS_DIR) if VALID_FILE in f]
    assert len(possible_question_files) == 2
    assert len(valid_question_files) == len(possible_question_files)
    for valid_filename in valid_question_files:
        assert valid_filename in possible_question_files
        (split, dataset_name) = valid_question_files[valid_filename]
        assert split in to_test.DATASET_SPLIT_NAMES
        assert dataset_name in valid_filename

def test_create_output_dirs(tmpdir):
    mock_args = MockArgs(output_language_dir=tmpdir)
    MOCK_DATASET_NAME = '1_test_test'
    
    mock_question_files_and_metadata = {
        MOCK_DATASET_NAME + split : (split, MOCK_DATASET_NAME)
        for split in to_test.DATASET_SPLIT_NAMES
    }
    question_files_and_output_dirs = to_test.create_output_dirs(mock_args, mock_question_files_and_metadata)
    
    train_dir = os.path.join(tmpdir, MOCK_DATASET_NAME, 'train')
    val_dir = os.path.join(tmpdir, MOCK_DATASET_NAME, 'val')
    assert os.path.isdir(train_dir)
    assert os.path.isdir(val_dir)
    
    for filename in mock_question_files_and_metadata:
        assert filename in question_files_and_output_dirs

def test_get_processed_language_and_vocab():
    default_questions, default_processed = get_default_questions_and_ground_truth_processed()
    gold_task_name = f"0_{default_questions[0]['question']}"
    
    processed_language, vocab = to_test.get_processed_language_and_vocab(default_questions)
    
    assert len(set(vocab)) == len(vocab)
    assert len(vocab) > 0
    assert len(processed_language) == 1
    
    for task_name in processed_language:
        assert task_name == gold_task_name
        assert processed_language[task_name] == [default_processed]

def test_processed_question_text():
    default_questions, default_processed = get_default_questions_and_ground_truth_processed()
    
    processed_text = to_test.process_question_text(default_questions[0]['question'])
    assert processed_text == default_processed

def test_integration_main(tmpdir):
    TEST_PREFIX = 'CLEVR'
    mock_args = MockArgs(
        questions_dir = DEFAULT_QUESTIONS_DIR,
        question_classes_to_generate = [to_test.GENERATE_ALL_FLAG],
        question_files_prefix = TEST_PREFIX,
        output_language_dir=tmpdir
    )
    to_test.main(mock_args)
    
    for question_class in get_default_question_classes_in_dir():
        for split in to_test.DATASET_SPLIT_NAMES:
            language_file = os.path.join(tmpdir, question_class, split, to_test.LANGUAGE_FILENAME)
            with open(language_file, 'r') as f:
                language_data = json.load(f)
                assert len(language_data) > 0
                for task_name in language_data:
                    assert len(task_name.split("_")) > 0
                    assert len(language_data[task_name][0].split()) > 0
            
            vocab_file = os.path.join(tmpdir, question_class, split, to_test.VOCAB_FILENAME)
            with open(vocab_file, 'r') as f:
                vocab = json.load(f)
                assert len(set(vocab)) == len(vocab)
                assert len(vocab) > 0
                
    