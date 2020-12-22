#### Utilities for generating augmented CLEVR dataset.
import argparse, json, os, itertools, random, shutil
from pathlib import Path

"""utils.py | Author: Catherine Wong.
This contains utilities to:
    Generate a set of shared input scenes used across the various questsion.
"""

parser = argparse.ArgumentParser()

### Generate scene subsets
parser.add_argument('--generate_toy_first_n', default=None,
                    help="Generate a toy scene file containing the first n scenes.")

### Misc.
parser.add_argument("--output_scene_dir", default='data/clevr_dreams/scenes/')
parser.add_argument('--input_scene_file', default='data/clevr_no_images/scenes/CLEVR_train_scenes.json',
    help="JSON file containing ground-truth scene information for all images " +
         "from render_images.py")

def generate_toy_first_n(args):
    n = int(args.generate_toy_first_n)
    input_scene_name = os.path.basename(args.input_scene_file).split('.json')[0]
    output_scene_file = os.path.join(args.output_scene_dir, f'{input_scene_name}_{n}.json')
    Path(args.output_scene_dir).mkdir(parents=True, exist_ok=True)
    print(f"Generating toy first n; writing to {output_scene_file}")
    with open(args.input_scene_file, 'r') as f:
        scene_data = json.load(f)

    with open(output_scene_file, 'w') as f:
        json.dump({
        'info': scene_data['info'],
        'scenes' : scene_data['scenes'][:n]
        }, f)

def main(args):
    if args.generate_toy_first_n:
        generate_toy_first_n(args)
        return
    

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)