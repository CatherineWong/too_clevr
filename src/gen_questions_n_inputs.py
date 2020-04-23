"""
Generate questions with n I/O examples per scene.
"""
import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng

parser = argparse.ArgumentParser()


# Control the number of tasks we generate
parser.add_argument('--question_templates', default='None',
                    nargs='*',
                    help='Which question templates to generate for.')
parser.add_argument('--instances_per_template', default=1, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--num_scenes_per_question', default=3, type=int,
    help="The number of scenes that serve as examples for each image.")
parser.add_argument('--no_boolean', default=1, type=int, help='Whether to remove boolean questions from the dataset.')

# File handling.
parser.add_argument('--input_scene_file', default='data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json',
    help="JSON file containing ground-truth scene information for all images " +
         "from render_images.py")
parser.add_argument('--metadata_file', default='data/clevr_dreams/1_metadata.json',
    help="JSON file containing metadata about functions")
parser.add_argument('--template_dir', default='data/clevr_dreams/question_templates',
    help="Directory containing JSON templates for questions")


def main(args):
    with open(args.metadata_file, 'r') as f:
      metadata = json.load(f)
      dataset = metadata['dataset']
    functions_by_name = {}
    boolean_functions = {}
    for f in metadata['functions']:
      functions_by_name[f['name']] = f
      if f['output'] == 'Bool':
          boolean_functions[f['name']] = f
    metadata['_functions_by_name'] = functions_by_name
    metadata['_boolean_fns'] = boolean_functions
    
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
            if bool(args.no_boolean) and template['nodes'][-1]['type'] in metadata['_boolean_fns']:
                num_bool += 1
                continue
            else:
              num_loaded_templates += 1
              key = (fn, i)
              templates[key] = template
    print(f'Read {num_loaded_templates} templates from disk, skipped {num_bool} boolean templates.')
    

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
