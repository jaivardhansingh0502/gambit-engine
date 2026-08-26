#include "Board.h"
#include <iostream>
#include <cstdlib>
#include <string>
#include <windows.h>


using namespace std;

const string RESET = "\033[0m";
const string LIGHT = "\033[48;5;255m";
const string DARK  = "\033[48;5;22m";

string Board::getPieceSymbol(char piece)
{
    switch(piece)
    {
        case 'K': return "♔";
        case 'Q': return "♕";
        case 'R': return "♖";
        case 'B': return "♗";
        case 'N': return "♘";
        case 'P': return "♙";

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
                board[i][j] = '.';
        }
    }

    whiteTurn = true ;
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
    for(int i = 0; i < 8; i++)
    {
        cout << 8 - i << " ";

        for(int j = 0; j < 8; j++)
        {
            if((i + j) % 2 == 0)
            {
                cout << LIGHT ;
            }
            else
            {
                cout << DARK ;
            }

            cout << " " << getPieceSymbol(board[i][j]) << " ";
            cout << RESET ;
        }

        cout << endl;
    }

    cout << "    a  b  c  d  e  f  g  h" << endl;
}

void Board :: makeMove(Move move)
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();

    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    board[endRow][endCol] = board[startRow][startCol];

    board[startRow][startCol] = '.';

    whiteTurn = !whiteTurn ;
}


bool Board :: isValid(Move move)
{
    int startRow = move.getStartRow();
    int startCol = move.getStartCol();

    int endRow = move.getEndRow();
    int endCol = move.getEndCol();

    // Starting square empty
    if(board[startRow][startCol] == '.')
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
    if(endPiece != '.')
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

    }