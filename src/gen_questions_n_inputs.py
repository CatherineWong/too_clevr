"""
Generate questions with n I/O examples per scene.
"""
import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng
import question_utils as qutils
from collections import defaultdict, Counter

parser = argparse.ArgumentParser()


# Control the number of tasks we generate
parser.add_argument('--question_templates', default='None',
                    nargs='*',
                    help='Which question templates to generate for.')
parser.add_argument('--instances_per_template', default=5, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--n_scenes_per_question', default=4, type=int,
    help="The number of scenes that serve as examples for each image.")
parser.add_argument('--no_boolean', default=1, type=int, help='Whether to remove boolean questions from the dataset.')

# File handling.
parser.add_argument('--output_questions_file', default='data/clevr_dreams/questions/CLEVR_train_questions_1000.json',
    help="JSON file containing ground-truth scene information for all images " +
         "from render_images.py")
parser.add_argument('--input_scene_file', default='data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json',
    help="JSON file containing ground-truth scene information for all images " +
         "from render_images.py")
parser.add_argument('--metadata_file', default='data/clevr_dreams/1_metadata.json',
    help="JSON file containing metadata about functions")
parser.add_argument('--template_dir', default='data/clevr_dreams/question_templates',
    help="Directory containing JSON templates for questions")

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
    
def instantiate_templates_dfs(
                all_scenes,
                template,
                metadata,
                answer_counts,
                max_instances=None,
                n_scenes_per_question=None):
    
    text_questions = defaultdict(list)
    
    scenes_per_q = Counter()
    random.shuffle(all_scenes)
    # Just try instantiating the questions for a set of scenes.
    for s in all_scenes:
        ts, qs, ans = qutils.instantiate_templates_dfs(
                        s,
                        template,
                        metadata,
                        answer_counts,
                        synonyms=[],
                        max_instances=1000,
                        verbose=False)
        for i, tq in enumerate(ts):
            text_questions[tq].append((s, qs[i], ans[i])) 
        
        scenes_per_q.update(ts)
        valid_qs = [q for q, count in scenes_per_q.items() if count >= n_scenes_per_question] 
        if len(valid_qs) >= max_instances:
            break
    
    # Try to get a range of questions.
    # Randomly sample among the question in valid qs.
    final_qs = random.sample(valid_qs, max_instances)
    text_questions = {
        q : random.sample(text_questions[q], n_scenes_per_question)
        for q in final_qs
    } 
    return text_questions

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
    
    # Read file containing input scenes
    all_scenes = []
    with open(args.input_scene_file, 'r') as f:
      scene_data = json.load(f)
      all_scenes = scene_data['scenes']
      scene_info = scene_data['info']
      
    def reset_counts():
      # Maps a template (filename, index) to the number of questions we have
      # so far using that template
      template_counts = {}
      # Maps a template (filename, index) to a dict mapping the answer to the
      # number of questions so far of that template type with that answer
      template_answer_counts = {}
      node_type_to_dtype = {n['name']: n['output'] for n in metadata['functions']}
      for key, template in templates.items():
        template_counts[key[:2]] = 0
        final_node_type = template['nodes'][-1]['type']
        final_dtype = node_type_to_dtype[final_node_type]
        answers = metadata['types'][final_dtype]
        if final_dtype == 'Bool':
          answers = [True, False]
        if final_dtype == 'Integer':
          if metadata['dataset'] == 'CLEVR-v1.0':
            answers = list(range(0, 11))
        template_answer_counts[key[:2]] = {}
        for a in answers:
          template_answer_counts[key[:2]][a] = 0
      return template_counts, template_answer_counts
    template_counts, template_answer_counts = reset_counts()
    
    questions = []
    templates_items = list(templates.items())
    for i, ((fn, idx), template) in enumerate(templates_items):
        print(f'trying template {fn} {idx} : {i}/{len(templates_items)}') 
        ts = instantiate_templates_dfs(
                        all_scenes,
                        template,
                        metadata,
                        template_answer_counts[(fn, idx)],
                        max_instances=args.instances_per_template,
                        n_scenes_per_question=args.n_scenes_per_question)
        for t in ts:
            scenes, programs, answers = [spa[0] for spa in ts[t]], [spa[1] for spa in ts[t]], [spa[-1] for spa in ts[t]]
            scene_fns = [scene['image_filename'] for scene in scenes]
            img_indices = [int(os.path.splitext(scene_fn)[0].split('_')[-1]) for scene_fn in scene_fns]
            
            # Fix the programs as per the original code.
            for p in programs:
                for f in p:
                  if 'side_inputs' in f:
                    f['value_inputs'] = f['side_inputs']
                    del f['side_inputs']
                  else:
                    f['value_inputs'] = []
            
            questions.append({
                'split': scene_info['split'],
                'question': t,
                'template_filename': fn,
                'question_family_index': idx,
                'question_index': len(questions),
                'image_filenames' : scene_fns,
                'image_indices' : img_indices,
                'answers' : answers,
                'program' : programs
            })
    
    print(f"Generated {len(questions)} questions!")
    with open(args.output_questions_file, 'w') as f:
      print('Writing output to %s' % args.output_questions_file)
      json.dump({
          'info': scene_info,
          'questions': questions,
        }, f)
        

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
