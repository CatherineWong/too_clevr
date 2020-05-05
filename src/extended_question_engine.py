import json, os, math, copy
from collections import defaultdict

"""
Extended question handler, which handles scenes involving counterfactuals and 
other CLEVR-Humans inspired questions.
Draws closely on: https://github.com/facebookresearch/clevr-dataset-gen
Utilities for working with function program representations of questions.

Some of the metadata about what question node types are available etc are stored
in a JSON metadata file.
"""

def scene_handler(scene_struct, inputs, side_inputs):
  # Just return all objects in the scene
  return scene_struct['objects']

def make_filter_handler(attribute):
  def filter_handler(scene_struct, inputs, side_inputs):
    assert len(inputs) == 1
    assert len(side_inputs) == 1
    value = side_inputs[0]
    output = []
    for obj in inputs[0]:
      atr = obj[attribute]
      if value == atr or value in atr:
        output.append(idx)
    return output
  return filter_handler
  
def make_transform_handler(attribute):
    # Transform objects in Y that appear in X to have attribute A
    def transform_handler(scene_struct, inputs, side_inputs):
      assert len(inputs) == 2
      assert len(side_inputs) == 1
      value = side_inputs[0]
      output = copy.deepcopy(inputs[0])
      selection_ids = [obj['id'] for obj in inputs[1]]
      for obj in inputs[0]:
        if obj in selection_ids:
            output[attribute] = value
      return output
    return transform_handler
    
execute_handlers = {
  # CLEVR Extended
  'transform_color': make_transform_handler('color'),
  'transform_material': make_transform_handler('material'),
  'transform_size': make_transform_handler('size'),
  'transform_shape': make_transform_handler('shape'),
  

  # CLEVR 1.0
  'scene': scene_handler,
  'filter_color': make_filter_handler('color'),
  'filter_shape': make_filter_handler('shape'),
  'filter_material': make_filter_handler('material'),
  'filter_size': make_filter_handler('size'),
  'filter_objectcategory': make_filter_handler('objectcategory'),
}


def answer_question(program, metadata, scene_struct, all_outputs=False,
                    cache_outputs=True):
    
    # To handle transforms, we add an 'object_id' to the scene struct 
    scene_struct = copy.deepcopy(scene_struct)
    for i, o in enumerate(scene_struct['objects']):
        o['id'] = i
    all_input_types, all_output_types = [], []
    node_outputs = []
    
    for node in program:
        node_type = node['type']
        msg = 'Could not find handler for "%s"' % node_type
        assert node_type in execute_handlers, msg
        handler = execute_handlers[node_type]
        node_inputs = [node_outputs[idx] for idx in node['inputs']]
        side_inputs = node.get('side_inputs', [])
        node_output = handler(scene_struct, node_inputs, side_inputs)
        node_outputs.append(node_output)
        if node_output == '__INVALID__':
          break
    if all_outputs:
      return node_outputs
    else:
      return node_outputs[-1]