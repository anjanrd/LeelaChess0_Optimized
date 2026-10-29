# Checked references and claim scope

Primary bibliographic/concept sources checked 29 October 2026. Local experiment numbers are audited against CSVs, not inferred from these papers.

[1] Rejwana Haque, Ting Han Wei, Martin Müller. **On the Road to Perfection? Evaluating Leela Chess Zero Against Endgame Tablebases**. Advances in Computer Games (ACG 2021), LNCS 13262, pp. 142–152 (2022). [Primary source](https://link.springer.com/chapter/10.1007/978-3-031-11488-5_13).

Claim used: Raw policy and MCTS decision errors evaluated against exact endgame solutions. Access: Publisher book metadata and author-hosted paper search excerpt verified; direct author PDF fetch returned 404. Exact proposal error counts are not asserted.

[2] Guangxuan Xiao, Ji Lin, Mickael Seznec, Hao Wu, Julien Demouth, Song Han. **SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models**. ICML, PMLR 202, pp. 38087–38099 (2023). [Primary source](https://proceedings.mlr.press/v202/xiao23c.html).

Claim used: Training-free W8A8 PTQ using compensating activation/weight rescaling. No LLM speedup is transferred to BT3. Access: Publisher page and abstract/BibTeX verified.

[3] Elias Frantar, Dan Alistarh. **SparseGPT: Massive Language Models Can be Accurately Pruned in One-Shot**. ICML, PMLR 202, pp. 10323–10337 (2023). [Primary source](https://proceedings.mlr.press/v202/frantar23a.html).

Claim used: One-shot pruning with support for semi-structured patterns and quantization. Our numerical/chess results come from local evidence. Access: Publisher page and abstract/BibTeX verified.

[4] Elias Frantar, Saleh Ashkboos, Torsten Hoefler, Dan Alistarh. **GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers**. arXiv:2210.17323, revised 22 March 2023 (2022). [Primary source](https://arxiv.org/abs/2210.17323).

Claim used: Related one-shot weight quantization using approximate second-order information. The current PTQ ladder does not implement GPTQ. Access: Primary arXiv record verified.

[5] Asit Mishra, Jorge Albericio Latorre, Jeff Pool, Darko Stosic, Dusan Stosic, Ganesh Venkatesh, Chong Yu, Paulius Micikevicius. **Accelerating Sparse Deep Neural Networks**. arXiv:2104.08378 (2021). [Primary source](https://arxiv.org/abs/2104.08378).

Claim used: 2:4 sparse arithmetic hardware concept; this does not prove selected sparse tactics or speed on the current laptop. Access: Primary arXiv abstract/metadata verified.

[6] Samuel Webb Williams, Andrew Waterman, David A. Patterson. **Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures**. UC Berkeley Technical Report UCB/EECS-2008-134 (2008). [Primary source](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.html).

Claim used: Visual performance model relating compute and memory traffic; our bytes/precision/fusion assumptions require explicit local review. Access: Author-institution technical report record verified; citation uses this 2008 report, not unverified journal metadata.

[7] Stockfish developers. **Introducing NNUE Evaluation**. Official Stockfish blog, 7 August 2020 (2020). [Primary source](https://stockfishchess.org/blog/2020/introducing-nnue-evaluation/).

Claim used: Efficient incremental CPU neural evaluation used with alpha-beta search. Related design context only; no new Stockfish benchmark. Access: Official project article verified.

The Haque paper belongs to ACG 2021 but the proceedings are published in 2022. Its original proposal numerical example is not repeated without checking the paper table. This does not alter the local experiment results.
