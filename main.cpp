#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <iostream>
#include <string>
#include <vector>

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

    vector<BoardState> stateStack;

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
                stateStack.push_back(
                    chessboard.saveState()
                );

                chessboard.makeMove(move);

                cout << "MOVE_OK" << endl;
            }
            else
            {
                cout << "MOVE_INVALID" << endl;
            }
        }

        else if(command == "UNDO_MOVE")
        {
            if(stateStack.empty())
            {
                cout << "UNDO_EMPTY" << endl;
            }
            else
            {
                BoardState previousState =
                    stateStack.back();

                stateStack.pop_back();

                chessboard.restoreState(
                    previousState
                );

                cout << "UNDO_OK" << endl;
            }
        }

        else if(command == "NEW_GAME")
        {
            chessboard.initializeBoard();

            stateStack.clear();

            cout << "NEW_GAME_OK" << endl;
        }
    }

    return 0;
}