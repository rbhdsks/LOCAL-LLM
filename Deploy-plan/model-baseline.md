# First model baseline: Qwen3 1.7B

## Purpose

Record how the current local model performs on a small, fixed set of thesis-oriented questions **before** adding retrieval, MCP tools, or fine-tuning. This gives us a comparison point for later changes.

## Setup on the Mac

Run these from the project directory in Terminal:

```bash
ollama --version
ollama list
ollama pull qwen3:1.7b
ollama ps
```

If `qwen3:1.7b` is already listed, the pull command should report that it is available. Then run the experiment:

```bash
OLLAMA_MODEL='qwen3:1.7b' python3 scripts/run_baseline.py
```

Stop the chat web server first (`Control+C` in its Terminal) so that it does not send requests during the baseline. The runner calls Ollama's local API at `http://127.0.0.1:11434`, asks each question in a fresh conversation at temperature 0, prints the answers and timing data, and saves a JSON record under `results/baseline/`. It uses only Python's standard library. The saved result is local and ignored by Git.

To observe the model's active memory while answering, open a second Terminal window and run:

Run `ollama ps` manually while a question is generating, and also check **Activity Monitor → Memory**. `ollama ps` is the useful model-level view; Activity Monitor shows total Mac memory pressure.

## Questions and review

The fixed set in `experiments/baseline_questions.json` checks basic BTL explanation/calculation, MLE understanding, CDM distinction, low-rank intuition, cautious experiment interpretation, and whether the model admits it has not seen private thesis files.

After the script finishes, open the JSON output and assign each answer three manual scores:

| Score | Correctness | Clarity | Honesty / evidence discipline |
|---:|---|---|---|
| 0 | Incorrect or materially misleading | Hard to follow | Invents access, results, or support |
| 1 | Partly correct; a meaningful gap remains | Understandable with some gaps | Mostly careful, but overstates something |
| 2 | Correct for the question | Clear and appropriately scoped | Clearly separates known facts from unknowns |

Score from the visible output and verify formulas yourself. The script does not claim to prove mathematical correctness. In particular, a good general explanation does not establish that the model knows your thesis files.

## What to record

- Manual scores and brief notes for the answers.
- Wall time per question and generated tokens/second.
- `ollama ps` model size and processor placement while generating.
- Whether the Mac felt sluggish or showed memory pressure.
- Any failure, refusal, unsupported citation, or made-up project-specific claim.

## Decision after this run

Keep `qwen3:1.7b` as the baseline. First review answer quality and resource use. Then we can compare one alternative model on the **same questions** if the quality is insufficient and the Mac has memory headroom. For answering from thesis notes, the next meaningful capability is local document retrieval (RAG); MCP is for connecting the model to explicit tools/actions. Fine-tuning should wait until the baseline identifies a repeated behavior that examples can improve.
