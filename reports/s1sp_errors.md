# s1sp errors from existing results

No engines, tablebase probes, or scoring commands were run. Result values are the saved tablebase labels, from the root side-to-move perspective: +1 win, 0 draw, -1 loss. A chosen move is wrong when it is absent from `correct`.

## Study B, requested budget 1600 (14 positions)

| ID | Class | FEN | s1sp chosen | Chosen TB result | Root TB result | Correct moves | fp16 chosen | fp16 correct? |
|---:|---|---|---|---:|---:|---|---|---|
| 2173 | KQvKQ | `1k6/5K2/8/8/1q6/8/5Q2/8 w - - 0 1` | f7f6 | -1 | +0 | f2a2, f2c2, f2e2, f2e3, f2f1, f2f3, f2f5, f2f6, f2g1, f2g2, f2g3, f2h2, f7e6, f7e8, f7g6, f7g7, f7g8 | f2g3 | yes |
| 6609 | KRPvKR | `4k1r1/7p/8/8/8/3K4/R7/8 w - - 0 1` | d3d2 | -1 | +0 | a2a1, a2a4, a2a5, a2a6, a2a7, a2a8, a2b2, a2c2, a2d2, a2e2, a2f2, a2h2, d3c3, d3c4, d3d4, d3e3, d3e4 | a2a8 | yes |
| 7369 | KQPvKQ | `1k6/7p/2Q5/4K3/8/8/q7/8 w - - 0 1` | e5e4 | -1 | +0 | c6b5, c6b6, c6c1, c6c3, c6c5, c6d5, c6d6, c6d7, c6e4, c6e6, c6e8, c6f3, c6f6, c6h1, c6h6, e5d4, e5d6, e5f4, e5f5, e5f6 | c6d6 | yes |
| 7383 | KQPvKQ | `2K5/8/4k3/8/8/6p1/2Q5/5q2 b - - 0 1` | g3g2 | +0 | +1 | f1f5, f1f8 | f1f5 | yes |
| 7394 | KQPvKQ | `2k5/8/1q6/8/1p6/4K3/Q7/8 w - - 0 1` | e3d2 | -1 | +0 | e3d3, e3e2, e3e4 | e3e2 | yes |
| 7411 | KQPvKQ | `4K3/8/3p4/3Q4/7k/8/7q/8 w - - 0 1` | d5d3 | -1 | +0 | d5c4, d5c6, d5d1, d5d4, d5e4, d5e6, d5f3, d5f7, e8d7, e8d8, e8e7, e8f7 | e8d7 | yes |
| 7442 | KQPvKQ | `6k1/3q4/6KQ/5P2/8/8/8/8 w - - 0 1` | h6h2 | -1 | +0 | f5f6, g6f6, g6g5, g6h5, h6c1, h6e3, h6f4, h6g5, h6h3, h6h4 | h6g5 | yes |
| 8232 | KBPvKN | `8/1N6/7p/8/3K4/8/7b/5k2 w - - 0 1` | b7d8 | -1 | +0 | d4e3, d4e4 | d4e4 | yes |
| 8631 | KPPvKP | `8/1k5p/3P4/8/K7/3P4/8/8 w - - 0 1` | d6d7 | -1 | +0 | a4b3, a4b4, a4b5 | a4b5 | yes |
| 9021 | KQvKRP | `6QK/8/2k5/1p3r2/8/8/8/8 b - - 0 1` | f5d5 | +0 | +1 | f5h5 | f5h5 | yes |
| 9780 | KQRvKQ | `1q6/6r1/7Q/k4K2/8/8/8/8 b - - 0 1` | g7g8 | +0 | +1 | b8a7, b8b1, b8b2, b8b5, b8b7, b8c7, b8c8, b8f8, b8g3, b8g8, g7a7, g7b7, g7c7, g7d7, g7e7, g7f7, g7g1, g7g2, g7g3, g7h7 | g7f7 | yes |
| 9817 | KQRvKQ | `3k4/K7/2Q5/8/7q/8/8/3r4 b - - 0 1` | d1h1 | +0 | +1 | d1a1, d1d2, d1d3, d1d4, d1d7, d1e1, d8e7, h4b4, h4d4, h4e1, h4e7, h4f2, h4f4, h4g3, h4g4, h4g5, h4h1, h4h2, h4h3, h4h5, h4h7 | h4e7 | yes |
| 9827 | KQRvKQ | `4Q3/2q5/8/8/8/6k1/4R3/5K2 b - - 0 1` | c7f4 | -1 | +0 | c7c1 | c7c1 | yes |
| 11004 | KPPvKN | `5K2/8/6p1/1p1k4/8/8/5N2/8 b - - 0 1` | b5b4 | +0 | +1 | d5e6 | d5e6 | yes |

