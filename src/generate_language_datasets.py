"""
Utilities for generating the 'language' dataset.
"""

import argparse, json, os, itertools, random, shutil
import time, copy
import re
import extended_question_engine as extended_qeng
import question_utils as qutils
from collections import defaultdict, Counter
import pathlib


# File handling.
parser = argparse.ArgumentParser()
parser.add_argument('--questions_dir', default='data/clevr_dreams/questions',
    help="Directory containing JSON questions files to generate train and test language for.")
parser.add_argument('--output_language_dir', default='data/clevr_dreams/language',
    help="Top level directory under which we will write the language files.")

def process_question_text(text):
    # remove punctuation, capitalization, and split plurals
    text = text.lower()
    punctuation = ["?", ".", ","]
    text = "".join([c for c in text if c not in punctuation])
    plurals = ['things', 'cylinders', 'spheres', 'cubes']
    for p in plurals:
        text = text.replace(p, f'{p[:-1]} s')
    return text

def main(args):
    for questions_file in os.listdir(args.questions_dir):
        if not questions_file.endswith('.json'): continue
        print(f"Now generating language for: {questions_file}.")
        prefix = 'CLEVR_train_' if 'CLEVR_train_' in questions_file else 'CLEVR_val_'
        dataset_name = questions_file.split(prefix)[-1].split('.json')[0]
        split = 'train' if 'train' in questions_file else 'test'
        
        # Make the language directory if it does not exist
        language_dir = os.path.join(args.output_language_dir, dataset_name, split)
        pathlib.Path(language_dir).mkdir(parents=True, exist_ok=True)
        
        fn = os.path.join(args.questions_dir, questions_file)
        with open(fn, 'r') as f:
            qs = json.load(f)["questions"]
        
        questions = {}
        vocab = set()
        for q in qs:
            question_text = q['question'] if type(q['question']) is str else q['question'][0]
            task_name = f"{q['question_index']}_{question_text}"
            processed = process_question_text(question_text)
            vocab.update(processed.split())
            questions[task_name] = [processed]
    
        # Write language
        out_fn = os.path.join(language_dir, 'language.json')
        print(f"Writing text for [{len(questions)}] questions.")
        with open(out_fn, 'w') as f:
            json.dump(questions, f)
        
        # Write vocab
        vocab = list(vocab)
        print(f"Writing vocab of [{len(vocab)}] words.")
        out_fn = os.path.join(language_dir, 'vocab.json')
        with open(out_fn, 'w') as f:
            json.dump(vocab, f)
            
            
        
        
    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)  