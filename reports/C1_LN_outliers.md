# LN output outlier ratios

Worst input-channel absolute maximum / median live-channel maximum. Before and after SmoothQuant at alpha 0.5, as printed in reports/outliers.txt.

| LN output | Before | After |
|---|---|---|
| `/attn_body/ln2` | 20.4 | 4.4 |
| `/encoder0/ln1` | 69.0 | 4.7 |
| `/encoder0/ln2` | 8.6 | 4.3 |
| `/encoder0/smolgen/ln1` | 2.6 | 2.5 |
| `/encoder1/ln1` | 51.9 | 5.2 |
| `/encoder1/ln2` | 8.0 | 4.0 |
| `/encoder1/smolgen/ln1` | 2.2 | 2.4 |
| `/encoder10/ln1` | 30.1 | 4.1 |
| `/encoder10/ln2` | 5.8 | 3.6 |
| `/encoder10/smolgen/ln1` | 2.5 | 2.7 |
| `/encoder11/ln1` | 28.3 | 3.6 |
| `/encoder11/ln2` | 6.5 | 3.6 |
| `/encoder11/smolgen/ln1` | 2.9 | 2.9 |
| `/encoder12/ln1` | 21.9 | 4.3 |
| `/encoder12/ln2` | 8.5 | 3.5 |
| `/encoder12/smolgen/ln1` | 2.5 | 2.6 |
| `/encoder13/ln1` | 26.1 | 3.2 |
| `/encoder13/ln2` | 11.3 | 3.5 |
| `/encoder13/smolgen/ln1` | 2.1 | 2.3 |
| `/encoder14/ln1` | 20.0 | 3.6 |
| `/encoder14/ln2` | 665019.9 | 124666.6 |
| `/encoder14/smolgen/ln1` | 2.1 | 2.3 |
| `/encoder2/ln1` | 48.9 | 4.7 |
| `/encoder2/ln2` | 6.2 | 4.2 |
| `/encoder2/smolgen/ln1` | 2.6 | 2.7 |
| `/encoder3/ln1` | 44.4 | 4.6 |
| `/encoder3/ln2` | 5.6 | 4.2 |
| `/encoder3/smolgen/ln1` | 5.4 | 5.2 |
| `/encoder4/ln1` | 40.4 | 4.2 |
| `/encoder4/ln2` | 5.2 | 3.9 |
| `/encoder4/smolgen/ln1` | 5.0 | 4.5 |
| `/encoder5/ln1` | 36.6 | 4.1 |
| `/encoder5/ln2` | 4.6 | 3.8 |
| `/encoder5/smolgen/ln1` | 2.9 | 2.9 |
| `/encoder6/ln1` | 33.7 | 4.1 |
| `/encoder6/ln2` | 4.8 | 4.4 |
| `/encoder6/smolgen/ln1` | 2.9 | 2.9 |
| `/encoder7/ln1` | 32.8 | 3.6 |
| `/encoder7/ln2` | 4.9 | 3.8 |
| `/encoder7/smolgen/ln1` | 3.6 | 3.7 |
| `/encoder8/ln1` | 33.8 | 4.4 |
| `/encoder8/ln2` | 5.7 | 4.1 |
| `/encoder8/smolgen/ln1` | 2.5 | 2.9 |
| `/encoder9/ln1` | 32.7 | 3.7 |
| `/encoder9/ln2` | 5.9 | 3.8 |
| `/encoder9/smolgen/ln1` | 2.5 | 2.6 |

FFN input encoder ln1: before 20.0..69.0; after 3.2..5.2.

QKV inputs (attn_body/ln2 and encoder0..13/ln2): before 4.6..20.4; after 3.5..4.4.

Smolgen ln1: before 2.1..5.4; after 2.3..5.2.
