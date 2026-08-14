#ifndef QUEEN_H
#define QUEEN_H

#include "Move.h"

class Queen {
public:
    bool isValidQueenMove(Move move, char board[8][8]);
};

#endif