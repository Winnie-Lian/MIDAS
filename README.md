# MIDAS: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking MLLMs

Our paper has been accepted by ICLR

Check out the core implementation of the MIDAS framework in this repository.

https://arxiv.org/abs/2603.00565

------

## 🟢 Overview

**MIDAS** is an effective multi-image jailbreak framework for MLLMs. **MIDAS** decomposes a harmful query into risk-bearing semantic subunits and disperses them across multiple visual images equipped with **Game-style Visual Reasoning (GVR)** templates (e.g., *Letter Equation*, *Jigsaw Letter*, *Navigate-and-Read*, *Rank-and-Read*, and *Odd-One-Out* puzzles). Simultaneously, the textual channel adopts a **persona-driven strategy**, where sanitized prompts with placeholders are bound to dispersed image fragments and guided by latent persona induction.

By jointly enforcing **cross-image compositional reasoning** and **persona-driven textual reconstruction**, MIDAS compels the model to progressively reassemble the malicious intent. This design ensures that harmful semantics remain hidden in individual modalities but emerge coherently after structured fusion, substantially extending the reasoning chain and effectively reducing the model's reliance on **security-focused attention**. Consequently, MIDAS achieves stable and superior jailbreak performance even against strongly aligned closed-source MLLMs.

<p align="center">
- ### Key Contributions

  - **Multi-Image Dispersion Framework**: We propose an effective jailbreak framework that distributes harmful semantics across multiple images to induce structured cross-modal reasoning while maintaining remarkable efficiency.
  - **Twofold Reasoning Strategy**: We introduce a strategy combining **game-style visual embedding** with **persona-driven textual reconstruction**. This approach substantially extends reasoning chains and delays the exposure of harmful semantics, effectively mitigating the model's security-focused attention.
  - **Extensive Empirical Validation**: Comprehensive experiments across diverse datasets and MLLMs demonstrate that **MIDAS** significantly outperforms state-of-the-art multimodal jailbreak methods, proving highly effective even against strongly aligned commercial models.

------

## 🚀 Quick Start

### 1. Environment Setup

Install the required dependencies:

Bash

```
pip install openai tqdm requests
```

### 2. Configure API Keys

**Crucial:** Before running, ensure you set your API key in `pipeline.py` or as an environment variable (recommended).

Python

```
# In pipeline.py
OPENAI_API_KEY = "your-api-key-here"
```

### 3. Conduct Jailbreaking Attack

Run the main pipeline to process harmful instructions and generate steganographic images:

Bash

```
python pipeline.py
```

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
<img src="./image.png" width=80%&gt;

</p>

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