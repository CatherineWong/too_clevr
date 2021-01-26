"""
render_answers.py | Author : Catherine Wong
This outputs the output scenes for questions that require scene transformations, given a symbolic scene specification.

It expects a Blender material files from the original clever-dataset-gen repo.
It also expects a set of question files.

Example usage:
    blender --background --python render_answers.py --
        --question_templates 2_localization
        --splits train val
        --num_questions_per_template -1 # For all scenes
"""

from __future__ import print_function
import math, sys, random, argparse, json, os, tempfile
from datetime import datetime as dt
from collections import Counter, defaultdict
import pathlib

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

DATASET_SPLIT_NAMES = ['train', 'val']
DEFAULT_CLEVR_PREFIX = 'CLEVR'
SPLIT_TAG = "split"
QUESTION_CLASS_TAG = "question_class"
QUESTIONS_TO_RENDER_TAG = 'questions_to_render'
OUTPUT_DIR_TAG = 'output_dir'
ANSWER_IMAGE_FILENAME_TEMPLATE_TAG  = 'answer_image_filename'
INPUT_IMAGE_FILENAME_TEMPLATE_TAG  = 'input_image_filename'
OUTPUT_IMAGE_DICT_FILENAME = "output_images.json"
DISTRACTOR_IMAGE_DICT_FILENAME = "distractor_images.json"

DEFAULT_IMAGE_DATA_DIR = "/Users/catwong/Desktop/zyzzyva/code/too_clevr/metadata/clevr_shared_metadata/image_generation_data"
DEFAULT_BLEND_FILE = "base_scene.blend"
DEFAULT_PROPERTIES_FILE = "properties.json"
DEFAULT_SHAPE_FILES_DIR = "shapes"
DEFAULT_MATERIALS_FILE_DIR = 'materials'

DEFAULT_TOP_LEVEL_CLEVER_DATA_DIR = "/Users/catwong/Desktop/zyzzyva/code/too_clevr/data/"
DEFAULT_DATASET_DIR = "clevr_icml_2021"
DEFAULT_QUESTIONS_DIR = "questions"
DEFAULT_IMAGE_OUTPUT_DIR = "images"
parser = argparse.ArgumentParser()

# Scene file and output settings
parser.add_argument('--question_templates', 
                    nargs='*',
                    help='Which question templates to generate for.')
parser.add_argument('--splits', 
                    nargs='*',
                    help='Which splits to generate for.')
parser.add_argument("--num_scenes_per_question", default=3, type=int,
                    help="The maximum number of scenes we render per question..")
parser.add_argument("--start_at_scene", default=3, type=int,
                                        help="Which scene to start at, if we have already rendered some.")
parser.add_argument("--num_questions_per_template", default=1, type=int,
                    help="The number of questions to render answer scene images for. If -1, we render all of the questions for a given template.")
parser.add_argument("--render_inputs", default=1, type=int,
                    help="Also re-render the inputs. [Not yet implemented]")
parser.add_argument("--render_distractors", action='store_true',
                    help="Only render the distractors. [Not yet implemented]")

# Scene storage settings.   
parser.add_argument('--input_questions_dir', default=os.path.join(DEFAULT_TOP_LEVEL_CLEVER_DATA_DIR, DEFAULT_DATASET_DIR, DEFAULT_QUESTIONS_DIR),
    help="The base directory containing question files to render images for.")
parser.add_argument('--output_image_dir', default=os.path.join(DEFAULT_TOP_LEVEL_CLEVER_DATA_DIR, DEFAULT_DATASET_DIR, DEFAULT_IMAGE_OUTPUT_DIR),
    help="The base directory where output images will be stored. It will be " +
         "created if it does not exist.")
         
# Input BLENDR options
parser.add_argument('--base_scene_blendfile', default=os.path.join(DEFAULT_IMAGE_DATA_DIR, DEFAULT_BLEND_FILE), help="Base blender file on which all scenes are based; includes ground plane, lights, and camera.")
parser.add_argument('--properties_json', default=os.path.join(DEFAULT_IMAGE_DATA_DIR, DEFAULT_PROPERTIES_FILE), help="JSON file defining objects, materials, sizes, and colors. ")
parser.add_argument('--shape_dir', default=os.path.join(DEFAULT_IMAGE_DATA_DIR, DEFAULT_SHAPE_FILES_DIR), help="Directory where .blend files for object models are stored")
parser.add_argument('--material_dir', default=os.path.join(DEFAULT_IMAGE_DATA_DIR, DEFAULT_MATERIALS_FILE_DIR), help="Directory where .blend files for materials are stored")
parser.add_argument('--shape_color_combos_json', default=None,
    help="Optional path to a JSON file mapping shape names to a list of " +
         "allowed color names for that shape. This allows rendering images " +
         "for CLEVR-CoGenT.")
