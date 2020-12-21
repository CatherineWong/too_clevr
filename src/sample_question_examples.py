"""
Utilities for sampling examples of questions to generate a testing suite.
"""
import argparse, json, os, random
from collections import defaultdict

parser = argparse.ArgumentParser()

all_train_questions = [
    'CLEVR_train_curriculum',
    'CLEVR_train_1_zero_hop',
    'CLEVR_train_1_one_hop',
    'CLEVR_train_1_compare_integer',
    'CLEVR_train_1_same_relate',
    'CLEVR_train_1_single_or',
    'CLEVR_train_2_remove',
    'CLEVR_train_2_transform'
]

parser.add_argument('--input_scene_file',
                    default='data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json',
                    help="JSON file containing ground-truth scene information for all images from render_images.py")
parser.add_argument('--input_questions_files', 
                    nargs="*",
                    default=all_train_questions,
                    help="Which question files to generate scenes for.")
parser.add_argument('--input_questions_dir', 
                    default='data/clevr_dreams/questions',
                    help="The base directory containing question files to render images for.")
# Collecting the files automatically
parser.add_argument("--output_filename",
                    default="example_questions")  

def main(args):
    # Load questions from disk.
    test_qs = {"questions" : []}
    for input_question_file in args.input_questions_files:
        question_fn = os.path.join(args.input_questions_dir, input_question_file + '.json')
        
        template_to_questions = defaultdict(list)
        with open(question_fn, 'r') as f:
            questions = json.load(f)
        for q in questions['questions']:
            template_idx = "%s_%s" % (q['template_filename'], q['template_index'])
            template_to_questions[template_idx].append(q['question_index'])
        
        # Scenes per template
        if "curriculum" in question_fn: 
            n_scenes = 2
        else:
             n_scenes = 1
        
        for template_idx in template_to_questions:
            sample_q_indices  = random.sample(template_to_questions[template_idx], n_scenes)
            sample_qs = [questions['questions'][q_idx] for q_idx in sample_q_indices]
            test_qs["questions"] += sample_qs

    output_fn = os.path.join(args.input_questions_dir, "CLEVR_train_" + args.output_filename + '.json')
    with open(output_fn, "w") as f:
        json.dump(test_qs, f)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)