"""
gen_n_inputs.py | Author : Catherine Wong

This takes a set of input scenes, then generates a set of grouped scenes (keyed by the shared objects and their attributes) that can be used to quickly create questions that involve filter queries for that object, and require multiple I/O scene examples.

These grouped scenes are the input for the generate_questions_extended.py pipeline for generating the new questions (e.g. scene transforming) in the extended version of the dataset.

TODO Produces a dict with:
    unique: exactly one object with the given property.
    multiple: any number of objects with the given property.
    
    Under each type: a list of 
        {
            attributes: [list of attributes]
            scenes: [list of scenes with objects of that attribute]
        }

TODO: example usage: 
"""
import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng
import question_utils as qutils
from collections import defaultdict, Counter

DEFAULT_TRAIN_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_train_scenes_5000.json"
DEFAULT_VAL_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_val_scenes_5000.json"

DEFAULT_GROUPING_TEMPLATE_FILE = "../metadata/clevr_shared_metadata/grouped_scenes/grouping_template.json"
DEFAULT_QUESTION_METADATA = "../metadata/clevr_original_metadata/1_metadata.json"

UNIQUE = 'unique'
MULTIPLE = 'multiple'
GROUPING_TEMPLATE_TYPES = [UNIQUE, MULTIPLE] # For 'filter unique' vs. 'filter multiple' query balancing

# File handling.
parser = argparse.ArgumentParser()
parser.add_argument('--random_seed', default=0)

# Arguments for the scenes used to generate inputs.
parser.add_argument('--default_train_scenes', help="If provided, we use a default set of training scenes.", action='store_true')
parser.add_argument('--default_val_scenes', help="If provided, we use a default set of validation scenes.", action='store_true')
parser.add_argument('--input_scene_file', 
    help="If provided, we reference a specific set of input scenes.")
    
# Which metadata file to use for the questions.
parser.add_argument('--metadata_file', default=DEFAULT_QUESTION_METADATA, help="JSON file containing metadata about functions")
# Which 'grouping template' to use: this contains default filter queries that are used to re-use existing functionality for creating non-degenerate filter groups.
parser.add_argument('--grouping_template_file', default=DEFAULT_GROUPING_TEMPLATE_FILE,
    help="JSON file containing template questions used to create filter groups.")
    
    
# Arguments that determine parameters of the questions we generate.   
 
parser.add_argument('--instances_per_template', default=50, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--n_scenes_per_question', default=5, type=int,
    help="The number of scenes that serve as examples for each image.")
parser.add_argument('--max_time_to_instantiate', default=100, type=int, help="The amount of time to spend attempting to instantiate on a given try.") 


# Arguments to determine where we write and store the output scenes.
parser.add_argument('--output_scenes_directory',
    help="Directory in which to write out the generated scenes.",
    required=True)
parser.add_argument('--output_scenes_prefix',
    default="grouped",
    help="If included, a different prefix for the output files.")

def set_random_seed(args):
    seed = args.random_seed
    print(f"Setting random seed to: {seed}")
    random.seed(seed)
    
def get_initial_input_scenes(args):
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
     
    print(f"Initializing with [{len(all_scenes)}] scenes from {scenes_file}")
    return scenes_file, all_scenes, scene_info

def get_question_metadata(args):
    with open(args.metadata_file, 'r') as f:
      metadata = json.load(f)
    functions_by_name = {}
    for f in metadata['functions']:
      functions_by_name[f['name']] = f
    metadata['_functions_by_name'] = functions_by_name
    return metadata

def get_grouping_templates(args):
    with open(args.grouping_template_file, 'r') as f:
        all_grouping_templates = json.load(f)
    
    # Check that the templates are all a single-filter.
    for template_type in all_grouping_templates:
        assert template_type in GROUPING_TEMPLATE_TYPES
        grouping_templates = all_grouping_templates[template_type]
        print(f"Read in {len(grouping_templates)} templates of type {template_type} from {args.grouping_template_file}")
        for grouping_template in grouping_templates:
            assert "nodes" in grouping_template
            program = grouping_template["nodes"]
            assert program[0]["type"] == "scene"
            assert (program[1]["type"] == "filter_unique") or (program[1]["type"] == "filter_count")
    return all_grouping_templates