## Study A raw: six KQvK errors (6 positions)

| ID | Class | FEN | s1sp chosen | Chosen TB result | Root TB result | Correct moves | fp16 chosen | fp16 correct? |
|---:|---|---|---|---:|---:|---|---|---|
| 188 | KQvK | `4K1k1/8/8/8/8/2q5/8/8 b - - 0 1` | c3c7 | +0 | +1 | c3a1, c3a3, c3a5, c3b2, c3b3, c3b4, c3c1, c3c2, c3c4, c3c5, c3c6, c3c8, c3d2, c3d3, c3d4, c3e1, c3e3, c3e5, c3f3, c3f6, c3g3, c3g7, c3h3, c3h8, g8g7, g8h7, g8h8 | c3c6 | yes |
| 216 | KQvK | `7k/8/1K6/3Q4/8/8/8/8 w - - 0 1` | d5f7 | +0 | +1 | b6a5, b6a6, b6a7, b6b5, b6b7, b6c5, b6c6, b6c7, d5a2, d5a5, d5a8, d5b3, d5b5, d5b7, d5c4, d5c5, d5c6, d5d1, d5d2, d5d3, d5d4, d5d6, d5d7, d5d8, d5e4, d5e5, d5e6, d5f3, d5f5, d5g2, d5g5, d5h1, d5h5 | d5g5 | yes |
| 218 | KQvK | `7k/8/8/8/8/8/6K1/5Q2 w - - 0 1` | f1f7 | +0 | +1 | f1a1, f1a6, f1b1, f1b5, f1c1, f1c4, f1d1, f1d3, f1e1, f1e2, f1f2, f1f3, f1f4, f1f5, f1f6, f1f8, f1g1, f1h1, g2f2, g2f3, g2g1, g2g3, g2h1, g2h2, g2h3 | g2f3 | yes |
| 229 | KQvK | `8/1q6/8/8/5k2/8/8/K7 b - - 0 1` | b7b3 | +0 | +1 | b7a6, b7a7, b7a8, b7b4, b7b5, b7b6, b7b8, b7c6, b7c7, b7c8, b7d5, b7d7, b7e4, b7e7, b7f3, b7f7, b7g2, b7g7, b7h1, b7h7, f4e3, f4e4, f4e5, f4f3, f4f5, f4g3, f4g4, f4g5 | f4e3 | yes |
| 234 | KQvK | `8/2K5/8/8/8/4Q3/8/7k w - - 0 1` | e3f2 | +0 | +1 | c7b6, c7b7, c7b8, c7c6, c7c8, c7d6, c7d7, c7d8, e3a3, e3a7, e3b3, e3b6, e3c1, e3c3, e3c5, e3d2, e3d3, e3d4, e3e1, e3e2, e3e4, e3e5, e3e6, e3e7, e3e8, e3f3, e3f4, e3g5, e3h3, e3h6 | c7d6 | yes |
| 235 | KQvK | `8/2K5/8/8/8/8/1Q6/7k w - - 0 1` | b2f2 | +0 | +1 | b2a1, b2a2, b2a3, b2b1, b2b3, b2b4, b2b5, b2b6, b2b7, b2b8, b2c1, b2c2, b2c3, b2d2, b2d4, b2e2, b2e5, b2f6, b2g7, b2h8, c7b6, c7b7, c7b8, c7c6, c7c8, c7d6, c7d7, c7d8 | c7d6 | yes |