parser.add_argument('--save_blendfiles', type=int, default=0, help="Setting --save_blendfiles 1 will cause the blender scene file for each generated image to be stored in the directory specified by " +
"the --output_blend_dir flag. These files are not saved by default because they take up ~5-10MB each.")

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
                output_img):
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

    ### Old inherited plane code.
    # This will give ground-truth information about the scene and its objects
    # Put a plane on the ground so we can compute cardinal directions
    bpy.ops.mesh.primitive_plane_add(radius=5)
    plane = bpy.context.object

    def rand(L):
      return 2.0 * L * (random.random() - 0.5)

    # Add random jitter to camera position
    if args.camera_jitter > 0:
      for i in range(3):
        bpy.data.objects['Camera'].location[i] += rand(args.camera_jitter)

    # Figure out the left, up, and behind directions along the plane and record
    # them in the scene structure
    camera = bpy.data.objects['Camera']
    plane_normal = plane.data.vertices[0].normal
    cam_behind = camera.matrix_world.to_quaternion() * Vector((0, 0, -1))
    cam_left = camera.matrix_world.to_quaternion() * Vector((-1, 0, 0))
    cam_up = camera.matrix_world.to_quaternion() * Vector((0, 1, 0))
    plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
    plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
    plane_up = cam_up.project(plane_normal).normalized()

    # Delete the plane; we only used it for normals anyway. The base scene file
    # contains the actual ground plane.
    utils.delete_object(plane)
    ####
    
    objects, blender_objects = add_objects(scene['objects'])
    
    # Add random jitter to lamp positions
    if args.key_light_jitter > 0:
      for i in range(3):
        bpy.data.objects['Lamp_Key'].location[i] += rand(args.key_light_jitter)
    if args.back_light_jitter > 0:
      for i in range(3):
        bpy.data.objects['Lamp_Back'].location[i] += rand(args.back_light_jitter)
    if args.fill_light_jitter > 0:
      for i in range(3):
        bpy.data.objects['Lamp_Fill'].location[i] += rand(args.fill_light_jitter)
    
    # Render the scene and dump the scene data structure
    while True:
      try:
        bpy.ops.render.render(write_still=True)
        break
      except Exception as e:
        print(e)

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
     
    # Add individual objects
    blender_objects = []
    for obj_struct in objects:
        r = properties['sizes'][obj_struct['size']]
        rgba = color_name_to_rgba[obj_struct['color']]
        obj_name = properties['shapes'][obj_struct['shape']]
        theta = obj_struct['rotation']
        (x, y, z) = obj_struct['3d_coords']
        
        # For cube, adjust the size a bit
        if obj_name == 'Cube':
          r /= math.sqrt(2)
        
        # Actually add the object to the scene
        utils.add_object(args.shape_dir, obj_name, r, (x, y), theta=theta)
        obj = bpy.context.object
        blender_objects.append(obj)
        
        # Attach a random material
        mat_name =  properties['materials'][obj_struct['material']]
        utils.add_material(mat_name, Color=rgba)
    return objects, blender_objects

def get_metadata_from_question_file(args, candidate_question_file):
    """
    Returns (split, class) from the {PREFIX}_{SPLIT}_{QUESTION_CLASS}.json file
    """
    split_question_file = candidate_question_file.split("_")
    assert split_question_file[0] == DEFAULT_CLEVR_PREFIX
    dataset_split = split_question_file[1]
    assert dataset_split  in DATASET_SPLIT_NAMES
    question_class = "_".join(split_question_file[2:]).split(".json")[0]
    return dataset_split, question_class
    
def get_questions_to_render_for_template(args, question_file):
    """Loads the questions for a given file and samples only a few per template if need be."""
    with open(question_file, 'r') as f:
        questions = json.load(f)
        
    # Find the scenes that we will be rendering for.
    template_to_questions = defaultdict(list)
    for q in questions['questions']:
        if type(q['answers'][0]) == type(dict()):
            template_idx = "%s_%s" % (q['template_filename'], q['template_index'])
            template_to_questions[template_idx].append(q)
    # Scenes per template
    qs_per_template = {
        template_idx : random.sample(template_to_questions[template_idx], args.num_questions_per_template if args.num_questions_per_template > 0 else len(template_to_questions[template_idx]))
        for template_idx in template_to_questions
    }
    print("For question file : %s, found a total of %d templates. Rendering up to %d questions per template" % (question_file, len(qs_per_template), args.num_questions_per_template))
    return qs_per_template

    
def get_all_questions_for_templates(args):
    """Loads all the questions for the templates, sampling a limited subset if applicable.
    Returns a dict of the form: {
        question_input_file : [
            'questions_to_render' : {
                question_template_idx : [list of questions]
            'split' : split,
            'question_class' : question_class
            }
        ]
    }"""
    question_files_to_questions_to_render = dict()
    
    candidate_question_files = [candidate_file for candidate_file in os.listdir(args.input_questions_dir) if candidate_file.endswith(".json")]
    for candidate_question_file in candidate_question_files:
        (dataset_split, question_class) = get_metadata_from_question_file(args, candidate_question_file)
        if dataset_split in args.splits and question_class in args.question_templates:
            full_question_filepath = os.path.join(args.input_questions_dir, candidate_question_file)
            questions_to_render = get_questions_to_render_for_template(args, full_question_filepath)
            question_files_to_questions_to_render[full_question_filepath] = {
                QUESTIONS_TO_RENDER_TAG : questions_to_render,
                SPLIT_TAG : dataset_split,
                QUESTION_CLASS_TAG : question_class
            }
    return question_files_to_questions_to_render
            
