# InfiAgent-DAEval Upstream Notes

Cloned from: https://github.com/InfiAgent/InfiAgent
Commit SHA: 3d6c4a70198e0a41fadf539f5b43c88b8c1a2d9c
License: Apache License 2.0

## File Paths (relative to benchmarks/data/InfiAgent/)
- Questions: `examples/DA-Agent/data/da-dev-questions.jsonl`
- Labels/answers: `examples/DA-Agent/data/da-dev-labels.jsonl`
- Data tables (CSV files): `examples/DA-Agent/data/da-dev-tables/`

## JSON Field Names (read off actual files — do NOT assume)

### Questions file (`da-dev-questions.jsonl`)
- Question ID: `id` (integer, 0-indexed but not contiguous — values like 0, 5, 6, 7, 8, ...)
- Question text: `question`
- Attached file(s): `file_name` (single CSV filename, e.g. `"test_ave.csv"`)
- Answer format spec: `format` (template string, e.g. `@mean_fare[mean_fare_value] where "mean_fare_value" is ...`)
- Constraints: `constraints` (free-text description of computation rules)
- Concepts: `concepts` (array of strings, e.g. `["Summary Statistics"]`)
- Difficulty flag: `level` (string, values: `"easy"`, `"medium"`, `"hard"`)

### Labels file (`da-dev-labels.jsonl`)
- Question ID: `id` (integer — matches `id` in questions file)
- Label/answer: `common_answers` (array of 2-element arrays: `[[answer_name, answer_value], ...]`)
  - `answer_name` is the bare name used in the `@name[value]` format (e.g. `"mean_fare"`)
  - `answer_value` is a string (numeric values stored as strings, e.g. `"34.65"`)

**Note:** A single question can have multiple sub-answers, each as a separate entry in `common_answers`.

## Scorer
- Path: `examples/DA-Agent/eval_closed_form.py`
- Key function: `evaluate_responses(labels, responses)`
- Answer extraction function: `extract_format(input_string)` — uses regex `@(\w+)\[(.*?)\]`
- Equality check: `is_equal(response, label)` — exact string match OR float match within `1e-6`
- Accuracy functions:
  - `evaluate_accuracy_by_question(results)` — whole-question accuracy (all sub-answers must be correct)
  - `evaluate_accuracy_by_sub_question(results)` — per sub-answer accuracy
  - `evaluate_accuracy_proportional_by_sub_question_adjusted(results)` — proportional score
- Invocation:
  ```bash
  python eval_closed_form.py \
    --questions_file_path data/da-dev-questions.jsonl \
    --labels_file_path data/da-dev-labels.jsonl \
    --responses_file_path <your_responses.jsonl>
  ```
- Responses file format expected: JSONL with fields `id` (int) and `response` (string containing `@name[value]` tokens)

## Sample Records

### Record 1 (questions file — easy)
```json
{
  "id": 0,
  "question": "Calculate the mean fare paid by the passengers.",
  "concepts": ["Summary Statistics"],
  "constraints": "Calculate the mean fare using Python's built-in statistics module or appropriate statistical method in pandas. Rounding off the answer to two decimal places.",
  "format": "@mean_fare[mean_fare_value] where \"mean_fare_value\" is a floating-point number rounded to two decimal places.",
  "file_name": "test_ave.csv",
  "level": "easy"
}
```

### Record 1 (labels file — matching id=0)
```json
{
  "id": 0,
  "common_answers": [["mean_fare", "34.65"]]
}
```

### Record 2 (questions file — medium, multiple concepts)
```json
{
  "id": 5,
  "question": "Generate a new feature called \"FamilySize\" by summing the \"SibSp\" and \"Parch\" columns. Then, calculate the Pearson correlation coefficient (r) between the \"FamilySize\" and \"Fare\" columns.",
  "concepts": ["Feature Engineering", "Correlation Analysis"],
  "constraints": "Create a new column 'FamilySize' that is the sum of 'SibSp' and 'Parch' for each row.\nCalculate the Pearson correlation coefficient between 'FamilySize' and 'Fare'\nDo not perform any further data cleaning or preprocessing steps before calculating the correlation.",
  "format": "@correlation_coefficient[r_value]\nwhere \"r_value\" is the Pearson correlation coefficient between 'FamilySize' and 'Fare', a number between -1 and 1, rounded to two decimal places.",
  "file_name": "test_ave.csv",
  "level": "medium"
}
```

### Record 2 (labels file — matching id=5)
```json
{
  "id": 5,
  "common_answers": [["correlation_coefficient", "0.21"]]
}
```

## Answer Format

A correct prediction must embed answers as `@answer_name[value]` tokens anywhere in the response string. The scorer uses the regex `@(\w+)\[(.*?)\]` to extract all `(name, value)` pairs. A prediction is correct for a sub-answer if the extracted value equals the label exactly (string match) or within `1e-6` as floats.

Example prediction string accepted by the scorer:
```
@mean_fare[34.65]
```

Multi-answer example (Shapiro-Wilk question):
```
@shapiro_wilk_statistic[0.56]
@shapiro_wilk_p_value[0.0002]
```

## Notes

1. **IDs are not contiguous.** The 257 questions use integer IDs but they are not 0–256 consecutively (e.g., the second question is id=5, not id=1). Always join by `id`, never by array index.

2. **`file_name` is a bare filename**, not a path. The corresponding CSV lives at `examples/DA-Agent/data/da-dev-tables/<file_name>`. Downstream code must prepend that prefix to load the data.

3. **`common_answers` is a list of 2-lists, not a dict.** Access as `[[name, value], ...]`. The eval script does `{ans[0]: ans[1] for ans in label["common_answers"]}` to convert to a dict.

4. **`level` (not "hard")** is the difficulty flag. Three values: `"easy"`, `"medium"`, `"hard"`. There is no separate boolean `hard` field.

5. **`format` drives the output spec.** It describes what `@name[value]` tokens the model must produce and what the value represents. The `reformat.py` script can post-process raw model outputs that did not follow the format.

6. **257 total questions**, 257 labels — one-to-one correspondence by `id`.

7. **Scorer equality is lenient on floats** (`abs(a - b) < 1e-6`) but strict on strings — rounding instructions in `constraints` and `format` are significant.
