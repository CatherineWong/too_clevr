import argparse, json, os
"""
gen_extended_templates.py | Author : Catherine Wong

This generates additional question CLEVR-style question templates. It is largely a pretty-formatted utility for  creating JSON files. It outputs files to a provided template directory.

Templates are an array of questions of the form:
{
    "text" : [<type: string; example '"Find the <Z> things."'],
    "group"
}

The original templates and format are taken from the CLEVR_1.0_templates JSON format by Justin Johnson: https://github.com/facebookresearch/clevr-dataset-gen/tree/master/question_generation 


Example usage: python3 gen_exten
"""

parser = argparse.ArgumentParser()
parser.add_argument('--template_dir', default='data/clevr_dreams/question_templates',
    help="Directory containing JSON templates for questions")

def main(args):
    fn = "2_localization_train"
    questions = [
    {"text": ["Find the <Z> things."],
    "group": "multiple",
    "nodes": [
      {"type": "scene",
      "inputs": [],
      },
      {"type": "filter",
       "inputs": [0],
       "side_inputs": ["<Z>"],
     },
    ],
    "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
     "constraints": {"filter" : "choose_exactly"}
    },
    {"text": ["Find the <C> things."],
    "group": "multiple",
    "nodes": [
      {"type": "scene",
      "inputs": [],
      },
      {"type": "filter",
       "inputs": [0],
       "side_inputs": ["<C>"],
     },
    ],
    "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
     "constraints": {"filter" : "choose_exactly"}
    },
    {"text": ["Find the <M> things."],
    "group": "multiple",
    "nodes": [
      {"type": "scene",
      "inputs": [],
      },
      {"type": "filter",
       "inputs": [0],
       "side_inputs": ["<M>"],
     },
    ],
    "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
     "constraints": {"filter" : "choose_exactly"}
    },
    {"text": ["Find the <S>s."],
    "group": "multiple",
    "nodes": [
      {"type": "scene",
      "inputs": [],
      },
      {"type": "filter",
       "inputs": [0],
       "side_inputs": ["<S>"],
     },
    ],
    "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
     "constraints": {"filter" : "choose_exactly"}
    },
    
        {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        },
        {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        },
        {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        },
    ]
    with open(os.path.join(args.template_dir, fn + '.json'), 'w') as f:
        json.dump(questions, f)
    
    fn = "2_localization_val"
    questions = [
        {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        },
        {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        },
        {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
         },
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        },
    ]
    with open(os.path.join(args.template_dir, fn + '.json'), 'w') as f:
        json.dump(questions, f)
    
    fn = "2_remove"
    questions = [
            {"text": ["What if you removed all of the <Z> <C> <M> <S>s?"],
            "group": "multiple",
            "nodes": [
              {"type": "scene",
              "inputs": [],
              },
              {"type": "filter",
               "inputs": [0],
               "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
             },
             {
               "type": "remove",
               "inputs": [0, 1],
             }
            ],
            "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}],
             "constraints": {}
          },
          {"text": ["If you removed the <Z> <C> <M> <S>s, how many things would be left?"],
          "group": "multiple",
          "nodes": [
            {"type": "scene",
            "inputs": [],
            },
            {"type": "filter",
             "inputs": [0],
             "side_inputs": ["<Z>", "<C>", "<M>", "<S>"],
           },
           {
             "type": "remove",
             "inputs": [0, 1],
           },
           {
            "type" : "count",
             "inputs" : [2]
           }
          ],
          "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}],
           "constraints": {}
        },
        {"text": ["If you removed the <C> things, how many <S>s would be left?"],
        "group": "multiple",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          {"type": "filter",
           "inputs": [0],
           "side_inputs": ["<C>"],
         },
         {
           "type": "remove",
           "inputs": [0, 1],
         },
         {"type": "filter_shape",
          "inputs": [2],
          "side_inputs": ["<S>"],
        },
        {
         "type" : "count",
          "inputs" : [3]
        }
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}],
         "constraints": {"filter" : "choose_exactly"}
      },
      {"text": ["If you removed the <S>s, how many <Z> things would be left?"],
      "group": "multiple",
      "nodes": [
        {"type": "scene",
        "inputs": [],
        },
        {"type": "filter",
         "inputs": [0],
         "side_inputs": ["<S>"],
       },
       {
         "type": "remove",
         "inputs": [0, 1],
       },
       {"type": "filter_size",
        "inputs": [2],
        "side_inputs": ["<Z>"],
      },
      {
       "type" : "count",
        "inputs" : [3]
      }
      ],
      "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}],
       "constraints": {"filter" : "choose_exactly"}
    },
      {"text": ["If you removed the <C> <S>s, how many <S>s would be left?"],
      "group": "multiple",
      "nodes": [
        {"type": "scene",
        "inputs": [],
        },
        {"type": "filter",
         "inputs": [0],
         "side_inputs": ["<C>", "<S>"],
       },
       {
         "type": "remove",
         "inputs": [0, 1],
       },
       {"type": "filter_shape",
        "inputs": [2],
        "side_inputs": ["<S>"],
      },
      {
       "type" : "count",
        "inputs" : [3]
      }
      ],
      "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}],
       "constraints": {"filter" : "choose_exactly"}
    }
    ]
    with open(os.path.join(args.template_dir, fn + '.json'), 'w') as f:
        json.dump(questions, f)
    
    fn = "2_transform"
    questions = [
        {"text": ["What if the <Z> <C> <M> <S> became a <Z2> <C2> <M2> <S2>?"],
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
      },
      {"text": ["What if all the <Z> <C> <M> <S>s became <Z2> <C2> <M2> <S2>s?"],
      "group": "multiple",
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
    },
    {"text": ["If all of the <Z> <C> <M> <S>s became <C2>, how many <C2> things would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<C2>"]}, {"type": "filter_color", "inputs": [2], "side_inputs": ["<C2>"]}, {"type": "count", "inputs": [3]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": []},
    {"text": ["If all of the <Z> <C> <M> <S>s became <M2>, how many <M2> things would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<M2>"]}, {"type": "filter_color", "inputs": [2], "side_inputs": ["<M2>"]}, {"type": "count", "inputs": [3]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": []},
    {"text": ["If all of the <Z> <C> <M> <S>s became <C2> <S2>s, how many <C2> <S2>s would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<C2>","<S2>"]}, {"type": "filter_color", "inputs": [2], "side_inputs": ["<C2>"]}, {"type": "filter_shape", "inputs": [3], "side_inputs": ["<S2>"]}, {"type": "count", "inputs": [4]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": {"transform":"choose_all"}},
    {"text": ["If all of the <Z> <C> <M> <S>s became <Z2>, how many <Z> things would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<Z2>"]}, {"type": "filter_size", "inputs": [2], "side_inputs": ["<Z>"]}, {"type": "count", "inputs": [3]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": {"transform":"choose_all", "<Z>" : "instantiated"}}
    ]
    with open(os.path.join(args.template_dir, fn + '.json'), 'w') as f:
        json.dump(questions, f)
    
    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)   