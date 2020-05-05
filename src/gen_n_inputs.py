"""
Groups questions by their I/O properties. 
Produces a dict with:
    unique: exactly one object with the given property.
    multiple: any number of objects with the given property.
    
    Under each type: a list of 
        {
            attributes: [list of attributes]
            scenes: [list of scenes with objects of that attribute]
        }
"""
import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng
import question_utils as qutils
from collections import defaultdict, Counter

def check_constraints(param_name_to_type, template, state, outputs, scene_idx):
    # Check to make sure constraints are satisfied for the current state
    skip_state = False
    for constraint in template['constraints']:
      if constraint['type'] == 'NEQ':
        p1, p2 = constraint['params']
        v1, v2 = state['vals'][scene_idx].get(p1), state['vals'][scene_idx].get(p2)
        if v1 is not None and v2 is not None and v1 != v2:
          if verbose:
            print('skipping due to NEQ constraint')
            print(constraint)
            print(state['vals'])
          skip_state = True
          break
      elif constraint['type'] == 'NULL':
        p = constraint['params'][0]
        p_type = param_name_to_type[p]
        v = state['vals'][scene_idx].get(p)
        if v is not None:
          skip = False
          if p_type == 'Shape' and v != 'thing': skip = True
          if p_type != 'Shape' and v != '': skip = True
          if skip:
            if verbose:
              print('skipping due to NULL constraint')
              print(constraint)
              print(state['vals'][scene_idx])
            skip_state = True
            break
      elif constraint['type'] == 'OUT_NEQ':
        i, j = constraint['params']
        i = state['input_map'][scene_idx].get(i, None)
        j = state['input_map'][scene_idx].get(j, None)
        if i is not None and j is not None and outputs[scene_idx][i] == outputs[scene_idx][j]:
          if verbose:
            print('skipping due to OUT_NEQ constraint')
            print(outputs[scene_idx][i])
            print(outputs[scene_idx][j])
          skip_state = True
          break
      else:
        assert False, 'Unrecognized constraint type "%s"' % constraint['type']
    return skip_state

def extract_filter_options(program):
    filter_options = []
    filter_program = []
    for q in program:
        if q['type'].startswith("filter"):
            attribute_type = q['type'].split("_")[1].title() # e.g. 'Large'
            attribute = q['side_inputs'][0]
            filter_options.append((attribute_type, attribute))
        # Correct and add in the program.
        if q['type'].startswith("filter") or q['type'].startswith("scene"):
            if 'side_inputs' in q:
              q['value_inputs'] = q['side_inputs']
              del  q['side_inputs']
            else:
              q['value_inputs'] = []
            filter_program.append(q)
    return tuple(sorted(filter_options)), filter_program

def instantiate_templates_dfs(
                all_scenes,
                template,
                metadata,
                answer_counts=None,
                max_instances=None,
                n_scenes_per_question=None,
                max_time=100,
                curr_group_idx=None):
    
    tic = time.time()
    text_questions = defaultdict(list)
    
    scenes_per_q = Counter()
    random.shuffle(all_scenes)
    # Just try instantiating the questions for a set of scenes.
    for i, s in enumerate(all_scenes):
        if i > 0 and i % 100 == 0: print(f"On scene [{i}/{len(all_scenes)}]")
        ts, qs, ans = qutils.instantiate_templates_dfs(
                        s,
                        template,
                        metadata,
                        answer_counts=defaultdict(),
                        synonyms=[],
                        max_instances=max_instances,
                        verbose=False)
        
        for i, tq in enumerate(ts):
            filter_options, filter_program = extract_filter_options(qs[i])
            text_questions[tq].append((s, filter_options, filter_program))
        scenes_per_q.update(ts)
        valid_qs = [q for q, count in scenes_per_q.items() if count >= n_scenes_per_question] 
        if len(valid_qs) >= max_instances:
            break
        toc = time.time()
        if (toc - tic) > max_time:
            print("Out of time!")
            break
    
    # Randomly sample among the question in valid qs.
    final_qs = random.sample(valid_qs, min(max_instances, len(valid_qs)))
    text_questions = {
        q : random.sample(text_questions[q], n_scenes_per_question)
        for q in final_qs
    } 
    
    filter_groups = defaultdict()
    for i, q in enumerate(text_questions):
        group = {
            'filter_options': None,
            'input_image_filenames': [],
            'input_image_indexes' : [],
            'filter_programs' : [],
        }
        
        for s, filter_options, filter_program in text_questions[q]:
            if group['filter_options'] is None:
                group['filter_options'] = filter_options
            else:
                assert filter_options == group['filter_options'] 
            
            group['input_image_filenames'].append(s['image_filename'])
            group['input_image_indexes'].append(int(os.path.splitext(s['image_filename'])[0].split('_')[-1]))
            group['filter_programs'].append(filter_program)
        filter_groups[curr_group_idx] = group
        curr_group_idx += 1
    # Return this in a form indexed by the filter attributes.
    return curr_group_idx, filter_groups
# File handling.
parser = argparse.ArgumentParser()
parser.add_argument('--output_scenes_file', default='data/clevr_dreams/grouped_scenes/grouped_CLEVR_train_questions_1000.json',
    help="JSON file containing the ouput grouped scenes " +
         "from render_images.py")
parser.add_argument('--input_scene_file', default='data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json',
    help="JSON file containing ground-truth scene information for all images " +
         "from render_images.py")
parser.add_argument('--metadata_file', default='data/clevr_dreams/1_metadata.json',
    help="JSON file containing metadata about functions")
parser.add_argument('--grouping_template_file', default='data/clevr_dreams/grouped_scenes/grouping_template.json',
    help="Directory containing JSON templates for questions")
    
parser.add_argument('--instances_per_template', default=50, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--n_scenes_per_question', default=5, type=int,
    help="The number of scenes that serve as examples for each image.")

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
    
    # Load the one-hop template, which will be our guide.
    # Load templates from disk
    # Key is (filename, file_idx)
    with open(args.grouping_template_file, 'r') as f:
        templates = json.load(f)
    
    # Read file containing input scenes
    all_scenes = []
    with open(args.input_scene_file, 'r') as f:
      scene_data = json.load(f)
      all_scenes = scene_data['scenes']
      scene_info = scene_data['info']
     
    grouped_scenes = {
        count_type : dict()
        for count_type in templates
    }
    
    curr_group_idx = 0
    for count_type in templates:
        print(f"Object count_type: [{count_type}]; n={len(templates[count_type])} templates.")
        for i, template in enumerate(templates[count_type]):
            if count_type == 'multiple':
                n_instances = args.instances_per_template * len(templates['unique'])
            else:
                n_instances = args.instances_per_template
                
            print(f"Instantiating scenes for template {i}")
            curr_group_idx, filter_groups = instantiate_templates_dfs(
                            all_scenes,
                            template,
                            metadata,
                            max_instances=n_instances,
                            n_scenes_per_question=args.n_scenes_per_question, 
                            curr_group_idx=curr_group_idx)
            grouped_scenes[count_type].update(filter_groups)
            print(f"Found {len(filter_groups)} scenes, now on scene_idx {curr_group_idx}")
    with open(args.output_scenes_file, 'w') as f:
      print('Writing output to %s' % args.output_scenes_file)
      json.dump({
          'info': scene_info,
          'grouped_scenes': grouped_scenes,
        }, f)
                            
    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
