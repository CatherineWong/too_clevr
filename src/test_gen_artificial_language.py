import gen_artificial_language as to_test
import os
import json
from types import SimpleNamespace as MockArgs

"""
test_gen_artificial_language.py  | Author: Catherine Wong

Expected usage:
"""
DEFAULT_LANGUAGE_DIR = '../metadata/clevr_test_metadata/language/synthetic'
def test_get_synthetic_language_datasets():
    mock_args = MockArgs(
                        question_classes_to_generate=[to_test.GENERATE_ALL_FLAG],
                        language_dir=DEFAULT_LANGUAGE_DIR)
    valid_language_files = to_test.get_synthetic_language_datasets_and_metadata(mock_args)
    possible_question_classes = os.listdir(DEFAULT_LANGUAGE_DIR) 
    num_splits = 2
    assert len(valid_language_files) == len(possible_question_classes) * num_splits
    
    for valid_filename in valid_language_files:
        (split, dataset_name) = valid_language_files[valid_filename]
        assert split in to_test.DATASET_SPLIT_NAMES
        assert dataset_name in possible_question_classes

def test_create_output_dirs(tmpdir):
    mock_args = MockArgs(output_language_dir=tmpdir)
    MOCK_DATASET_NAME = '1_test_test'
    
    mock_question_files_and_metadata = {
        MOCK_DATASET_NAME + split : (split, MOCK_DATASET_NAME)
        for split in to_test.DATASET_SPLIT_NAMES
    }
    question_files_and_output_dirs = to_test.create_output_dirs(mock_args, mock_question_files_and_metadata)
    
    train_dir = os.path.join(tmpdir, MOCK_DATASET_NAME, 'train')
    test_dir = os.path.join(tmpdir, MOCK_DATASET_NAME, 'test')
    assert os.path.isdir(train_dir)
    assert os.path.isdir(test_dir)
    
    for filename in mock_question_files_and_metadata:
        assert (filename, MOCK_DATASET_NAME) in question_files_and_output_dirs