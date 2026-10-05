#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <iostream>
#include "Board.h"
#include "Evaluation.h"

using namespace std;

int main()
{
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);

    Board chessboard;
    Evaluation evaluation;

    chessboard.initializeBoard();

    cout << "BOARD" << endl;

    chessboard.printBoardForAI();

    cout << "MOVES" << endl;

    chessboard.printLegalMovesForAI();

    cout << "END" << endl;

    return 0;
}