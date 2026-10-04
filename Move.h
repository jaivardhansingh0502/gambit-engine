#ifndef MOVE_H
#define MOVE_H

#include <string>

using namespace std;

class Move {
private:
    int startRow;
    int startCol;
    int endRow;
    int endCol;

    char promotionPiece ;

public:
    Move(int sR, int sC, int eR, int eC, char promotion = ' ');
    Move(string from, string to);

    int getStartRow();
    int getStartCol();
    int getEndRow();
    int getEndCol();

    char getPromotionPiece();

    string getChessNotation();
};

#endif