"""
gen_questions_extended.py | Author : Catherine Wong

This generates program-induction style questions for the extended CLEVR templates.
The questions have n scene inputs, rather than just one; the extended CLEVR templates
also use a modified execution engine (extended_question_engine.py) to support additional primitives (such as transform or remove), and include Scene -> Scene 
tasks (e.g. "Find all the red objects", or "What if all the small blue cubes were large?").

It requires question_templates JSON files, and a set of scenes grouped by the presence of a shared, filterable object set (e.g. scenes that all have small blue cubes), generated by gen_n_inputs.py

Example usage: 
gen_questions_extended --random_seed 0
    --default_train_scenes
    --question_templates all
    --instances_per_template 15
    --max_generation_tries_per_instantiation 500
    --output_questions_directory DIRECTORY
    --output_questions_prefix CLEVR
"""
import argparse, json, os, itertools, random, shutil
import time, copy
import re
import extended_question_engine as extended_qeng
import question_utils as qutils
from collections import defaultdict, Counter
from gen_n_inputs import UNIQUE, MULTIPLE, GROUPING_TEMPLATE_TYPES

DEFAULT_TRAIN_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_train_scenes_5000.json"
DEFAULT_VAL_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_val_scenes_5000.json"
DEFAULT_GROUPED_TRAIN_SCENES = "../metadata/clevr_shared_metadata/grouped_scenes/grouped_CLEVR_train_scenes_5000.json" # Grouped scenes generated from the train scenes.
DEFAULT_GROUPED_VAL_SCENES = "../metadata/clevr_shared_metadata/grouped_scenes/grouped_CLEVR_val_scenes_5000.json" # Grouped scenes generated from the val scenes.

DEFAULT_EXTENDED_QUESTION_METADATA = "../metadata/clevr_extended_metadata/2_metadata.json"

DEFAULT_EXTENDED_TEMPLATES_DIR = "../metadata/clevr_extended_metadata/question_templates"

GENERATE_ALL_FLAG = 'all'

NUM_SAMPLE_QUESTIONS_TO_DISPLAY = 5
TRAIN_SPLIT, VAL_SPLIT = 'train', 'val'

# Special extended question primitives
PRIMITIVE_FILTER = "filter"
PRIMITIVE_TRANSFORM = "transform"
PRIMITIVE_REMOVE = "remove"

# File handling.
parser = argparse.ArgumentParser()
parser.add_argument('--random_seed', default=0)

# Arguments for the scenes used to generate inputs.
parser.add_argument('--default_train_scenes', help="If provided, we use a default set of training scenes and their grouped scenes.", action='store_true')
parser.add_argument('--default_val_scenes', help="If provided, we use a default set of validation scenes and their grouped scenes.", action='store_true')
parser.add_argument('--input_scene_file', 
    help="If provided, we reference a specific set of input scenes.")
parser.add_argument('--input_grouped_scene_file', 
    help="If provided, we reference a specific set of grouped input scenes. Note that this must be generated from the same scene file as the provided input_scene_file in this case.")
    
# Which metadata file to use for the questions.
parser.add_argument('--metadata_file', default=DEFAULT_EXTENDED_QUESTION_METADATA, help="JSON file containing metadata about functions")

# Arguments used to determine which question templates to use. 
parser.add_argument('--template_dir', default=DEFAULT_EXTENDED_TEMPLATES_DIR, help="Directory containing JSON templates for questions. Note that these should only be templates for the extended template questions, not original CLEVR questions.")
parser.add_argument('--question_templates', 
                    nargs='*',
                    help='Which question templates to generate for. Use "all" for all of the templates in the directory.')
                    
