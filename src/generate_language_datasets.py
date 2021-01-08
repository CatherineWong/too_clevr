"""
gen_language_datasets.py | Author: Catherine Wong

This generates the separated test and train splits containing just the natural language question query for each CLEVR task, along with a vocabulary file, in
the standardized dataset format used in the other DreamCoder + Language domains.

It expects a directory containing train/val questions for a question template class
of the form '{prefix}_train_{question_class}.json'.
It will then generate a directory and files of the form:
    {question_class}/
        test/ -> language.json and vocab.json
        train/ ..
for each of the question classes.
Each language file is a dictionary in the form:
    {
    "0_full original question text" : [tokenized question text],
    }

Example usage: python3 generate_language_datasets.py --questions_dir clevr_dreams/questions
    --question_classes_to_generate all
    --question_files_prefix CLEVR
    --output_language_dir clevr_dreams/language
"""

import argparse, json, os, itertools, random, shutil
import time, copy
import re
import extended_question_engine as extended_qeng
import question_utils as qutils
from collections import defaultdict, Counter
import pathlib

GENERATE_ALL_FLAG = 'all'
DEFAULT_QUESTIONS_PREFIX = 'CLEVR'
LANGUAGE_FILENAME = 'language.json'
VOCAB_FILENAME = 'vocab.json'
DATASET_SPLIT_NAMES = ['train', 'val']
DATASET_SPLIT_TO_CANONICAL_SPLIT = {
    'train' : 'train',
    'val' : 'test'
}

# File handling.
parser = argparse.ArgumentParser()

parser.add_argument('--questions_dir', required=True,
    help="Directory containing JSON questions files to extract train and test language for.")
parser.add_argument('--question_classes_to_generate', 
                    nargs='*',
                    help='Which question classes to generate for, or "all" for all in the directory.')
parser.add_argument('--question_files_prefix', 
                    default="CLEVR",
                    help='The common prefix for all the question files.')
                    
parser.add_argument('--output_language_dir', required=True,
    help="Top level directory under which we will write the language files.")

def to_canonical_split(split):
    """Helper method since the 'split' names in DreamCoder are assumed differently than in CLEVR. 
    """
    return DATASET_SPLIT_TO_CANONICAL_SPLIT[split]
    
def get_metadata_from_question_file(filename, args):
    """
    Returns (filename, split, class) from '{prefix}_{split}_{class}.json'.
    Prefix should not have underscores.
    Class can have underscores.
    """
    split_filename = filename.split("_")
    assert split_filename[0] == args.question_files_prefix
    assert split_filename[1] in DATASET_SPLIT_NAMES
    split = split_filename[1] 
    dataset_name = "_".join(split_filename[2:]).split('.json')[0] # Remove the JSON
    return (filename, split, dataset_name)
    
def get_question_files_and_metadata(args):
    """
    Gets any valid question files from the directory, along with their metadata (the question class name, and the split.)
    Files should be named in the form '{prefix}_{split}_{class}.json'
    Returns valid question files in the form:
        {
            filename : (split, dataset_name)
        }
    """
    generate_all = (args.question_classes_to_generate == [GENERATE_ALL_FLAG])
    
    candidate_question_files = [file for file in os.listdir(args.questions_dir) if file.endswith('.json') and file.startswith(args.question_files_prefix)]
    valid_question_files = dict()
    for candidate_question_file in candidate_question_files:
         (filename, split, dataset_name) = get_metadata_from_question_file(candidate_question_file, args)
         if generate_all or (dataset_name in args.question_classes_to_generate):
             valid_question_files[filename] = (split, dataset_name)
    return valid_question_files

def create_output_dirs(args, question_files_and_metadata):
    """
    Creates the {question_class}/ -> test/ train/ directories for the given question files, and stores these directories with the question_files for writing output.
    Returns a dict of the form: { filename: output_dir_path }
    """
    question_files_and_output_dirs = dict()
    
    for question_file in question_files_and_metadata:
        split, dataset_name = question_files_and_metadata[question_file]
        canonical_split = to_canonical_split(split)
        output_directory = os.path.join(args.output_language_dir, dataset_name, canonical_split)
        pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
        question_files_and_output_dirs[question_file] = output_directory
    return question_files_and_output_dirs

def iteratively_write_out_processed_language_dataset(args, question_files_and_output_dirs):
    """
    Iterates over the input question files, writing out a language.json and vocab.json to their corresponding output directory.
    """
    for question_file in question_files_and_output_dirs:
        full_question_filepath = os.path.join(args.questions_dir, question_file)
        output_dir = question_files_and_output_dirs[question_file]
        
        (_, _, dataset_name) = get_metadata_from_question_file(question_file, args)
        
        print(f"Writing language dataset for {full_question_filepath}.")
        with open(full_question_filepath, 'r') as f:
            input_questions = json.load(f)["questions"]
            processed_language, vocab = get_processed_language_and_vocab(input_questions, dataset_name)  
            
            # Write out the processed langage object.
            output_filename = os.path.join(output_dir, LANGUAGE_FILENAME)
            print(f"Writing question text for [{len(processed_language)}] questions to {output_filename}")
            with open(output_filename, 'w') as f:
                json.dump(processed_language, f)
            
            # Write out the vocabulary object.
            output_filename= os.path.join(output_dir, VOCAB_FILENAME)
            print(f"Writing vocab of [{len(vocab)}] words to {output_filename}")
            with open(output_filename, 'w') as f:
                json.dump(vocab, f)     
            
def get_processed_language_and_vocab(input_questions, question_file):
    """
    Generates the processed_language and vocab objects from the original set of CLEVR questions.
    task names are of the form: {INDEX}-{DATASET_NAME}-{QUESTION_TEXT}    
    Returns:
        processed_language:  { task_name :  [processed_text]}
        vocab = [vocabulary_tokens]
    """
    processed_language = {}
    vocab = set()
    for question_object in input_questions:
        question_text = question_object['question'] if type(question_object['question']) is str else question_object['question'][0]
    
        task_name = f"{question_object['question_index']}-{question_file}-{question_text}"
        processed = process_question_text(question_text)
        vocab.update(processed.split())
        processed_language[task_name] = [processed]
    vocab = list(vocab)
    return processed_language, vocab  
        
def process_question_text(question_text):
    """
    Processing to tokenize the question text into a standarized format.
    We remove punctuation, capitalization, and split plural objects.
    """
    question_text = question_text.lower()
    punctuation = ["?", ".", ",", ";"]
    question_text = "".join([c for c in question_text if c not in punctuation])
    plurals = ['things', 'cylinders', 'spheres', 'cubes']
    for p in plurals:
        question_text = question_text.replace(p, f'{p[:-1]} s')
    return question_text

def main(args):
    question_files_and_metadata = get_question_files_and_metadata(args)
    question_files_and_output_dirs = create_output_dirs(args, question_files_and_metadata)
    iteratively_write_out_processed_language_dataset(args, question_files_and_output_dirs)
                    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)  