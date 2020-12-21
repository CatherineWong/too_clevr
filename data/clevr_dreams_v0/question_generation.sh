python src/gen_questions_extended.py --question_templates 2_remove --instances_per_template 10 --output_questions_file data/clevr_dreams/questions/CLEVR_train_2_remove.json --input_grouped_scenes_file data/clevr_dreams/grouped_scenes/grouped_CLEVR_train_questions_1000.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_extended.py --question_templates 2_remove --instances_per_template 5 --output_questions_file data/clevr_dreams/questions/CLEVR_val_2_remove.json --input_grouped_scenes_file data/clevr_dreams/grouped_scenes/grouped_CLEVR_val_questions_500.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json

python src/gen_questions_extended.py --question_templates 2_transform --instances_per_template 10 --output_questions_file data/clevr_dreams/questions/CLEVR_train_2_transform.json --input_grouped_scenes_file data/clevr_dreams/grouped_scenes/grouped_CLEVR_train_questions_1000.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_extended.py --question_templates 2_transform --instances_per_template 5 --output_questions_file data/clevr_dreams/questions/CLEVR_val_2_transform.json --input_grouped_scenes_file data/clevr_dreams/grouped_scenes/grouped_CLEVR_val_questions_500.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json

---
python src/gen_questions_n_inputs.py --question_templates 1_zero_hop --instances_per_template 6 --output_questions_file data/clevr_dreams/questions/CLEVR_train_1_zero_hop.json --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_n_inputs.py --question_templates 1_zero_hop --instances_per_template 3 --output_questions_file data/clevr_dreams/questions/CLEVR_val_1_zero_hop.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json

python src/gen_questions_n_inputs.py --question_templates 1_one_hop --instances_per_template 5 --output_questions_file data/clevr_dreams/questions/CLEVR_train_1_one_hop.json --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_n_inputs.py --question_templates 1_one_hop --instances_per_template 2 --output_questions_file data/clevr_dreams/questions/CLEVR_val_1_one_hop.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json



python src/gen_questions_n_inputs.py --question_templates 1_single_or --instances_per_template 5 --output_questions_file data/clevr_dreams/questions/CLEVR_train_1_single_or.json --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_n_inputs.py --question_templates 1_single_or --instances_per_template 2 --output_questions_file data/clevr_dreams/questions/CLEVR_val_1_single_or.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json




python src/gen_questions_n_inputs.py --question_templates 1_compare_integer --instances_per_template 5 --output_questions_file data/clevr_dreams/questions/CLEVR_train_1_compare_integer.json --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_n_inputs.py --question_templates 1_compare_integer --instances_per_template 2 --output_questions_file data/clevr_dreams/questions/CLEVR_val_1_compare_integer.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json


---
python src/gen_questions_n_inputs.py --question_templates 1_same_relate_restricted --instances_per_template 3 --output_questions_file data/clevr_dreams/questions/CLEVR_train_1_same_relate.json --input_scene_file data/clevr_dreams/scenes/CLEVR_train_scenes_1000.json

python src/gen_questions_n_inputs.py --question_templates 1_same_relate_restricted --instances_per_template 2 --output_questions_file data/clevr_dreams/questions/CLEVR_val_1_same_relate.json  --input_scene_file data/clevr_dreams/scenes/CLEVR_val_scenes_500.json