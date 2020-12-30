"""
gen_questions_n_inputs.py | Author: Catherine Wong.

This generates program-induction style versions of the original CLEVR templates, which now have n scene inputs, rather than just one.

It requires question_templates JSON files, and a common set of scenes to reference.

Example usage:
python3 gen_questions_n_inputs.py --default_train_scenes
    --question_templates 1_zero_hop 1_one_hop
    --instances_per_template 10
    --n_scenes_per_question 10
    --no_boolean 1
    --output_questions_directory ../data/clevr_dreams/questions
    
"""
import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng
import question_utils as qutils
from collections import defaultdict, Counter

DEFAULT_TRAIN_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_train_scenes_5000.json"
DEFAULT_VAL_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_val_scenes_5000.json"
DEFAULT_QUESTION_METADATA = "../metadata/clevr_original_metadata/1_metadata.json"

DEFAULT_ORIGINAL_TEMPLATES_DIR = "../metadata/clevr_original_metadata/question_templates"

# Template restrictions based on which questions can feasibly generate n inputs.
TEMPLATE_RESTRICTED_QUESTIONS = {
    '1_single_or' : [0, 1, 2, 4, 5],
    '1_compare_integer' : [0, 1, 2],
}
NUM_SAMPLE_QUESTIONS_TO_DISPLAY = 5
TRAIN_SPLIT, VAL_SPLIT = 'train', 'val'

parser = argparse.ArgumentParser()
parser.add_argument('--random_seed', default=0)

# Arguments for the scenes used to generate inputs.
parser.add_argument('--default_train_scenes', help="If provided, we use a default set of training scenes.", action='store_true')
parser.add_argument('--default_val_scenes', help="If provided, we use a default set of validation scenes.", action='store_true')
parser.add_argument('--input_scene_file', 
    help="If provided, we reference a specific set of input scenes.")

# Which metadata file to use for the questions.
parser.add_argument('--metadata_file', default=DEFAULT_QUESTION_METADATA, help="JSON file containing metadata about functions")

# Arguments used to determine which question templates to use. 
parser.add_argument('--template_dir', default=DEFAULT_ORIGINAL_TEMPLATES_DIR, help="Directory containing JSON templates for questions")
parser.add_argument('--question_templates', 
                    nargs='*',
                    help='Which question templates to generate for.')

# Arguments that determine parameters of the questions we generate.       
parser.add_argument('--instances_per_template', default=10, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--n_scenes_per_question', default=10, type=int,
    help="The number of scenes that serve as examples for each image.")
parser.add_argument('--no_boolean', default=0, type=int, help='Whether to remove boolean questions from the dataset.')
parser.add_argument('--max_generation_tries_per_instantiation', default=5, type=int, help="The number of randomized attempts we will take to instantiate a given question template.") 
parser.add_argument('--max_time_to_instantiate', default=100, type=int, help="The amount of time to spend attempting to instantiate on a given try.") 

# Arguments to determine where we write and store the output questions.
parser.add_argument('--output_questions_directory',
    help="Directory in which to write out the generated questions.",
    required=True)
parser.add_argument('--output_questions_prefix',
    default="CLEVR",
    help="If included, a different prefix for the output files.")


def set_random_seed(args):
    seed = args.random_seed
    print(f"Setting random seed to: {seed}")
    random.seed(seed)

def get_input_scenes(args):
    if args.default_train_scenes:
        assert(not args.default_val_scenes)
        scenes_file = DEFAULT_TRAIN_SCENES
    elif args.default_val_scenes:
        assert(not args.default_train_scenes)
        scenes_file = DEFAULT_VAL_SCENES
    elif args.input_scene_file:
        scenes_file = args.input_scene_file
    else:
        raise RuntimeError('No input scene file provided.')
    
    with open(scenes_file, 'r') as f:
        scene_data = json.load(f)
        all_scenes = scene_data['scenes']
        scene_info = scene_data['info']
    
    print(f"Using [{len(all_scenes)}] scenes from {scenes_file}")
    return scenes_file, all_scenes, scene_info

def get_question_metadata(args):
    with open(args.metadata_file, 'r') as f:
      metadata = json.load(f)
    functions_by_name = {}
    boolean_functions = {}
    for f in metadata['functions']:
      functions_by_name[f['name']] = f
      if f['output'] == 'Bool':
          boolean_functions[f['name']] = f
    metadata['_functions_by_name'] = functions_by_name
    metadata['_boolean_fns'] = boolean_functions
    
    return metadata

