#include "Queen.h"
#include <cstdlib>

bool Queen::isValidQueenMove(Move move , char board[8][8])

{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();
    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    char startPiece = board[startRow][startCol];
    char endPiece = board[endRow][endCol];

    int rowstep = 0;
    int colstep = 0;

    // White Queen
    if (startPiece == 'Q')
    {
        // Horizontal movement
        if ((startRow == endRow) &&
            (endPiece == '.' ||
             (endPiece >= 'a' && endPiece <= 'z')))
        {
            if (endCol > startCol)
            {
                colstep = 1;
            }
            else
            {
                colstep = -1;
            }

            int movecol = startCol + colstep;

            while (movecol != endCol)
            {
                if (board[startRow][movecol] == '.')
                {
                    movecol = movecol + colstep;
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        // Vertical movement
        else if ((startCol == endCol) &&
                 (endPiece == '.' ||
                  (endPiece >= 'a' && endPiece <= 'z')))
        {
            if (endRow > startRow)
            {
                rowstep = 1;
            }
            else
            {
                rowstep = -1;
            }

            int moverow = startRow + rowstep;

            while (moverow != endRow)
            {
                if (board[moverow][startCol] == '.')
                {
                    moverow = moverow + rowstep;
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        // Diagonal movement
        else if ((abs(startRow - endRow) == abs(startCol - endCol)) &&
                 (endPiece == '.' ||
                  (endPiece >= 'a' && endPiece <= 'z')))
        {
            if (endRow > startRow)
            {
                rowstep = 1;
            }
            else
            {
                rowstep = -1;
            }

            if (endCol > startCol)
            {
                colstep = 1;
            }
            else
            {
                colstep = -1;
            }

            int moverow = startRow + rowstep;
            int movecol = startCol + colstep;

            while (moverow != endRow && movecol != endCol)
            {
                if (board[moverow][movecol] == '.')
                {
                    moverow = moverow + rowstep;
                    movecol = movecol + colstep;
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        return false;
    }


    // Black Queen
    if (startPiece == 'q')
    {
        // Horizontal movement
        if ((startRow == endRow) &&
            (endPiece == '.' ||
             (endPiece >= 'A' && endPiece <= 'Z')))
        {
            if (endCol > startCol)
            {
                colstep = 1;
            }
            else
            {
                colstep = -1;
            }

            int movecol = startCol + colstep;

            while (movecol != endCol)
            {
                if (board[startRow][movecol] == '.')
                {
                    movecol = movecol + colstep;
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        // Vertical movement
        else if ((startCol == endCol) &&
                 (endPiece == '.' ||
                  (endPiece >= 'A' && endPiece <= 'Z')))
        {
            if (endRow > startRow)
            {
                rowstep = 1;
            }
            else
            {
                rowstep = -1;
            }

            int moverow = startRow + rowstep;

            while (moverow != endRow)
            {
                if (board[moverow][startCol] == '.')
                {
                    moverow = moverow + rowstep;
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        // Diagonal movement
        else if ((abs(startRow - endRow) == abs(startCol - endCol)) &&
                 (endPiece == '.' ||
                  (endPiece >= 'A' && endPiece <= 'Z')))
        {
            if (endRow > startRow)
            {
                rowstep = 1;
            }
            else
            {
                rowstep = -1;
            }

            if (endCol > startCol)
            {
                colstep = 1;
            }
            else
            {
                colstep = -1;
            }

            int moverow = startRow + rowstep;
            int movecol = startCol + colstep;

            while (moverow != endRow && movecol != endCol)
            {
                if (board[moverow][movecol] == '.')
                {
                    moverow = moverow + rowstep;
                    movecol = movecol + colstep;
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        return false;
    }

    return false;
}