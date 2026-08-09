#include<iostream>
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
        cout<<"Invalid move! No piece at starting position." << endl;
        
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

        return true ;
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