def get_training_text_questions(args, split):
    """Loads the training text questions for the template files if this is a validation split, so that we can avoid generating them for the validation split.
    Returns: {template_filename : []}
    """
    training_questions = dict()
    if split == VAL_SPLIT:
        for template_filename in args.question_templates:
            output_filename = os.path.join(args.output_questions_directory, f"{args.output_questions_prefix}_{TRAIN_SPLIT}_{template_filename}.json")
            with open(output_filename, 'r') as f:
                training_data = json.load(f)
                text_questions = [question['question'] for question in training_data['questions']]
                print(f"Loaded {len(text_questions)} training questions from {output_filename} for {template_filename}")
                training_questions[template_filename] = text_questions
    else:
        print(f"Split is training split, not loading training questions.")
        return {template_filename : [] for template_filename in args.question_templates}
        
    return training_questions

def get_question_templates(args, metadata):
    """Returns a dictionary of question templates for each file containing templates on a partiular question class: {template_filename :
        {(template_filename, original_question_idx): template}
    }"""
    
    templates = dict()
    for question_template_file in args.question_templates:
        templates[question_template_file] = dict()
        
        full_template_filepath = os.path.join(args.template_dir, question_template_file + ".json")
        
        num_skipped_boolean_questions = 0
        with open(full_template_filepath, 'r') as f:
            question_templates = json.load(f)
            for question_idx, template in enumerate(question_templates):
                # We include a subset of these questions, as the others tend to hang for rejection sampling.
                if question_template_file in TEMPLATE_RESTRICTED_QUESTIONS:
                    if question_idx not in TEMPLATE_RESTRICTED_QUESTIONS[question_template_file]: continue
                
                # We can skip Boolean questions, which are underconstrained.
                is_boolean_question = template['nodes'][-1]['type'] in metadata['_boolean_fns']
                if bool(args.no_boolean) and is_boolean_question:
                    question_text = template['text'][0]
                    print(f"Skipping boolean question: {question_text}")
                    num_skipped_boolean_questions += 1
                    continue
                    
                template_key = (question_template_file, question_idx)
                templates[question_template_file][template_key] = template
            print(f'Read {len(templates[question_template_file])} question templates from {full_template_filepath}, skipped {num_skipped_boolean_questions} boolean templates.')
    return templates

def instantiate_templates_dfs_multiple_inputs(
                all_scenes,
                template,
                metadata,
                answer_counts, # Holdover to allow answer distribution.
                max_instances=None, # Maximum instances of this template.
                n_scenes_per_question=None,
                max_time=100,
                training_questions_for_file=None):
    """
    Attempts to generate text questions that are valid for a set of n_scenes_per_question inputs.
    Uses a direct generalization of the original CLEVR instatiate_templates_qs code and simply reorganizes to attempt to generate multiple inputs per question.
    
    Avoids questions in training_questions_for_file.
    
    Contains heuristics to attempt to balance the length of the questions.
    Returns {question_text : [(scene, structured_question, structured_answer)]}.
    """
    tic = time.time()
    text_questions = defaultdict(list)
    
    scenes_per_q = Counter()
    random.shuffle(all_scenes)
    # Just try instantiating the questions for a set of scenes.
    for i, s in enumerate(all_scenes):
        if i > 0 and i % 100 == 0: print(f"On scene [{i}/{len(all_scenes)}]")
        # This generates a combinatorial set of valid questions for a given scene. 
        # It returns a set of text questions, structured questions, and answer objects.
        ts, qs, ans = qutils.instantiate_templates_dfs(
                        s,
                        template,
                        metadata,
                        answer_counts, # This is deprecated and not used.
                        synonyms=[],
                        max_instances=1000,
                        verbose=False,
                        no_empty_filter=True)
        non_duplicated_text_questions = []
        for i, tq in enumerate(ts):
            if tq in training_questions_for_file: continue # Avoid training questions to prevent duplication in the validation set.
            text_questions[tq].append((s, qs[i], ans[i])) 
            non_duplicated_text_questions.append(tq)
            
        scenes_per_q.update(non_duplicated_text_questions)
        
        buckets_to_text, valid_qs = get_valid_questions_by_text_length_bucket(scenes_per_q, text_questions, n_scenes_per_question, metadata=metadata, num_buckets=4)
        
        if len(valid_qs) >= max_instances:
            num_valid_questions_per_bucket = [len(value) for value in buckets_to_text.values()]
            num_buckets = len(buckets_to_text)
            # Break when we have roughly the minimum number for even distribution in each bucket.
            num_per_bucket = max((max_instances / num_buckets), 1)
            if min(num_valid_questions_per_bucket) >= num_per_bucket:
                break
        toc = time.time()
        if (toc - tic) > max_time:
            print("Out of time!")
            break
    # Try to get a range of questions.
    # Randomly sample among the question in valid qs by text length bucket, favoring longer buckets when possible
    final_qs = []
    for bucket in sorted(buckets_to_text, reverse=True):
        if len(buckets_to_text[bucket]) == 0: continue
        num_buckets = len(buckets_to_text)
        num_per_bucket = max(1, int(max_instances / num_buckets))
        questions_for_bucket = random.sample(buckets_to_text[bucket], min(num_per_bucket, len(buckets_to_text[bucket])))
        final_qs += questions_for_bucket
    text_questions = {
        q : random.sample(text_questions[q], n_scenes_per_question)
        for q in final_qs
    } 
    return text_questions

