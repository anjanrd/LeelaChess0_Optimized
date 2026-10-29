# Pre-match opening and protocol review

The existing match runner contains 50 legal opening sequences. All SAN sequences were parsed without an engine, converted to UCI and exported with their final FEN. This documents the existing book; its claimed balance is not independently established. Pair indices cycle through this finite book, so repeated-opening dependence is a limitation for statistical interpretation.

Preserve existing 10+0.1 clocks, color-swapped pairs, MoveOverheadMs=50, no pondering and one active GPU search at a time. The configured 250 pairs is provisional until B measures runtime. Tablebases are arbiter-only at <=5 pieces; engine SyzygyPath remains unset. The runner also has 1,000cp resignation after eight agreeing plies, <=10cp draw adjudication after ply 80, a 400-ply cap, normal chess rules and time forfeits. No protocol or code was changed in this review.

Before the final match, B should record the actual book/order, final pair count, clocks, options and adjudication settings. After receipt, A checks complete color pairs, legality/time/forfeit reasons, PGN/result agreement, paired score distribution and the Elo/CI calculation. Repeated openings and normal-approximation/zero-variance edge cases must be disclosed; an interval spanning zero is inconclusive. **WAIT R4:** actual games, pair count, Elo/CI and final playing-strength interpretation.
