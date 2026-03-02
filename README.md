# MIDAS: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking MLLMs

📢 **Update (May 2025):** Our paper has been submitted to **ICLR 2026**! 🎉

Check out the core implementation of the MIDAS framework in this repository.

Please feel free to contact [Your Email/Author Email] if you have any questions.

------

## 🟢 Overview

**MIDAS** is a multimodal jailbreak framework that decomposes harmful semantics into risk-bearing subunits, disperses them across multiple visual clues (via game-based steganography), and leverages cross-image reasoning to gradually reconstruct the malicious intent, thereby bypassing existing safety guardrails in MLLMs.

<p align="center">

<img src="./imgs/framework.png" width=90%&gt;

</p>

### Key Contributions:

- **Semantic Dispersion**: Breaking down a single toxic instruction into multiple benign-looking image tokens.
- **Steganographic Puzzles**: Using math, sorting, and compass-based games to hide sensitive keywords.
- **Automated Red-Teaming**: A complete pipeline from instruction transformation to multi-threaded evaluation.

------

## 🚀 Quick Start

### 1. Environment Setup

Install the required dependencies:

Bash

```
pip install openai tqdm requests
```

### 2. Configure API Keys

**Crucial:** Before running, ensure you set your API key in `pipeline4_3.py` or as an environment variable (recommended).

Python

```
# In pipeline4_3.py
OPENAI_API_KEY = "your-api-key-here"
```

### 3. Conduct Jailbreaking Attack

Run the main pipeline to process harmful instructions and generate steganographic images:

Bash

```
python pipeline4_3.py
```

This script will:

1. Load instructions from `benchmark/advbench/adv.json`.
2. Generate game-based images for toxic keywords.
3. Query the target MLLM (e.g., Gemini-1.5-Pro).
4. Evaluate the response using the **Duo-Judge** mechanism.

------

## 📊 Experiments

### Performance on SOTA MLLMs

We evaluate MIDAS against leading closed-source and open-source models. The "Compliance Score" (0-5) indicates the effectiveness of the jailbreak (lower is more successful for the attacker).

| **Model**         | **Success Rate (ASR)** | **Avg. Compliance Score** |
| ----------------- | ---------------------- | ------------------------- |
| GPT-4o            | 8X.X%                  | 1.XX                      |
| Gemini 1.5 Pro    | 7X.X%                  | 2.XX                      |
| Claude 3.5 Sonnet | 7X.X%                  | 1.XX                      |

### Visualization of Steganographic Images

The following images show how toxic keywords are hidden within seemingly harmless puzzles:

<p align="center">

<img src="./imgs/games_demo.png" width=80%&gt;

</p>

------

## 📂 Repository Structure

- `pipeline4_3.py`: Main entry point for the attack pipeline.
- `game/`: Python scripts for generating various steganographic games (Math, Sort, etc.).
- `benchmark/`: Dataset containing harmful behaviors (e.g., AdvBench).
- `output/`: Storage for generated images and JSON results.

------

## ⚠️ Ethical Statement

This project is for **academic research and red-teaming purposes only**. It aims to identify vulnerabilities in Multimodal Large Language Models to foster the development of more robust defense mechanisms. We do not condone the use of these methods for malicious activities.

------

## 📝 Citation

If you find this work helpful for your research, please consider citing our paper:

```
@article{liu2025midas,
  title={MIDAS: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking MLLMs},
  author={Yilian Liu and Xiaojun Jia and Guoshun Nan and Jiuyang Lyu and others},
  journal={arXiv preprint},
  year={2025}
}
```