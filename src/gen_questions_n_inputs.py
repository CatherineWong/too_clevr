"""
Generate questions with n I/O examples per scene.
"""
import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng
import question_utils as qutils

parser = argparse.ArgumentParser()


# Control the number of tasks we generate
parser.add_argument('--question_templates', default='None',
                    nargs='*',
                    help='Which question templates to generate for.')
parser.add_argument('--instances_per_template', default=1, type=int,
    help="The number of times each template should be instantiated.")
parser.add_argument('--n_scenes_per_question', default=3, type=int,
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
    text_questions, structured_questions, answers = [], [], []
    
    # Hacky -- just try instantiating all of the templates for a given set of scenes.
    initial_scenes = random.sample(all_scenes,n_scenes_per_question)
    ts, qs, ans = qutils.instantiate_templates_dfs(
                    initial_scenes[0],
                    template,
                    metadata,
                    answer_counts,
                    synonyms=[],
                    max_instances=None,
                    verbose=False)
    import pdb; pdb.set_trace()
    
    param_name_to_type = {p['name']: p['type'] for p in template['params']} 
    initial_scenes = random.sample(all_scenes,n_scenes_per_question)
    initial_state = {
      'nodes': [qutils.node_shallow_copy(template['nodes'][0])],
      'vals': { i: {} for (i, _) in enumerate(initial_scenes)},
      'input_map': { i: {0:0} for (i, _) in enumerate(initial_scenes)},
      'next_template_node': 1,
      'scenes' : { i: s for (i, s) in enumerate(initial_scenes)}
    }
    states = [initial_state]
    final_states = []
    while states:
      state = states.pop()
      
      # Evaluate the current state on all of the scenes.
      q = {'nodes': state['nodes']}
      outputs = {i : qeng.answer_question(q, metadata, state['scenes'][i], all_outputs=True, cache_outputs=False) for i in state['scenes']}
      answers = {i : outputs[i][-1] for i in outputs}
      new_scenes = {
        i : state['scenes'][i]
        for i in state['scenes'] if outputs[i][-1] != '__INVALID__'
      }
      if len(new_scenes) == 0: continue
      state['scenes'] = new_scenes
      
      # Check to make sure constraints are satisfied for the current state on all the vals.
      fails_constraints = {scene_idx : check_constraints(param_name_to_type, template, state, outputs, scene_idx) for scene_idx in state['scenes']}
     
      new_scenes = {
        i : state['scenes'][i]
        for i in state['scenes'] if not fails_constraints[i]
      }
      if len(new_scenes) == 0: continue
      state['scenes'] = new_scenes
      
      # We have already checked to make sure the answer is valid, so if we have
      # processed all the nodes in the template then the current state is a valid
      # question, so add it if it passes our rejection sampling tests.
      if state['next_template_node'] == len(template['nodes']):
        # TODO: add back in the template count satisfaction criteria.

        # If the template contains a raw relate node then we need to check for
        # degeneracy at the end
        has_relate = any(n['type'] == 'relate' for n in template['nodes'])
        if has_relate:
            degen = {i : qeng.is_degenerate(q, metadata, state['scenes'][i], answer=answers[i]) for i in state['scenes']}
            new_scenes = {
              i : state['scenes'][i]
              for i in state['scenes'] if not degen[i]
            }
            if len(new_scenes) == 0: continue
            state['scenes'] = new_scenes
        state['answers'] = answers
        final_states.append(state)
        if max_instances is not None and len(final_states) == max_instances:
          break
        continue
    
      # Get the next node from the template.
      next_node = template['nodes'][state['next_template_node']]
      next_node = qutils.node_shallow_copy(next_node)
      special_nodes = {
          'filter_unique', 'filter_count', 'filter_exist', 'filter',
          'relate_filter', 'relate_filter_unique', 'relate_filter_count',
          'relate_filter_exist',
      }
      # Calculate filter options across the scenes.
      filter_options = {}
      if next_node['type'] in special_nodes:
          for i in state['scenes']:
            if next_node['type'].startswith('relate_filter'):
              unique = (next_node['type'] == 'relate_filter_unique')
              include_zero = (next_node['type'] == 'relate_filter_count'
                              or next_node['type'] == 'relate_filter_exist')
              for k, v in qutils.find_relate_filter_options(answers[i], state['scenes'][i], metadata ,unique=unique, include_zero=include_zero).items():
                if k not in filter_options: filter_options[k] = dict()
                filter_options[k][i] = v
            else:
              initial_filter_options = qutils.find_filter_options(answers[i], state['scenes'][i], metadata) 
              if next_node['type'] == 'filter':
                # Remove null filter
                for i in filter_options:
                    initial_filter_optionss[i].pop((None, None, None, None), None)
              if next_node['type'] == 'filter_unique':
                # Get rid of all filter options that don't result in a single object
                initial_filter_options = {k: v for k, v in initial_filter_options.items()
                                  if len(v) == 1}
              else:
                # Add some filter options that do NOT correspond to the scene
                if next_node['type'] == 'filter_exist':
                  # For filter_exist we want an equal number that do and don't
                  num_to_add = len(initial_filter_options)
                elif next_node['type'] == 'filter_count' or next_node['type'] == 'filter':
                  # For filter_count add nulls equal to the number of singletons
                  num_to_add = sum(1 for k, v in initial_filter_options.items() if len(v) == 1)
                initial_filter_options = qutils.add_empty_filter_options(initial_filter_options, metadata, num_to_add)
            for k, v in initial_filter_options.items():
                if k not in filter_options: filter_options[k] = dict()
                filter_options[k][i] = v
          
          # Find filter option keys that are valid across multiple scenes.
          filter_option_keys = list(filter_options.keys())
          random.shuffle(filter_option_keys)
          for k in filter_option_keys:
            new_nodes = []
            for scene_idx in filter_option_keys[k]:
                cur_next_vals = {k: v for k, v in state['vals'][scene_idx].items()}
                next_input = state['input_map'][scene_idx][next_node['inputs'][0]]
                filter_side_inputs = next_node['side_inputs']
            

    return text_questions, structured_questions, answers

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
        ts, qs, ans = instantiate_templates_dfs(
                        all_scenes,
                        template,
                        metadata,
                        template_answer_counts[(fn, idx)],
                        max_instances=args.instances_per_template,
                        n_scenes_per_question=args.n_scenes_per_question)
                        

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
