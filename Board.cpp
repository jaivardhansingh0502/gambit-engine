#include "Board.h"
#include <iostream>
#include <cstdlib>
#include <string>

using namespace std;

void Board :: initializeBoard()
{
    char whitepieces[8] = {'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'};
    char blackpieces[8] = {'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'};

    for(int i = 0; i < 8; i++)
    {
        for(int j = 0; j < 8; j++)
        {
            if(i == 0)
                board[i][j] = blackpieces[j];

            else if(i == 7)
                board[i][j] = whitepieces[j];

            else if(i == 6)
                board[i][j] = 'P';

            else if(i == 1)
                board[i][j] = 'p';

            else
                board[i][j] = '.';
        }
    }
}


void Board :: takeinput()
{
    string from;
    string to;

    cout << endl;
    cout << "Enter the move in the format 'e2 e4' : " << endl;

    cout << "Enter start position: ";
    cin >> from;

    cout << "Enter end position: ";
    cin >> to;

    Move move(from, to);

    if(isValid(move))
    {
        makeMove(move);
    }

    else
    {
        cout << "Invalid move!" << endl;
    }
}


void Board :: displayBoard()
{
    for(int i = 0; i < 8; i++)
    {
        cout << 8 - i << " ";

        for(int j = 0; j < 8; j++)
        {
            cout << board[i][j] << ' ';
        }

        cout << endl;
    }

    cout << "  a b c d e f g h" << endl;
}


void Board :: makeMove(Move move)
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();

    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    board[endRow][endCol] = board[startRow][startCol];

    board[startRow][startCol] = '.';
}


bool Board :: isValid(Move move)
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();

    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    // Starting square empty
    if(board[startRow][startCol] == '.')
    {
        return false;
    }

    char startPiece = board[startRow][startCol];
    char endPiece = board[endRow][endCol];


    // Cannot capture your own piece
    if(endPiece != '.')
    {
        // Black piece trying to capture black piece
        if(startPiece >= 'a' && startPiece <= 'z' &&
           endPiece >= 'a' && endPiece <= 'z')
        {
            return false;
        }

        // White piece trying to capture white piece
        if(startPiece >= 'A' && startPiece <= 'Z' &&
           endPiece >= 'A' && endPiece <= 'Z')
        {
            return false;
        }
    }


    // Pawn
    if(startPiece == 'P' || startPiece == 'p')
    {
        return pawn.isValidPawnMove(move, board);
    }


    // Knight
    if(startPiece == 'N' || startPiece == 'n')
    {
        return knight.isValidKnightMove(move, board);
    }


    // Bishop
    if(startPiece == 'B' || startPiece == 'b')
    {
        return bishop.isValidBishopMove(move, board);
    }


    // Rook
    if(startPiece == 'R' || startPiece == 'r')
    {
        return rook.isValidRookMove(move, board);
    }


    // Queen
    if(startPiece == 'Q' || startPiece == 'q')
    {
        return queen.isValidQueenMove(move, board);
    }

    // King 
    if(startPiece == 'K' || startPiece == 'k')
    {
        return king.isValidKingMove(move, board);
    }

    return false;
}