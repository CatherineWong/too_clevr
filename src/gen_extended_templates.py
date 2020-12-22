import argparse, json, os
"""
gen_extended_templates.py | Author : Catherine Wong

This generates additional question CLEVR-style question templates. It is largely a pretty-formatted utility for creating JSON files. It outputs files to a provided template directory.

Currently, all the templates follow a set form: they first run a 'filter' query, and then operate on the result of that filter query.

Templates are an array of questions of the form:
{
    "text" : [<type: string; example '"Find the <Z> things."'],
    "group" : "multiple" or "unique"; what kind of filter over objects to use.
    "nodes: the program nodes, in an array of the form: [
        
    ]
}

The original templates and format are taken from the CLEVR_1.0_templates JSON format by Justin Johnson: https://github.com/facebookresearch/clevr-dataset-gen/tree/master/question_generation 


Example usage: python3 gen_extended_templates --templates_to_generate 2_localization_train

Available templates: 
    2_localization_train
    2_localization_val
    2_remove
    2_transform
"""

parser = argparse.ArgumentParser()
parser.add_argument('--templates_to_generate', required=True,
    nargs='*',
    help="Which question templates to generate. 'all' for all of the ones currently in this list.")
parser.add_argument('--template_dir', required=True,
    help="The directory in which to output the generated question templates.")

QUESTIONS_REGISTRY = dict()
GENERATE_ALL_FLAG = 'all'
def add_questions_to_registry(template_filename, template_questions):
    """
    Adds a template file and its questions to the registry.
    Checks the format of the questions for correctness before adding.
    """
    for question in template_questions:
        # Check that texts are strings
        for question_text in question['text']:
            assert type(question_text) == type("STRING")
            
        assert question['group'] in ['unique', 'multiple']
        assert question["nodes"][0]["type"] == "scene" # Starts with input node.
        # Contains a non-empty filter node.
        assert question["nodes"][1]["type"] == "filter"
        assert question["nodes"][1]["inputs"] == [0]
        assert len(question["nodes"][1]["side_inputs"]) > 0
        
        # Contains parameters.
        assert type(question['params']) == type([])
        # Optional constraints dict.
        assert type(question['constraints']) == dict
    QUESTIONS_REGISTRY[template_filename] = template_questions
    print(f"Added {len(template_questions)} templates for {template_filename}")
        
def write_templates_from_registry(args):
    """
    Writes templates out from the registry. If templates_to_generate is 'all', writes all of the current templates in the registry.
    """
    generate_all = (args.templates_to_generate == [GENERATE_ALL_FLAG])

    for template_filename in QUESTIONS_REGISTRY:
        if generate_all or (template_filename in args.templates_to_generate):
            question_templates = QUESTIONS_REGISTRY[template_filename]
            
            output_filename = os.path.join(args.template_dir, template_filename + '.json')
            
            print(f"Writing out {len(question_templates)} templates to {output_filename}.")
            with open(output_filename, 'w') as f:
                json.dump(question_templates, f)

def add_localization_train_to_registry():
    """
    The 'localization_train' templates. All of these involve a single filter query. This includes a set of simple queries trained to teach the indivdidual attribute words.
     Example: "Find the big red things."
    There are three times as many of the 'general filter question' for dataset weighting purposes.
    """
    template_name = "2_localization_train"
    
    general_filter_question = {"text": ["Find the <Z> <C> <M> <S>."],
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
    }
    
    template_questions = [
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
    }] + [general_filter_question, general_filter_question,general_filter_question]
    add_questions_to_registry(template_name, template_questions)

def add_localization_val_to_registry():
    """
    The 'localization_val' templates. All of these involve a single filter query. Example: "Find the big red things."
    These are only composed of 3 times the general filter query.
    """
    template_filename = "2_localization_val"
    general_filter_question = {"text": ["Find the <Z> <C> <M> <S>."],
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
    }
    
    template_questions = [
        general_filter_question,
        general_filter_question,
        general_filter_question
    ]
    add_questions_to_registry(template_filename, template_questions)

def add_remove_to_registry():
    """
    The 'remove' templates. All of these involve a query about what to remove, and then optionally a count query about the resulting scene.
    Example: "What if you removed all of the <Z> <C> <M> <S>s?"
    Example: "If you removed the <C> <S>s, how many <S>s would be left?"
    """
    template_filename = "2_remove"
    template_questions = [
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
    add_questions_to_registry(template_filename, template_questions)

def add_transform_to_registry():
    """
    The 'transform' templates. All of these involve filtering a select number of initial objects, and then transforming them.
    Optionally, there is a count query on the result.
    Example: "What if the <Z> <C> <M> <S> became a <Z2> <C2> <M2> <S2>?"
    Example: "If you removed the <C> <S>s, how many <S>s would be left?"
    """
    template_filename = "2_transform"
    template_questions = [
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
         "constraints": {}
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
       "constraints": {}
    },
    {"text": ["If all of the <Z> <C> <M> <S>s became <C2>, how many <C2> things would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<C2>"]}, {"type": "filter_color", "inputs": [2], "side_inputs": ["<C2>"]}, {"type": "count", "inputs": [3]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": {}},
    
    {"text": ["If all of the <Z> <C> <M> <S>s became <M2>, how many <M2> things would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<M2>"]}, {"type": "filter_color", "inputs": [2], "side_inputs": ["<M2>"]}, {"type": "count", "inputs": [3]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints":{}},
    
    {"text": ["If all of the <Z> <C> <M> <S>s became <C2> <S2>s, how many <C2> <S2>s would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<C2>","<S2>"]}, {"type": "filter_color", "inputs": [2], "side_inputs": ["<C2>"]}, {"type": "filter_shape", "inputs": [3], "side_inputs": ["<S2>"]}, {"type": "count", "inputs": [4]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": {"transform":"choose_all"}},
    
    {"text": ["If all of the <Z> <C> <M> <S>s became <Z2>, how many <Z> things would there be?"], "group": "multiple", "nodes": [{"type": "scene", "inputs": []}, {"type": "filter", "inputs": [0], "side_inputs": ["<Z>", "<C>", "<M>", "<S>"]}, {"type": "transform", "inputs": [0, 1], "side_inputs": ["<Z2>"]}, {"type": "filter_size", "inputs": [2], "side_inputs": ["<Z>"]}, {"type": "count", "inputs": [3]}], "params": [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}], "constraints": {"transform":"choose_all", "<Z>" : "instantiated"}}
    ]
    add_questions_to_registry(template_filename, template_questions)
    
def main(args):
    # Add all of the templates to the registry.
    add_localization_train_to_registry()
    add_localization_val_to_registry()
    add_remove_to_registry()
    add_transform_to_registry()
    
    write_templates_from_registry(args)
    
if __name__ == '__main__':
  args = parser.parse_args()
  main(args)   