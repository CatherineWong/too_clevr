"""
Renders individual 'answer' output scenes using Blender, given a scene specification. This file expects to be run from Blender like this:
blender --background --python render_answers.py -- [arguments to this script].

Uses Blendr data files from the clevr-dataset-gen repo.
"""

from __future__ import print_function
import math, sys, random, argparse, json, os, tempfile
from datetime import datetime as dt
from collections import Counter, defaultdict

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
parser.add_argument("--render_inputs", default=1, type=int,
                    help="Also renders inputs.")
                    
parser.add_argument('--input_questions_dir', default='/Users/catwong/Desktop/zyzzyva/code/too_clevr/data/clevr_dreams/questions',
    help="The base directory containing question files to render images for.")
parser.add_argument('--input_questions_file', default='CLEVR_val_2_transform',
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

def render_scene(args,
                scene,
                question_index,
                answer_index,
                output_img,
                output_blendfile=None):
    # Load the main blendfile
    bpy.ops.wm.open_mainfile(filepath=args.base_scene_blendfile)

    # Load materials
    utils.load_materials(args.material_dir)

    
    
    # Set render arguments so we can get pixel coordinates later.
    # We use functionality specific to the CYCLES renderer so BLENDER_RENDER
    # cannot be used.
    render_args = bpy.context.scene.render
    # Where we will render to 
    render_args.filepath = output_img
    render_args.engine = "CYCLES"
    render_args.resolution_x = args.width
    render_args.resolution_y = args.height
    render_args.resolution_percentage = 100
    render_args.tile_x = args.render_tile_size
    render_args.tile_y = args.render_tile_size
    if args.use_gpu == 1:
      # Blender changed the API for enabling CUDA at some point
      if bpy.app.version < (2, 78, 0):
        bpy.context.user_preferences.system.compute_device_type = 'CUDA'
        bpy.context.user_preferences.system.compute_device = 'CUDA_0'
      else:
        cycles_prefs = bpy.context.user_preferences.addons['cycles'].preferences
        cycles_prefs.compute_device_type = 'CUDA'

    # Some CYCLES-specific stuff
    bpy.data.worlds['World'].cycles.sample_as_light = True
    bpy.context.scene.cycles.blur_glossy = 2.0
    bpy.context.scene.cycles.samples = args.render_num_samples
    bpy.context.scene.cycles.transparent_min_bounces = args.render_min_bounces
    bpy.context.scene.cycles.transparent_max_bounces = args.render_max_bounces
    if args.use_gpu == 1:
      bpy.context.scene.cycles.device = 'GPU'
    
    # Set the camera -- for now, we will just ignore the camera. 
     
    # Add the objects.
    add_objects(scene['objects'])
    
    # Render the scene
    while True:
      try:
        bpy.ops.render.render(write_still=True)
        break
      except Exception as e:
        print(e)

    if output_blendfile is not None:
      bpy.ops.wm.save_as_mainfile(filepath=output_blendfile)

def add_objects(objects):
    # Load the property file
    with open(args.properties_json, 'r') as f:
      properties = json.load(f)
      color_name_to_rgba = {}
      for name, rgb in properties['colors'].items():
        rgba = [float(c) / 255.0 for c in rgb] + [1.0]
        color_name_to_rgba[name] = rgba
      material_mapping = [(v, k) for k, v in properties['materials'].items()]
      object_mapping = [(v, k) for k, v in properties['shapes'].items()]
      size_mapping = list(properties['sizes'].items())

    shape_color_combos = None
    if args.shape_color_combos_json is not None:
      with open(args.shape_color_combos_json, 'r') as f:
        shape_color_combos = list(json.load(f).items())
    
    # Add individual objects
    blender_objects = []
    for obj_struct in objects:
        r = properties['sizes'][obj_struct['size']]
        rgba = properties['colors'][obj_struct['color']]
        obj_name = properties['shapes'][obj_struct['shape']]
        theta = obj_struct['rotation']
        xyz = obj_struct['3d_coords']
        
        # Actually add the object to the scene
        utils.add_object(args.shape_dir, obj_name, r, loc=None, theta=theta, xyz=xyz)
        obj = bpy.context.object
        blender_objects.append(obj) 
        
        # Attach the material
        mat_name = properties['materials'][obj_struct['material']]
        utils.add_material(mat_name, Color=rgba)
    return objects, blender_objects
    
def main(args):
    num_digits = 6
    prefix = '%s_' % (args.input_questions_file) 
    img_answer_template = '%s%%0%dd_answer_%%d.png' % (prefix, num_digits)
    img_answer_template = os.path.join(args.output_image_dir, args.input_questions_file, img_answer_template)
    
    img_input_template = '%s%%0%dd_input_%%d.png' % (prefix, num_digits)
    img_input_template = os.path.join(args.output_image_dir, args.input_questions_file, img_answer_template)
    
    if not os.path.isdir(args.output_image_dir):
        print("Making directory: %s "% (args.output_image_dir))
        os.makedirs(args.output_image_dir)
    
    input_fn = os.path.join(args.input_questions_dir, args.input_questions_file + '.json')
    with open(input_fn, 'r') as f:
        questions = json.load(f)
    # Find the scenes that we will be rendering for.
    template_to_questions = defaultdict(list)
    for q in questions['questions']:
        template_idx = "%s_%s" % (q['template_filename'], q['template_index'])
        template_to_questions[template_idx].append(q['question_index'])
    # Scenes per template
    qs_per_template = {
        template_idx : random.sample(template_to_questions[template_idx], args.num_questions_per_template)
        for template_idx in template_to_questions
    }
    print("Found %d templates, rendering %d questions per template" % (len(qs_per_template), args.num_questions_per_template))


    # Render scenes.
    questions_log = ""
    text_questions = {}
    for i, template_idx in enumerate(qs_per_template):
        for j, q_idx in enumerate(qs_per_template[template_idx]):
            print("Now on scene %d / %d of %d / %d templates" % (
                (j+1),
                len(qs_per_template[template_idx]),
                (i+1), 
                len(qs_per_template)
            ))
            question = questions['questions'][q_idx]
            if type(question['answers'][0]) is not dict:
                continue
            print("...found answer templates to render.")
            print("Rendering for: %s" %  question['question'])
            # For convenience, we will store and log the text questions
            text_questions[q_idx] = question['question']
            questions_log += "INDEX, %d,\n" % q_idx
            questions_log += "QUESTION,"+question['question'][0] + "\n"
            
            # if args.render_inputs:
            #     # Find and render the input scenes.
            #     img_path = img_input_template % (q_idx, k)
            #     questions_log += "IMG_INPUT,%s\n" % os.path.basename(img_path)
            
            for k, scene in enumerate(question['answers']):
                img_path = img_answer_template % (q_idx, k)
                questions_log += "IMG_ANSWER,%s\n" % os.path.basename(img_path)
                render_scene(args,
                            scene,
                            question_index=q_idx,
                            answer_index=k,
                            output_img=img_path)
                if k > 0: break
            

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

        
    
    
