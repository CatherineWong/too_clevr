"""
Renders individual 'answer' output scenes using Blender, given a scene specification. This file expects to be run from Blender like this:
blender --background --python render_answers.py -- [arguments to this script].

Uses Blendr data files from the clevr-dataset-gen repo.
"""

from __future__ import print_function
import math, sys, random, argparse, json, os, tempfile
from datetime import datetime as dt
from collections import Counter

INSIDE_BLENDER = True
try:
  import bpy, bpy_extras
  from mathutils import Vector
except ImportError as e:
  INSIDE_BLENDER = False
if INSIDE_BLENDER:
  try:
    import utils
  except ImportError as e:
    print("\nERROR")
    print("Running render_images.py from Blender and cannot import utils.py.") 
    print("You may need to add a .pth file to the site-packages of Blender's")
    print("bundled python with a command like this:\n")
    print("echo $PWD >> $BLENDER/$VERSION/python/lib/python3.5/site-packages/clevr.pth")
    print("\nWhere $BLENDER is the directory where Blender is installed, and")
    print("$VERSION is your Blender version (such as 2.78).")
    sys.exit(1)


parser = argparse.ArgumentParser()

# Input BLENDR options
parser.add_argument('--base_scene_blendfile', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data_gen/clevr-dataset-gen/image_generation/data/base_scene.blend',
    help="Base blender file on which all scenes are based; includes " +
          "ground plane, lights, and camera.")
parser.add_argument('--properties_json', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data_gen/clevr-dataset-gen/image_generation/data/properties.json',
    help="JSON file defining objects, materials, sizes, and colors. " +
         "The \"colors\" field maps from CLEVR color names to RGB values; " +
         "The \"sizes\" field maps from CLEVR size names to scalars used to " +
         "rescale object models; the \"materials\" and \"shapes\" fields map " +
         "from CLEVR material and shape names to .blend files in the " +
         "--object_material_dir and --shape_dir directories respectively.")
parser.add_argument('--shape_dir', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data_gen/clevr-dataset-gen/image_generation/data/shapes',
    help="Directory where .blend files for object models are stored")
parser.add_argument('--material_dir', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data_gen/clevr-dataset-gen/image_generation/data/materials',
    help="Directory where .blend files for materials are stored")
parser.add_argument('--shape_color_combos_json', default=None,
    help="Optional path to a JSON file mapping shape names to a list of " +
         "allowed color names for that shape. This allows rendering images " +
         "for CLEVR-CoGenT.")

# Scene file and output settings
parser.add_argument("--num_questions_per_template", default=1, type=int,
                    help="The number of questions to render answer scene images for.")
parser.add_argument('--input_questions_dir', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data/clevr_dreams/questions',
    help="The base directory containing question files to render images for.")
parser.add_argument('--input_questions_file', default='CLEVR_extended_questions',
    help="The base directory containing question files to render images for.")
parser.add_argument('--output_image_dir', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data/clevr_dreams/images',
    help="The base directory where output images will be stored. It will be " +
         "created if it does not exist.")
parser.add_argument('--save_blendfiles', type=int, default=0,
    help="Setting --save_blendfiles 1 will cause the blender scene file for " +
         "each generated image to be stored in the directory specified by " +
         "the --output_blend_dir flag. These files are not saved by default " +
         "because they take up ~5-10MB each.")

# Rendering options
parser.add_argument('--use_gpu', default=0, type=int,
    help="Setting --use_gpu 1 enables GPU-accelerated rendering using CUDA. " +
         "You must have an NVIDIA GPU with the CUDA toolkit installed for " +
         "to work.")
parser.add_argument('--width', default=320, type=int,
    help="The width (in pixels) for the rendered images")
parser.add_argument('--height', default=240, type=int,
    help="The height (in pixels) for the rendered images")
parser.add_argument('--key_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the key light position.")
parser.add_argument('--fill_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the fill light position.")
parser.add_argument('--back_light_jitter', default=1.0, type=float,
    help="The magnitude of random jitter to add to the back light position.")
parser.add_argument('--camera_jitter', default=0.5, type=float,
    help="The magnitude of random jitter to add to the camera position")
parser.add_argument('--render_num_samples', default=512, type=int,
    help="The number of samples to use when rendering. Larger values will " +
         "result in nicer images but will cause rendering to take longer.")
parser.add_argument('--render_min_bounces', default=8, type=int,
    help="The minimum number of bounces to use for rendering.")
parser.add_argument('--render_max_bounces', default=8, type=int,
    help="The maximum number of bounces to use for rendering.")
parser.add_argument('--render_tile_size', default=256, type=int,
    help="The tile size to use for rendering. This should not affect the " +
         "quality of the rendered image but may affect the speed; CPU-based " +
         "rendering may achieve better performance using smaller tile sizes " +
         "while larger tile sizes may be optimal for GPU-based rendering.")

def main(args):
    num_digits = 6
    prefix = '%s_' % (args.input_questions_file) 
    img_template = '%s%%0%dd.png' % (prefix, num_digits)
    img_template = os.path.join(args.output_image_dir, args.input_questions_file, img_template)
    
    if not os.path.isdir(args.output_image_dir):
        print(f"Making directory: {args.output_image_dir}")
        os.makedirs(args.output_image_dir)
    
    input_fn = os.path.join(args.input_questions_dir, args.input_questions_file + '.json')
    with open(input_fn, 'r') as f:
        questions = json.load(f)
    # Find the scenes that we will be rendering for.
    template_to_questions = defaultdict(list)
    for q in questions['questions']:
        template_idx = f"{q['template']}_{q['template_idx']}"
        template_to_questions[template_idx].append(q['question_index'])
    # Scenes per template
    qs_per_template = {
        template_idx : random.choice(template_to_questions[template_idx], args.num_questions_per_template)
    }
    print(f"Found {len(qs_per_template)} templates, rendering {args.num_questions_per_template} questions per template.")

if __name__ == '__main__':
  if INSIDE_BLENDER:
    # Run normally
    argv = utils.extract_args()
    args = parser.parse_args(argv)
    main(args)
  elif '--help' in sys.argv or '-h' in sys.argv:
    parser.print_help()
  else:
    print('Warning: not running inside Blender.')
    # Run normally
    args = parser.parse_args()
    main(args)

        
    
    
