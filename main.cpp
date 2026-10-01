#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <iostream>
#include "Board.h"

using namespace std;

int main()
{
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);

    cout << "Welcome to the Gambit Engine!" << endl;

    Board chessboard;

    chessboard.initializeBoard();

vector<Move> moves = chessboard.generateLegalMoves(true);

cout << "White legal moves: " << moves.size() << endl;

while(true)
{
    chessboard.takeinput();
    chessboard.displayBoard();
}
   

    return 0;
}

