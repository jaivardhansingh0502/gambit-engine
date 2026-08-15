#ifndef KING_H
#define KING_H

#include "Move.h"

class King {
public:
    bool isValidKingMove(Move move, char board[8][8]);
};

#endif