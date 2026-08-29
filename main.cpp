#include <iostream>
#include "Board.h"
#include <windows.h>
using namespace std;

int main()
{
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);

    cout << "Welcome to the Gambit Engine!" << endl;

    Board chessboard;

    chessboard.initializeBoard();
    chessboard.displayBoard();

    bool whiteTurn = true;

    while(true)
    {
        chessboard.takeinput();

        chessboard.displayBoard();

        if(chessboard.isCheckmate(!whiteTurn))
        {
            cout << "CHECKMATE!" << endl;
            break;
        }

        whiteTurn = !whiteTurn;
    }

    return 0;
}