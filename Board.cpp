#include "Board.h"
#include <iostream>
#include <cstdlib>
#include <string>



using namespace std;

const string RESET = "\033[0m";
const string LIGHT = "\033[48;5;255m";
const string DARK  = "\033[48;5;22m";

string Board::getPieceSymbol(char piece)
{
    switch(piece)
    {
        // White pieces
        case 'K': return "♔";
        case 'Q': return "♕";
        case 'R': return "♖";
        case 'B': return "♗";
        case 'N': return "♘";
        case 'P': return "♙";

        // Black pieces
        case 'k': return "♚";
        case 'q': return "♛";
        case 'r': return "♜";
        case 'b': return "♝";
        case 'n': return "♞";
        case 'p': return "♟";

        default: return " ";
    }
}

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
                board[i][j] = ' ';
        }
    }

    whiteTurn = true ;
    whiteKingMoved = false;
    blackKingMoved = false;
    whiteKingsideRookMoved = false;
    blackKingsideRookMoved = false;
    whiteQueensideRookMoved = false ;
    blackQueensideRookMoved = false ;
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
    cout << endl ;

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


void Board::displayBoard()
{
    // const string RESET = "\033[0m";

    // // Board colors
    // const string LIGHT = "\033[48;5;255m";
    // const string DARK  = "\033[48;5;22m";

    // // Piece colors
    // const string WHITE_PIECE = "\033[38;5;16m";
    // const string BLACK_PIECE = "\033[38;5;255m";

    // cout << "\n";

    // // Column labels
    // cout << "       a       b       c       d       e       f       g       h\n";

    // // Top border
    // cout << "    +-------+-------+-------+-------+-------+-------+-------+-------+\n";

    // for(int i = 0; i < 8; i++)
    // {
    //     // Each chess square is 7 characters wide × 5 lines high
    //     for(int line = 0; line < 5; line++)
    //     {
    //         // Print rank number only in the middle
    //         if(line == 2)
    //         {
    //             cout << " " << 8 - i << "  ";
    //         }
    //         else
    //         {
    //             cout << "    ";
    //         }

    //         for(int j = 0; j < 8; j++)
    //         {
    //             // Choose square color
    //             string background;

    //             if((i + j) % 2 == 0)
    //             {
    //                 background = LIGHT;
    //             }
    //             else
    //             {
    //                 background = DARK;
    //             }

    //             char pieceChar = board[i][j];

    //             // Start background color
    //             cout << background;

    //             // Empty square
    //             if(pieceChar == ' ')
    //             {
    //                 cout << "       ";
    //             }
    //             else
    //             {
    //                 string piece = getPieceSymbol(pieceChar);

    //                 // White pieces
    //                 if(pieceChar >= 'A' && pieceChar <= 'Z')
    //                 {
    //                     if(line == 2)
    //                     {
    //                         cout << "   "
    //                              << WHITE_PIECE
    //                              << piece
    //                              << background
    //                              << "   ";
    //                     }
    //                     else
    //                     {
    //                         cout << "       ";
    //                     }
    //                 }

    //                 // Black pieces
    //                 else
    //                 {
    //                     if(line == 2)
    //                     {
    //                         cout << "   "
    //                              << BLACK_PIECE
    //                              << piece
    //                              << background
    //                              << "   ";
    //                     }
    //                     else
    //                     {
    //                         cout << "       ";
    //                     }
    //                 }
    //             }

    //             // Reset after the COMPLETE square
    //             cout << RESET;
    //         }

    //         cout << "\n";
    //     }

    //     // Separator between rows
    //     if(i != 7)
    //     {
    //         cout << "    +-------+-------+-------+-------+-------+-------+-------+-------+\n";
    //     }
    // }

    // // Bottom border
    // cout << "    +-------+-------+-------+-------+-------+-------+-------+-------+\n";

    // // Column labels
    // cout << "       a       b       c       d       e       f       g       h\n";

    // cout << "\n";

    cout << "\n";

    cout << "       a       b       c       d       e       f       g       h\n";

    cout << "    ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐\n";

    for(int i = 0; i < 8; i++)
    {
        // Top empty line
        cout << "    ";

        for(int j = 0; j < 8; j++)
        {
            cout << "│       ";
        }

        cout << "│\n";

        // Piece / empty space
        cout << " " << 8 - i << "  ";

        for(int j = 0; j < 8; j++)
        {
            cout << "│   ";

            if(board[i][j] == ' ')
                cout << " ";
            else
                cout << board[i][j];

            cout << "   ";
        }

        cout << "│\n";

        // Bottom empty line
        cout << "    ";

        for(int j = 0; j < 8; j++)
        {
            cout << "│       ";
        }

        cout << "│\n";

        // Horizontal separator
        if(i != 7)
        {
            cout << "    ├───────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤\n";
        }
    }

    // Bottom border
    cout << "    └───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘\n";

    cout << "       a       b       c       d       e       f       g       h\n";

    cout << "\n";
}


