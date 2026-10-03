#include "Evaluation.h"

int Evaluation ::evaluateBoard(char board[8][8])
{

    int score = 0 ; 

    for(int i = 0 ; i < 8 ; i ++)
    {
        for(int j = 0 ; j < 8 ; j ++)
        {

            switch(board[i][j])
            {

                case 'P' :  
                    score = score + 1 ;
                    break ;


                case 'N'  :
                    score = score + 3 ;
                    break ;


                case 'B'  :
                    score = score + 3 ;
                    break ;
                

                case 'R'  :
                    score = score + 5 ;
                    break ;

                
                case 'Q'  :
                    score = score + 9 ;
                    break ;


                case 'p' :  
                    score = score - 1 ;
                    break ;


                case 'n'  :
                    score = score - 3 ;
                    break ;


                case 'b'  :
                    score = score - 3 ;
                    break ;
                

                case 'r'  :
                    score = score - 5 ;
                    break ;

                
                case 'q'  :
                    score = score - 9 ;
                    break ;
            }   
        }
    }

    return score ;
}