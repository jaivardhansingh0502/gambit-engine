#ifndef BOARD_H
#define BOARD_H

#include "Move.h"
#include "Pawn.h"
#include "Knight.h"
#include "Bishop.h"
#include "Rook.h"
#include "Queen.h"
#include "King.h"
#include <string>

class Board {
private:
    char board[8][8];

    Pawn pawn;
    Knight knight;
    Bishop bishop;
    Rook rook;
    Queen queen;
    King king ;

    string getPieceSymbol(char piece);


public:
    void initializeBoard();
    void displayBoard();
    void takeinput();
    void makeMove(Move move);

    bool isValid(Move move);
};

#endif