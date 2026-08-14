#ifndef BISHOP_H
#define BISHOP_H

#include "Move.h"

class Bishop {
public:
    bool isValidBishopMove(Move move, char board[8][8]);
};

#endif