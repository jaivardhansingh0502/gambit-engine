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

    cout << "Welcome to the Gambit Engine!" << endl;

    Board chessboard;
    Evaluation evaluation;

    chessboard.initializeBoard();
    chessboard.displayBoard();
    chessboard.printBoardForAI();
    cout << "\nLegal Moves for Python:\n";
    chessboard.printLegalMovesForAI();

    while(true)
    {
        chessboard.takeinput();

        chessboard.displayBoard();

        int score = evaluation.evaluateBoard(chessboard.getBoard());

        cout << "\nBoard Evaluation: " << score << endl;
    }

}