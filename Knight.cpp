#include "Knight.h"
#include <cstdlib>

bool Knight::isValidKnightMove(Move move , char board[8][8])
    {

        int startRow = move.getStartRow() ;
        int startCol = move.getStartCol() ;
        int endRow = move.getEndRow() ;
        int endCol = move.getEndCol() ;

        char startPiece = board[startRow][startCol] ;
        char endPiece = board[endRow][endCol] ;

        // White Move :
        if(startPiece == 'N')
        {
            if(((abs(startRow - endRow) == 1 && abs(startCol - endCol) == 2) || 
            (abs(startRow - endRow) == 2 && abs(startCol - endCol) == 1)) && 
            (endPiece == '.' || (endPiece >= 'a' && endPiece <= 'z')))
            {
                return true ;
            }

        }

        if(startPiece == 'n')
        {
            if(((abs(startRow - endRow) == 1 && abs(startCol - endCol) == 2) || 
            (abs(startRow - endRow) == 2 && abs(startCol - endCol) == 1)) && 
            (endPiece == '.' || (endPiece >= 'A' && endPiece <= 'Z')))
            {
                return true ;
            }

        }

        return false ;

    }