#include "Rook.h"

bool Rook::isValidRookMove(Move move, char board[8][8]) {
    
    int startRow = move.getStartRow() ;
        int startCol = move.getStartCol() ;
        int endRow = move.getEndRow() ;
        int endCol = move.getEndCol() ;

        char startPiece = board[startRow][startCol] ;
        char endPiece = board[endRow][endCol] ;

        int rowstep = 0 ;
        int colstep = 0 ;
        
        // White Piece :


        if(startPiece == 'R')
        {
            if(startRow - endRow == 0 && 
            ((endPiece == '.') || 
            (endPiece >= 'a' && endPiece <= 'z')))
            {

                if(endCol > startCol)
                {
                    colstep = 1 ;
                }

                else
                {
                    colstep = -1 ;
                }


                int movecol = startCol + colstep ;
                while(movecol != endCol)
                {
                    if(board[startRow][movecol] == '.')
                    {
                        movecol = movecol + colstep ;
                    }
                    
                    else
                    {
                        return false ;
                    }
                }
                return true ;
            }

            else if(startCol - endCol == 0 && 
                ((endPiece == '.') ||
                 (endPiece >= 'a' && endPiece <= 'z')))
            {   

                if(endRow > startRow)
                {
                    rowstep = 1 ;
                }

                else
                {
                    rowstep = -1 ;
                }


                int moverow = startRow + rowstep ;
                while(moverow != endRow )
                {
                    if(board[moverow][startCol] == '.')
                    {
                        moverow = moverow + rowstep ;
                    }

                    else
                    {
                        return false ;
                    }
                }
                return true ;
            }

            return false ;
        }


        // Black Piece :

        if(startPiece == 'r')
        {
            if(startRow - endRow == 0 && 
            ((endPiece == '.') || 
            (endPiece >= 'A' && endPiece <= 'Z')))
            {   

                if(endCol > startCol)
                {
                    colstep = 1 ;
                }

                else
                {
                    colstep = -1 ;
                }
                
                int movecol = startCol + colstep ;
                while(movecol != endCol)
                {
                    if(board[startRow][movecol] == '.')
                    {
                        movecol = movecol + colstep ;
                    }
                    
                    else
                    {
                        return false ;
                    }
                }
                return true ;
            }

            else if(startCol - endCol == 0 && 
                ((endPiece == '.') ||
                 (endPiece >= 'A' && endPiece <= 'Z')))
            {   
                
                if(endRow > startRow)
                {
                    rowstep = 1 ;
                }

                else
                {
                    rowstep = -1 ;
                }

                int moverow = startRow + rowstep ;
                while(moverow != endRow )
                {
                    if(board[moverow][startCol] == '.')
                    {
                        moverow = moverow + rowstep ;
                    }

                    else
                    {
                        return false ;
                    }
                }
                return true ;
            }

            return false ;
        }
        
}