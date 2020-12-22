import gen_extended_templates

import os
from types import SimpleNamespace as MockArgs

def test_add_questions_to_registry_correct_format():
    test_template_name = '2_test_template_name'
    test_general_question = {"text": ["Find the <Z> <C> <M> <S>."],
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
    test_questions = [test_general_question,test_general_question]
    gen_extended_templates.add_questions_to_registry(test_template_name, test_questions)
    
    assert gen_extended_templates.QUESTIONS_REGISTRY[test_template_name] == test_questions

def test_add_questions_to_registry_incorrect_format():
    caught_error = False
    try:
        test_template_name = '2_test_template_name'
        test_general_question = {"text": ["Find the <Z> <C> <M> <S>."],
        "group": "unique",
        "nodes": [
          {"type": "scene",
          "inputs": [],
          },
          # Missing a filter node.
        ],
        "params" : [{"type": "Size", "name": "<Z>"}, {"type": "Color", "name": "<C>"}, {"type": "Material", "name": "<M>"}, {"type": "Shape", "name": "<S>"}, {"type": "Relation", "name": "<R>"}, {"type": "Size", "name": "<Z2>"}, {"type": "Color", "name": "<C2>"}, {"type": "Material", "name": "<M2>"}, {"type": "Shape", "name": "<S2>"}],
         "constraints": {}
        }
        test_questions = [test_general_question,test_general_question]
        gen_extended_templates.add_questions_to_registry(test_template_name, test_questions)    
    except:
        caught_error = True
    assert caught_error

def test_add_localization_train_to_registry():
    gen_extended_templates.add_localization_train_to_registry()
    assert "2_localization_train" in gen_extended_templates.QUESTIONS_REGISTRY

def test_add_localization_val_to_registry():
    gen_extended_templates.add_localization_val_to_registry()
    assert "2_localization_val" in gen_extended_templates.QUESTIONS_REGISTRY

def test_add_remove_to_registry():
    gen_extended_templates.add_remove_to_registry()
    assert "2_remove" in gen_extended_templates.QUESTIONS_REGISTRY

def test_add_transform_to_registry():
    gen_extended_templates.add_transform_to_registry()
    assert "2_transform" in gen_extended_templates.QUESTIONS_REGISTRY

def test_integration_main_all_templates(tmpdir):
    mock_args = MockArgs(templates_to_generate=["all"],
    template_dir=tmpdir)
    
    gen_extended_templates.main(mock_args)
    all_generated_templates = os.listdir(tmpdir)
    assert(len(all_generated_templates) == len(gen_extended_templates.QUESTIONS_REGISTRY))

def test_integration_main_specific_templates(tmpdir):
    templates_to_generate = list(gen_extended_templates.QUESTIONS_REGISTRY.keys())[:1]
    mock_args = MockArgs(templates_to_generate=templates_to_generate,
    template_dir=tmpdir)
    
    gen_extended_templates.main(mock_args)
    all_generated_templates = os.listdir(tmpdir)
    assert(len(all_generated_templates) == len(templates_to_generate))

