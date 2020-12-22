### CLEVR Extended.
This repository contains utilities to generate program-induction style variants of the CLEVR dataset. Individual questions can be validate on one or more scenes as input.

This repository is adapted directly from the original CLEVR dataset generation code by Justin Johnson at: https://github.com/facebookresearch/clevr-dataset-gen/tree/master/question_generation

There are two main sources of questions: questions based on the original templates, and extended questions that use new functionalities and were not in the original dataset.

### Generating the shared scenes.
1. All of the questions reference a shared set of scenes. These scenes were created using utils.py, which extracted a set of scenes from the original CLEVR scenes file.
We provide a set of these scenes in metadata/clevr_shared_metadata

#### Questions based on the original templates.
Questions based on the original templates are created as follows:
1. Provide a dataset containing question templates. We provide templates in clevr_original_metadata, which were created by hand by selecting questions from the original templates.

The original question templates are from Justin Johnson's CLEVR dataset templates, here: https://github.com/facebookresearch/clevr-dataset-gen/tree/master/question_generation/CLEVR_1.0_templates

2. Create questions with multiple inputs and outputs using gen_questions_n_inputs.py. This must be run separately for training and validation. Sample runs are in clevr_dreams/question_generation.sh

#### Questions based on the original templates.