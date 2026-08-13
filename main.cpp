#include<iostream>
#include <cstdlib>
using namespace std ;

    class Move {
        private :

        int startRow ;
        int startCol ;
        int endRow ;
        int endCol ;

        public :
        Move(int sR , int sC , int eR , int eC){
            
            startRow = sR ;
            startCol = sC ;
            endRow = eR ;
            endCol = eC ;
        }

        Move(string from, string to) {
            startRow = '8' - from[1] ;
            startCol = from[0] - 'a' ;
            endRow = '8' - to[1] ;
            endCol = to[0] - 'a' ;
        }


        int getStartRow() { 
            return startRow;
         }


        int getStartCol() { 
            return startCol;
         }


        int getEndRow(){
            return endRow ;
        }
        

        int getEndCol(){
            return endCol ;
        }

        
    };

    class Board {
        private :
        char board[8][8] ;

        public:


            void initializeBoard() ;
            void displayBoard() ;
            void takeinput() ;
            void makeMove(Move move) ;
            bool isValid(Move move) ;
            bool isValidPawnMove(Move move) ;
            bool isValidKnightMove(Move move) ;
            bool isValidBishopMove(Move move) ;
            bool isValidRookMove(Move move) ;
            bool isValidQueenMove(Move move) ;



    } ;

    void Board :: initializeBoard()
    {

        char whitepieces[8] = {'R' , 'N', 'B' , 'Q', 'K','B','N','R'} ;
        char blackpieces[8] = {'r','n','b','q','k','b','n','r'} ;
        for(int i = 0 ;i<8;i++){
            for(int j = 0 ;j<8;j++){
                if(i == 0) board[i][j] = blackpieces[j] ;
                else if(i == 7) board[i][j] = whitepieces[j] ;
                else if(i == 6) board[i][j] = 'P' ;
                else if(i == 1) board[i][j] = 'p' ;
                else board[i][j] = '.' ;
            }
        }
        
    }



    void Board :: takeinput(){
        string from ;
        string to ;
        cout<<endl ;
        cout<<"Enter the move in the format 'e2 e4' : "<<endl ;
        cout<< "Enter start position: " ;
        cin>> from ;
        cout<< "Enter end position: " ;
        cin>> to ;

        Move move(from, to) ;
        
        
            // cout << "Start Row: " << move.getStartRow() << endl;
            // cout << "Start Col: " << move.getStartCol() << endl;
            // cout << "End Row: " << move.getEndRow() << endl;
            // cout << "End Col: " << move.getEndCol() << endl;
        
        
        if(isValid(move))
        makeMove(move) ;

        else 
        {
        cout<<"Invalid move!" << endl;
        }
        
    }


    void Board :: displayBoard(){
        for(int i = 0 ;i<8;i++){
            cout << 8 - i << " ";
            for(int j = 0 ;j<8;j++){
                cout<<board[i][j]<<' ';
            }
            cout<<endl ;
        }
        cout << "  a b c d e f g h";
    }

    void Board :: makeMove(Move move) {

        int startRow = move.getStartRow();
        int startCol = move.getStartCol();
        int endRow = move.getEndRow();
        int endCol = move.getEndCol();

        // Move the piece from the start position to the end position
        board[endRow][endCol] = board[startRow][startCol];
        // Clear the start position
        board[startRow][startCol] = '.';

    }


    bool Board :: isValid(Move move){

        int startRow = move.getStartRow() ;
        int startCol = move.getStartCol() ;
        int endRow = move.getEndRow() ;
        int endCol = move.getEndCol() ;
        
        if(board[startRow][startCol] == '.')
        {
            return false ;
        }
        
        char startPiece = board[startRow][startCol] ;
        char endPiece = board[endRow][endCol] ;


        if(board[endRow][endCol] != '.')
        {
            
           if(startPiece>='a' && startPiece<='z' && endPiece>='a' && endPiece<='z')
           {
            return false ;
           }

           if(startPiece>='A' && startPiece<='Z' && endPiece>='A' && endPiece<='Z')
           {
            return false ;
           }

        }


        if(startPiece == 'P' || startPiece == 'p')
        {
        return isValidPawnMove(move);
        }


        if(startPiece == 'N' || startPiece == 'n')
        {
            return isValidKnightMove(move) ;
        }


        if(startPiece == 'B' || startPiece == 'b')
        {
            return isValidBishopMove(move) ;
        }


        if(startPiece == 'R' || startPiece == 'r')
        {
            return isValidRookMove(move) ;
        }

        return true ;
    }

    bool Board :: isValidPawnMove(Move move)
    {
        int startRow = move.getStartRow() ;
        int startCol = move.getStartCol() ;
        int endRow = move.getEndRow() ;
        int endCol = move.getEndCol() ;

        char startPiece = board[startRow][startCol] ;
        char endPiece = board[endRow][endCol] ;

        
            // White pawn
            if(startPiece == 'P')
            {
                // One square forward
                if(startRow - endRow == 1 && startCol == endCol && endPiece == '.')
                {
                    return true;
                }

                // Two squares forward from starting position
                if(startRow == 6 && startRow - endRow == 2 && startCol == endCol && endPiece=='.' && board[endRow-1][endCol] == '.')
                {
                    return true;
                }

                // Capture the black piece :
                if(startRow - endRow == 1 && abs(startCol-endCol) == 1 && endPiece >='a' && endPiece <= 'z')
                {
                    return true ;
                }

            }

            // Black pawn
            if(startPiece == 'p')
            {
                // One square forward
                if(endRow - startRow == 1 && startCol == endCol && endPiece == '.')
                {
                    return true;
                }

                // Two squares forward from starting position
                if(startRow == 1 && endRow - startRow == 2 && startCol == endCol && endPiece=='.' && board[endRow-1][endCol] == '.')
                {
                    return true;
                }


                // Capture the white piece :
                if(endRow - startRow == 1 && abs(startCol-endCol) == 1 && endPiece >='A' && endPiece <= 'Z')
                {
                    return true ;
                }
            }

        return false ;

    }



    bool Board :: isValidKnightMove(Move move)
    {

        int startRow = move.getStartRow() ;
        int startCol = move.getStartCol() ;
        int endRow = move.getEndRow() ;
        int endCol = move.getEndCol() ;

        char startPiece = board[startRow][startCol] ;
        char endPiece = board[endRow][endCol] ;

        // White Move :
        if(startPiece == 'N')
        {
            if(((abs(startRow - endRow) == 1 && abs(startCol - endCol) == 2) || 
            (abs(startRow - endRow) == 2 && abs(startCol - endCol) == 1)) && 
            (endPiece == '.' || (endPiece >= 'a' && endPiece <= 'z')))
            {
                return true ;
            }

        }

        if(startPiece == 'n')
        {
            if(((abs(startRow - endRow) == 1 && abs(startCol - endCol) == 2) || 
            (abs(startRow - endRow) == 2 && abs(startCol - endCol) == 1)) && 
            (endPiece == '.' || (endPiece >= 'A' && endPiece <= 'Z')))
            {
                return true ;
            }

        }

        return false ;

    }

    
    bool Board :: isValidBishopMove(Move move)
    {

        int startRow = move.getStartRow() ;
        int startCol = move.getStartCol() ;
        int endRow = move.getEndRow() ;
        int endCol = move.getEndCol() ;

        char startPiece = board[startRow][startCol] ;
        char endPiece = board[endRow][endCol] ;

        int rowStep = 0 ;
        int colStep = 0 ;

        // White Piece :

        if(startPiece == 'B')
        {
            if((abs(startRow - endRow) == abs(startCol - endCol)) &&
             (endPiece == '.' || (endPiece >='a' && endPiece <= 'z')))
            {   

    
                if(endRow > startRow)
                {
                    rowStep = 1 ;
                }

                else
                {
                    rowStep = -1 ;
                }

                if(endCol > startCol)
                {
                    colStep = 1 ;
                }

                else
                {
                    colStep = -1 ;
                }
                
                int moverow = startRow + rowStep;
                int movecol = startCol + colStep;

                while(moverow != endRow && movecol != endCol)
                {
                    if(board[moverow][movecol] == '.')
                    {
                        moverow = moverow + rowStep ;
                        movecol = movecol + colStep ;
                    }

                    else
                    {
                        if(board[moverow][movecol] != '.')
                        {
                            return false ;
                        }
                    }
                }

                return true ;
            
            }

            return false ;
        }

        // Black Piece :

        if(startPiece == 'b')
        {
            if((abs(startRow - endRow) == abs(startCol - endCol)) &&
             (endPiece == '.' || (endPiece >='A' && endPiece <= 'Z')))
            {   

    
                if(endRow > startRow)
                {
                    rowStep = 1 ;
                }

                else
                {
                    rowStep = -1 ;
                }

                if(endCol > startCol)
                {
                    colStep = 1 ;
                }

                else
                {
                    colStep = -1 ;
                }
                
                int moverow = startRow + rowStep;
                int movecol = startCol + colStep;

                while(moverow != endRow && movecol != endCol)
                {
                    if(board[moverow][movecol] == '.')
                    {
                        moverow = moverow + rowStep ;
                        movecol = movecol + colStep ;
                    }

                    else
                    {
                        if(board[moverow][movecol] != '.')
                        {
                            return false ;
                        }
                    }
                }

                return true ;
            
            }

            return false ;
        }

        return false ;
    }


    bool Board :: isValidRookMove(Move move)
    {

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


    bool Board :: isValidQueenMove(Move move)
    {
        
    }


int main(){

    cout<<"Welcome to the Gambit Engine!"<<endl ;

    Board chessboard;
    chessboard.initializeBoard() ;
    chessboard.displayBoard() ;
    

    while(true){
        chessboard.takeinput() ;
        chessboard.displayBoard() ;
    }
    
}