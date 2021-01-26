"""
gen_distractor_output_scenes.py | Author : Catherine Wong 
Generates additional 'distractor' outputs for running multiple choice human experiments on scene -> scene tasks. 
Specifically, updates each question with a set of n_distractor choices for each of the desired 'test' questions. Writes over the question files with the updated objects.

Example usage:
    python gen_distractor_output_scenes.py
        --input_questions_directory DIRECTORY
        --question_classes all
"""
import argparse, json, os, random, copy

GENERATE_ALL_FLAG = 'all'
DEFAULT_CLEVR_PREFIX = "CLEVR"
DATASET_SPLIT_NAMES = ['train', 'val']
DEFAULT_TRAIN_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_train_scenes_5000.json"
DEFAULT_VAL_SCENES = "../metadata/clevr_shared_metadata/scenes/CLEVR_val_scenes_5000.json"
DISTRACTOR_TAG = 'distractors'
MAX_TRIES = 5 # Maximum tries to not generate a matching scene. Otherwise we'll just randomly remove some from the front.

ATTRIBUTE_TYPES = {
    'color' : ["gray", "red", "blue", "green", "brown", "purple", "cyan", "yellow"],
    'size' : ["small", "large"],
    "material" : ["rubber", "metal"]
}

parser = argparse.ArgumentParser()
parser.add_argument('--random_seed', default=0)
parser.add_argument('--input_questions_dir', required=True,
    help="Top level directory under which we will write the question files.")
parser.add_argument('--question_classes', 
                    nargs='*',
                    help='Which question classes to generate for, or "all" for all in the language directory.')
parser.add_argument('--num_answers_per_question',
                    type=int,
                    default=2,
                    help='How many answers per question we need to generate distractors for.')
parser.add_argument('--num_distractors_per_answer',
                    type=int,
                    default=4,
                    help='How many distractors to generate per answer.')

def set_random_seed(args):
    seed = args.random_seed
    print(f"Setting random seed to: {seed}")
    random.seed(seed)
    
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

def get_input_scenes(args):
    input_scenes = dict()
    for split, scenes_file in [('train', DEFAULT_TRAIN_SCENES), ('val', DEFAULT_VAL_SCENES)]:
        with open(scenes_file, 'r') as f:
            scene_data = json.load(f)
            all_scenes = scene_data['scenes']
            scene_info = scene_data['info']
            print(f"Using [{len(all_scenes)}] {split} scenes from {scenes_file}")
            input_scenes[split] = all_scenes
    return input_scenes

def iteratively_generate_and_write_out_distractor_files(args, question_files_and_metadata, input_scenes):
    for question_file in question_files_and_metadata:
        full_question_filepath = os.path.join(args.input_questions_dir, question_file)
        (split, dataset_name) = question_files_and_metadata[question_file]
        print(f"Reading restricted dataset for {full_question_filepath}...")
        with open(full_question_filepath, 'r') as f:
            input_questions_file_object = json.load(f)
            distractor_augmented_file_object = add_distractors_for_question_file_object(args, input_questions_file_object, input_scenes[split])
        # Write out the processed questions object.
        print(f"Writing restricted questions back to {full_question_filepath}")
        with open(full_question_filepath, 'w') as f:
            json.dump(distractor_augmented_file_object, f) 

def add_distractors_for_question_file_object(args, input_questions_file_object, input_scenes):
    """
    Takes an input file object and returns an object where the 'questions' array contains updated questions containing distractor scenes.
    Mutates: input_questions_file_object
    """
    assert 'questions' in input_questions_file_object
    input_questions = input_questions_file_object["questions"]
    distractor_augmented_questions = []
    for input_question in input_questions:
        distractor_augmented_question = add_distractors_for_question(args, input_question, input_scenes)
        distractor_augmented_questions.append(distractor_augmented_question)
    input_questions_file_object["questions"] = distractor_augmented_questions
    return input_questions_file_object

