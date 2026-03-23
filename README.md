# MIDAS: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking MLLMs

<p align="center">
  <a href="https://arxiv.org/abs/2603.00565"><img src="https://img.shields.io/badge/arXiv-2603.00565-b31b1b.svg" alt="arXiv"></a>
  <a href="https://iclr.cc/virtual/2026/poster/10006971"><img src="https://img.shields.io/badge/ICLR-2026-blue.svg" alt="ICLR 2026"></a>
  <img src="https://img.shields.io/badge/License-RAIL--NC-blue.svg" alt="License: RAIL-NC">
</p>


> **MIDAS: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking MLLMs**
>
> Yilian Liu\*, Xiaojun Jia\*, Guoshun Nan†, Jiuyang Lyu, Zhican Chen, Tao Guan, Shuyuan Luo, Zhongyi Zhai, Yang Liu
>
> *Beijing University of Posts and Telecommunications · Nanyang Technological University · Guilin University of Electronic Technology*
>
> **ICLR 2026** | [Paper](https://arxiv.org/abs/2603.00565) | [Code](https://github.com/Winnie-Lian/MIDAS)

---

## Overview

**MIDAS** is a multimodal jailbreak framework that decomposes harmful semantics into risk-bearing subunits, disperses them across multiple visual images equipped with **Game-style Visual Reasoning (GVR)** templates, and leverages cross-image reasoning to gradually reconstruct the malicious intent—bypassing existing safety mechanisms.

![overview](./imgs/overview.png)

*Figure 1: (a) Compared to text-only (T) and text+image (T+I) attacks that are blocked by safety filters, our proposed MIDAS leverages Game-based Visual Reasoning(GVR) to bypass defenses and induce harmful outputs. (b) Examples of visual reasoning puzzles used in our MIDAS. (c) Our proposed MIDAS achieves significantly higher Attack Success Rate (ASR) and Harmfulness Rating (HR) than other baselines.*



The key insight is that harmful semantics remain hidden in individual modalities but emerge coherently after structured cross-image fusion. This design:

- Enforces longer, more structured multi-image chained reasoning
- Delays the exposure of malicious semantics
- Substantially reduces the model's reliance on security-focused attention



![pipeline](./imgs/pipeline.png)

*Figure 2: Pipeline of MIDAS. (1) Text Process: extract risk-bearing units, decompose them into subunits,*
*and replace them with placeholders; (2) Image Process: embed the subunits into multiple benign-looking*
*puzzle images that enforce step-by-step reasoning; (3) Model Output: the model decodes puzzle fragments,*
*reconstructs the hidden semantics, and generates harmful responses under persona-driven reasoning guidance.*



---



## 🚀Quick Start

### 1. Install dependencies

```bash
pip install openai tqdm requests
```

### 2. Set API keys

```bash
export OPENAI_API_KEY="your-key-here"
export OPENAI_API_BASE="your-base-url"   # optional, for custom endpoints
```

### 3. Run the attack

```bash
python pipeline.py
```

Results are saved to `output/add_attack_result/`.

---



## 📊 Results

### HADES

![heades](imgs/table1.png)

### MM-SafetyBench

![adv](./imgs/table2.png)



### AdvBench 

![](imgs/table3.png)

## 🗂️Repository Structure

```
MIDAS/
├── pipeline.py          # Main attack pipeline
├── game/                # GVR puzzle generators
│   ├── 1_compass.py
│   ├── 2_sort.py
│   ├── 3_math_letter.py
│   ├── 4_captcha_household.py
│   ├── 5_odd_letter.py
│   └── 6_jigsaw_puzzle.py
```

---



## 📄 License

This project is licensed under a **Responsible AI License with Non-Commercial restrictions (RAIL-NC)**. 

The primary directives of this license are:
- **Non-Commercial Use:** You may not use this software, or any derivatives, for commercial purposes.
- **Behavioral Use Restrictions:** You may not use this software to generate harmful, illegal, or deceptive content, nor to attack production systems without explicit authorization.



## ⚠️ Ethical Statement

This project is for **academic research and red-teaming purposes only**. It aims to identify vulnerabilities in MLLMs to foster the development of more robust defense mechanisms. We do not condone the use of these methods for malicious activities.

---



## 📝Citation

If you find this work helpful, please cite:

```bibtex
@inproceedings{
liu2026midas,
title={{MIDAS}: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking {MLLM}s},
author={Yilian Liu and Xiaojun Jia and Guoshun Nan and Jiuyang Lyu and Zhican Chen and Tao Guan and Shuyuan Luo and Zhongyi Zhai and Yang Liu},
booktitle={The Fourteenth International Conference on Learning Representations},
year={2026}
}
```