void Board :: makeMove(Move move)
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();

    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    char piece = board[startRow][startCol];


    // =========================
    // WHITE KING SIDE CASTLING
    // =========================

    if(piece == 'K' &&
       startRow == 7 && startCol == 4 &&
       endRow == 7 && endCol == 6)
    {
        board[7][4] = ' ';
        board[7][6] = 'K';

        board[7][7] = ' ';
        board[7][5] = 'R';

        whiteKingMoved = true;
        whiteKingsideRookMoved = true;

        whiteTurn = !whiteTurn;
        return;
    }


    // =========================
    // WHITE QUEEN SIDE CASTLING
    // =========================

    if(piece == 'K' &&
       startRow == 7 && startCol == 4 &&
       endRow == 7 && endCol == 2)
    {
        board[7][4] = ' ';
        board[7][2] = 'K';

        board[7][0] = ' ';
        board[7][3] = 'R';

        whiteKingMoved = true;
        whiteQueensideRookMoved = true;

        whiteTurn = !whiteTurn;
        return;
    }


    // =========================
    // BLACK KING SIDE CASTLING
    // =========================

    if(piece == 'k' &&
       startRow == 0 && startCol == 4 &&
       endRow == 0 && endCol == 6)
    {
        board[0][4] = ' ';
        board[0][6] = 'k';

        board[0][7] = ' ';
        board[0][5] = 'r';

        blackKingMoved = true;
        blackKingsideRookMoved = true;

        whiteTurn = !whiteTurn;
        return;
    }


    // =========================
    // BLACK QUEEN SIDE CASTLING
    // =========================

    if(piece == 'k' &&
       startRow == 0 && startCol == 4 &&
       endRow == 0 && endCol == 2)
    {
        board[0][4] = ' ';
        board[0][2] = 'k';

        board[0][0] = ' ';
        board[0][3] = 'r';

        blackKingMoved = true;
        blackQueensideRookMoved = true;

        whiteTurn = !whiteTurn;
        return;
    }




    if(piece == 'P' && startRow - endRow == 2 )
    {

        lastPawnRow = endRow;
        lastPawnCol = endCol;
        lastMoveWasDoublePawn = true;

    }


    else if(piece == 'p' && endRow - startRow == 2)
    {

        lastPawnRow = endRow ;
        lastPawnCol = endCol ;
        lastMoveWasDoublePawn = true ;

    }


    else
    {
        lastMoveWasDoublePawn = false ;
    }


    // =========================
    // NORMAL MOVE
    // =========================

    board[endRow][endCol] = piece;
    board[startRow][startCol] = ' ';

    

    // =========================
    // PAWN PROMOTION
    // =========================

    if(piece == 'P' && endRow == 0)
    {
        promotePawn(endRow, endCol);
    }

    if(piece == 'p' && endRow == 7)
    {
        promotePawn(endRow, endCol);
    }

    // =========================
    // MOVEMENT HISTORY
    // =========================

    if(piece == 'K')
    {
        whiteKingMoved = true;
    }

    if(piece == 'k')
    {
        blackKingMoved = true;
    }

    if(piece == 'R')
    {
        if(startRow == 7 && startCol == 7)
        {
            whiteKingsideRookMoved = true;
        }

        if(startRow == 7 && startCol == 0)
        {
            whiteQueensideRookMoved = true;
        }
    }

    if(piece == 'r')
    {
        if(startRow == 0 && startCol == 7)
        {
            blackKingsideRookMoved = true;
        }

        if(startRow == 0 && startCol == 0)
        {
            blackQueensideRookMoved = true;
        }
    }

    whiteTurn = !whiteTurn;
}




