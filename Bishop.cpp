#include "Bishop.h"
#include "Move.h"
#include <cstdlib>

bool Bishop::isValidBishopMove(Move move, char board[8][8])
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();
    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    char startPiece = board[startRow][startCol];
    char endPiece = board[endRow][endCol];

    int rowStep = 0;
    int colStep = 0;

    // White Piece :
    if (startPiece == 'B')
    {
        if ((abs(startRow - endRow) == abs(startCol - endCol)) &&
            (endPiece == '.' || (endPiece >= 'a' && endPiece <= 'z')))
        {
            if (endRow > startRow)
            {
                rowStep = 1;
            }
            else
            {
                rowStep = -1;
            }

            if (endCol > startCol)
            {
                colStep = 1;
            }
            else
            {
                colStep = -1;
            }

            int moverow = startRow + rowStep;
            int movecol = startCol + colStep;

            while (moverow != endRow && movecol != endCol)
            {
                if (board[moverow][movecol] == '.')
                {
                    moverow = moverow + rowStep;
                    movecol = movecol + colStep;
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

    // Black Piece :
    if (startPiece == 'b')
    {
        if ((abs(startRow - endRow) == abs(startCol - endCol)) &&
            (endPiece == '.' || (endPiece >= 'A' && endPiece <= 'Z')))
        {
            if (endRow > startRow)
            {
                rowStep = 1;
            }
            else
            {
                rowStep = -1;
            }

            if (endCol > startCol)
            {
                colStep = 1;
            }
            else
            {
                colStep = -1;
            }

            int moverow = startRow + rowStep;
            int movecol = startCol + colStep;

            while (moverow != endRow && movecol != endCol)
            {
                if (board[moverow][movecol] == '.')
                {
                    moverow = moverow + rowStep;
                    movecol = movecol + colStep;
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