def get_valid_questions_by_text_length_bucket(scenes_per_q, text_questions, n_scenes_per_question, metadata, num_buckets=3):
    """
    Partitions the text questions into buckets based on how many attribute words they have, counting how many valid questions we have in each text bucket.
    """
    attribute_words = []
    for type in metadata['types']:
        if metadata['types'][type] is not None:
            attribute_words += metadata['types'][type]
            attribute_words += [w + 's' for w in metadata['types'][type]] # plurals
    
    # Length is the number of attribute words in a given text question.
    text_questions_to_length = {
        text_question : len([w for w in text_question.split() if w in attribute_words]) for text_question in text_questions
    }
    all_lengths = list(text_questions_to_length.values())
    max_length, min_length = max(all_lengths), min(all_lengths)
    min_length = max(1, min_length)# Don't allow degenerate questions with no attribute words
    bucket_size = max(int((max_length - min_length) / num_buckets), 1) 
    buckets = list(range(min_length, max_length, bucket_size))
    if buckets[-1] <= max_length:
        buckets.append( max_length + 1)
    # Buckets are keyed by (lower_bound, upper_bound) on question length
    buckets_to_text = {
        (buckets[i], buckets[i+1]) : []
        for i in range(len(buckets) - 1)
    }
    
    # Divvy up the valid questions by bucket length.
    valid_qs = [q for q, count in scenes_per_q.items() if count >= n_scenes_per_question] 
    
    for valid_text_question in valid_qs:
        length = text_questions_to_length[valid_text_question]
        # Find the bucket it goes in
        for (lower_bound, upper_bound) in buckets_to_text:
            if (length >= lower_bound) and (length < upper_bound):
                buckets_to_text[(lower_bound, upper_bound)].append(valid_text_question)
                
    return buckets_to_text, valid_qs
    
def postprocess_instantiated_questions(instantiated_questions,
dataset_split, template_filename, template_index):
    """
    Post-processing on the set of questions generated by instantiate_templates_dfs_multiple_inputs.
    
    Runs checks to remove degenerate questions.
    
    Takes: {question_text : [(scene, structured_question, structured_answer)]}.
    Turns the questions into a single, structured dictionary object in the original CLEVR-questions format.
    """
    post_processed_questions = []
    for question_text in instantiated_questions:
        # Unpack the scenes / programs / answers for a given question.
        scenes, programs, answers = [spa[0] for spa in instantiated_questions[question_text]], [spa[1] for spa in instantiated_questions[question_text]], [spa[-1] for spa in instantiated_questions[question_text]]
        image_filenames = [scene['image_filename'] for scene in scenes]
        img_indices = [int(os.path.splitext(scene_fn)[0].split('_')[-1]) for scene_fn in image_filenames]
        
        # Post-hoc renaming convention from the original Johnson et. al code.
        for p in programs:
            for f in p:
              if 'side_inputs' in f:
                f['value_inputs'] = f['side_inputs']
                del f['side_inputs']
              else:
                f['value_inputs'] = []
        
        # Degeneracy check: don't allow all the answers to be the same
        if type(answers[0]) is not dict and len(set(answers)) < 2:
            continue
        else:
            post_processed_questions.append({
                'split': dataset_split,
                'question': question_text,
                'template_filename': template_filename,
                'template_index': template_index,
                'question_index': None, # Will assign later.
                'image_filenames' :image_filenames,
                'image_indices' : img_indices,
                'answers' : answers,
                'program' : programs
            })
    return post_processed_questions

