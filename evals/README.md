# MoveInSync AI Agent Evaluation Suite

Comprehensive evaluation framework for testing the Movi AI agent's accuracy, reliability, and performance.

## Overview

This evaluation suite measures:
- **Tool Selection Accuracy**: Does the agent pick the correct tool for each query?
- **Entity Extraction**: Does it extract parameters correctly?
- **HITL Behavior**: Does it trigger human-in-the-loop for high-impact operations?
- **Context Awareness**: Does it understand page context?
- **Performance**: Latency and throughput metrics
- **Regression Detection**: Automatic alerts if metrics drop below baseline

## Files

- **`dataset.json`**: Comprehensive test dataset with 50+ test cases covering:
  - Tool selection (20 cases)
  - Edge cases (5 cases)
  - Context awareness (4 cases)
  - HITL validation (3 cases)
  - Entity extraction (3 cases)
  - Performance benchmarks (2 cases)

- **`eval_suite.py`**: Main evaluation framework with:
  - Automated test execution
  - Accuracy metrics calculation
  - Regression detection against baseline
  - Detailed reporting

- **`baseline.json`**: Baseline metrics for regression detection
  - Updated automatically with `--save-baseline` flag
  - CI fails if current metrics drop >5% below baseline

- **`eval_chat.py`**: Legacy simple eval script (deprecated, use eval_suite.py)

## Usage

### Run Full Evaluation

```bash
python evals/eval_suite.py
```

### Run with Custom Dataset

```bash
python evals/eval_suite.py --dataset path/to/custom_dataset.json
```

### Save New Baseline

After improving the agent, save current metrics as new baseline:

```bash
python evals/eval_suite.py --save-baseline
```

### View Results

Results are saved with timestamps in `evals/results_YYYYMMDD_HHMMSS.json`

## Metrics

### Tool Selection Accuracy
Percentage of queries where the agent selected the correct tool.

**Target: ≥ 90%**

### Entity Extraction Accuracy
Percentage of queries where entities were correctly extracted.

**Target: ≥ 85%**

### HITL Accuracy
Percentage of operations where HITL was correctly triggered (or not).

**Target: 100%** (critical for safety)

### Overall Accuracy
Combined score across all test categories.

**Target: ≥ 85%** (CI gate)

## CI Integration

The eval suite runs automatically in CI:

```yaml
- name: Run evaluation suite
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python evals/eval_suite.py --baseline evals/baseline.json
```

**CI fails if:**
- Overall accuracy < 85%
- Tool selection accuracy drops >5% below baseline
- Entity extraction drops >5% below baseline
- HITL accuracy is not 100%

## Adding New Test Cases

Edit `dataset.json`:

```json
{
  "tool_selection": [
    {
      "id": "tool_XXX",
      "input": "User query here",
      "context_page": "buses",
      "expected_tool": "get_all_trips",
      "expected_entities": {
        "trip_name": "Morning Shift"
      },
      "category": "query",
      "requires_hitl": false
    }
  ]
}
```

**Test Categories:**
- `tool_selection`: Basic tool selection tests
- `edge_cases`: Error handling, edge cases
- `context_awareness`: Page context tests
- `hitl_validation`: HITL trigger tests
- `entity_extraction`: Parameter extraction tests
- `performance`: Latency benchmarks

## Troubleshooting

### Eval fails with OpenAI API error
Set your API key: `export OPENAI_API_KEY=sk-...`

### All tests fail
Check that backend imports work: `python -c "from backend.Agents.graph import app"`

### Baseline not found
Run once with `--save-baseline` to create initial baseline

## Best Practices

1. **Run locally before pushing**: Catch regressions early
2. **Update baseline carefully**: Only after verified improvements
3. **Add test cases for bugs**: Every bug fix should add a regression test
4. **Monitor CI failures**: Address eval regressions immediately

## Future Improvements

- [ ] Multi-turn conversation tests
- [ ] Vision/image analysis evals
- [ ] Voice transcription accuracy
- [ ] Cost tracking per test
- [ ] Parallel eval execution
- [ ] Fuzzing for edge case discovery
