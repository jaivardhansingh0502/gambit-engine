
#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "Board.h"
#include "Evaluation.h"
#include "Search.h"

using namespace std;

static bool isThreefoldRepetition(const vector<string>& positionHistory)
{
    if(positionHistory.empty()) return false;
    const string& current = positionHistory.back();
    int count = 0;
    for(const string& key : positionHistory)
    {
        if(key == current)
        {
            count++;
            if(count >= 3) return true;
        }
    }
    return false;
}

int main()
{



    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);



    Board chessboard;
    Evaluation evaluation;
    Search searchEngine;



    chessboard.initializeBoard();

    vector<BoardState> stateStack;
    vector<string> positionHistory;
    positionHistory.push_back(chessboard.getPositionKey());



    string command;

    while(cin >> command)
    {



        if(command == "GET_MOVES")
        {
            bool isDrawOver = (
                chessboard.isInsufficientMaterial() ||
                chessboard.isFiftyMoveDraw() ||
                isThreefoldRepetition(positionHistory)
            );

            cout << "BOARD" << endl;

            chessboard.printBoardForAI();

            cout << "MOVES" << endl;

            if(!isDrawOver)
            {
                chessboard.printLegalMovesForAI();
            }

            cout << "STATUS" << endl;



            if(chessboard.isCheckmate(chessboard.getWhiteTurn()))
            {
                cout << "CHECKMATE" << endl;
            }



            else if(chessboard.isStalemate(chessboard.getWhiteTurn()))
            {
                cout << "STALEMATE" << endl;
            }



            else if(chessboard.isInsufficientMaterial())
            {
                cout << "DRAW_INSUFFICIENT_MATERIAL" << endl;
            }



            else if(chessboard.isFiftyMoveDraw())
            {
                cout << "DRAW_FIFTY_MOVE" << endl;
            }



            else if(isThreefoldRepetition(positionHistory))
            {
                cout << "DRAW_THREEFOLD_REPETITION" << endl;
            }



            else if(chessboard.isKinginCheck(chessboard.getWhiteTurn()))
            {
                cout << "CHECK" << endl;
            }





            else
            {
                cout << "NORMAL" << endl;
            }



            cout << "TURN" << endl;


            cout << (chessboard.getWhiteTurn() ? "WHITE" : "BLACK") << endl;

            

            cout << "END" << endl;


        }




        else if(command == "MAKE_MOVE")
        {



            string moveString;
            cin >> moveString;



            if(chessboard.isCheckmate(chessboard.getWhiteTurn()) ||
               chessboard.isStalemate(chessboard.getWhiteTurn()) ||
               chessboard.isInsufficientMaterial() ||
               chessboard.isFiftyMoveDraw() ||
               isThreefoldRepetition(positionHistory))
            {



                cout << "GAME_OVER" << endl;
                continue;


            }




            if(moveString.length() < 4 || moveString.length() > 5)
            {
                cout << "MOVE_INVALID" << endl;
                continue;
            }

            if(moveString.length() == 5)
            {
                char promo = tolower(moveString[4]);
                if(promo != 'q' && promo != 'r' && promo != 'b' && promo != 'n')
                {
                    cout << "MOVE_INVALID" << endl;
                    continue;
                }
            }

            string from = moveString.substr(0, 2);
            string to = moveString.substr(2);




            Move move(from, to);



            if(chessboard.isValid(move))
            {


                stateStack.push_back(
                    chessboard.saveState()
                );



                chessboard.makeMove(move);
                positionHistory.push_back(chessboard.getPositionKey());



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

                if(!positionHistory.empty())
                {
                    positionHistory.pop_back();
                }

                cout << "UNDO_OK" << endl;


            }

        }

        else if(command == "NEW_GAME")
        {


            chessboard.initializeBoard();

            stateStack.clear();
            positionHistory.clear();
            positionHistory.push_back(chessboard.getPositionKey());

            cout << "NEW_GAME_OK" << endl;


        }

        else if(command == "EVALUATE")
        {
            int score = evaluation.evaluateBoard(chessboard.getBoard());
            cout << "EVAL " << score << endl;
        }

        else if(command == "GET_FEN")
        {
            cout << "FEN " << chessboard.getFEN() << endl;
        }

        else if(command == "SET_FEN")
        {
            string fenLine;
            getline(cin >> ws, fenLine);
            if(chessboard.loadFEN(fenLine))
            {
                stateStack.clear();
                positionHistory.clear();
                positionHistory.push_back(chessboard.getPositionKey());
                cout << "FEN_OK" << endl;
            }
            else
            {
                cout << "FEN_INVALID" << endl;
            }
        }

        else if(command == "BEST_MOVE")
        {
            int maxDepth = 4;
            int timeLimitMs = 1500;
            cin >> maxDepth >> timeLimitMs;

            SearchResult res = searchEngine.findBestMove(chessboard, maxDepth, timeLimitMs, true);
            if(res.bestMove.empty())
            {
                cout << "BEST_MOVE NONE 0 0" << endl;
            }
            else
            {
                cout << "BEST_MOVE " << res.bestMove << " " << res.score << " " << res.nodes << endl;
            }
        }

        else if(command == "ANALYZE_MOVE")
        {
            int maxDepth = 3;
            int timeLimitMs = 150;
            cin >> maxDepth >> timeLimitMs;

            SearchResult res = searchEngine.findBestMove(chessboard, maxDepth, timeLimitMs, false);
            if(res.bestMove.empty())
            {
                cout << "ANALYZE_MOVE NONE 0 0" << endl;
            }
            else
            {
                cout << "ANALYZE_MOVE " << res.bestMove << " " << res.score << " " << res.nodes << endl;
            }
        }

        else if(command == "PERFT")
        {
            int depth = 1;
            cin >> depth;
            BoardState backup = chessboard.saveState();
            unsigned long long count = searchEngine.perft(chessboard, depth);
            chessboard.restoreState(backup);
            cout << "PERFT " << count << endl;
        }

        else if(command == "uci")
        {
            cout << "id name Gambit Chess Engine" << endl;
            cout << "id author Jaivardhan Singh" << endl;
            cout << "uciok" << endl;
        }

        else if(command == "isready")
        {
            cout << "readyok" << endl;
        }

        else if(command == "ucinewgame")
        {
            chessboard.initializeBoard();
            stateStack.clear();
            positionHistory.clear();
            positionHistory.push_back(chessboard.getPositionKey());
        }

        else if(command == "position")
        {
            string rest;
            getline(cin, rest);
            istringstream iss(rest);
            string tok;
            bool parseMoves = false;

            if(iss >> tok)
            {
                if(tok == "startpos")
                {
                    chessboard.initializeBoard();
                    stateStack.clear();
                    positionHistory.clear();
                    positionHistory.push_back(chessboard.getPositionKey());
                    if(iss >> tok && tok == "moves")
                    {
                        parseMoves = true;
                    }
                }
                else if(tok == "fen")
                {
                    string fenStr;
                    while(iss >> tok)
                    {
                        if(tok == "moves")
                        {
                            parseMoves = true;
                            break;
                        }
                        if(!fenStr.empty()) fenStr += ' ';
                        fenStr += tok;
                    }
                    if(chessboard.loadFEN(fenStr))
                    {
                        stateStack.clear();
                        positionHistory.clear();
                        positionHistory.push_back(chessboard.getPositionKey());
                    }
                }
            }

            if(parseMoves)
            {
                string mv;
                while(iss >> mv)
                {
                    if(mv.size() < 4 || mv.size() > 5) continue;
                    Move m(mv.substr(0, 2), mv.substr(2));
                    if(chessboard.isValid(m))
                    {
                        stateStack.push_back(chessboard.saveState());
                        chessboard.makeMove(m);
                        positionHistory.push_back(chessboard.getPositionKey());
                    }
                }
            }
        }

        else if(command == "go")
        {
            string rest;
            getline(cin, rest);
            istringstream iss(rest);
            string tok;
            bool hasDepth = false;
            bool hasMoveTime = false;
            int maxDepth = 5;
            int timeLimitMs = 1500;
            int wtime = 0, btime = 0, winc = 0, binc = 0;

            while(iss >> tok)
            {
                if(tok == "depth" && (iss >> maxDepth))
                {
                    hasDepth = true;
                    maxDepth = max(1, maxDepth);
                }
                else if(tok == "movetime" && (iss >> timeLimitMs))
                {
                    hasMoveTime = true;
                    timeLimitMs = max(10, timeLimitMs);
                }
                else if(tok == "wtime") { iss >> wtime; }
                else if(tok == "btime") { iss >> btime; }
                else if(tok == "winc") { iss >> winc; }
                else if(tok == "binc") { iss >> binc; }
                else if(tok == "infinite")
                {
                    hasDepth = true;
                    maxDepth = 8;
                    timeLimitMs = 10000;
                    hasMoveTime = true;
                }
            }

            if(hasDepth && !hasMoveTime && wtime == 0 && btime == 0)
            {
                timeLimitMs = 30000;
            }
            else if(!hasMoveTime && (wtime > 0 || btime > 0))
            {
                if(!hasDepth) maxDepth = 8;
                int remain = chessboard.getWhiteTurn() ? wtime : btime;
                int inc = chessboard.getWhiteTurn() ? winc : binc;
                timeLimitMs = max(50, min(5000, remain / 25 + inc / 2));
            }
            else if(hasMoveTime && !hasDepth)
            {
                maxDepth = 10;
            }

            SearchResult res = searchEngine.findBestMove(chessboard, maxDepth, timeLimitMs, true);
            if(res.bestMove.empty())
            {
                cout << "bestmove 0000" << endl;
            }
            else
            {
                int sideScore = chessboard.getWhiteTurn() ? res.score : -res.score;
                cout << "info depth " << maxDepth << " score cp " << sideScore << " nodes " << res.nodes << endl;
                cout << "bestmove " << res.bestMove << endl;
            }
        }

        else if(command == "setoption" || command == "stop" || command == "ponderhit")
        {
            string ignoreRest;
            getline(cin, ignoreRest);
        }

        else if(command == "quit")
        {
            break;
        }

    }


    
    return 0;
}
