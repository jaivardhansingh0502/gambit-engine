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

public:
    Move(int sR, int sC, int eR, int eC);
    Move(string from, string to);

    int getStartRow();
    int getStartCol();
    int getEndRow();
    int getEndCol();
};

#endif