# Arguments that determine parameters of the questions we generate.       
parser.add_argument('--instances_per_template', default=15, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--max_generation_tries_per_instantiation', default=500, type=int, help="The number of randomized attempts we will take to instantiate a given question template.") 

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
    
def uniform_bernoulli_flip():
    return random.uniform(0, 1) > 0.5

def get_input_scenes_and_grouped_scenes(args):
    """
    Loads the input scenes as a provided file or from a default, along with the 
    corresponding pre-processed 'grouped scenes' file containing scenes grouped
    by a filterable object.
    Grouped scenes should have been generated by gen_n_inputs.py, and contain "unique" and "multiple" object scenes based on how many of each filterable object they contain.
    """
    if args.default_train_scenes:
        assert(not args.default_val_scenes)
        scenes_file = DEFAULT_TRAIN_SCENES
        grouped_scenes_file = DEFAULT_GROUPED_TRAIN_SCENES
    elif args.default_val_scenes:
        assert(not args.default_train_scenes)
        scenes_file = DEFAULT_VAL_SCENES
        grouped_scenes_file = DEFAULT_GROUPED_VAL_SCENES
    elif args.input_scene_file:
        assert args.input_grouped_scene_file
        scenes_file = args.input_scene_file
        grouped_scenes_file = args.input_grouped_scene_file
        
    else:
        raise RuntimeError('No input scene or grouped scene file provided.')
    
    with open(scenes_file, 'r') as f:
        scene_data = json.load(f)
        all_scenes = scene_data['scenes']
        scene_info = scene_data['info']
    print(f"Using [{len(all_scenes)}] scenes from {scenes_file}")
    
    # Read file containing input grouped scene templates.
    with open(grouped_scenes_file, 'r') as f:
        grouped_scene_data = json.load(f)
        assert grouped_scene_data['info']['split'] == scene_info['split']
        assert grouped_scene_data['info']['version'] == scene_info['version']
        grouped_scenes = grouped_scene_data['grouped_scenes']
        
        unique_object_scenes, multiple_object_scenes = grouped_scenes['unique'], grouped_scenes['multiple']
        # Check the length of the first scene group in the 'unique' set as an example.
        num_scenes_per_group = len(unique_object_scenes['0']['input_image_filenames'])
    print(f"Using scenes from {grouped_scenes_file} with {num_scenes_per_group} scenes per instance and {len(unique_object_scenes)} unique object scenes; and {len(multiple_object_scenes)} multiple_object_scenes.")
    
    return scenes_file, all_scenes, scene_info, grouped_scenes_file, grouped_scenes

def get_question_metadata(args):    
    with open(args.metadata_file, 'r') as f:
      metadata = json.load(f)
      dataset = metadata['dataset']
    functions_by_name = {}
    for f in metadata['functions']:
      functions_by_name[f['name']] = f
    metadata['_functions_by_name'] = functions_by_name
    assert PRIMITIVE_TRANSFORM in metadata['_functions_by_name']
    assert PRIMITIVE_REMOVE in metadata['_functions_by_name']
    
    return metadata

def get_training_text_questions(args, split):
    """Loads the training text questions for the template files if this is a validation split, so that we can avoid generating them for the validation split.
    Returns: {template_filename : []}
    """
    training_questions = dict()
    if split == VAL_SPLIT:
        for template_filename in args.question_templates:
            cleaned_template_filename = template_filename.split("_val")[0] # For templates with separate train and val versions.
            output_filename = os.path.join(args.output_questions_directory, f"{args.output_questions_prefix}_{TRAIN_SPLIT}_{cleaned_template_filename}.json")
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
    generate_all = (args.question_templates == [GENERATE_ALL_FLAG])
    candidate_template_files = [file for file in os.listdir(args.template_dir) if file.endswith('.json')]
    
    templates = dict()
    for candidate_template_file in candidate_template_files:
        template_class_name = candidate_template_file.split('.json')[0]
        if generate_all or (template_class_name in args.question_templates):
            full_template_filepath = os.path.join(args.template_dir, candidate_template_file)
            templates[template_class_name] = dict()
            
            with open(full_template_filepath, 'r') as f:
                question_templates = json.load(f)
                for question_idx, template in enumerate(question_templates):
                    template_key = (template_class_name, question_idx)
                    templates[template_class_name][template_key] = template
                    
                print(f'Read {len(templates[template_class_name])} question templates from {full_template_filepath}.')
    return templates

def generate_extended_questions_for_all_template_files(args, all_templates,
    dataset_split, metadata, all_scenes, all_grouped_scenes, training_text_questions):
    """
    Generates a set of questions for a set of template files, which should be from the 'extended template' set, all of which assume a common 'filterable' object format.
    For each template file, attempts to generate a set of n_instances_per_template questions.
    
    Avoids generating the same questions for train and val sets.
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
        
        questions_for_file = generate_questions_for_template_file(args, templates_for_file,
            dataset_split, metadata, all_scenes, all_grouped_scenes, training_questions_for_file)
        
        all_generated_questions[template_filename] = questions_for_file
    return all_generated_questions

def generate_questions_for_template_file(args, templates_for_file, dataset_split, metadata, all_scenes, grouped_scenes, training_questions_for_file):
    """
    Attempts to generate a set of questions for a single template file.
    Takes a single dict containing the question templates for a particular file in the form:
        {(template_filename, original_question_idx): template}
        
    For each question in the template file, attepts repeatedly to instantiate questions, up to a given number of tries.
    Returns a list of questions indexed for that template.
    """
    generated_questions = []
    templates_items = list(templates_for_file.items())
    for i, ((template_filename, template_index), template) in enumerate(templates_items):
        print(f'Trying question template {template_filename} {template_index} : {i}/{len(templates_items)} in this file.') 
        print(f"Question template text: {template['text'][0]}")
        
        instantiated_questions = instantiate_extended_template_multiple_inputs(all_scenes=all_scenes,
                                                      grouped_scenes=grouped_scenes,
                                                      template=template,
                                                      metadata=metadata,
                                                      max_instances=args.instances_per_template,
                                                      max_tries=args.max_generation_tries_per_instantiation,
                                                      training_questions_for_file=training_questions_for_file)
        postprocessed_questions = postprocess_instantiated_questions(instantiated_questions,
            dataset_split=dataset_split, template_filename=template_filename,
            template_index=template_index)
        
        postprocessed_questions = postprocessed_questions[:args.instances_per_template]
        generated_questions += postprocessed_questions
        
        # Display a sample of the final questions
        print(f"Sample question text:")
        for question in random.sample(postprocessed_questions, min(NUM_SAMPLE_QUESTIONS_TO_DISPLAY, len(postprocessed_questions))):
            print(f"\t: {question['question']}")
    
    # Add indices to all of the questions for this template file
    for question_index, question in enumerate(generated_questions):
        question['question_index'] = question_index
    
    print(f"Successfully generated {len(generated_questions)} questions.")
    return generated_questions

def instantiate_extended_template_multiple_inputs(all_scenes,
                                                  grouped_scenes,
                                                  template,
                                                  metadata,
                                                  max_instances=None, # Maximum instances of this template.
                                                  max_tries=1000,
                                                  print_every=100,
                                                  training_questions_for_file=None):
    """
    Attempts to generate text questions for the given question template.
    Attempts up to max_tries times to generate up to max_instances questions for the template.
    
    Returns {question_text : (scenes_object, programs, answers)}.
    """
    generated_text_questions = defaultdict(list)
    buckets_to_text = defaultdict(list)
    for curr_try in range(max_tries):
        if curr_try % print_every == 0:
            print(f"For this template, currently on try: {curr_try} / {max_tries}")
        template_copy = copy.deepcopy(template) # We modify the template while instantiating it
        text, programs, scenes, answers, did_succeed = instantiate_extended_template_from_grouped_scenes(all_scenes,
                                                        grouped_scenes,
                                                        template_copy, 
                                                        metadata)
        if not did_succeed: continue
        if text in generated_text_questions: continue # Don't repeat questions
        if text in training_questions_for_file: continue # Avoid training questions to prevent duplication in the validation set.
        generated_text_questions[text] = (scenes, programs, answers)
        
        buckets_to_text = get_valid_questions_by_text_length_bucket(generated_text_questions, metadata=metadata, num_buckets=3)
        
        if len(generated_text_questions) > max_instances:
            num_valid_questions_per_bucket = [len(value) for value in buckets_to_text.values()]
            num_buckets = len(buckets_to_text)
            # Break when we have roughly the minimum number for even distribution in each bucket.
            num_per_bucket = max((max_instances / num_buckets), 1)
            if min(num_valid_questions_per_bucket) >= num_per_bucket:
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
        q : generated_text_questions[q]
        for q in final_qs
    } 
    
    return text_questions

def get_valid_questions_by_text_length_bucket(text_questions, metadata, num_buckets=3):
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
    
    if len(buckets) == 0: # Special case: no buckets.
        buckets = [0, max_length + 1]
    elif buckets[-1] <= max_length:
        buckets.append(max_length + 1)
    # Buckets are keyed by (lower_bound, upper_bound) on question length
    buckets_to_text = {
        (buckets[i], buckets[i+1]) : []
        for i in range(len(buckets) - 1)
    }
    
    # Divvy up the questions by bucket length.
    for text_question in text_questions:
        length = text_questions_to_length[text_question]
        # Find the bucket it goes in
        for (lower_bound, upper_bound) in buckets_to_text:
            if (length >= lower_bound) and (length < upper_bound):
                buckets_to_text[(lower_bound, upper_bound)].append(text_question)
                
    return buckets_to_text
    
def postprocess_instantiated_questions(instantiated_questions,
    dataset_split, template_filename, template_index):
    """
    Post-processing on the set of questions generated by instantiate_extended_template_multiple_inputs.
    
    Takes: {question_text : (scenes_object, program, answers)}.
    Turns the questions into a single, structured dictionary object in the original CLEVR-questions format.
    """
    postprocessed_questions = []
    for question_text in instantiated_questions:
        scenes_object, program, answers = instantiated_questions[question_text]
        
        # Post-hoc renaming convention from the original Johnson et. al code.
        for f in program:
          if 'side_inputs' in f:
            f['value_inputs'] = f['side_inputs']
            del f['side_inputs']
          else:
            f['value_inputs'] = []
        
        postprocessed_questions.append({
            'split': dataset_split,
            'question': question_text,
            'template_filename': template_filename,
            'template_index': template_index,
            'question_index': None, # Will assign later.
            'image_filenames' : scenes_object['input_image_filenames'],
            'image_indices' : scenes_object['input_image_indexes'],
            'answers' : answers,
            'program' : program
        })
            
    return postprocessed_questions

def instantiate_extended_template_from_grouped_scenes(
    all_input_scenes,
    grouped_input_scenes,
    template,
    metadata):
    """
    Instantiates a template from the extended question format, which expects all questions to involve a single filter option (e.g. queries that involve first filtering on one or more attributes, and then running additional computations on that set of filtered objects.)

    To speed computation, this uses sets of grouped_input_scenes that have already instantiated their filter nodes. It choose one or more options from that set of shared attributes, then layers additional transformations or computations after it.
    Returns: instantiated_text (String text of instantiated program), program (an array of program nodes), input_scenes, answers, did_succeed (Boolean)
    """
    did_succeed = False # Flag set to indicate success instantiating
    
    # First, we construct the instantiated program itself, using a filter option selected from one of the grouped scenes. This involves destructively modifying the program nodes themselves. 
    # params are the placeholder parameter variables (e.g. <S>, Size) that must be grounded out into attributes
    instantiated_program, params, input_scenes = [], template["params"], None
    new_node_idxs = {i : i for i in range(len(template['nodes']))} # Mutable dictionary that maps the original program indices to their most recently updated pointer, since we 'expand' filter and transform nodes into more than one node.
    for original_idx, node in enumerate(template['nodes']):
        if node['type'] == 'scene': 
            instantiated_program.append(node)
        elif node['type'] == PRIMITIVE_FILTER: # Un-expanded filter node
            filter_program, input_scenes = build_filter_option(grouped_input_scenes=grouped_input_scenes, filter_node=node, constraints=template["constraints"], group=template['group'], params=params, original_idx=original_idx, curr_node_idx=len(instantiated_program), new_node_idxs=new_node_idxs)
            instantiated_program += filter_program
        elif node['type'] == PRIMITIVE_TRANSFORM: # Un-expanded transform node
            instantiated_program += build_transform_option(transform_node=node, constraints=template["constraints"], metadata=metadata, params=template['params'], original_idx=original_idx, curr_node_idx=len(instantiated_program), new_node_idxs=new_node_idxs)
        else:
            instantiated_program += build_other_instantiated_program_node(other_node=node, metadata=metadata, curr_node_idx=len(instantiated_program), original_idx=original_idx, new_node_idxs=new_node_idxs, params=params)
            
    # Build the program text
    instantiated_text = instantiate_question_text(template, params, template["constraints"])
    
    # Run the program on the scenes to generate the answers
    answers = []
    for input_image_index in input_scenes['input_image_indexes']:
        input_scene = all_input_scenes[int(input_image_index)]
        ans = extended_qeng.answer_question(instantiated_program, 
                                            metadata,
                                            input_scene, all_outputs=False, cache_outputs=False)
    
        answers.append(ans)
    # Don't allow the answers to all be identical
    if type(answers[0]) is not dict and len(set(answers)) < 2:
        return [], None, None, None, did_succeed
    
    did_succeed = True
    return instantiated_text, instantiated_program, input_scenes, answers, did_succeed

def build_filter_option(grouped_input_scenes, filter_node, constraints, group, params, original_idx, curr_node_idx, new_node_idxs):
    """
    Constructs the 'filter' program nodes for a full program.
    Expects a set of grouped_input_scenes with pre-instantiated filter programs, which it uses to generate the resulting program nodes.
        grouped_scenes are of the form: {
            group (e.g. UNIQUE/MULTIPLE) : {
                group_index : {
                    filter_options : [["Color", "red"], ["Material", "rubber"]],
                    filter_programs: [[program nodes], [program nodes]]
                }
            }
        }
        
    Returns:
        filter_program: [array of filter nodes that point to each other]
        grouped_scenes_object: the object for the corresponding grouped scenes we filtered on.
    Modifies: new_node_idx so that the filter node now points to the end of the filter chain.
    template['params'] to contain the instantiated parameter
    """
    assert (filter_node["type"] == PRIMITIVE_FILTER)
    # Select a set of grouped scenes with corresponding filterable attributes
    if "filter" not in constraints: # Unconstrained: any set of attributes will do.
        filter_option_idx = random.choice(list(grouped_input_scenes[group].keys()))
        grouped_scenes_object = grouped_input_scenes[group][filter_option_idx]
        filter_options = grouped_scenes_object["filter_options"]
    else: # Constrained: we must choose scenes with specific filter type requirements
        param_to_type = {p['name'] : p['type'] for p in params}
        # Directly search for a filter that meets the required constraints
        if constraints["filter"] == "choose_exactly":
            req_types = set([param_to_type[p] for p in filter_node['side_inputs']])
            candidate_grouped_scene_indices = []
            for candidate_index in grouped_input_scenes[group]:
                input_scenes = grouped_input_scenes[group][candidate_index]
                filter_options = input_scenes["filter_options"]
                filter_types = set([opt[0] for opt in filter_options]) # Options are (FilterType, FilterAttribute); this gets the type only
                if req_types == filter_types:
                    candidate_grouped_scene_indices.append(candidate_index)
            filter_option_idx = random.choice(candidate_grouped_scene_indices)
            grouped_scenes_object = grouped_input_scenes[group][str(filter_option_idx)]
            filter_options = grouped_scenes_object["filter_options"]
        else:
            print(f"Error: unknown filter constraint {constraints['filter']}.")
            assert False
    
    # Construct the filter program nodes themselves, using the updated pointer values.
    filter_program = []
    for i, (attr_type, attr_value) in enumerate(filter_options):
        # Redirect these nodes to filter from each other.
        assert len(filter_node['inputs']) == 1 # Should take only one input.
        input_idx = new_node_idxs[filter_node['inputs'][0]] if len(filter_program) == 0 else curr_node_idx + len(filter_program) - 1 # Redirect filter nodes to point to the previous node in the set 
        filter_program.append({
            "type": f"filter_{attr_type.lower()}",
            "side_inputs": [attr_value], # What to filter on
            "inputs": [input_idx]
        })
        for p in params: # Replace the grounding variables with their real values
            if p['type'] == attr_type and p['name'] in filter_node['side_inputs']:
                p['value'] = attr_value
    # Redirect anything that filtered from the unexpanded filter node to filter from the final filter node in the chain of filters.
    assert (new_node_idxs[original_idx]) == original_idx # Should not have been previously modified
    new_node_idxs[original_idx] = curr_node_idx + len(filter_program) - 1
    return filter_program, grouped_scenes_object

def build_transform_option(transform_node, constraints, metadata, params, original_idx, curr_node_idx, new_node_idxs):
    """
    Constructs the 'transform' program nodes for a full program.
    
    Expects a 'transform' node of the form: {
        inputs: [scene_node_idx, subset_of_scene_node_idx], 
        side_inputs: [<param_name>, <param_name>],
        constraints : []
    }
        
    Returns:
        transform_program: [array of transform nodes that point to each other]
    Modifies: new_node_idx so that the filter node now points to the end of the filter chain.
    template['params'] to contain the instantiated parameter
    """
    assert (transform_node['type'] == PRIMITIVE_TRANSFORM)
    # Expand the transform into several params that have not yet been used.
    param_to_type = {p['name'] : p['type'] for p in params}
    
    # Choose a subset of the parameters to instantiate.
    candidate_params= [param for param in params if param['name'] in transform_node['side_inputs']]
    if ("transform" in constraints and constraints["transform"] == "choose_all"):
        params_to_instantiate = candidate_params
    else:
        # Choose a non-empty random subset.
        num_params_to_instantiate = random.randint(1,len(candidate_params))
        params_to_instantiate = random.sample(candidate_params, num_params_to_instantiate)
    
    # Iteratively choose parameter values and construct transformation nodes.
    transform_program = []
    for param in params_to_instantiate:
        used_param_vals = set([p['value'] for p in params_to_instantiate if 'value' in p])
        param_type = param_to_type[param['name']]
        param_choices = set(metadata['types'][param_type]) - used_param_vals
        param_choice = random.choice(list(param_choices))
        param['value'] = param_choice
    
        # Redirect these transform nodes to take each other as the input scene
        input_scene = new_node_idxs[transform_node['inputs'][0]] if len(transform_program) < 1 else curr_node_idx + len(transform_program) - 1
        selector_set = new_node_idxs[transform_node['inputs'][1]]
        inputs = [input_scene, selector_set] # All transform arguments are of the form (input_scene, selector subset)
        
        transform_program.append({
            "type": f"transform_{param_type.lower()}",
            "side_inputs": [param_choice],
            "inputs": inputs
        })
    
    # Redirect anything that pointed to this node to take from the final transform node
    new_node_idxs[original_idx] = len(transform_program) + curr_node_idx - 1
    return transform_program
            
def build_other_instantiated_program_node(other_node, metadata, curr_node_idx, original_idx, new_node_idxs, params):
    """
    Constructs other forms of program nodes (such as remove), instantiating unbound parameters randomly and setting the node pointer indices to the updated values.
    
    Returns:
        instantiated_program: [array of nodes updated with instantiated params]
        grouped_scenes_object: the object for the corresponding grouped scenes we filtered on.
    Modifies: new_node_idx so that this node now points to its new current value in the potentially overall extended prgram.
    template['params'] to contain the instantiated parameters.
    """
    param_to_val = {p['name'] : p['value'] for p in params if 'value' in p}
    
    # Instantiate any unbound parameters.
    if 'side_inputs' not in other_node:
        side_inputs = []
    else:
        side_inputs = []
        for param_name in other_node['side_inputs']:
            if param_name in param_to_val:
                side_inputs.append(param_to_val[param_name])
            else:
                # Instantiate any unbound parameters.
                side_inputs.append(instantiate_param_random(param_name, metadata, params))
    
    instantiated_program =  [{
        "type" : other_node["type"],
        "side_inputs" : side_inputs,
        "inputs" : [new_node_idxs[old_idx] for old_idx in other_node["inputs"]]
    }]
    new_node_idxs[original_idx] = len(instantiated_program) + curr_node_idx - 1
    return instantiated_program

def instantiate_param_random(param_name, metadata, params):
    """
    Instantiates the param_name parameter by randomly selecting from the set of choices for a given parameter type.
    Modifies: params dictionary to include an instantiated value.
    """
    for p in params:
        if p['name'] == param_name:
            param_choices = set(metadata['types'][p['type']])
            param_choice = random.choice(list(param_choices))
            p['value'] = param_choice
            return p['value']
    assert False # We should have found the parameter we tried to instantiate.

def instantiate_question_text(template, params, constraints):
    """
    Returns a text question string with the original parameter variables (e.g. <S>) replaced with their grounded literal values.
    Takes: a template containing a text question with variable names, 
    params as a dict mapping those variable names to instantiated values,
    constraints_dict containing parameters that must be instantiated
    Returns: text, did_succeed flag (false if we failed to satisfy a constraint.)
    """
    assert len(template['text']) == 1 # The original CLEVR templates allowed synonyms.
    
    instantiated_text = template['text'][0]
    # Assert that we have instantiated at least one value.
    instantiated_params = [p for p in params if 'value' in p]
    assert len(instantiated_params) > 0
    for p in params:
        if 'value' not in p:
            if p['name'] in constraints:
                 assert False
            p_value = "" if p['type'] != 'Shape' else "thing"
        else:
            p_value = p['value']
        instantiated_text = instantiated_text.replace(p['name'], p_value)
    # Remove extraneous spaces
    instantiated_text = " ".join(instantiated_text.split())
    return instantiated_text

def write_output_questions_files(args, scene_info, all_generated_questions):
    split = scene_info['split']
    for template_filename in all_generated_questions:
        cleaned_template_filename = template_filename.split("_val")[0] # For templates with separate train and val versions.
        cleaned_template_filename = cleaned_template_filename.split("_train")[0] # For templates with separate train and val versions.
        generated_questions_for_template = all_generated_questions[template_filename]
        output_filename = os.path.join(args.output_questions_directory, f"{args.output_questions_prefix}_{split}_{cleaned_template_filename}.json")
        
        with open(output_filename, 'w') as f:
          print(f'Writing {len(generated_questions_for_template)} questions out to {output_filename}')
          json.dump({
              'info': scene_info,
              'questions': generated_questions_for_template
            }, f)
    
def main(args):
    set_random_seed(args)
    scenes_file, all_scenes, scene_info, grouped_scenes_file, all_grouped_scenes = get_input_scenes_and_grouped_scenes(args)
    training_text_questions = get_training_text_questions(args, scene_info['split'])
    
    metadata = get_question_metadata(args)
    all_question_templates = get_question_templates(args, metadata)
    
    all_generated_questions = generate_extended_questions_for_all_template_files(args, all_question_templates,
        scene_info['split'], metadata, all_scenes, all_grouped_scenes, training_text_questions)
    
    write_output_questions_files(args, scene_info, all_generated_questions)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)    