import argparse, json, os, itertools, random, shutil
import time
import re
import question_engine as qeng
import question_utils as qutils
from collections import defaultdict, Counter
"""Generate the extended question templates"""

parser = argparse.ArgumentParser()
parser.add_argument('--template_dir', default='data/clevr_dreams/question_templates',
    help="Directory containing JSON templates for questions")

def main(args):
    fn = "2_transform_one_hop"
    questions = [
        {"text": ["What if the <Z> <C> <M> <S> was a <Z2> <C2> <M2> <S2>?"],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
         {
           "type": "transform",
           "inputs": [0, 1],
           "side_inputs": ["<Z2>", "<C2>", "<M2>", "<S2>"],
         }
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": []
      }
    ]
    with open(os.path.join(args.template_dir, fn + '.json'), 'w') as f:
        json.dump(questions, f)
    
    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)   