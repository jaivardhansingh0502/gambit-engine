#include "Pawn.h"
#include <cstdlib>

bool Pawn::isValidPawnMove(Move move, char board[8][8]) {
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();
    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    char startPiece = board[startRow][startCol];
    char endPiece = board[endRow][endCol];

    if (startPiece == 'P') {
        if (startRow - endRow == 1 &&
             startCol == endCol && 
             endPiece == '.') {
            return true;
        }
        if (startRow == 6 && 
            startRow - endRow == 2 && startCol == endCol && 
            endPiece == '.' && 
            board[endRow - 1][endCol] == '.') {
            return true;
        }
        if (startRow - endRow == 1 && abs(startCol - endCol) == 1 
        && endPiece >= 'a' && endPiece <= 'z') {
            return true;
        }
    }

    if (startPiece == 'p') {
        if (endRow - startRow == 1 && 
            startCol == endCol && 
            endPiece == '.') {
            return true;
        }
        if (startRow == 1 && endRow - startRow == 2 && 
            startCol == endCol && endPiece == '.' && 
            board[endRow - 1][endCol] == '.') {
            return true;
        }
        if (endRow - startRow == 1 && abs(startCol - endCol) == 1 
        && endPiece >= 'A' && 
        endPiece <= 'Z') {
            return true;
        }
    }

    return false;
}