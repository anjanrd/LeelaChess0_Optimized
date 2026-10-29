"""Classical-112 input helpers, independently checked against native lc0."""

import json
import os
import subprocess
from pathlib import Path

import chess
import numpy as np

RUNTIME = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "lc0-int8"
BRIDGE = RUNTIME / "build/encoder-bridge/encoder_bridge"


def policy_vocabulary():
    moves = []
    for source in chess.SQUARES:
        for target in chess.SQUARES:
            df = abs(chess.square_file(source) - chess.square_file(target))
            dr = abs(chess.square_rank(source) - chess.square_rank(target))
            if source != target and (df == 0 or dr == 0 or df == dr or sorted([df, dr]) == [1, 2]):
                moves.append(chess.square_name(source) + chess.square_name(target))
    for source_file in range(8):
        for target_file in range(max(0, source_file - 1), min(8, source_file + 2)):
            for promotion in "qrb":
                moves.append(chess.square_name(chess.square(source_file, 6)) +
                             chess.square_name(chess.square(target_file, 7)) + promotion)
    assert len(moves) == len(set(moves)) == 1858
    return moves


VOCABULARY = policy_vocabulary()
POLICY_INDEX = {move: i for i, move in enumerate(VOCABULARY)}


def replay(record):
    board = chess.Board(record["fen"])
    if not board.is_valid():
        raise ValueError("Invalid starting position")
    snapshots = [board.copy(stack=True)]
    for uci in record.get("moves", []):
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal history move: {uci}")
        board.push(move)
        snapshots.append(board.copy(stack=True))
    return board, snapshots


def oriented_square(square, side):
    return square if side == chess.WHITE else chess.square_mirror(square)


def policy_key(board, move):
    source, target = move.from_square, move.to_square
    if board.is_castling(move):
        target = chess.square(7 if board.is_kingside_castling(move) else 0, chess.square_rank(source))
    key = chess.square_name(oriented_square(source, board.turn)) + chess.square_name(oriented_square(target, board.turn))
    # Knight promotions use the ordinary from/to slot; q/r/b have extra slots.
    if move.promotion and move.promotion != chess.KNIGHT:
        key += chess.piece_symbol(move.promotion)
    return key


def legal_move_indices(board):
    return {move.uci(): POLICY_INDEX[policy_key(board, move)] for move in board.legal_moves}


def classical_planes(record):
    board, snapshots = replay(record)
    history = [(item, item.is_repetition(2)) for item in reversed(snapshots)]
    # With fill=no, lc0 can infer one genuine predecessor from a FEN EP flag.
    first = snapshots[0]
    if first.ep_square is not None:
        prior = first.copy(stack=False)
        mover = not first.turn
        destination = first.ep_square + (8 if mover == chess.WHITE else -8)
        origin = first.ep_square + (-8 if mover == chess.WHITE else 8)
        prior.remove_piece_at(destination)
        prior.set_piece_at(origin, chess.Piece(chess.PAWN, mover))
        prior.turn = mover
        prior.ep_square = None
        history.append((prior, False))
    result = np.zeros((112, 8, 8), dtype=np.float32)
    for depth, (snapshot, repetition) in enumerate(history[:8]):
        for color_offset, color in [(0, board.turn), (6, not board.turn)]:
            for piece in chess.PIECE_TYPES:
                for square in snapshot.pieces(piece, color):
                    index = oriented_square(square, board.turn)
                    result[13 * depth + color_offset + piece - 1, index // 8, index % 8] = 1
        if repetition:
            result[13 * depth + 12] = 1
    for plane, side, kingside in [(104, board.turn, False), (105, board.turn, True),
                                  (106, not board.turn, False), (107, not board.turn, True)]:
        right = board.has_kingside_castling_rights(side) if kingside else board.has_queenside_castling_rights(side)
        result[plane] = float(right)
    result[108] = float(board.turn == chess.BLACK)
    result[109] = board.halfmove_clock
    result[111] = 1
    return result


def native_encode(records, fill="no"):
    if fill not in {"no", "fen_only"}:
        raise ValueError("Unsupported history fill")
    lines = [record["fen"] + "\t" + " ".join(record.get("moves", [])) for record in records]
    output = subprocess.run([str(BRIDGE), fill], input="\n".join(lines) + "\n",
                            check=True, capture_output=True, text=True)
    items = [json.loads(line) for line in output.stdout.splitlines()]
    if len(items) != len(records):
        raise RuntimeError("Native encoder result count mismatch")
    return items


def dense_planes(native):
    result = np.zeros((112, 64), dtype=np.float32)
    if len(native["planes"]) != 112:
        raise ValueError("Expected 112 planes")
    for index, (mask, value) in enumerate(native["planes"]):
        for square in range(64):
            if (mask >> square) & 1:
                result[index, square] = value
    return result.reshape(112, 8, 8)


def input_object(backends, native):
    result = backends.Input()
    for plane, (mask, value) in enumerate(native["planes"]):
        result.set_mask(plane, mask)
        result.set_val(plane, value)
    return result


def legal_policy(logits, board):
    logits = np.asarray(logits, dtype=np.float32)
    if logits.shape != (1858,) or not np.isfinite(logits).all():
        raise ValueError("Expected 1858 finite policy logits")
    mapping = legal_move_indices(board)
    moves = sorted(mapping)
    if not moves:
        raise ValueError("Terminal positions have no legal policy distribution")
    values = logits[[mapping[move] for move in moves]]
    values = values - np.max(values)
    probabilities = np.exp(values)
    probabilities /= np.sum(probabilities, dtype=np.float32)
    return moves, probabilities, moves[int(np.argmax(probabilities))]


def wdl_from_qd(q, draw):
    result = np.array([(1 - draw + q) / 2, draw, (1 - draw - q) / 2], dtype=np.float32)
    if not np.isfinite(result).all() or np.min(result) < -1e-6 or np.max(result) > 1 + 1e-6:
        raise ValueError("Invalid WDL values")
    return result
