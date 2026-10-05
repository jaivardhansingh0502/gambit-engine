#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <iostream>
#include <string>

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

    string command;

    while(cin >> command)
    {
        if(command == "GET_MOVES")
        {
            cout << "BOARD" << endl;

            chessboard.printBoardForAI();

            cout << "MOVES" << endl;

            chessboard.printLegalMovesForAI();

            cout << "END" << endl;
        }

        else if(command == "MAKE_MOVE")
        {
            string moveString;

            cin >> moveString;

            string from = moveString.substr(0, 2);
            string to = moveString.substr(2, 2);

            Move move(from, to);

            if(chessboard.isValid(move))
            {
                chessboard.makeMove(move);

                cout << "MOVE_OK" << endl;
            }
            else
            {
                cout << "MOVE_INVALID" << endl;
            }
        }
    }

    return 0;
}