def check_differing_scenes(scene_1, scene_2):
    """
    Check if two scenes are different. Return True if not.
    """
    # First check if the scenes simply have different objects.
    scene_1_objs, scene_2_objs = scene_1['objects'], scene_2['objects']
    scene_1_obj_ids = set([obj['id'] for obj in scene_1_objs])
    scene_2_obj_ids = set([obj['id'] for obj in scene_2_objs])
    if scene_1_obj_ids !=  scene_2_obj_ids : return True
    # Second check
    sorted_scene_1 = sorted(scene_1['objects'], key=lambda o : o['id'])
    sorted_scene_2 = sorted(scene_2['objects'], key=lambda o : o['id'])
    for obj_1, obj_2 in zip(sorted_scene_1, sorted_scene_2):
        for attribute_type in ATTRIBUTE_TYPES:
            if obj_1[attribute_type] != obj_2[attribute_type]:
                return True
    return False

def get_copied_scene(input_scene):
    """Gets a deep copy of a scene."""
    return copy.deepcopy(input_scene)
    
def remove_some_random_objects_if_possible(input_scene, true_answer):
    """
    Fallback distractor transformation. Removes some random number of objects if its possible to keep at least one and not match the true answer; returns None if not applicable (e.g. the input_scene only has 1 object).
    """
    input_scene = get_copied_scene(input_scene)
    input_scene_objects = input_scene['objects']
    true_answer_objects = true_answer['objects']
    # We will keep between (1, input_scene-1 objects) except for len(true_answer) objects
    possible_to_keep = set(range(1, len(input_scene_objects) - 2)) - set([len(true_answer_objects)])
    if len(possible_to_keep) == 0: return None
    num_objects_to_keep = random.choice(list(possible_to_keep))
    remaining_objects = random.sample(input_scene_objects, num_objects_to_keep)
    input_scene['objects'] = remaining_objects
    return input_scene
    
def transform_some_random_attribute(input_scene, true_answer):
    """
    Fallback distractor transformation. Transforms a random attribute on an object.
    """
    input_scene_objects = input_scene['objects']
    true_answer_objects = true_answer['objects']
    scene_to_transform = true_answer if len(true_answer_objects) > 0 else input_scene
    scene_to_transform  = get_copied_scene(scene_to_transform)
    attribute_to_change = random.choice(list(ATTRIBUTE_TYPES.keys()))
    # Change that attribute on all of the objects.
    existing_attribute_value = scene_to_transform['objects'][0][attribute_to_change]
    possible_attribute_options = set(ATTRIBUTE_TYPES[attribute_to_change]) - set([existing_attribute_value])
    new_attribute_value = random.choice(list(possible_attribute_options))
    for obj in scene_to_transform['objects']:
        obj[attribute_to_change] = new_attribute_value
    return scene_to_transform

def gen_distractor_random_filter_input_scene(input_scene, true_answer):
    """Randomly filters on an attribute and insures the result is not the true answer."""
    input_scene = get_copied_scene(input_scene)
    input_scene_objects = input_scene['objects']
    base_object = random.choice(input_scene_objects)
    num_attributes_to_filter = random.choice([1, 2]) # More than this and it gets tricky
    attributes_to_filter = random.sample(list(ATTRIBUTE_TYPES.keys()), num_attributes_to_filter)
    attributes_to_keep = {
        attribute: base_object[attribute] for attribute in  attributes_to_filter
    }
    final_objects = []
    for object in input_scene_objects:
        should_keep = True
        for attribute, attribute_value in attributes_to_keep.items():
            if object[attribute] != attribute_value:
                should_keep = False
        if should_keep:
            final_objects.append(object)
    input_scene['objects'] = final_objects
    return input_scene, attributes_to_keep
    
def gen_distractor_random_remove_input_scene(input_scene, true_answer):
    """Randomly removes using an attribute that is disjoint with the true answer."""
    input_scene = get_copied_scene(input_scene)
    input_scene_objects = input_scene['objects']
    base_object = random.choice(input_scene_objects)
    num_attributes_to_filter = random.choice([1, 2]) # More than this and it gets tricky
    attributes_to_filter = random.sample(list(ATTRIBUTE_TYPES.keys()), num_attributes_to_filter)
    attributes_to_remove = {
        attribute: base_object[attribute] for attribute in  attributes_to_filter
    }
    final_objects = []
    for object in input_scene_objects:
        for attribute, attribute_value in attributes_to_remove.items():
            if object[attribute] != attribute_value:
                final_objects.append(object)
    input_scene['objects'] = final_objects
    return input_scene, attributes_to_remove

