import argparse, json, os, itertools, random, shutil
import time
import re
import extended_question_engine as extended_qeng
import question_utils as qutils
from collections import defaultdict, Counter

def uniform_bernoulli_flip():
    return random.uniform(0, 1) > 0.5

def build_filter_option(grouped_input_scenes, f, group, params):
    # Select a filter option from the grouped input scenes.
    filter_option_idx = random.randint(0, len(grouped_input_scenes[group]))
    input_scenes = grouped_input_scenes[group][str(filter_option_idx)]
    filter_options = input_scenes["filter_options"]
    
    filter_program = []
    for attr_type, attr_value in filter_options:
        filter_program.append({
            "type": f"filter_{attr_type.lower()}",
            "side_inputs": [attr_value],
            "inputs": f['inputs']
        })
        for p in params: 
            if p['type'] == attr_type and p['name'] in f['side_inputs']:
                p['value'] = attr_value
    return filter_program, input_scenes

def build_transform_option(f, metadata, params):
    # Expand the transform into several params that have not yet been used.
    param_to_type = {p['name'] : p['type'] for p in params}
    transform_program = []
    for param in params:
        if param['name'] in f['side_inputs']:
            if uniform_bernoulli_flip():
                used_param_vals = set([p['value'] for p in params if 'value' in p])
                param_type = param_to_type[param['name']]
                param_choices = set(metadata['types'][param_type]) - used_param_vals
                param_choice = random.choice(list(param_choices))
                param['value'] = param_choice
                transform_program.append({
                    "type": f"transform_{param_type.lower()}",
                    "side_inputs": [param_choice],
                    "inputs": f['inputs']
                })
    return transform_program

def instantiate_question_text(template, params):
    instantiated_texts = []
    for template_text in template['text']:
        instantiated_text = template_text
        for p in params:
            if 'value' not in p:
                p_value = "" if p['type'] != 'Shape' else "thing"
            else:
                p_value = p['value']
            instantiated_text = instantiated_text.replace(p['name'], p_value)
        # Remove extraneous spaces
        instantiated_text = " ".join(instantiated_text.split())
        instantiated_texts.append(instantiated_text)
    return instantiated_texts

def instantiate_template(
    all_input_scenes,
    grouped_input_scenes,
    template,
    metadata):
    """Instantiate template scenes with a single filter option.
    Choose from the preselected 'filter' and layer additional transformations
    on top.
    """
    program, params, input_scenes = [], template["params"], None
    # Build up the instantiated program.
    for f in template['nodes']:
        if f['type'] == 'scene':
            program.append(f)
        elif f['type'] == 'filter':
            filter_program, input_scenes = build_filter_option(grouped_input_scenes, f, template['group'], params)
            program += filter_program
        elif f['type'] == 'transform':
            program += build_transform_option(f, metadata, params)
        else:
            assert False
    # Build the program text
    instantiated_text = instantiate_question_text(template, params)
    
    # Run the program on the scenes to generate the answers
    answers = []
    for input_image_index in input_scenes['input_image_indexes']:
        input_scene = all_input_scenes[int(input_image_index)]
        answers.append(extended_qeng.answer_question(program, 
                                                    metadata,
                                                    input_scene, all_outputs=False, cache_outputs=False))
        import pdb; pdb.set_trace()

def instantiate_templates_extended(all_input_scenes,
                                   grouped_input_scenes,
                                   template,
                                   metadata,
                                   max_instances,
                                   max_time=100):
    final_qs = []
    text_questions = set()
    tic = time.time()
    while True:
        t, q, input_scenes, ans = instantiate_template(all_input_scenes,
                                           grouped_input_scenes,
                                           template,
                                           metadata) 
        if t not in text_questions:
            text_questions.add(t)
            final_qs.append({
                'question': t,
                # TODO: rest of scene data
            })
        
        toc = time.time()
        if (toc - tic) > max_time:
            print("Out of time!")
            break         


# File handling.
parser = argparse.ArgumentParser()

parser.add_argument('--question_templates', 
                    nargs='*',
                    default=['2_transform_one_hop'],
                    help='Which question templates to generate for.')
parser.add_argument('--instances_per_template', default=15, type=int,
    help="The number of times each template should be instantiated.")

parser.add_argument('--input_scene_file', default='data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json',
    help="JSON file containing ground-truth scene information for all input images from render_images.py")
parser.add_argument('--input_grouped_scenes_file', default='data/clevr_dreams/grouped_scenes/grouped_CLEVR_train_questions_1000.json', help="JSON file containing the ouput grouped scenes from render_images.py")
parser.add_argument('--metadata_file', default='data/clevr_dreams/2_metadata.json',
    help="JSON file containing metadata about functions")
parser.add_argument('--template_dir', default='data/clevr_dreams/question_templates',
    help="Directory containing JSON templates for questions")
parser.add_argument('--output_questions_file', default='data/clevr_dreams/questions/CLEVR_extended_questions.json')

def main(args):
    with open(args.metadata_file, 'r') as f:
      metadata = json.load(f)
      dataset = metadata['dataset']
    functions_by_name = {}
    for f in metadata['functions']:
      functions_by_name[f['name']] = f
    metadata['_functions_by_name'] = functions_by_name
    
    # Load templates from disk
    # Key is (filename, file_idx)
    num_loaded_templates = 0
    num_bool = 0
    templates = {}
    for fn in os.listdir(args.template_dir):
      if not fn.endswith('.json'): continue
      if args.question_templates is not None and os.path.basename(fn.split('.json')[0]) not in args.question_templates:
          continue
      with open(os.path.join(args.template_dir, fn), 'r') as f:
        base = os.path.splitext(fn)[0]
        for i, template in enumerate(json.load(f)):
            num_loaded_templates += 1
            key = (fn, i)
            templates[key] = template
    print(f'Read {num_loaded_templates} templates from disk.')
    
    # Read file containing input scenes
    all_scenes = []
    with open(args.input_scene_file, 'r') as f:
      scene_data = json.load(f)
      all_scenes = scene_data['scenes']
      scene_info = scene_data['info']
    
    # Read file containing input grouped scene templates.
    with open(args.input_grouped_scenes_file, 'r') as f:
        scene_data = json.load(f)
        grouped_scenes = scene_data['grouped_scenes']
    
    questions = []
    templates_items = list(templates.items())
    for i, ((fn, idx), template) in enumerate(templates_items):
        print(f'trying template {fn} {idx} : {i}/{len(templates_items)}') 
        instantiate_templates_extended(all_scenes,
                                       grouped_scenes,
                                       template,
                                       metadata,
                                       args.instances_per_template)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)    