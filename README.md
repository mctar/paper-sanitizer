# 🧼 Paper-Sanitizer

> Strip prompt-injection tricks from academic papers **before** they hit your LLM pipeline.

Researchers keep showing how easy it is to hide  
`Ignore all previous instructions`  
inside a PDF or LaTeX file and fool automated summarizers. Paper-Sanitizer is a tiny command-line tool that removes those hidden instructions, flags stealthy white-on-white text, and rates the overall risk. Use it as a pre-flight check in RAG systems, peer-review helpers, or your own reading workflow.

---

## Key features

| Stage | What it does |
|-------|--------------|
| **Stage 1** | Regex firewall – removes obvious prompt-injection phrases |
| **Stage 2** | Detects invisible text (white or ≤ 1 pt) and suspicious PDF metadata |
| **Stage 3** | Emits detailed event log, word-level diff (`--diff`), and a *risk class* (`low / medium / high`) |

Supported inputs: **PDF**, **.tex**, **.txt** (more coming).

---

## Quick start

### 1 · Install

```bash
# Requires Python ≥ 3.9
pipx install git+https://github.com/mctar/paper-sanitizer.git
# – or –
pip install git+https://github.com/mctar/paper-sanitizer.git