def gen_distractor_random_transform_input_scene(input_scene, true_answer):
    """Randomly transforms on an attribute."""
    input_scene = get_copied_scene(input_scene)
    input_scene_objects = input_scene['objects']
    base_object = random.choice(input_scene_objects)
    num_attributes_to_filter = random.choice([1, 2]) # More than this and it gets tricky
    attributes_to_filter = random.sample(list(ATTRIBUTE_TYPES.keys()), num_attributes_to_filter)
    attributes_to_filter_on = {
        attribute: base_object[attribute] for attribute in  attributes_to_filter
    }
    attribute_to_transform = random.choice(list(ATTRIBUTE_TYPES.keys()))
    # Something other than the base objects attribute
    new_candidate_values = set(ATTRIBUTE_TYPES[attribute_to_transform]) - set([base_object[attribute_to_transform]])
    transformed_value = random.choice(list(new_candidate_values))
    
    final_objects = []
    for object in input_scene_objects:
        should_transform = True
        for attribute, attribute_value in attributes_to_filter_on.items():
            if object[attribute] != attribute_value:
                should_transform = False
        if should_transform:
            object[attribute_to_transform] = transformed_value
        final_objects.append(object)
    input_scene['objects'] = final_objects
    return input_scene, {
        'filter_on': attributes_to_filter_on,
        'transformed_to': (attribute_to_transform, transformed_value)
    }
    
def generate_distractor_and_check_not_same_for_max_tries(max_tries, distractor_fn, input_scene, true_answer):
    """
    Runs the distractor_fn up to max_tries times and then just executes a random remove otherwise.
    """
    for one_try in range(max_tries):        
        new_scene, _ = distractor_fn(input_scene, true_answer)
        if check_differing_scenes(true_answer, new_scene):
            return new_scene
    # Failed to generate a new scene. Try removing some random number of objects.
    removed_object_scene = remove_some_random_objects_if_possible(input_scene, true_answer)
    if removed_object_scene is not None:
        return removed_object_scene 
    # Failed to remove an object. Just change an attribute on the true answer.
    return transform_some_random_attribute(input_scene, true_answer)
    
def add_object_ids_to_input(input_scene):
    """
    Helper method to add input IDs to the input scene.
    Mutates input scene
    """
    for obj_id, obj in enumerate(input_scene['objects']):
        obj['id'] = obj_id
    return input_scene
    
def add_distractors_for_question(args, input_question, input_scenes):
    """
    Adds distractors by randomly sampling a type of distractor to add.
    Always samples at least one of each type if possible. Distractors can be random transformations, random removals, structured (filter-based) removals; or structured (filter-based) transformations.

    """ 
    example_output = input_question['answers'][0]
    if type(example_output) != type(dict()):
        return input_question
        
    distractor_fns = [
        gen_distractor_random_filter_input_scene,
        gen_distractor_random_remove_input_scene,
        gen_distractor_random_transform_input_scene
    ]
    # We only generate questions for a subset of answers
    input_image_indices = input_question['image_indices'][:args.num_answers_per_question]
    all_distractors = []
    for example_idx, input_image_idx in enumerate(input_image_indices):
        input_scene, true_answer = input_scenes[input_image_idx], input_question['answers'][example_idx]
        input_scene = add_object_ids_to_input(input_scene)
        # Generate up to args.num_distractors_per_answer distractors
        distractors_for_input = []
        for i in range(args.num_distractors_per_answer):
            distractor_fn_idx = i if i < len(distractor_fns) else random.randint(0, len(distractor_fns) - 1)
            distractor_fn = distractor_fns[distractor_fn_idx]
            distractor_scene = generate_distractor_and_check_not_same_for_max_tries(MAX_TRIES, distractor_fn, input_scene, true_answer)
            distractors_for_input.append(distractor_scene)
        all_distractors.append(distractors_for_input)
    input_question[DISTRACTOR_TAG] = all_distractors
    return input_question

def main(args):
    set_random_seed(args)
    question_files_and_metadata = get_question_files_and_metadata(args)
    input_scenes = get_input_scenes(args)
    iteratively_generate_and_write_out_distractor_files(args, question_files_and_metadata, input_scenes)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)  