def get_all_output_dirs_for_question_files(args, questions_to_render):
    """Creates all of the output directories for the corresponding question templates.
    Modifies: questions_to_render
    """
    for question_file in questions_to_render:
        split, dataset_name = questions_to_render[question_file][SPLIT_TAG], questions_to_render[question_file][QUESTION_CLASS_TAG]
        output_directory = os.path.join(args.output_image_dir, dataset_name, split)
        pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
        questions_to_render[question_file][OUTPUT_DIR_TAG] = output_directory
    return questions_to_render

def get_image_scene_file_name_templates(args, questions_to_render):
    """
    Creates the standardized template naming convention for the output images, which will be updated for the corresponding scenes, of the form: DIR/{question_template}/{question_template}_{question}_answer_{answer_number}.png
    Mutates: questions_to_render
    """
    num_digits_in_filename = 6
    for question_file in questions_to_render:
        split, dataset_name = questions_to_render[question_file][SPLIT_TAG], questions_to_render[question_file][QUESTION_CLASS_TAG]
        output_directory = questions_to_render[question_file][OUTPUT_DIR_TAG]
        prefix = '%s_%s_%s' % (DEFAULT_CLEVR_PREFIX, split, dataset_name)
        
        img_answer_template = '%s%%0%dd_answer_%%d.png' % (prefix, num_digits_in_filename)
        img_answer_template = os.path.join(output_directory, img_answer_template)
    
        img_input_template = '%s%%0%dd_input_%%d.png' % (prefix, num_digits_in_filename)
        img_input_template = os.path.join(output_directory, img_input_template)
        questions_to_render[question_file][ANSWER_IMAGE_FILENAME_TEMPLATE_TAG] = img_answer_template
        questions_to_render[question_file][INPUT_IMAGE_FILENAME_TEMPLATE_TAG] = img_input_template
    return questions_to_render

def add_distractor_to_image_path(img_path, distractor_idx):
    basename = img_path.split(".png")[0]
    basename += "_distractor_" + str(distractor_idx)
    return basename + ".png"
def iteratively_render_all_scenes(args, questions_to_render):
    for question_file in questions_to_render:
        task_name_to_images = defaultdict(list)
        question_class = questions_to_render[question_file][QUESTION_CLASS_TAG]
        questions_per_template_for_class = questions_to_render[question_file][QUESTIONS_TO_RENDER_TAG]
        img_answer_template = questions_to_render[question_file][ANSWER_IMAGE_FILENAME_TEMPLATE_TAG]
        for i, template_idx in enumerate(questions_per_template_for_class):
            for j, question_object in enumerate(questions_per_template_for_class[template_idx]):
                print("Now on scene %d / %d of %d / %d templates\n" % (
                    (j+1),
                    len(questions_per_template_for_class[template_idx]),
                    (i+1), 
                    len(questions_per_template_for_class)
                ))
                question_text = question_object['question']
                task_name = "%d-%s-%s" % (question_object['question_index'], question_class, question_text)
                print("Rendering for: %s" %  question_text)
                
                for k, scene in enumerate(question_object['answers'][:args.num_scenes_per_question]):
                    if k < args.start_at_scene: continue
                    img_path = img_answer_template % (question_object['question_index'], k)
                    
                    if args.render_distractors:
                        if k < len(question_object['distractors']):
                            distractors_for_answer = question_object['distractors'][k]
                            for distractor_idx, distractor_scene in enumerate(distractors_for_answer):
                                img_path = add_distractor_to_image_path(img_path, distractor_idx)
                                render_scene(args,
                                            distractor_scene,
                                            question_index=question_object['question_index'],
                                            answer_index=k,
                                            output_img=img_path)
                    else:
                        render_scene(args,
                                    scene,
                                    question_index=question_object['question_index'],
                                    answer_index=k,
                                    output_img=img_path)
                    base_name = os.path.basename(img_path)
                    task_name_to_images[task_name].append(base_name)
        output_dir = questions_to_render[question_file][OUTPUT_DIR_TAG]
        write_out_rendered_image_file(args, output_dir, task_name_to_images)

def write_out_rendered_image_file(args, output_dir, task_name_to_images):
    """Writes out the JSON file containing the image filenames."""
    output_filename = OUTPUT_IMAGE_DICT_FILENAME if not args.render_distractors else DISTRACTOR_IMAGE_DICT_FILENAME
    output_filename= os.path.join(output_dir, OUTPUT_IMAGE_DICT_FILENAME)
    with open(output_filename, 'w') as f:
        json.dump(task_name_to_images, f)   

def main(args):
    questions_to_render = get_all_questions_for_templates(args)
    questions_to_render =  get_all_output_dirs_for_question_files(args, questions_to_render)
    questions_to_render = get_image_scene_file_name_templates(args, questions_to_render)
    iteratively_render_all_scenes(args, questions_to_render)
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

        
    
    
