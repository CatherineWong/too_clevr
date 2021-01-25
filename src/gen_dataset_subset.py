"""
gen_dataset_subset.py | Author : Catherine Wong
Utility file for generating subsets of existing datasets satisfying key properties for various experiments.
A common usecase is to generate a subset of a dataset only containing questions satisfying a specific set of return properties.

Example usage:
    gen_dataset_subset.py 
        --input_questions_directory DIRECTORY
        --output_questions_directory DIRECTORY
        --question_classes all
        --restrict_return_type bool int scene
"""

import argparse, json, os, sys
import pathlib

GENERATE_ALL_FLAG = 'all'
DEFAULT_CLEVR_PREFIX = 'CLEVR'
DATASET_SPLIT_NAMES = ['train', 'val']
INT_TYPE = 'int'
BOOL_TYPE = 'bool'
SCENE_TYPE = 'scene'
STRING_TYPE = 'string'

parser = argparse.ArgumentParser()
parser.add_argument('--input_questions_dir', required=True,
    help="Top level directory under which we will write the question files.")
parser.add_argument('--output_questions_dir', required=True,
    help="Top level directory under which we will write the output files.")
parser.add_argument('--question_classes', 
                    nargs='*',
                    help='Which question classes to generate for, or "all" for all in the language directory.')
parser.add_argument('--restrict_return_type', 
                    nargs='*',
                    help='If provided, we will only keep questions with a restricted return type. Choose from bool, int, string, scene')

def get_metadata_from_question_file(filename, args):
    """
    Returns (filename, split, class) from '{prefix}_{split}_{class}.json'.
    Prefix should not have underscores.
    Class can have underscores.
    """
    split_filename = filename.split("_")
    assert split_filename[0] == DEFAULT_CLEVR_PREFIX
    assert split_filename[1] in DATASET_SPLIT_NAMES
    split = split_filename[1] 
    dataset_name = "_".join(split_filename[2:]).split('.json')[0] # Remove the JSON
    return (filename, split, dataset_name)
            
def get_question_files_and_metadata(args):
    """
    Gets any valid question files from the directory, along with their metadata (the question class name and the split.)
    Files should be named in the form '{prefix}_{split}_{class}.json'
    Returns valid question files in the form:
        {
            filename : (split, dataset_name)
        }
    """
    generate_all = (args.question_classes == [GENERATE_ALL_FLAG])
    
    candidate_question_files = [file for file in os.listdir(args.input_questions_dir) if file.endswith('.json') and file.startswith(DEFAULT_CLEVR_PREFIX)]
    valid_question_files = dict()
    for candidate_question_file in candidate_question_files:
         (filename, split, dataset_name) = get_metadata_from_question_file(candidate_question_file, args)
         if generate_all or (dataset_name in args.question_classes):
             valid_question_files[filename] = (split, dataset_name)
    return valid_question_files

def create_output_dirs(args, question_files_and_metadata):
    """
    Creates the top_level output dir for the question files, and then pre-calculates the full filepaths with which to write the corresponding output files.
    Returns a dict of the form: { filename: output_dir_path }
    """
    question_files_and_output_dirs = dict()
    
    pathlib.Path(args.output_questions_dir).mkdir(parents=True, exist_ok=True)
    for question_file in question_files_and_metadata:
        output_file = os.path.join(args.output_questions_dir, question_file)
        question_files_and_output_dirs[question_file] = output_file 
    return question_files_and_output_dirs

def check_return_type_restriction(input_question, return_type_restrictions):
    output_example = input_question['answers'][0]
    if type(output_example) == type(0):
        return_type = INT_TYPE
    elif type(output_example) == type(True):
        return_type = BOOL_TYPE
    elif type(output_example) == type(dict()):
        return_type = SCENE_TYPE
    elif type(output_example) == type(""):
        return_type = STRING_TYPE
    else:
        print(f"Unknown return type for example: {output_example}.")
        sys.exit(0)
    return return_type in return_type_restrictions
        
def get_restricted_questions_object(args, input_questions_file_object):
    """
    Takes an input file object and returns an object where the 'questions' array only contains questions satisfying a set of restrictions.
    Mutates: initial_questions_file_object
    """
    assert 'questions' in input_questions_file_object
    input_questions = input_questions_file_object["questions"]
    restricted_questions = []
    for input_question in input_questions:
        return_type_restrictions = args.restrict_return_type
        if check_return_type_restriction(input_question, return_type_restrictions):
            restricted_questions.append(input_question)
    input_questions_file_object["questions"] = restricted_questions
    print(f"Read {len(input_questions)} -> restricted to {len(restricted_questions)}.")
    return input_questions_file_object
    
def iteratively_write_out_restricted_language_dataset(args, question_files_and_output_dirs):
    """
    Iterates over the input question files, writing out a subset of the questions with the provided restrictions to the correpsonding output file.
    """
    for question_file in question_files_and_output_dirs:
        full_question_filepath = os.path.join(args.input_questions_dir, question_file)
        print(f"Writing restricted dataset for {full_question_filepath}...")
        with open(full_question_filepath, 'r') as f:
            input_questions_file_object = json.load(f)
            restricted_questions_object = get_restricted_questions_object(args, input_questions_file_object)
        # Write out the processed questions object.
        output_filename = question_files_and_output_dirs[question_file]
        print(f"Writing restricted questions to {output_filename}")
        with open(output_filename, 'w') as f:
            json.dump(restricted_questions_object, f)        

def main(args):
    question_files_and_metadata = get_question_files_and_metadata(args)
    question_files_and_output_dirs = create_output_dirs(args, question_files_and_metadata)
    iteratively_write_out_restricted_language_dataset(args, question_files_and_output_dirs)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)  