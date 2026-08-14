#ifndef PAWN_H
#define PAWN_H

#include "Move.h"

class Pawn {
public:
    bool isValidPawnMove(Move move, char board[8][8]);
};

#endif