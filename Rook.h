#ifndef ROOK_H
#define ROOK_H

#include "Move.h"

class Rook {
public:
    bool isValidRookMove(Move move, char board[8][8]);
};

#endif