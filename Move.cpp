#include "Move.h"

Move::Move(int sR, int sC, int eR, int eC) {
    startRow = sR;
    startCol = sC;
    endRow = eR;
    endCol = eC;
}

Move::Move(string from, string to) {
    startRow = '8' - from[1];
    startCol = from[0] - 'a';
    endRow = '8' - to[1];
    endCol = to[0] - 'a';
}

int Move::getStartRow() {
    return startRow;
}

int Move::getStartCol() {
    return startCol;
}

int Move::getEndRow() {
    return endRow;
}

int Move::getEndCol() {
    return endCol;
}