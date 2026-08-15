#include "King.h"
#include <cstdlib>

bool King::isValidKingMove(Move move, char board[8][8])
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();
    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    char startPiece = board[startRow][startCol];
    char endPiece = board[endRow][endCol];

    // White King
    if(startPiece == 'K')
    {
        if(abs(startRow - endRow) <= 1 &&
           abs(startCol - endCol) <= 1 &&
           (endPiece == '.' ||
            (endPiece >= 'a' && endPiece <= 'z')))
        {
            if(startRow != endRow || startCol != endCol)
            {
                return true;
            }
        }
    }

    // Black King
    if(startPiece == 'k')
    {
        if(abs(startRow - endRow) <= 1 &&
           abs(startCol - endCol) <= 1 &&
           (endPiece == '.' ||
            (endPiece >= 'A' && endPiece <= 'Z')))
        {
            if(startRow != endRow || startCol != endCol)
            {
                return true;
            }
        }
    }

    return false;
}