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
    BoardState state = chessboard.saveState();

Move testMove("e2", "e4");

chessboard.makeTemporaryMove(testMove);

cout << "After temporary move:" << endl;
chessboard.displayBoard();

chessboard.restoreState(state);

cout << "After restore:" << endl;
chessboard.displayBoard();

chessboard.displayBoard();
   

    while(true)
    {
        chessboard.takeinput();
        chessboard.displayBoard();
    }

    return 0;
}

