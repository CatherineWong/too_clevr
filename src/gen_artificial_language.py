"""
gen_artificial_language.py | Author: Catherine Wong

This generates the `artificial language` datasets used to run a human experiment, which use a much simpler and more rudimentary lexicon that is designed to allow human subjects to be able to learn the meanings of new words in a short experimental context.

It expects a directory containing the synthetic language data for a question class.

Each language file it outputs is a dictionary in the form 
{
"0_full original question text" : [tokenized artificial language text],
}

Example usage: python3 gen_artificial_language.py
    --language_dir clevr_icml_2021/synthetic/language
    --question_classes_to_generate all
    --output_language_dir clevr_icml_2021/artificial/language
"""
import argparse, json, os, sys
import pathlib
import artificial_language_utils 

GENERATE_ALL_FLAG = 'all'
DATASET_SPLIT_NAMES = ['train', 'test']
LANGUAGE_FILENAME = 'language.json'
VOCAB_FILENAME = 'vocab.json'

TRANSLATION_FN_REGISTRY = {
    "2_localization" :  artificial_language_utils.translate_localization_text,
    "2_remove" : artificial_language_utils.translate_remove_text, 
    "2_transform" : artificial_language_utils.translate_transform_text,
    "1_compare_integer" : artificial_language_utils.translate_compare_integer_text,
    "1_single_or" : artificial_language_utils.translate_single_or_text,
    "1_zero_hop" : artificial_language_utils.translate_zero_hop_text,
    "1_one_hop" : artificial_language_utils.translate_one_hop_text,
    "1_zero_hop_no_string" : artificial_language_utils.translate_zero_hop_text,
    "1_one_hop_no_string" : artificial_language_utils.translate_one_hop_text,
    "1_same_relate_restricted" : artificial_language_utils.translate_same_relate_restricted_text,
}

parser = argparse.ArgumentParser()
parser.add_argument('--language_dir', required=True,
    help="Directory containing JSON synthetic language files from which we will generate artificial language data.")
parser.add_argument('--question_classes_to_generate', 
                    nargs='*',
                    help='Which question classes to generate for, or "all" for all in the language directory.')
        
parser.add_argument('--output_language_dir', required=True,
    help="Top level directory under which we will write the language files.")

def get_metadata_for_language_dataset_question_class(question_class, args):
    """
    Returns an array of [(filename, split, class)] tuples for a given question class in a language dataset.
    """
    valid_metadata = []
    question_class_dir = os.path.join(args.language_dir, question_class)
    for split in DATASET_SPLIT_NAMES:
        candidate_language_filename = os.path.join(args.language_dir, question_class, split, LANGUAGE_FILENAME)
        if os.path.exists(candidate_language_filename):
            valid_metadata += [(candidate_language_filename, split, question_class)]
    return valid_metadata

def get_synthetic_language_datasets_and_metadata(args):
    """
    Gets any valid synthetic language files from the directory, along with their metadata (the question class name and the split).
    Language files should be in a {question_class}/{split}/language.json
    
    Returns valid synthetic language files in the form:
    {
        filename : (split, dataset_name)
    }
    """
    generate_all = (args.question_classes_to_generate == [GENERATE_ALL_FLAG])
    candidate_question_classes = [dir for dir in os.listdir(args.language_dir) if os.path.isdir(os.path.join(args.language_dir, dir))]
    
    valid_language_files = dict()
    for candidate_question_class in candidate_question_classes:
        if generate_all or candidate_question_class in args.question_classes_to_generate:
            metadata_for_question_classes = get_metadata_for_language_dataset_question_class(candidate_question_class, args)
            for  (filename, split, dataset_name) in metadata_for_question_classes:
                valid_language_files[filename] = (split, dataset_name)
    return valid_language_files

    
def create_output_dirs(args, synthetic_language_datasets):
    """
    Creates the {question_class}/ -> test/ train/ directories for the given question files, and stores these directories with the question_files for writing output.
    Returns a dict of the form: { (filename, question_class): output_dir_path }
    """
    language_files_and_output_dirs = dict()
    for language_file in synthetic_language_datasets:
        split, dataset_name = synthetic_language_datasets[language_file]
        output_directory = os.path.join(args.output_language_dir, dataset_name, split)
        pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
        language_files_and_output_dirs[(language_file, dataset_name)] = output_directory
    return language_files_and_output_dirs

def iteratively_write_out_artificial_language_dataset(args, synthetic_language_and_output_dirs):
    """
    Iterates over the synthetic language files, writing out a language.json and vocab.json to the corresponding output directory using the artificial language translation.
    """
    for (language_file, dataset_name) in synthetic_language_and_output_dirs:
        output_dir = synthetic_language_and_output_dirs[(language_file, dataset_name)]
        print(f"Writing language dataset for {language_file}.")
        
        with open(language_file, 'r') as f:
            synthetic_language_dataset = json.load(f)
            artificial_language, vocab = get_artificial_language_and_vocab(synthetic_language_dataset, dataset_name)
            
            # Write out the artificial language object.
            output_filename = os.path.join(output_dir, LANGUAGE_FILENAME)
            print(f"Writing question text for [{len(artificial_language)}] questions to {output_filename}")
            with open(output_filename, 'w') as f:
                json.dump(artificial_language, f)
            
            # Write out the vocabulary object.
            output_filename= os.path.join(output_dir, VOCAB_FILENAME)
            print(f"Writing vocab of [{len(vocab)}] words to {output_filename}")
            with open(output_filename, 'w') as f:
                json.dump(vocab, f)   

def get_artificial_language_and_vocab(synthetic_language_dataset, dataset_name):
    """
    Generates the artificial_language and vocab objects from the original set of CLEVR questions.
    
    Returns:
        artificial_language : {task_name : [artificial_test]}
        vocab = [vocabulary_tokens]
    """  
    artificial_language = {}
    vocab = set()
    for task_name in synthetic_language_dataset:
        synthetic_text = synthetic_language_dataset[task_name][0]
        artificial = translate_synthetic_to_artificial_language(synthetic_text, dataset_name)
        vocab.update(artificial.split())
        artificial_language[task_name] = [artificial]
    vocab = list(vocab)
    return artificial_language, vocab 

def translate_synthetic_to_artificial_language(synthetic_language_text, dataset_name):
    """
    'Translates' the synthetic language to a set of artificial language tokens.
    Uses a 'translation' file of ordered replacement tokens.
    """
    translation_fn = TRANSLATION_FN_REGISTRY[dataset_name]
    translation = translation_fn(synthetic_language_text)
    for token in translation.split():
        if token.islower():
            print(f"Errror for dataset: {dataset_name}")
            print(f"Error translating: {synthetic_language_text} -> {translation}")
            sys.exit(0)
    return translation
        
    
def main(args):
    synthetic_language_datasets =  get_synthetic_language_datasets_and_metadata(args)
    language_files_and_output_dirs = create_output_dirs(args, synthetic_language_datasets)
    iteratively_write_out_artificial_language_dataset(args, language_files_and_output_dirs)
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)  