def instantiate_template_with_filter_options(all_scenes,
                                            template,
                                            metadata,
                                            max_time,
                                            max_instances,
                                            n_scenes_per_question):
    """Attempts to instantiate a template and extracts the specific filter attributes and the relevant program nodes from the question template.
    
    Returns a dictionary keyed by the original text question used to generate it, because unique questions correspond to a unique group of scenes with the same filter basis.
    {text_question: [array of len n_scenes_per_question of (scene, filter_options, filter_program) tuples.]}
    """
    tic = time.time()
    text_questions = defaultdict(list)
    
    unique_scenes_per_text_question = Counter() # Keeps track of how many scenes have been instantiated so far for a given text question.
    
    random.shuffle(all_scenes)
    # Just try instantiating the questions for a set of scenes.
    for scene_index, scene in enumerate(all_scenes):
        if scene_index > 0 and scene_index % 100 == 0: print(f"On scene [{scene_index}/{len(all_scenes)}]")
        
        text_questions, programs, _ = qutils.instantiate_templates_dfs(
                        scene,
                        template,
                        metadata,
                        answer_counts=defaultdict(),
                        synonyms=[],
                        max_instances=max_instances,
                        verbose=False,
                        no_empty_filter=True)
        
        # Extract the attributes and program that we filter on for that query.
        for text_question_index, text_question in enumerate(ts):
            filter_options, filter_program = extract_filter_options(programs[text_question_index])
            text_questions[text_question].append((scene, filter_options, filter_program))
            
        unique_scenes_per_text_question.update(text_questions)
        questions_with_n_scenes = [q for q, count in unique_scenes_per_text_question.items() if count >= n_scenes_per_question] 
        if len(questions_with_n_scenes) >= max_instances:
            break
        toc = time.time()
        if (toc - tic) > max_time:
            print("Out of time!")
            break
    # Randomly sample among the question in valid qs.
    final_candidate_questions = random.sample(questions_with_n_scenes, min(max_instances, len(questions_with_n_scenes)))
    # Randomly sample among the scenes for that question.
    instantiated_questions = {
        question : random.sample(text_questions[question], n_scenes_per_question)
        for question in final_candidate_questions
    } 
    return instantiated_questions

def extract_filter_options(program):
    """
    Extracts the set of attributes on which we filtered, and the set of nodes doing the filtering, from a given instantiated program.
    
    Returns (tuple of (attribute_type, attribute)), (tuple of program nodes)
    """
    filter_options = []
    filter_program = []
    for node in program:
        if node['type'].startswith("filter"):
            attribute_type = node['type'].split("_")[1].title() # e.g. 'Color'
            attribute = q['side_inputs'][0]  # e.g. 'Color'
            filter_options.append((attribute_type, attribute))
        
        # Correct and add in the associated program, using the renaming convention 
        # in Johnson et. al
        if node['type'].startswith("filter") or node['type'].startswith("scene"):
            if 'side_inputs' in node:
              node['value_inputs'] = node['side_inputs']
              del node['side_inputs']
            else:
              node['value_inputs'] = []
            filter_program.append(node)
    return tuple(sorted(filter_options)), filter_program

