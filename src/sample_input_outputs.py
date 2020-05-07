"""
Utilities for sampling inputs and outputs of questions.
Generates an SCP script for copying over only the sampled images, and 
question_log files that print the question and the inputs / outputs in readable form.
"""
import argparse, json, os, random
from collections import defaultdict

SSH_PATH = "zyzzyva@openmind7.mit.edu"
CLEVR_PATHS = {
    "train": '/om2/user/zyzzyva/CLEVR_v1.0/images/train',
    "test": '/om2/user/zyzzyva/CLEVR_v1.0/images/test'
}

parser = argparse.ArgumentParser()

all_train_questions = [
    'CLEVR_train_1_zero_hop',
    'CLEVR_train_1_one_hop',
    'CLEVR_train_1_compare_integer',
    'CLEVR_train_1_same_relate',
    'CLEVR_train_1_single_or',
    'CLEVR_train_2_remove',
    'CLEVR_train_2_transform'
]

# Scene file and output settings
parser.add_argument("--num_questions_per_template", default=3, type=int,
                    help="The number of questions to render answer scene images for.")
parser.add_argument('--input_questions_dir', 
                    default='data/clevr_dreams/questions',
                    help="The base directory containing question files to render images for.")
parser.add_argument('--input_questions_files', 
                    nargs="*",
                    default=all_train_questions,
                    help="Which question files to generate scenes for.")
parser.add_argument('--input_scene_file',
                    default='data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json',
                    help="JSON file containing ground-truth scene information for all images from render_images.py")

# Collecting the files automatically
parser.add_argument("--output_dir",
                    default="data/clevr_dreams/images/")  


def main(args):
    # Load questions from disk.
    
    files_to_scp = set()
    
    for input_question_file in args.input_questions_files:
        question_fn = os.path.join(args.input_questions_dir, input_question_file + '.json')
        
        template_to_questions = defaultdict(list)
        with open(question_fn, 'r') as f:
            questions = json.load(f)
        for q in questions['questions']:
            template_idx = "%s_%s" % (q['template_filename'], q['template_index'])
            template_to_questions[template_idx].append(q['question_index'])
        
        # Scenes per template
        qs_per_template = {
            template_idx : random.sample(template_to_questions[template_idx], args.num_questions_per_template)
            for template_idx in template_to_questions
        }
        
        print("Found %d templates, sampling %d questions per template" % (len(qs_per_template), args.num_questions_per_template))
        
        questions_log = ""
        for i, template_idx in enumerate(qs_per_template):
            for j, q_idx in enumerate(qs_per_template[template_idx]):
                question = questions['questions'][q_idx]
                print("Now on scene %d / %d of %d / %d templates" % (
                    (j+1),
                    len(qs_per_template[template_idx]),
                    (i+1), 
                    len(qs_per_template)
                ))
                question = questions['questions'][q_idx]
                
                if type(question['answers'][0]) is dict: # Requires rendering
                    continue
                print("...found answer samples.")
                
                if type(question['question']) is list:
                    text = question['question'][0]
                else:
                    text = question['question']
                
                questions_log += f"TEMPLATE_INDEX, {template_idx}\n"
                questions_log += "INDEX, %d,\n" % q_idx
                questions_log += "QUESTION,"+text + "\n"
                
                # Get the image file names
                for k, (input_image_fn, answer) in enumerate(zip(question['image_filenames'], question["answers"])):
                    questions_log += f"INPUT_CLEVR_IMG, {input_image_fn}, ANSWER, {answer}\n"
                    files_to_scp.add(input_image_fn)
            questions_log += "\n\n"
        with open(os.path.join(args.output_dir, input_question_file + '_nonrendered_questions_log.txt'), 'w') as f:
            f.write(questions_log)
            
    # Write the SCP log
    if 'train' in args.input_scene_file:
        fn_prefix = CLEVR_PATHS['train']
    else:
        fn_prefix = CLEVR_PATHS['test']
    
    img_download_dir = os.path.join(args.output_dir, "original_images")
    if not os.path.isdir(img_download_dir):
        print("Making directory: %s "% (img_download_dir))
        os.makedirs(img_download_dir)
        
    print(f"Found {len(files_to_scp)} files to SCP.")
    full_fns = [os.path.join(fn_prefix, fn) for fn in files_to_scp]
    scp_command = f'scp -T {SSH_PATH}:"{" ".join(full_fns)}" "."'    
    with open(os.path.join(img_download_dir, 'scp_command.sh'), 'w') as f:
        f.write(scp_command)

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)