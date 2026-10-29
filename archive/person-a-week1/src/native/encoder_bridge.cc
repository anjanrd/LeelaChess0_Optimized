// Project adapter around the unmodified, pinned lc0 encoder.
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>

#include "chess/board.h"
#include "chess/position.h"
#include "neural/encoder.h"

int main(int argc, char** argv) {
  using namespace lczero;
  InitializeMagicBitboards();
  if (argc == 2 && std::string(argv[1]) == "vocab") {
    std::cout << '[';
    for (int i = 0; i < 1858; ++i) {
      if (i) std::cout << ',';
      std::cout << '"' << MoveFromNNIndex(i, 0).ToString(false) << '"';
    }
    std::cout << "]\n";
    return 0;
  }
  if (argc != 2 || (std::string(argv[1]) != "no" &&
                    std::string(argv[1]) != "fen_only")) return 2;
  const auto fill = std::string(argv[1]) == "no" ? FillEmptyHistory::NO
                                                : FillEmptyHistory::FEN_ONLY;
  std::string line;
  try {
    while (std::getline(std::cin, line)) {
      const auto separator = line.find('\t');
      const std::string fen = line.substr(0, separator);
      std::istringstream moves(separator == std::string::npos ? "" : line.substr(separator + 1));
      ChessBoard board;
      int rule50, fullmoves;
      board.SetFromFen(fen, &rule50, &fullmoves);
      PositionHistory history;
      history.Reset(board, rule50, fullmoves * 2 - (board.flipped() ? 1 : 2));
      std::string uci;
      while (moves >> uci) {
        auto move = history.Last().GetBoard().ParseMove(uci);
        const auto legal = history.Last().GetBoard().GenerateLegalMoves();
        if (std::find(legal.begin(), legal.end(), move) == legal.end()) {
          throw std::runtime_error("Illegal history move: " + uci);
        }
        history.Append(move);
      }
      int transform = -1;
      const auto planes = EncodePositionForNN(
          pblczero::NetworkFormat::INPUT_CLASSICAL_112_PLANE,
          history, 8, fill, &transform);
      std::cout << "{\"transform\":" << transform
                << ",\"history_length\":" << history.GetLength()
                << ",\"repetitions\":" << history.Last().GetRepetitions()
                << ",\"planes\":[";
      for (size_t i = 0; i < planes.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[' << planes[i].mask << ',' << planes[i].value << ']';
      }
      std::cout << "],\"legal\":[";
      bool first = true;
      for (auto move : history.Last().GetBoard().GenerateLegalMoves()) {
        const auto index = MoveToNNIndex(move, transform);
        if (history.IsBlackToMove()) move.Flip();
        if (!first) std::cout << ',';
        first = false;
        std::cout << "[\"" << move.ToString(false) << "\"," << index << ']';
      }
      std::cout << "]}\n";
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