def postprocess_instantiated_questions_into_grouped_scenes(
    instantiated_questions,
    current_grouped_scene_index
):
    """
    Post-processes the output of the instantiated questions into a dictionary of grouped_scene objects.
    Returns a dict of the form:
        {grouped_scene_index : 
            {
                "filter_options": (sorted tuple of attribute types),
                "input_image_filenames" : [string filenames],
                "input_image_indexes" : [int indexes],
                "filter_programs" : [
                    [array of program nodes]
                ]
            }
        }
    """
    grouped_scenes = defaultdict()
    for text_question in text_questions:
        # Instantiate a blank group object.
        group = {
            'filter_options': None,
            'input_image_filenames': [],
            'input_image_indexes' : [],
            'filter_programs' : [],
        }
        
        for scene, filter_options, filter_program in text_questions[text_question]:
            # Set the filter option once.
            if group['filter_options'] is None:
                group['filter_options'] = filter_options
            else:
                assert filter_options == group['filter_options'] 
            
            group['input_image_filenames'].append(scene['image_filename'])
            group['input_image_indexes'].append(int(os.path.splitext(scene['image_filename'])[0].split('_')[-1]))
            group['filter_programs'].append(filter_program)
        grouped_scenes[current_grouped_scene_index] = group
        current_grouped_scene_index += 1

    return current_grouped_scene_index, grouped_scenes

def generate_grouped_scenes_for_question_template(
                all_scenes,
                template,
                metadata,
                max_time,
                max_instances,
                n_scenes_per_question,
                current_grouped_scene_index):
    """Instantiates questions based on a template, then 
       post processes them into the grouped scene format.
    """
    instantiated_questions = instantiate_template_with_filter_options(all_scenes,
                                                template,
                                                metadata,
                                                max_time,
                                                max_instances,
                                                n_scenes_per_question)
    updated_grouped_scene_index, grouped_scenes = postprocess_instantiated_questions_into_grouped_scenes(instantiated_questions,curcurrent_grouped_scene_index)
    
    return updated_grouped_scene_index, grouped_scenes
    
def generate_grouped_scenes_for_all_question_templates(args, all_grouping_templates, all_scenes):
        # Initialize the final output type.
        all_grouped_scenes = {
            grouping_template_type : dict()
            for grouping_template_type in GROUPING_TEMPLATE_TYPES
        }
        
        current_grouped_scene_index = 0 # Global index for the grouped scenes.
        for grouping_template_type in all_grouping_templates:
            grouping_templates = all_grouping_templates[grouping_template_type]
            print(f"Now generating grouped scenes from the {len(grouping_templates)} templates of type: {grouping_template_type}"
            
            # Since there are fewer ways to generate 'multiple object' templates, we scale them up to balance the dataset/
            if grouping_template_type == MULTIPLE:
                n_instances_per_template = args.instances_per_template *            len(all_grouping_templates[UNIQUE])
            else:
                n_instances_per_template = args.instances_per_template

            for i, template in enumerate(grouping_templates):
                print(f"Attempting to instantiate {n_instances_per_template} instances of grouped scenes for template {i}/{len(grouping_templates)}")
                current_grouped_scene_index, grouped_scenes = generate_grouped_scenes_for_question_template(
                                all_scenes=all_scenes,
                                template=template,
                                metadata=metadata,
                                max_instances=n_instances_per_template,
                                max_time=args.max_time_to_instantiate,
                                n_scenes_per_question=args.n_scenes_per_question, 
                                current_grouped_scene_index=current_grouped_scene_index)
                grouped_scenes[count_type].update(grouped_scene)
                print(f"Found {len(grouped_scene)} scenes.")
        return all_grouped_scenes

def write_output_grouped_scenes_file(args, scene_info, input_scene_file, all_grouped_scenes):
    split = scene_info['split']
    output_filename = os.path.join(args.output_scenes_directory,
    f"{args.output_scenes_prefix}_{input_scene_file}")
    
    with open(output_filename, 'w') as f:
      print(f'Writing out grouped scenes to {output_filename}')
      json.dump({
          'info': scene_info,
          'grouped_scenes': grouped_scenes,
        }, f)        
    
def main(args):
    set_random_seed(args)
    input_scene_file, all_scenes, scene_info = get_input_scenes(args)
    metadata = get_question_metadata(args)
    all_grouping_templates = get_grouping_templates(args)
     
    all_grouped_scenes = generate_grouped_scenes_for_all_question_templates(args, all_grouping_templates, all_scenes)
    
    write_output_questions_files(args, scene_info, input_scene_file, all_grouped_scenes)        
    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
