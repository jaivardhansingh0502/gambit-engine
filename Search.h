#ifndef SEARCH_H
#define SEARCH_H

#include "Board.h"
#include <string>

struct SearchResult
{
    std::string bestMove;
    int score;
    long long nodes;
};

class Search
{
public:
    Search();
    SearchResult findBestMove(Board& board, int maxDepth, int timeLimitMs, bool useBook = true);
    unsigned long long perft(Board& board, int depth);
};

#endif