def generate_questions_for_template_file(args, templates_for_file,
    dataset_split, metadata, all_scenes, training_questions_for_file):
    """
    Attempts to generate a set of questions for a single template file.
    Takes a single dict containing the question templates for a particular file in the form:
        {(template_filename, original_question_idx): template}
        
    For each question in the template file, attepts repeatedly to instantiate questions, up to a given number of tries.
    
    Avoids questions in 'training questions for file'.
    Returns a list of questions indexed for that template.
    """
    max_tries = args.max_generation_tries_per_instantiation
    max_time = args.max_time_to_instantiate
    
    generated_questions = []
    templates_items = list(templates_for_file.items())
    for i, ((template_filename, template_index), template) in enumerate(templates_items):
        print(f'Trying question template {template_filename} {template_index} : {i}/{len(templates_items)} in this file.') 
        print(f"Question template text: {template['text'][0]}")
        
        curr_try = 0
        questions_for_template = []
        while True:
            print(f"For this template, currently on try: {curr_try} / {max_tries}")
            
            instantiated_questions = instantiate_templates_dfs_multiple_inputs(all_scenes=all_scenes,
            template=template,
            metadata=metadata,
            max_time=max_time,
            max_instances=args.instances_per_template,
            n_scenes_per_question=args.n_scenes_per_question,
            answer_counts=None,
            training_questions_for_file=training_questions_for_file)
            
            postprocessed_questions = postprocess_instantiated_questions(instantiated_questions,
                dataset_split=dataset_split, template_filename=template_filename,
                template_index=template_index)
                
            curr_try += 1
            questions_for_template += postprocessed_questions
            if len(questions_for_template) >= args.instances_per_template or curr_try >= max_tries:
                selected_questions = questions_for_template[:args.instances_per_template]
                generated_questions += selected_questions
                # Print sample questions.
                print(f"Sample question text:")
                for question in random.sample(selected_questions, min(NUM_SAMPLE_QUESTIONS_TO_DISPLAY, len(selected_questions))):
                    print(f"\t: {question['question']}")
                break
    # Add indices to all of the questions for this template.
    for question_index, question in enumerate(generated_questions):
        question['question_index'] = question_index
    
    print(f"Successfully generated {len(generated_questions)} questions.")
    return generated_questions

def generate_questions_for_all_template_files(args, all_templates,
    dataset_split, metadata, all_scenes, training_text_questions):
    """
    Generates a set of questions for a set of template files.
    Attempts to generate a set of questions for a single template file.
    Takes a dict containing the different template questions in the form:
        {
            template_filename: {(template_filename, original_question_idx): template}
        }
            
    Returns {[template_filename] : [question_objects]}
    """
    all_generated_questions = {}
    for template_filename in all_templates:
        templates_for_file = all_templates[template_filename]
        training_questions_for_file = training_text_questions[template_filename]
        questions_for_file = generate_questions_for_template_file(args, templates_for_file, dataset_split, metadata, all_scenes, training_questions_for_file)
        
        all_generated_questions[template_filename] = questions_for_file
    return all_generated_questions
        
def write_output_questions_files(args, scene_info, all_generated_questions):
    split = scene_info['split']
    for template_filename in all_generated_questions:
        generated_questions_for_template = all_generated_questions[template_filename]
        output_filename = os.path.join(args.output_questions_directory, f"{args.output_questions_prefix}_{split}_{template_filename}.json")
        
        with open(output_filename, 'w') as f:
          print(f'Writing {len(generated_questions_for_template)} questions out to {output_filename}')
          json.dump({
              'info': scene_info,
              'questions': generated_questions_for_template
            }, f)

def main(args):
    set_random_seed(args)
    scene_file, all_scenes, scene_info = get_input_scenes(args)
    metadata = get_question_metadata(args)
    all_question_templates = get_question_templates(args, metadata)
    training_text_questions = get_training_text_questions(args, scene_info['split'])
    
    all_generated_questions = generate_questions_for_all_template_files(args,
    all_question_templates, scene_info['split'], metadata, all_scenes, training_text_questions)

    write_output_questions_files(args, scene_info, all_generated_questions)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