bool Board :: isValid(Move move)
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();

    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    // Starting square empty
    if(board[startRow][startCol] == ' ')
    {
        return false;
    }

    char startPiece = board[startRow][startCol];
    char endPiece = board[endRow][endCol];

    // Agar white ki turn hai to vhi move kr skta hai :

    if(whiteTurn)
    {
        if(startPiece >= 'a' && startPiece <= 'z')
        {
            return false ;
        }
    }
    
    // BlackTurn me only black piece can move :

    else
    {
        if(startPiece >= 'A' && startPiece <= 'Z')
        {
            return false ;
        }
    }

    // Cannot capture your own piece
    if(endPiece != ' ')
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


        if(isValidCastling(move, whiteTurn))
        {
            return true;
        }


        return king.isValidKingMove(move, board);
    }

    return false;
}


    bool Board :: isKinginCheck(bool whiteTurn)
    {
       
        char king ;

        if(whiteTurn)
        {
            king = 'K' ;
        }

        else
        {
            king = 'k' ;
        }

        int kingRow = -1 ;
        int kingCol = -1 ;

        for(int i = 0 ;i < 8 ;i++)
        {
            for(int j = 0 ; j < 8 ;j++)
            {
                if(board[i][j] == king)
                {
                    kingRow = i ;
                    kingCol = j ;
                    break ;
                }
            }
            if(kingRow != -1)
            break;
        }

        // PAWN


        char opponentPiece ;

        if(whiteTurn)
        {
            opponentPiece = 'p' ;
        }

        else
        {
            opponentPiece = 'P' ;
        }

        for(int i = 0 ; i < 8 ;i++)
        {
            for(int j = 0 ; j < 8 ;j++)
            {
                if(board[i][j] == opponentPiece) 
                {
                    
                    if(whiteTurn)
                    {
                        if(i + 1 < 8)
                        {
                            
                            // Left Diagonal :

                            if( j-1 >= 0 && kingRow == i + 1 && kingCol == j-1)
                            {
                                return true ;
                            }

                            // Right Diagonal :

                            else if( j + 1 <8 && kingRow == i + 1 && kingCol == j+1)
                            {
                                return true ;
                            }
                        }
                    }

                    else 
                    {
                        if( i - 1 >= 0)
                        {

                            // Left Diagonal :

                            if(j-1 >= 0 && kingRow == i - 1 && kingCol == j-1)
                            {
                                return true ;
                            }

                            // Right Diagonal :

                            else if( j + 1 < 8 && kingRow == i - 1 && kingCol == j+1)
                            {
                                return true ;
                            }
                        }
                    }
                }
            }
        }


        // Knight :

        if(whiteTurn)
        {
            opponentPiece = 'n' ;
        }

        else
        {
            opponentPiece = 'N' ;
        }


        for(int i = 0 ; i < 8 ;i++)
        {
            for(int j = 0 ; j < 8 ; j++)
            {
                if(board[i][j] ==  opponentPiece)
                {
                    
                        // cosidering left + upward movement (2 step row ++ and 1 col --)
                        if( i + 2 < 8 && j - 1 >=0 && i + 2 == kingRow && j - 1 == kingCol)
                        {
                            return true ;
                        }

                        // Considering left + downward movement (2 step row -- and 1 step col --)
                        else if(i - 2 >=0 && j - 1 >=0 && i - 2 == kingRow && j - 1 == kingCol)
                        {
                            return true ;
                        }

                        // Considering right + upward movement (2 step row ++ and 1 step col ++)
                        else if( i + 2 < 8 && j + 1 < 8 && i + 2 == kingRow && j + 1 == kingCol)
                        {
                            return true ;
                        }

                        // Considering right + downward movement (2 step row -- and 1 step col ++)
                        else if(i - 2 >= 0 && j + 1 < 8 && i - 2 == kingRow && j + 1 == kingCol)
                        {
                            return true ;
                        }

                        // cosidering left + upward movement (1 step row ++ and 2 col --)
                        if( i + 1 < 8 && j - 2 >=0 && i + 1 == kingRow && j - 2 == kingCol)
                        {
                            return true ;
                        }

                        // Considering left + downward movement (1 step row -- and 2 step col --)
                        else if(i - 1 >=0 && j - 2 >=0 && i - 1 == kingRow && j - 2 == kingCol)
                        {
                            return true ;
                        }

                        // Considering right + upward movement (1 step row ++ and 2 step col ++)
                        else if( i + 1 < 8 && j + 2 < 8 && i + 1 == kingRow && j + 2 == kingCol)
                        {
                            return true ;
                        }

                        // Considering right + downward movement (1 step row -- and 2 step col ++)
                        else if(i - 1 >= 0 && j + 2 < 8 && i - 1 == kingRow && j + 2 == kingCol)
                        {
                            return true ;
                        }
                    
                }
            }
        }


        // Bishop 

        if(whiteTurn)
        {
            opponentPiece = 'b' ;
        }

        else 
        {
            opponentPiece = 'B' ;
        }

        for(int i = 0 ; i < 8 ; i++)
        
        {
            for(int j = 0 ; j < 8 ;j++)
            {
                if(board[i][j] == opponentPiece)
                {

                    // Left upwards diagonally 

                    int currentRow = i + 1;
                    int currentCol = j - 1;

                    while(currentRow < 8 && currentCol >= 0)
                    {
                        // King mil gaya
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Koi piece mil gaya → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow++;
                        currentCol--;
                    }

                    // Left Downwards Diagonally

                    currentRow = i - 1 ;
                    currentCol = j - 1 ;

                    while(currentRow >= 0 && currentCol >= 0)
                    {
                        // King Found
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow--;
                        currentCol--;
                    }


                    // Right Downwards 

                    currentRow = i - 1 ;
                    currentCol = j + 1 ;

                    while(currentRow >= 0 && currentCol < 8)
                    {
                        // King Found
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow--;
                        currentCol++;
                    }

                    
                    // Right Upwards 

                    currentRow = i + 1 ;
                    currentCol = j + 1 ;

                    while(currentRow < 8 && currentCol < 8)
                    {
                        // King Found
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow++;
                        currentCol++;
                    }

                    
                }
            }
        }


        // Rook 

        if(whiteTurn)
        {
            opponentPiece = 'r' ;
        }

        else
        {
            opponentPiece = 'R' ;
        }


        for(int i = 0 ; i < 8 ; i++)
        {
            for(int j = 0 ; j < 8 ; j++)
            {
                if(board[i][j] == opponentPiece)
                {

                    int currentRow  ;
                    int currentCol ;

                    // Upward Moving 
                    
                    currentRow = i + 1 ;

                    while(currentRow < 8)
                    {
                        if(currentRow == kingRow && j == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[currentRow][j] != ' ')
                        {
                            break;
                        }

                        currentRow++ ;
                    }

                    // Downward Moving 

                    currentRow = i - 1 ;
                    

                    while(currentRow >= 0)
                    {
                        if(currentRow == kingRow && j == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[currentRow][j] != ' ')
                        {
                            break;
                        }

                        currentRow-- ;
                    }

                    // Left Movement 

                    currentCol = j - 1 ;
                    

                    while(currentCol >= 0)
                    {
                        if(i == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[i][currentCol] != ' ')
                        {
                            break;
                        }

                        currentCol-- ;
                    }


                    // Right Movement 

                    currentCol = j + 1 ;
                    

                    while(currentCol < 8)
                    {
                        if(i == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[i][currentCol] != ' ')
                        {
                            break;
                        }

                        currentCol++ ;
                    }
                }
            }
        }

        // Queen 

        if(whiteTurn)
        {
            opponentPiece = 'q' ;
        }

        else
        {
            opponentPiece = 'Q' ;
        }

        for(int i = 0 ; i < 8 ; i ++)
        {
            for(int j = 0 ; j < 8 ; j ++)
            {
                if(board[i][j] == opponentPiece)
                {
                    // Left upwards diagonally 

                    int currentRow = i + 1;
                    int currentCol = j - 1;

                    while(currentRow < 8 && currentCol >= 0)
                    {
                        // King mil gaya
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Koi piece mil gaya → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow++;
                        currentCol--;
                    }

                    // Left Downwards Diagonally

                    currentRow = i - 1 ;
                    currentCol = j - 1 ;

                    while(currentRow >= 0 && currentCol >= 0)
                    {
                        // King Found
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow--;
                        currentCol--;
                    }


                    // Right Downwards 

                    currentRow = i - 1 ;
                    currentCol = j + 1 ;

                    while(currentRow >= 0 && currentCol < 8)
                    {
                        // King Found
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow--;
                        currentCol++;
                    }

                    
                    // Right Upwards 

                    currentRow = i + 1 ;
                    currentCol = j + 1 ;

                    while(currentRow < 8 && currentCol < 8)
                    {
                        // King Found
                        if(currentRow == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Bishop block
                        if(board[currentRow][currentCol] != ' ')
                        {
                            break;
                        }

                        // Next diagonal square
                        currentRow++;
                        currentCol++;
                    }

                    currentRow = i + 1 ;

                    while(currentRow < 8)
                    {
                        if(currentRow == kingRow && j == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[currentRow][j] != ' ')
                        {
                            break;
                        }

                        currentRow++ ;
                    }

                    // Downward Moving 

                    currentRow = i - 1 ;
                    

                    while(currentRow >= 0)
                    {
                        if(currentRow == kingRow && j == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[currentRow][j] != ' ')
                        {
                            break;
                        }

                        currentRow-- ;
                    }

                    // Left Movement 

                    currentCol = j - 1 ;
                    

                    while(currentCol >= 0)
                    {
                        if(i == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[i][currentCol] != ' ')
                        {
                            break;
                        }

                        currentCol-- ;
                    }


                    // Right Movement 

                    currentCol = j + 1 ;
                    

                    while(currentCol < 8)
                    {
                        if(i == kingRow && currentCol == kingCol)
                        {
                            return true;
                        }

                        // Different Piece → Rook block
                        if(board[i][currentCol] != ' ')
                        {
                            break;
                        }

                        currentCol++ ;
                    }

                }
            }
        }

        // King 

        if(whiteTurn)
        {
            opponentPiece = 'k' ;
        }

        else
        {
            opponentPiece = 'K' ;
        }


        for(int i = 0 ; i < 8 ; i++)
        {
            for(int j = 0 ; j < 8 ; j++)
            {

                if(board[i][j] == opponentPiece)
                {
                    if(i+1 == kingRow && j == kingCol)
                    {
                        return true ;
                    }

                    if(i == kingRow && j + 1 == kingCol)
                    {
                        return true ;
                    }

                    if(i + 1 == kingRow && j + 1 == kingCol)
                    {
                        return true ;
                    }

                    if(i-1 == kingRow && j == kingCol)
                    {
                        return true ;
                    }

                    if(i == kingRow && j - 1 == kingCol)
                    {
                        return true ;
                    }

                    if(i + 1 == kingRow && j - 1 == kingCol)
                    {
                        return true ;
                    }

                    if(i - 1 == kingRow && j + 1 == kingCol)
                    {
                        return true ;
                    }

                    if( i - 1 == kingRow && j - 1 == kingCol)
                    {
                        return true ;
                    }
                }
            }
        }
        return false;
    }

    bool Board ::canKingEscape(bool whiteTurn)
    {
        char king ; 

        if(whiteTurn)
        {
            king = 'K' ;
        }
        
        else
        {
            king = 'k' ;
        }

        int kingRow = -1 ;
        int kingCol = -1 ;


        for(int i = 0 ; i < 8 ; i ++)
        {
            for(int j = 0 ; j < 8 ; j++ )
            {
                if(board[i][j] == king)
                {
                    kingRow = i ; 
                    kingCol = j ;
                    break ;
                }
            }
        }

        for(int rowChange = -1 ; rowChange <= 1 ; rowChange++)
        {
            for(int colChange = -1 ; colChange <= 1 ; colChange++)
            {

                // Current Position of King :
                if(rowChange == 0 && colChange == 0) 
                {
                    continue ;
                }


                // Declare new row and new col for further use :
                int newRow = kingRow + rowChange ;
                int newCol = kingCol + colChange ;


                // Outside Board Check :
                if(newRow < 0 || newRow >= 8 || newCol < 0 || newCol >= 8)
                {
                    continue ;
                }
                


                if(whiteTurn)
                {
                    if(board[newRow][newCol] >= 'A' &&
                    board[newRow][newCol] <= 'Z')
                        continue;
                }
                else
                {
                    if(board[newRow][newCol] >= 'a' &&
                    board[newRow][newCol] <= 'z')
                        continue;
                }


                char destination = board[newRow][newCol];

                    // Temporary move
                    board[kingRow][kingCol] = ' ';
                    board[newRow][newCol] = king;

                    // Check the NEW board position
                    bool stillInCheck = isKinginCheck(whiteTurn);

                    // Undo temporary move
                    board[kingRow][kingCol] = king;
                    board[newRow][newCol] = destination;

                    // Safe square found
                    if(!stillInCheck)
                        return true;
            }
        }
        return false ;
    }

    bool Board :: canRookSaveKing(bool whiteTurn)
    {
        char rook ;
        char king ;

        if(whiteTurn)
        {
            rook = 'R' ;
            king = 'K' ;
        }

        else
        {
            rook = 'r' ;
            king = 'k' ;
        }

        for(int i = 0 ; i < 8 ; i ++)
        {
            for(int j = 0 ; j < 8 ; j ++)
            {
                if(board[i][j] == rook)
                {
                    for(int rowChange = -7 ; rowChange < 8 ; rowChange++)
                    {
                        for(int colChange = -7 ; colChange < 8 ; colChange++)
                        {

                            // Same Square :
                            if(rowChange == 0 && colChange == 0)
                            {
                                continue ;
                            }


                            // Rook Can not move diagonally :
                            if(rowChange != 0 && colChange != 0)
                            {
                                continue ;
                            }


                            int newRow = i + rowChange ;
                            int newCol = j + colChange ;


                            // Boundary check
                            if(newRow < 0 || newRow >= 8 ||
                            newCol < 0 || newCol >= 8)
                            {
                                continue;
                            }


                            // Right Move : 
                            int currentRow = i ; 
                            int currentCol = j + 1 ; 

                            while(currentCol < 8)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = rook ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = rook ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = rook ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = rook ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentCol ++ ;
                            }





                             // left Move : 
                            currentRow = i ; 
                            currentCol = j - 1 ; 

                            while(currentCol >= 0)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = rook ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = rook ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = rook ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = rook ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentCol -- ;
                            }





                             // Up Move : 
                            currentRow = i + 1; 
                            currentCol = j ; 

                            while(currentRow < 8)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = rook ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = rook ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = rook ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = rook ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentRow ++ ;
                            }




                             // Down Move : 
                            currentRow = i - 1; 
                            currentCol = j ; 

                            while(currentRow >= 0)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = rook ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = rook ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = rook ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = rook ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentRow -- ;
                            }
                        }
                    }
                }
            }
        }
        return false ;
    }



    bool Board :: canBishopSaveKing(bool whiteTurn)
    {
        char bishop ;
        char king ;

        if(whiteTurn)
        {
            bishop = 'B' ;
            king = 'K' ;
        }

        else
        {
            bishop = 'b' ;
            king = 'k' ;
        }

        for(int i = 0 ; i < 8 ; i++)
        {
            for(int j = 0 ; j < 8 ; j++)
            {
                if(board[i][j] == bishop)
                {
                    for(int rowChange = -7 ; rowChange < 8 ; rowChange++)
                    {
                        for(int colChange = -7 ; colChange < 8 ; colChange++)
                        {
                            
                            // If rowdiff and coldiff not equal skip 
                            if( abs(rowChange) != abs(colChange) )
                            {
                                continue ;
                            }

                            // Same Square :
                            if(rowChange == 0 && colChange == 0)
                            {
                                continue ;
                            }

                            int newRow = i + rowChange;
                            int newCol = j + colChange;

                            // Boundary
                            if(newRow < 0 || newRow >= 8 ||
                            newCol < 0 || newCol >= 8)
                            {
                                continue;
                            }

                            // Right Upside Diagonal ;

                            int currentRow = i + 1 ;
                            int currentCol = j + 1 ;

                            while(currentRow < 8 && currentCol < 8)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = bishop ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = bishop ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = bishop ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = bishop ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol ++ ;
                                currentRow ++ ;
                            }


                            
                            // Right Downside Diagonal ;

                             currentRow = i - 1 ;
                             currentCol = j + 1 ;

                            while(currentRow >= 0 && currentCol < 8)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = bishop ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = bishop ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = bishop ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = bishop ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol ++ ;
                                currentRow -- ;
                            }



                            // Left Downside Diagonal ;

                             currentRow = i - 1 ;
                             currentCol = j - 1 ;

                            while(currentRow >= 0 && currentCol >= 0)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = bishop ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = bishop ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = bishop ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = bishop ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol -- ;
                                currentRow -- ;
                            }



                            // left Upside Diagonal ;

                             currentRow = i + 1 ;
                             currentCol = j - 1 ;

                            while(currentRow < 8 && currentCol >= 0)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = bishop ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = bishop ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = bishop ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = bishop ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol -- ;
                                currentRow ++ ;
                            }
                        }
                    }
                }
            }
        }
        return false ;
    }


    bool Board :: canKnightSaveKing(bool whiteTurn)
    {

        char knight ;
        char king ; 
        
        if(whiteTurn)
        {
            king = 'K' ;
            knight = 'N' ;
        }

        else
        {
            king = 'k' ;
            knight = 'n' ;
        }

        
        for(int i = 0 ; i < 8 ; i ++)
        {
            for(int j = 0 ; j < 8 ; j ++)
            {
                if(board[i][j] == knight)
                {
                
                   for(int rowChange = -2 ; rowChange <= 2 ; rowChange++) 
                    {
                     for(int colChange = -2 ; colChange <= 2 ; colChange++)
                    {
                        
                        // ColChange can not be equal to rowChange 
                        if(abs(colChange) + abs(rowChange) != 3)
                        {
                            continue ;
                        }

                        // Actual Square 
                        if(rowChange == 0 && colChange == 0)
                        {
                            continue ;
                        }




                        // Right(2) + Down(1)

                        if(rowChange == 1 && colChange == 2)
                        {

                            if(i + 1 < 8 && j + 2 < 8)
                            {

                                if(board[i+1][j+2] == ' ')
                                {

                                    // Temporary
                                    board[i+1][j+2] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i+1][j+2] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Right(2) + Up(1)

                        if(rowChange == -1 && colChange == 2)
                        {

                            if(i - 1 >= 0 && j + 2 < 8)
                            {

                                if(board[i-1][j+2] == ' ')
                                {

                                    // Temporary
                                    board[i-1][j+2] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i-1][j+2] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Left(2) + Down(1)

                        if(rowChange == 1 && colChange == -2)
                        {

                            if(i + 1 < 8 && j - 2 >= 0)
                            {

                                if(board[i+1][j-2] == ' ')
                                {

                                    // Temporary
                                    board[i+1][j-2] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i+1][j-2] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Left(2) + Up(1)

                        if(rowChange == -1 && colChange == -2)
                        {

                            if(i - 1 >= 0 && j - 2 >= 0)
                            {

                                if(board[i-1][j-2] == ' ')
                                {

                                    // Temporary
                                    board[i-1][j-2] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i-1][j-2] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Down(2) + Right(1)

                        if(rowChange == 2 && colChange == 1)
                        {

                            if(i + 2 < 8 && j + 1 < 8)
                            {

                                if(board[i+2][j+1] == ' ')
                                {

                                    // Temporary
                                    board[i+2][j+1] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i+2][j+1] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Down(2) + Left(1)

                        if(rowChange == 2 && colChange == -1)
                        {

                            if(i + 2 < 8 && j - 1 >= 0)
                            {

                                if(board[i+2][j-1] == ' ')
                                {

                                    // Temporary
                                    board[i+2][j-1] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i+2][j-1] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Up(2) + Right(1)

                        if(rowChange == -2 && colChange == 1)
                        {

                            if(i - 2 >= 0 && j + 1 < 8)
                            {

                                if(board[i-2][j+1] == ' ')
                                {

                                    // Temporary
                                    board[i-2][j+1] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i-2][j+1] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }


                        // Up(2) + Left(1)

                        if(rowChange == -2 && colChange == -1)
                        {

                            if(i - 2 >= 0 && j - 1 >= 0)
                            {

                                if(board[i-2][j-1] == ' ')
                                {

                                    // Temporary
                                    board[i-2][j-1] = knight ;
                                    board[i][j] = ' ' ;

                                    // Check King
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo
                                    board[i-2][j-1] = ' ' ;
                                    board[i][j] = knight ;
                                }
                            }
                        }
                    }
                    }
                }
            }
        }
        return false ;
    }


    bool Board :: canQueenSaveKing(bool whiteTurn)
    {


        char queen ;
        char king ;

        if(whiteTurn)
        {
            queen = 'Q' ;
        }

        else
        {
            queen = 'q' ;
        }


        for(int i = 0 ; i < 8 ; i ++)
        {
            for(int j = 0 ; j < 8 ; j ++)
            {

                if(board[i][j] == queen)
                {

                    for(int rowChange = -7 ; rowChange < 8 ; rowChange++)
                    {
                        for(int colChange = -7 ; colChange < 8 ; colChange++)
                        {


                        // Same square
                        if(rowChange == 0 && colChange == 0)
                        {
                            continue;
                        }


                        // Queen moves like Rook OR Bishop
                        if(rowChange != 0 && colChange != 0 &&
                        abs(rowChange) != abs(colChange))
                        {
                            continue;
                        }


                        int newRow = i + rowChange;
                        int newCol = j + colChange;


                        // Boundary
                        if(newRow < 0 || newRow >= 8 ||
                        newCol < 0 || newCol >= 8)
                        {
                            continue;
                        }

                        // Now this is a valid Queen destination

                        

                        // Rook Part : 


                        // Right Move : 
                            int currentRow = i ; 
                            int currentCol = j + 1 ; 

                            while(currentCol < 8)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = queen ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentCol ++ ;
                            }





                             // left Move : 
                            currentRow = i ; 
                            currentCol = j - 1 ; 

                            while(currentCol >= 0)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = queen ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentCol -- ;
                            }





                             // Up Move : 
                            currentRow = i + 1; 
                            currentCol = j ; 

                            while(currentRow < 8)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = queen ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentRow ++ ;
                            }




                             // Down Move : 
                            currentRow = i - 1; 
                            currentCol = j ; 

                            while(currentRow >= 0)
                            {
                                
                                // Empty Space : 
                                if(board[currentRow][currentCol] == ' ')
                                {
                                    
                                    // Temprarily Move and check :

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    // Check kro if possible
                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo the move : 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;

                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char CapturedPiece = board[currentRow][currentCol] ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ; 

                                        // check if it does the Work \

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }
                                        

                                        // Undo 
                                        board[i][j] = queen ;
                                        board[currentRow][currentCol] = CapturedPiece ;
                                    }

                                    // Koi bhi aur piece mil gaya to ye case Fail hai ;
                                    break ;
                                }

                                currentRow -- ;
                            }


                            // Bishop Part


                            // Right Upside Diagonal ;

                            currentRow = i + 1 ;
                            currentCol = j + 1 ;

                            while(currentRow < 8 && currentCol < 8)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = queen ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol ++ ;
                                currentRow ++ ;
                            }


                            
                            // Right Downside Diagonal ;

                             currentRow = i - 1 ;
                             currentCol = j + 1 ;

                            while(currentRow >= 0 && currentCol < 8)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = queen ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol ++ ;
                                currentRow -- ;
                            }



                            // Left Downside Diagonal ;

                             currentRow = i - 1 ;
                             currentCol = j - 1 ;

                            while(currentRow >= 0 && currentCol >= 0)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = queen ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol -- ;
                                currentRow -- ;
                            }



                            // left Upside Diagonal ;

                             currentRow = i + 1 ;
                             currentCol = j - 1 ;

                            while(currentRow < 8 && currentCol >= 0)
                            {
                                
                                // Empty Space ;
                                if(board[currentRow][currentCol] == ' ')
                                {

                                    // Temporary Move 

                                    board[i][j] = ' ' ;
                                    board[currentRow][currentCol] = queen ;

                                    if(!isKinginCheck(whiteTurn))
                                    {
                                        return true ;
                                    }

                                    // Undo 
                                    board[i][j] = queen ;
                                    board[currentRow][currentCol] = ' ' ;
                                }

                                else
                                {

                                    // White Turn and Black Piece in Between : 
                                    
                                    if ((whiteTurn && board[currentRow][currentCol] >= 'a' &&
                                    board[currentRow][currentCol] <= 'z') ||
                                    (!whiteTurn && board[currentRow][currentCol] >= 'A' &&
                                    board[currentRow][currentCol] <= 'Z'))
                                    {

                                        char capturedPiece = board[currentRow][currentCol] ;

                                        // Temporary Move ;

                                        board[currentRow][currentCol] = queen ;
                                        board[i][j] = ' ' ;

                                        if(!isKinginCheck(whiteTurn))
                                        {
                                            return true ;
                                        }

                                        // Undo 

                                        board[currentRow][currentCol] = capturedPiece ;
                                        board[i][j] = queen ;
                                        
                                    }

                                    // If any other move then break the loop 
                                    break ;
                                }

                                currentCol -- ;
                                currentRow ++ ;
                            }
                    }
                }


                }
            }
        }

        return false ;
    }


    bool Board :: canPawnSaveKing(bool whiteTurn)
{
    char pawn;

    if(whiteTurn)
    {
        pawn = 'P';
    }
    else
    {
        pawn = 'p';
    }

    for(int i = 0; i < 8; i++)
    {
        for(int j = 0; j < 8; j++)
        {
            if(board[i][j] == pawn)
            {
                // =========================================
                // WHITE PAWN
                // =========================================

                if(whiteTurn)
                {
                    // One Square Forward

                    if(i - 1 >= 0 && board[i-1][j] == ' ')
                    {
                        // Temporary Move
                        board[i][j] = ' ';
                        board[i-1][j] = pawn;

                        if(!isKinginCheck(whiteTurn))
                        {
                            return true;
                        }

                        // Undo
                        board[i][j] = pawn;
                        board[i-1][j] = ' ';
                    }


                    // Two Square Forward
                    // Only from starting position

                    if(i == 6)
                    {
                        if(board[i-1][j] == ' ' &&
                           board[i-2][j] == ' ')
                        {
                            // Temporary Move
                            board[i][j] = ' ';
                            board[i-2][j] = pawn;

                            if(!isKinginCheck(whiteTurn))
                            {
                                return true;
                            }

                            // Undo
                            board[i][j] = pawn;
                            board[i-2][j] = ' ';
                        }
                    }


                    // Diagonal Left Capture

                    if(i - 1 >= 0 && j - 1 >= 0)
                    {
                        if(board[i-1][j-1] >= 'a' &&
                           board[i-1][j-1] <= 'z')
                        {
                            char capturedPiece = board[i-1][j-1];

                            // Temporary Move
                            board[i][j] = ' ';
                            board[i-1][j-1] = pawn;

                            if(!isKinginCheck(whiteTurn))
                            {
                                return true;
                            }

                            // Undo
                            board[i][j] = pawn;
                            board[i-1][j-1] = capturedPiece;
                        }
                    }


                    // Diagonal Right Capture

                    if(i - 1 >= 0 && j + 1 < 8)
                    {
                        if(board[i-1][j+1] >= 'a' &&
                           board[i-1][j+1] <= 'z')
                        {
                            char capturedPiece = board[i-1][j+1];

                            // Temporary Move
                            board[i][j] = ' ';
                            board[i-1][j+1] = pawn;

                            if(!isKinginCheck(whiteTurn))
                            {
                                return true;
                            }

                            // Undo
                            board[i][j] = pawn;
                            board[i-1][j+1] = capturedPiece;
                        }
                    }
                }


                // =========================================
                // BLACK PAWN
                // =========================================

                else
                {
                    // One Square Forward

                    if(i + 1 < 8 && board[i+1][j] == ' ')
                    {
                        // Temporary Move
                        board[i][j] = ' ';
                        board[i+1][j] = pawn;

                        if(!isKinginCheck(whiteTurn))
                        {
                            return true;
                        }

                        // Undo
                        board[i][j] = pawn;
                        board[i+1][j] = ' ';
                    }


                    // Two Square Forward
                    // Only from starting position

                    if(i == 1)
                    {
                        if(board[i+1][j] == ' ' &&
                           board[i+2][j] == ' ')
                        {
                            // Temporary Move
                            board[i][j] = ' ';
                            board[i+2][j] = pawn;

                            if(!isKinginCheck(whiteTurn))
                            {
                                return true;
                            }

                            // Undo
                            board[i][j] = pawn;
                            board[i+2][j] = ' ';
                        }
                    }


                    // Diagonal Left Capture

                    if(i + 1 < 8 && j - 1 >= 0)
                    {
                        if(board[i+1][j-1] >= 'A' &&
                           board[i+1][j-1] <= 'Z')
                        {
                            char capturedPiece = board[i+1][j-1];

                            // Temporary Move
                            board[i][j] = ' ';
                            board[i+1][j-1] = pawn;

                            if(!isKinginCheck(whiteTurn))
                            {
                                return true;
                            }

                            // Undo
                            board[i][j] = pawn;
                            board[i+1][j-1] = capturedPiece;
                        }
                    }


                    // Diagonal Right Capture

                    if(i + 1 < 8 && j + 1 < 8)
                    {
                        if(board[i+1][j+1] >= 'A' &&
                           board[i+1][j+1] <= 'Z')
                        {
                            char capturedPiece = board[i+1][j+1];

                            // Temporary Move
                            board[i][j] = ' ';
                            board[i+1][j+1] = pawn;

                            if(!isKinginCheck(whiteTurn))
                            {
                                return true;
                            }

                            // Undo
                            board[i][j] = pawn;
                            board[i+1][j+1] = capturedPiece;
                        }
                    }
                }
            }
        }
    }

    return false;
}


bool Board::canSaveKing(bool whiteTurn)
{
    if(canKingEscape(whiteTurn))
        return true;

    if(canKnightSaveKing(whiteTurn))
        return true;

    if(canBishopSaveKing(whiteTurn))
        return true;

    if(canRookSaveKing(whiteTurn))
        return true;

    if(canQueenSaveKing(whiteTurn))
        return true;

    if(canPawnSaveKing(whiteTurn))
        return true;

    return false;
}


bool Board::isCheckmate(bool whiteTurn)
{
    if(!isKinginCheck(whiteTurn))
    {
        return false;
    }

    if(canSaveKing(whiteTurn))
    {
        return false;
    }

    return true;
}


bool Board :: hasLegalMoves(bool whiteTurn)
{
    for(int i = 0 ; i < 8 ; i ++)
    {
        for(int j = 0 ; j < 8 ; j ++)
        {
            char piece = board[i][j] ;

            // Empty Square
            if(piece == ' ')
            {
                continue ;
            }

            // White Piece
            if(whiteTurn){

                if(piece < 'A' || piece > 'Z')
                    continue;

            }

            // Black Piece
            else{

                if(piece < 'a' || piece > 'z')
                    continue;

            }

            // Consider all possible moves for this piece
            for(int newRow = 0 ; newRow < 8 ; newRow ++)
            {
                for(int newCol = 0 ; newCol < 8 ; newCol ++)
                {
                    char destination = board[newRow][newCol];

                    // Don't capture own piece
                    if(whiteTurn && destination >= 'A' && destination <= 'Z')
                        continue;

                    if(!whiteTurn && destination >= 'a' && destination <= 'z')
                        continue;

                    // Convert board position to chess notation
                    string from;
                    string to;

                    from += ('a' + j);
                    from += ('8' - i);

                    to += ('a' + newCol);
                    to += ('8' - newRow);
                    
                    Move move(from, to);

                    // Check Validity of Move
                    if(!isValid(move))
                    {
                        continue ;
                    }

                    // Temporary Move

                    char capturedPiece = board[newRow][newCol];
                    board[newRow][newCol] = piece;  
                    
                    board[i][j] = ' ';

                     // Is king safe after the move?
                    bool illegal = isKinginCheck(whiteTurn);

                    // Undo the move
                    board[i][j] = piece;
                    board[newRow][newCol] = capturedPiece;

                    if(!illegal)
                        return true;

                }
            }
        }
    }

    return false ;
}

bool Board::isStalemate(bool whiteTurn)
{
    if(isKinginCheck(whiteTurn))
        return false;

    if(hasLegalMoves(whiteTurn))
        return false;

    return true;
}


bool Board :: isValidCastling(Move move , bool whiteTurn)
{
    int startRow = move.getStartRow();
    int endRow = move.getEndRow();
    int startCol = move.getStartCol();
    int endCol = move.getEndCol();


    // =========================
    // KING SIDE CASTLING
    // =========================

    if(whiteTurn)
    {
        // White King Side Castling
        if(startRow == 7 && startCol == 4 &&
           endRow == 7 && endCol == 6)
        {
            if(whiteKingMoved || whiteKingsideRookMoved)
            {
                return false;
            }

            if(board[7][7] != 'R')
            {
                return false;
            }

            if(board[7][5] != ' ' || board[7][6] != ' ')
            {
                return false;
            }

            if(isKinginCheck(whiteTurn))
            {
                return false;
            }

            // Temporary Move King to f1
            board[7][4] = ' ';
            board[7][5] = 'K';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[7][5] = ' ';
                board[7][4] = 'K';
                return false;
            }

            // Temporary Move King to g1
            board[7][5] = ' ';
            board[7][6] = 'K';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[7][6] = ' ';
                board[7][4] = 'K';
                return false;
            }

            // Restore original position
            board[7][6] = ' ';
            board[7][4] = 'K';

            return true;
        }
    }
    else
    {
        // Black King Side Castling
        if(startRow == 0 && startCol == 4 &&
           endRow == 0 && endCol == 6)
        {
            if(blackKingMoved || blackKingsideRookMoved)
            {
                return false;
            }

            if(board[0][7] != 'r')
            {
                return false;
            }

            if(board[0][5] != ' ' || board[0][6] != ' ')
            {
                return false;
            }

            if(isKinginCheck(whiteTurn))
            {
                return false;
            }

            // Temporary Move King to f8
            board[0][4] = ' ';
            board[0][5] = 'k';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[0][5] = ' ';
                board[0][4] = 'k';
                return false;
            }

            // Temporary Move King to g8
            board[0][5] = ' ';
            board[0][6] = 'k';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[0][6] = ' ';
                board[0][4] = 'k';
                return false;
            }

            // Restore original position
            board[0][6] = ' ';
            board[0][4] = 'k';

            return true;
        }
    }


    // =========================
    // QUEEN SIDE CASTLING
    // =========================

    if(whiteTurn)
    {
        // White Queen Side Castling
        if(startRow == 7 && startCol == 4 &&
           endRow == 7 && endCol == 2)
        {
            if(whiteKingMoved || whiteQueensideRookMoved)
            {
                return false;
            }

            if(board[7][0] != 'R')
            {
                return false;
            }

            if(board[7][3] != ' ' ||
               board[7][2] != ' ' ||
               board[7][1] != ' ')
            {
                return false;
            }

            if(isKinginCheck(whiteTurn))
            {
                return false;
            }

            // Temporary Move King to d1
            board[7][4] = ' ';
            board[7][3] = 'K';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[7][3] = ' ';
                board[7][4] = 'K';
                return false;
            }

            // Temporary Move King to c1
            board[7][3] = ' ';
            board[7][2] = 'K';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[7][2] = ' ';
                board[7][4] = 'K';
                return false;
            }

            // Restore original position
            board[7][2] = ' ';
            board[7][4] = 'K';

            return true;
        }
    }
    else
    {
        // Black Queen Side Castling
        if(startRow == 0 && startCol == 4 &&
           endRow == 0 && endCol == 2)
        {
            if(blackKingMoved || blackQueensideRookMoved)
            {
                return false;
            }

            if(board[0][0] != 'r')
            {
                return false;
            }

            if(board[0][3] != ' ' ||
               board[0][2] != ' ' ||
               board[0][1] != ' ')
            {
                return false;
            }

            if(isKinginCheck(whiteTurn))
            {
                return false;
            }

            // Temporary Move King to d8
            board[0][4] = ' ';
            board[0][3] = 'k';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[0][3] = ' ';
                board[0][4] = 'k';
                return false;
            }

            // Temporary Move King to c8
            board[0][3] = ' ';
            board[0][2] = 'k';

            if(isKinginCheck(whiteTurn))
            {
                // Undo Move
                board[0][2] = ' ';
                board[0][4] = 'k';
                return false;
            }

            // Restore original position
            board[0][2] = ' ';
            board[0][4] = 'k';

            return true;
        }
    }

    return false;
}


void Board :: promotePawn(int row , int col)
{

    char piece ;

    cout<<"Promote Pawn to Piece : " ;
    cin>> piece ;

    // White :

    if(piece == 'Q' || piece == 'R' || piece == 'B' || piece == 'N')
    {
        board[row][col] = piece ;
    }

    // Black :

    else if( piece == 'q' || piece == 'r' || piece == 'b' || piece == 'n')
    {
        board[row][col] = piece ;
    }

    else
    {
        cout << "Invalid choice! Promoting to Queen." << endl;

        if(board[row][col] == 'P')
        {
            board[row][col] = 'Q';
        }
        else
        {
            board[row][col] = 'q';
        }

    }

}