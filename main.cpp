#include <iostream>
#include "Board.h"

using namespace std;

int main()
{
    cout << "Welcome to the Gambit Engine!" << endl;

    Board chessboard;

    chessboard.initializeBoard();
    chessboard.displayBoard();

    while(true)
    {
        chessboard.takeinput();
        chessboard.displayBoard();
    }

    return 0;
}