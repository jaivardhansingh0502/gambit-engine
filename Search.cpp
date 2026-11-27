#include "Search.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <random>
#include <unordered_map>
#include <vector>

using namespace std;

namespace
{
const int INF_SCORE = 10000000;
const int MATE_SCORE = 100000;
const int MATE_BOUND = 90000;
const int TT_SIZE = 1 << 16; // 65536 entries
const int MAX_PLY = 64;

enum TTFlag : uint8_t
{
    TT_EMPTY = 0,
    TT_EXACT = 1,
    TT_LOWER = 2,
    TT_UPPER = 3
};

struct TTEntry
{
    uint64_t key = 0;
    int depth = -1;
    int score = 0;
    TTFlag flag = TT_EMPTY;
    char bestMove[6] = {0};
};

// ---------------- PIECE-SQUARE TABLES (TAPERED MG / EG) ----------------

const int PAWN_MG_PST[8][8] = {
    { 0,   0,   0,   0,   0,   0,   0,   0},
    {35,  45,  45,  50,  50,  45,  45,  35},
    {10,  10,  20,  32,  32,  20,  10,  10},
    { 5,   5,  12,  26,  26,  12,   5,   5},
    { 0,   0,   4,  24,  24,   4,   0,   0},
    { 6,  -4, -10,   2,   2, -10,  -4,   6},
    { 6,  12,  12, -22, -22,  12,  12,   6},
    { 0,   0,   0,   0,   0,   0,   0,   0}
};

const int PAWN_EG_PST[8][8] = {
    { 0,   0,   0,   0,   0,   0,   0,   0},
    {75,  75,  75,  80,  80,  75,  75,  75},
    {45,  45,  45,  45,  45,  45,  45,  45},
    {25,  25,  25,  25,  25,  25,  25,  25},
    {10,  10,  10,  12,  12,  10,  10,  10},
    { 0,   0,   0,   0,   0,   0,   0,   0},
    {-5,  -5,  -5,  -5,  -5,  -5,  -5,  -5},
    { 0,   0,   0,   0,   0,   0,   0,   0}
};

const int KNIGHT_PST[8][8] = {
    {-50,-40,-30,-30,-30,-30,-40,-50},
    {-40,-20,  0,  0,  0,  0,-20,-40},
    {-30,  0, 12, 16, 16, 12,  0,-30},
    {-30,  5, 16, 22, 22, 16,  5,-30},
    {-30,  0, 16, 22, 22, 16,  0,-30},
    {-30,  6, 12, 16, 16, 12,  6,-30},
    {-40,-20,  0,  5,  5,  0,-20,-40},
    {-50,-40,-30,-30,-30,-30,-40,-50}
};

const int BISHOP_PST[8][8] = {
    {-20,-10,-10,-10,-10,-10,-10,-20},
    {-10,  0,  0,  0,  0,  0,  0,-10},
    {-10,  0,  6, 12, 12,  6,  0,-10},
    {-10,  6,  6, 12, 12,  6,  6,-10},
    {-10,  0, 12, 12, 12, 12,  0,-10},
    {-10, 10, 10, 10, 10, 10, 10,-10},
    {-10,  6,  0,  0,  0,  0,  6,-10},
    {-20,-10,-10,-10,-10,-10,-10,-20}
};

const int ROOK_PST[8][8] = {
    { 0,  0,  0,  0,  0,  0,  0,  0},
    { 8, 14, 14, 14, 14, 14, 14,  8},
    {-5,  0,  0,  0,  0,  0,  0, -5},
    {-5,  0,  0,  0,  0,  0,  0, -5},
    {-5,  0,  0,  0,  0,  0,  0, -5},
    {-5,  0,  0,  0,  0,  0,  0, -5},
    {-5,  0,  0,  0,  0,  0,  0, -5},
    { 0,  0,  2,  6,  6,  2,  0,  0}
};

const int QUEEN_PST[8][8] = {
    {-20,-10,-10, -5, -5,-10,-10,-20},
    {-10,  0,  0,  0,  0,  0,  0,-10},
    {-10,  0,  5,  5,  5,  5,  0,-10},
    { -5,  0,  5,  6,  6,  5,  0, -5},
    {  0,  0,  5,  6,  6,  5,  0, -5},
    {-10,  5,  5,  5,  5,  5,  0,-10},
    {-10,  0,  5,  0,  0,  0,  0,-10},
    {-20,-10,-10, -5, -5,-10,-10,-20}
};

const int KING_MID_PST[8][8] = {
    {-30,-40,-40,-50,-50,-40,-40,-30},
    {-30,-40,-40,-50,-50,-40,-40,-30},
    {-30,-40,-40,-50,-50,-40,-40,-30},
    {-30,-40,-40,-50,-50,-40,-40,-30},
    {-20,-30,-30,-40,-40,-30,-30,-20},
    {-10,-20,-20,-20,-20,-20,-20,-10},
    { 20, 20,  0,  0,  0,  0, 20, 20},
    { 20, 32, 12,  0,  0, 12, 32, 20}
};

const int KING_END_PST[8][8] = {
    {-50,-40,-30,-20,-20,-30,-40,-50},
    {-30,-20,-10,  0,  0,-10,-20,-30},
    {-30,-10, 20, 32, 32, 20,-10,-30},
    {-30,-10, 32, 44, 44, 32,-10,-30},
    {-30,-10, 32, 44, 44, 32,-10,-30},
    {-30,-10, 20, 32, 32, 20,-10,-30},
    {-30,-30,  0,  0,  0,  0,-30,-30},
    {-50,-30,-30,-30,-30,-30,-30,-50}
};

const int PASSED_PAWN_MG[8] = {0, 75, 50, 32, 18, 10, 5, 0};
const int PASSED_PAWN_EG[8] = {0, 150, 110, 75, 45, 25, 14, 0};

int pieceValueCp(char piece)
{
    switch(tolower(static_cast<unsigned char>(piece)))
    {
        case 'p': return 100;
        case 'n': return 320;
        case 'b': return 330;
        case 'r': return 500;
        case 'q': return 900;
        case 'k': return 20000;
        default: return 0;
    }
}

int piecePhaseWeight(char piece)
{
    switch(tolower(static_cast<unsigned char>(piece)))
    {
        case 'n': return 1;
        case 'b': return 1;
        case 'r': return 2;
        case 'q': return 4;
        default: return 0;
    }
}

int pieceOrderingPst(char piece, int row, int col)
{
    int r = isupper(static_cast<unsigned char>(piece)) ? row : (7 - row);
    switch(tolower(static_cast<unsigned char>(piece)))
    {
        case 'p': return PAWN_MG_PST[r][col];
        case 'n': return KNIGHT_PST[r][col];
        case 'b': return BISHOP_PST[r][col];
        case 'r': return ROOK_PST[r][col];
        case 'q': return QUEEN_PST[r][col];
        default: return 0;
    }
}

bool hasNonPawnMaterial(Board& chessboard, bool whiteTurn)
{
    char (*b)[8] = chessboard.getBoard();
    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            char p = b[r][c];
            if(p == ' ') continue;
            bool isWhite = isupper(static_cast<unsigned char>(p)) != 0;
            if(isWhite != whiteTurn) continue;
            char lp = static_cast<char>(tolower(static_cast<unsigned char>(p)));
            if(lp == 'n' || lp == 'b' || lp == 'r' || lp == 'q')
            {
                return true;
            }
        }
    }
    return false;
}

// ---------------- BUILT-IN ECO OPENING BOOK ----------------

const unordered_map<string, vector<string>>& getOpeningBookMap()
{
    static const unordered_map<string, vector<string>> BOOK = []() {
        unordered_map<string, vector<string>> table;

        auto addLine = [&](const vector<string>& moves) {
            Board b;
            b.initializeBoard();
            for(const string& mv : moves)
            {
                if(mv.size() < 4) break;
                Move m(mv.substr(0, 2), mv.substr(2, 2));
                if(!b.isValid(m)) break;
                string key = b.getPositionKey();
                auto& bucket = table[key];
                if(find(bucket.begin(), bucket.end(), mv) == bucket.end())
                {
                    bucket.push_back(mv);
                }
                b.makeMove(m);
            }
        };

        // Open Games (Italian, Ruy Lopez, Scotch)
        addLine({"e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3", "g8f6", "d2d3"});
        addLine({"e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "d2d3", "f8c5"});
        addLine({"e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5", "e4d5"});
        addLine({"e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7"});
        addLine({"e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6", "e1g1", "f6e4"});
        addLine({"e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "f8c5"});

        // Sicilian Defense (Najdorf, Classical, Scheveningen, Rossolimo)
        addLine({"e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"});
        addLine({"e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "b8c6"});
        addLine({"e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3"});
        addLine({"e2e4", "c7c5", "g1f3", "b8c6", "f1b5", "g7g6", "e1g1"});
        addLine({"e2e4", "c7c5", "g1f3", "e7e6", "d2d4", "c5d4", "f3d4", "b8c6"});

        // French Defense (Classical, Tarrasch, Advance)
        addLine({"e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "g8f6", "c1g5", "f8e7"});
        addLine({"e2e4", "e7e6", "d2d4", "d7d5", "b1d2", "g8f6", "e4e5", "f6d7"});
        addLine({"e2e4", "e7e6", "d2d4", "d7d5", "e4e5", "c7c5", "c2c3", "b8c6"});

        // Caro-Kann Defense
        addLine({"e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "c8f5"});
        addLine({"e2e4", "c7c6", "d2d4", "d7d5", "e4e5", "c8f5", "g1f3", "e7e6"});

        // Queen's Gambit (QGD, Slav, QGA)
        addLine({"d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5", "f8e7", "e2e3"});
        addLine({"d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "d5c4"});
        addLine({"d2d4", "d7d5", "c2c4", "d5c4", "g1f3", "g8f6", "e2e3"});

        // Indian Defenses (Nimzo, QID, KID, Grunfeld)
        addLine({"d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "e2e3", "e8g8"});
        addLine({"d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "b7b6", "g2g3", "c8b7"});
        addLine({"d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6", "g1f3", "e8g8"});
        addLine({"d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5", "c4d5", "f6d5"});

        // English & Reti
        addLine({"c2c4", "e7e5", "b1c3", "g8f6", "g1f3", "b8c6"});
        addLine({"c2c4", "g8f6", "b1c3", "e7e6", "g1f3", "d7d5"});
        addLine({"g1f3", "d7d5", "c2c4", "e7e6", "d2d4", "g8f6"});
        addLine({"g1f3", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7"});

        return table;
    }();
    return BOOK;
}

string tryOpeningBookMove(Board& board, vector<Move>& legalMoves)
{
    const auto& book = getOpeningBookMap();
    auto it = book.find(board.getPositionKey());
    if(it == book.end() || it->second.empty())
    {
        return "";
    }

    vector<string> candidates;
    for(const string& bookMv : it->second)
    {
        for(auto& lm : legalMoves)
        {
            if(lm.getChessNotation() == bookMv)
            {
                candidates.push_back(bookMv);
                break;
            }
        }
    }
    if(candidates.empty()) return "";

    static mt19937_64 bookRng(
        static_cast<uint64_t>(chrono::steady_clock::now().time_since_epoch().count())
    );
    uniform_int_distribution<size_t> dist(0, candidates.size() - 1);
    return candidates[dist(bookRng)];
}

// ---------------- TAPERED & POSITIONAL EVALUATION ----------------

int evaluateCentipawns(Board& chessboard)
{
    char (*b)[8] = chessboard.getBoard();
    int mgScore = 0;
    int egScore = 0;
    int phase = 0;

    int wBishops = 0, bBishops = 0;
    int wkR = -1, wkC = -1, bkR = -1, bkC = -1;

    int wPawnCount[8] = {0};
    int bPawnCount[8] = {0};

    struct Sq { int r; int c; };
    Sq wKnights[10], bKnights[10], wRooks[10], bRooks[10], wPawns[8], bPawns[8];
    int wKnightN = 0, bKnightN = 0, wRookN = 0, bRookN = 0, wPawnN = 0, bPawnN = 0;

    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            char p = b[r][c];
            if(p == ' ') continue;

            if(p == 'K') { wkR = r; wkC = c; continue; }
            if(p == 'k') { bkR = r; bkC = c; continue; }

            phase += piecePhaseWeight(p);
            int val = pieceValueCp(p);
            bool isWhite = isupper(static_cast<unsigned char>(p)) != 0;
            char lp = static_cast<char>(tolower(static_cast<unsigned char>(p)));
            int relR = isWhite ? r : (7 - r);

            int mgPst = 0;
            int egPst = 0;
            switch(lp)
            {
                case 'p':
                    mgPst = PAWN_MG_PST[relR][c];
                    egPst = PAWN_EG_PST[relR][c];
                    if(isWhite)
                    {
                        wPawnCount[c]++;
                        if(wPawnN < 8) wPawns[wPawnN++] = {r, c};
                    }
                    else
                    {
                        bPawnCount[c]++;
                        if(bPawnN < 8) bPawns[bPawnN++] = {r, c};
                    }
                    break;
                case 'n':
                    mgPst = egPst = KNIGHT_PST[relR][c];
                    if(isWhite) { if(wKnightN < 10) wKnights[wKnightN++] = {r, c}; }
                    else { if(bKnightN < 10) bKnights[bKnightN++] = {r, c}; }
                    break;
                case 'b':
                    mgPst = egPst = BISHOP_PST[relR][c];
                    if(isWhite) wBishops++;
                    else bBishops++;
                    break;
                case 'r':
                    mgPst = egPst = ROOK_PST[relR][c];
                    if(isWhite) { if(wRookN < 10) wRooks[wRookN++] = {r, c}; }
                    else { if(bRookN < 10) bRooks[bRookN++] = {r, c}; }
                    break;
                case 'q':
                    mgPst = egPst = QUEEN_PST[relR][c];
                    break;
            }

            if(isWhite)
            {
                mgScore += val + mgPst;
                egScore += val + egPst;
            }
            else
            {
                mgScore -= (val + mgPst);
                egScore -= (val + egPst);
            }
        }
    }

    // Bishop pair
    if(wBishops >= 2) { mgScore += 32; egScore += 45; }
    if(bBishops >= 2) { mgScore -= 32; egScore -= 45; }

    // Doubled & isolated pawns
    for(int c = 0; c < 8; c++)
    {
        if(wPawnCount[c] > 1)
        {
            int pen = (wPawnCount[c] - 1) * 12;
            mgScore -= pen;
            egScore -= pen;
        }
        if(bPawnCount[c] > 1)
        {
            int pen = (bPawnCount[c] - 1) * 12;
            mgScore += pen;
            egScore += pen;
        }

        if(wPawnCount[c] > 0)
        {
            bool hasNeighbor = (c > 0 && wPawnCount[c - 1] > 0) || (c < 7 && wPawnCount[c + 1] > 0);
            if(!hasNeighbor) { mgScore -= 14; egScore -= 10; }
        }
        if(bPawnCount[c] > 0)
        {
            bool hasNeighbor = (c > 0 && bPawnCount[c - 1] > 0) || (c < 7 && bPawnCount[c + 1] > 0);
            if(!hasNeighbor) { mgScore += 14; egScore += 10; }
        }
    }

    // Passed pawns & protected pawn chains
    for(int i = 0; i < wPawnN; i++)
    {
        int r = wPawns[i].r, c = wPawns[i].c;
        bool passed = true;
        for(int rr = r - 1; rr >= 1 && passed; rr--)
        {
            for(int dc = -1; dc <= 1; dc++)
            {
                int nc = c + dc;
                if(nc >= 0 && nc < 8 && b[rr][nc] == 'p')
                {
                    passed = false;
                    break;
                }
            }
        }
        if(passed)
        {
            mgScore += PASSED_PAWN_MG[r];
            egScore += PASSED_PAWN_EG[r];
        }
        if(r < 7 && ((c > 0 && b[r + 1][c - 1] == 'P') || (c < 7 && b[r + 1][c + 1] == 'P')))
        {
            mgScore += 7;
            egScore += 8;
        }
    }

    for(int i = 0; i < bPawnN; i++)
    {
        int r = bPawns[i].r, c = bPawns[i].c;
        bool passed = true;
        for(int rr = r + 1; rr <= 6 && passed; rr++)
        {
            for(int dc = -1; dc <= 1; dc++)
            {
                int nc = c + dc;
                if(nc >= 0 && nc < 8 && b[rr][nc] == 'P')
                {
                    passed = false;
                    break;
                }
            }
        }
        if(passed)
        {
            mgScore -= PASSED_PAWN_MG[7 - r];
            egScore -= PASSED_PAWN_EG[7 - r];
        }
        if(r > 0 && ((c > 0 && b[r - 1][c - 1] == 'p') || (c < 7 && b[r - 1][c + 1] == 'p')))
        {
            mgScore -= 7;
            egScore -= 8;
        }
    }

    // Knight outposts (supported on rank 4-6 and not attackable by enemy pawn on adjacent files)
    for(int i = 0; i < wKnightN; i++)
    {
        int r = wKnights[i].r, c = wKnights[i].c;
        if(r >= 2 && r <= 4)
        {
            bool supported = (c > 0 && b[r + 1][c - 1] == 'P') || (c < 7 && b[r + 1][c + 1] == 'P');
            if(supported)
            {
                bool attackable = false;
                for(int rr = r - 1; rr >= 1 && !attackable; rr--)
                {
                    if((c > 0 && b[rr][c - 1] == 'p') || (c < 7 && b[rr][c + 1] == 'p'))
                        attackable = true;
                }
                if(!attackable) { mgScore += 18; egScore += 12; }
            }
        }
    }
    for(int i = 0; i < bKnightN; i++)
    {
        int r = bKnights[i].r, c = bKnights[i].c;
        if(r >= 3 && r <= 5)
        {
            bool supported = (c > 0 && b[r - 1][c - 1] == 'p') || (c < 7 && b[r - 1][c + 1] == 'p');
            if(supported)
            {
                bool attackable = false;
                for(int rr = r + 1; rr <= 6 && !attackable; rr++)
                {
                    if((c > 0 && b[rr][c - 1] == 'P') || (c < 7 && b[rr][c + 1] == 'P'))
                        attackable = true;
                }
                if(!attackable) { mgScore -= 18; egScore -= 12; }
            }
        }
    }

    // Rooks on open/semi-open files & 7th rank
    for(int i = 0; i < wRookN; i++)
    {
        int r = wRooks[i].r, c = wRooks[i].c;
        if(wPawnCount[c] == 0)
        {
            int bonus = (bPawnCount[c] == 0) ? 22 : 12;
            mgScore += bonus;
            egScore += bonus;
        }
        if(r == 1) { mgScore += 18; egScore += 24; }
    }
    for(int i = 0; i < bRookN; i++)
    {
        int r = bRooks[i].r, c = bRooks[i].c;
        if(bPawnCount[c] == 0)
        {
            int bonus = (wPawnCount[c] == 0) ? 22 : 12;
            mgScore -= bonus;
            egScore -= bonus;
        }
        if(r == 6) { mgScore -= 18; egScore -= 24; }
    }

    // King PST & middlegame pawn shield
    if(wkR >= 0)
    {
        mgScore += KING_MID_PST[wkR][wkC];
        egScore += KING_END_PST[wkR][wkC];
        if(wkR >= 6)
        {
            for(int dc = -1; dc <= 1; dc++)
            {
                int fc = wkC + dc;
                if(fc < 0 || fc >= 8) continue;
                if(b[wkR - 1][fc] == 'P') mgScore += 12;
                else if(wkR - 2 >= 0 && b[wkR - 2][fc] == 'P') mgScore += 6;
                else if(wPawnCount[fc] == 0) mgScore -= 14;
            }
        }
    }
    if(bkR >= 0)
    {
        mgScore -= KING_MID_PST[7 - bkR][bkC];
        egScore -= KING_END_PST[7 - bkR][bkC];
        if(bkR <= 1)
        {
            for(int dc = -1; dc <= 1; dc++)
            {
                int fc = bkC + dc;
                if(fc < 0 || fc >= 8) continue;
                if(b[bkR + 1][fc] == 'p') mgScore -= 12;
                else if(bkR + 2 < 8 && b[bkR + 2][fc] == 'p') mgScore -= 6;
                else if(bPawnCount[fc] == 0) mgScore += 14;
            }
        }
    }

    int clampedPhase = min(24, max(0, phase));
    int eval = (mgScore * clampedPhase + egScore * (24 - clampedPhase)) / 24;
    eval += chessboard.getWhiteTurn() ? 8 : -8;
    return eval;
}

int evaluateSideToMove(Board& chessboard, bool whiteTurn)
{
    int whiteEval = evaluateCentipawns(chessboard);
    return whiteTurn ? whiteEval : -whiteEval;
}

// ---------------- ZOBRIST HASHING ----------------

struct ZobristTables
{
    uint64_t pieces[12][64];
    uint64_t sideToMove;
    uint64_t castling[16];
    uint64_t epFile[9];

    ZobristTables()
    {
        mt19937_64 rng(0x9E3779B97F4A7C15ULL);
        for(int p = 0; p < 12; p++)
            for(int sq = 0; sq < 64; sq++)
                pieces[p][sq] = rng();
        sideToMove = rng();
        for(int i = 0; i < 16; i++) castling[i] = rng();
        for(int i = 0; i < 9; i++) epFile[i] = rng();
    }

    int pieceIndex(char ch) const
    {
        switch(ch)
        {
            case 'P': return 0;
            case 'N': return 1;
            case 'B': return 2;
            case 'R': return 3;
            case 'Q': return 4;
            case 'K': return 5;
            case 'p': return 6;
            case 'n': return 7;
            case 'b': return 8;
            case 'r': return 9;
            case 'q': return 10;
            case 'k': return 11;
            default: return -1;
        }
    }

    uint64_t hash(const BoardState& st) const
    {
        uint64_t h = 0;
        for(int r = 0; r < 8; r++)
        {
            for(int c = 0; c < 8; c++)
            {
                int idx = pieceIndex(st.board[r][c]);
                if(idx >= 0)
                    h ^= pieces[idx][r * 8 + c];
            }
        }
        if(st.whiteTurn) h ^= sideToMove;
        int castleMask = 0;
        if(!st.whiteKingMoved && !st.whiteKingsideRookMoved) castleMask |= 1;
        if(!st.whiteKingMoved && !st.whiteQueensideRookMoved) castleMask |= 2;
        if(!st.blackKingMoved && !st.blackKingsideRookMoved) castleMask |= 4;
        if(!st.blackKingMoved && !st.blackQueensideRookMoved) castleMask |= 8;
        h ^= castling[castleMask];
        int ep = (st.lastMoveWasDoublePawn && st.lastPawnCol >= 0 && st.lastPawnCol < 8)
            ? st.lastPawnCol
            : 8;
        h ^= epFile[ep];
        return h;
    }
};

const ZobristTables ZOBRIST;

int encodeScoreForTT(int score, int ply)
{
    if(score >= MATE_BOUND) return score + ply;
    if(score <= -MATE_BOUND) return score - ply;
    return score;
}

int decodeScoreFromTT(int score, int ply)
{
    if(score >= MATE_BOUND) return score - ply;
    if(score <= -MATE_BOUND) return score + ply;
    return score;
}

// ---------------- SEARCH CONTEXT (NEGAMAX + PVS + NMP + LMR + TT) ----------------

struct SearchContext
{
    vector<TTEntry> tt;
    string killers[MAX_PLY][2];
    int history[2][64][64];
    uint64_t pathHashes[MAX_PLY];
    long long nodes = 0;
    chrono::steady_clock::time_point deadline;
    bool hasDeadline = false;
    bool timedOut = false;

    SearchContext() : tt(TT_SIZE)
    {
        memset(history, 0, sizeof(history));
        memset(pathHashes, 0, sizeof(pathHashes));
    }

    bool checkTimeout()
    {
        if(timedOut) return true;
        if(hasDeadline && (nodes & 255) == 0)
        {
            if(chrono::steady_clock::now() >= deadline)
            {
                timedOut = true;
            }
        }
        return timedOut;
    }

    bool isPathRepetition(uint64_t key, int ply) const
    {
        for(int i = ply - 2; i >= 0; i -= 2)
        {
            if(pathHashes[i] == key)
            {
                return true;
            }
        }
        return false;
    }

    void recordKiller(int ply, const string& moveStr)
    {
        if(ply < 0 || ply >= MAX_PLY) return;
        if(killers[ply][0] != moveStr)
        {
            killers[ply][1] = killers[ply][0];
            killers[ply][0] = moveStr;
        }
    }

    void recordHistory(bool whiteTurn, Move& m, int depth)
    {
        int side = whiteTurn ? 0 : 1;
        int fromSq = m.getStartRow() * 8 + m.getStartCol();
        int toSq = m.getEndRow() * 8 + m.getEndCol();
        int bonus = min(400, depth * depth * 4);
        int& cell = history[side][fromSq][toSq];
        cell += bonus;
        if(cell > 40000)
        {
            for(int s = 0; s < 2; s++)
                for(int f = 0; f < 64; f++)
                    for(int t = 0; t < 64; t++)
                        history[s][f][t] /= 2;
        }
    }

    void orderMoves(Board& chessboard, vector<Move>& moves, int ply, const string& ttMove)
    {
        char (*b)[8] = chessboard.getBoard();
        int side = chessboard.getWhiteTurn() ? 0 : 1;
        struct ScoredMove
        {
            Move move;
            int score;
        };
        vector<ScoredMove> scored;
        scored.reserve(moves.size());

        for(auto& m : moves)
        {
            string notation = m.getChessNotation();
            int sc = 0;

            if(!ttMove.empty() && notation == ttMove)
            {
                sc = 2000000;
            }
            else
            {
                int sr = m.getStartRow(), scCol = m.getStartCol();
                int er = m.getEndRow(), ecCol = m.getEndCol();
                char attacker = b[sr][scCol];
                char victim = b[er][ecCol];

                bool isEp = (tolower(static_cast<unsigned char>(attacker)) == 'p' && scCol != ecCol && victim == ' ');
                if(victim != ' ')
                {
                    sc = 100000 + pieceValueCp(victim) * 10 - pieceValueCp(attacker) / 10;
                }
                else if(isEp)
                {
                    sc = 100000 + 1000 - 10;
                }

                char promo = m.getPromotionPiece();
                if(promo != ' ')
                {
                    sc += 90000 + pieceValueCp(promo);
                }

                if(sc == 0 && ply >= 0 && ply < MAX_PLY)
                {
                    if(notation == killers[ply][0]) sc = 50000;
                    else if(notation == killers[ply][1]) sc = 45000;
                    else
                    {
                        sc += history[side][sr * 8 + scCol][er * 8 + ecCol];
                    }
                }

                if(tolower(static_cast<unsigned char>(attacker)) == 'k' && abs(ecCol - scCol) == 2)
                {
                    sc += 80;
                }

                sc += pieceOrderingPst(attacker, er, ecCol) - pieceOrderingPst(attacker, sr, scCol);
            }

            scored.push_back({m, sc});
        }

        sort(scored.begin(), scored.end(), [](const ScoredMove& a, const ScoredMove& b) {
            return a.score > b.score;
        });

        for(size_t i = 0; i < scored.size(); i++)
        {
            moves[i] = scored[i].move;
        }
    }

    int quiescence(Board& chessboard, int alpha, int beta, int qDepth, int ply)
    {
        nodes++;
        bool whiteTurn = chessboard.getWhiteTurn();
        if(checkTimeout()) return evaluateSideToMove(chessboard, whiteTurn);

        if(chessboard.isInsufficientMaterial() || chessboard.isFiftyMoveDraw())
        {
            return 0;
        }

        bool inCheck = chessboard.isKinginCheck(whiteTurn);
        int standPat = -INF_SCORE;
        int best = -INF_SCORE;
        if(!inCheck)
        {
            standPat = evaluateSideToMove(chessboard, whiteTurn);
            if(qDepth <= 0 || standPat >= beta)
            {
                return standPat;
            }
            best = standPat;
            alpha = max(alpha, best);
        }

        vector<Move> moves = chessboard.generateLegalMoves(whiteTurn);
        if(moves.empty())
        {
            return inCheck ? -(MATE_SCORE - ply) : 0;
        }

        char (*b)[8] = chessboard.getBoard();
        vector<Move> tactical;
        tactical.reserve(moves.size());
        for(auto& m : moves)
        {
            if(inCheck)
            {
                tactical.push_back(m);
                continue;
            }
            int sr = m.getStartRow(), scCol = m.getStartCol();
            int er = m.getEndRow(), ecCol = m.getEndCol();
            bool isEp = (tolower(static_cast<unsigned char>(b[sr][scCol])) == 'p' && scCol != ecCol && b[er][ecCol] == ' ');
            bool isCapture = (b[er][ecCol] != ' ') || isEp;
            bool isPromo = (m.getPromotionPiece() != ' ');
            if(isCapture || isPromo)
            {
                if(!isPromo && !isEp && standPat + pieceValueCp(b[er][ecCol]) + 200 < alpha)
                {
                    continue;
                }
                tactical.push_back(m);
            }
        }

        orderMoves(chessboard, tactical, ply, "");

        for(auto& m : tactical)
        {
            BoardState st = chessboard.saveState();
            chessboard.makeMove(m);
            int score;
            if(inCheck && qDepth <= 0)
            {
                bool nextWhite = chessboard.getWhiteTurn();
                if(chessboard.isInsufficientMaterial() || chessboard.isFiftyMoveDraw())
                {
                    score = 0;
                }
                else
                {
                    vector<Move> nextMoves = chessboard.generateLegalMoves(nextWhite);
                    if(nextMoves.empty())
                    {
                        score = chessboard.isKinginCheck(nextWhite) ? (MATE_SCORE - (ply + 1)) : 0;
                    }
                    else
                    {
                        score = -evaluateSideToMove(chessboard, nextWhite);
                    }
                }
            }
            else
            {
                score = -quiescence(chessboard, -beta, -alpha, qDepth - 1, ply + 1);
            }
            chessboard.restoreState(st);

            if(timedOut) return best;

            if(score > best) best = score;
            if(best > alpha) alpha = best;
            if(alpha >= beta) break;
        }

        return best;
    }

    int negamax(Board& chessboard, int depth, int alpha, int beta, int ply, bool allowNull)
    {
        nodes++;
        bool whiteTurn = chessboard.getWhiteTurn();
        if(checkTimeout()) return evaluateSideToMove(chessboard, whiteTurn);

        if(ply > 0 && (chessboard.isInsufficientMaterial() || chessboard.isFiftyMoveDraw()))
        {
            return 0;
        }

        if(ply >= MAX_PLY - 1)
        {
            return evaluateSideToMove(chessboard, whiteTurn);
        }

        BoardState curState = chessboard.saveState();
        uint64_t key = ZOBRIST.hash(curState);
        if(ply > 0 && isPathRepetition(key, ply))
        {
            return 0;
        }
        pathHashes[ply] = key;

        bool isPV = (beta - alpha) > 1;
        bool inCheck = chessboard.isKinginCheck(whiteTurn);
        if(inCheck && ply < 24)
        {
            depth++;
        }

        if(depth <= 0)
        {
            return quiescence(chessboard, alpha, beta, 4, ply);
        }

        TTEntry& entry = tt[key & (TT_SIZE - 1)];
        string ttMove;
        if(entry.flag != TT_EMPTY && entry.key == key)
        {
            ttMove = entry.bestMove;
            if(!isPV && entry.depth >= depth)
            {
                int ttScore = decodeScoreFromTT(entry.score, ply);
                if(entry.flag == TT_EXACT) return ttScore;
                if(entry.flag == TT_LOWER && ttScore >= beta) return ttScore;
                if(entry.flag == TT_UPPER && ttScore <= alpha) return ttScore;
            }
        }

        vector<Move> moves = chessboard.generateLegalMoves(whiteTurn);
        if(moves.empty())
        {
            return inCheck ? -(MATE_SCORE - ply) : 0;
        }

        // Null-Move Pruning (skip in PV, check, or pure pawn endgames)
        if(!isPV && !inCheck && allowNull && depth >= 3 && hasNonPawnMaterial(chessboard, whiteTurn))
        {
            int staticEval = evaluateSideToMove(chessboard, whiteTurn);
            if(staticEval >= beta)
            {
                int R = (depth >= 6) ? 3 : 2;
                int nullDepth = max(0, depth - 1 - R);
                BoardState nullBackup = chessboard.saveState();
                chessboard.makeNullMove();
                int nullScore = -negamax(chessboard, nullDepth, -beta, -beta + 1, ply + 1, false);
                chessboard.restoreState(nullBackup);

                if(timedOut) return alpha;
                if(nullScore >= beta && nullScore < MATE_BOUND)
                {
                    return beta;
                }
            }
        }

        orderMoves(chessboard, moves, ply, ttMove);

        int origAlpha = alpha;
        int bestScore = -INF_SCORE;
        string bestLocalMove;
        char (*b)[8] = chessboard.getBoard();

        for(size_t moveIdx = 0; moveIdx < moves.size(); moveIdx++)
        {
            Move& m = moves[moveIdx];
            int sr = m.getStartRow(), scCol = m.getStartCol();
            int er = m.getEndRow(), ecCol = m.getEndCol();
            bool isEp = (tolower(static_cast<unsigned char>(b[sr][scCol])) == 'p' && scCol != ecCol && b[er][ecCol] == ' ');
            bool isCapture = (b[er][ecCol] != ' ') || isEp;
            bool isPromo = (m.getPromotionPiece() != ' ');
            bool isQuiet = !isCapture && !isPromo;

            BoardState st = chessboard.saveState();
            chessboard.makeMove(m);

            int score;
            if(moveIdx == 0)
            {
                score = -negamax(chessboard, depth - 1, -beta, -alpha, ply + 1, true);
            }
            else
            {
                bool didLmr = false;
                if(depth >= 3 && moveIdx >= 3 && isQuiet && !inCheck)
                {
                    int reduction = (depth >= 6 && moveIdx >= 8) ? 2 : 1;
                    int reducedDepth = max(1, depth - 1 - reduction);
                    score = -negamax(chessboard, reducedDepth, -alpha - 1, -alpha, ply + 1, true);
                    didLmr = true;
                }
                else
                {
                    score = alpha + 1; // Trigger zero-window full depth search below
                }

                if(!timedOut && (!didLmr || score > alpha))
                {
                    score = -negamax(chessboard, depth - 1, -alpha - 1, -alpha, ply + 1, true);
                    if(!timedOut && isPV && score > alpha && score < beta)
                    {
                        score = -negamax(chessboard, depth - 1, -beta, -alpha, ply + 1, true);
                    }
                }
            }

            chessboard.restoreState(st);

            if(timedOut) return bestScore;

            if(score > bestScore)
            {
                bestScore = score;
                bestLocalMove = m.getChessNotation();
            }
            if(bestScore > alpha)
            {
                alpha = bestScore;
                if(alpha >= beta)
                {
                    if(isQuiet)
                    {
                        recordKiller(ply, bestLocalMove);
                        recordHistory(whiteTurn, m, depth);
                    }
                    break;
                }
            }
        }

        if(!timedOut && !bestLocalMove.empty())
        {
            entry.key = key;
            entry.depth = depth;
            entry.score = encodeScoreForTT(bestScore, ply);
            if(bestScore <= origAlpha) entry.flag = TT_UPPER;
            else if(bestScore >= beta) entry.flag = TT_LOWER;
            else entry.flag = TT_EXACT;
            size_t len = min<size_t>(5, bestLocalMove.size());
            for(size_t i = 0; i < len; i++) entry.bestMove[i] = bestLocalMove[i];
            entry.bestMove[len] = '\0';
        }

        return bestScore;
    }
};
} // namespace

Search::Search() {}

SearchResult Search::findBestMove(Board& board, int maxDepth, int timeLimitMs)
{
    SearchResult result{"", 0, 0};
    BoardState rootBackup = board.saveState();

    bool whiteTurn = board.getWhiteTurn();
    vector<Move> legalMoves = board.generateLegalMoves(whiteTurn);
    if(legalMoves.empty())
    {
        return result;
    }

    string bookMove = tryOpeningBookMove(board, legalMoves);
    if(!bookMove.empty())
    {
        result.bestMove = bookMove;
        result.score = 0;
        result.nodes = 1;
        return result;
    }

    SearchContext ctx;
    if(timeLimitMs > 0)
    {
        ctx.hasDeadline = true;
        ctx.deadline = chrono::steady_clock::now() + chrono::milliseconds(timeLimitMs);
    }

    uint64_t rootKey = ZOBRIST.hash(rootBackup);
    ctx.pathHashes[0] = rootKey;

    int targetDepth = max(1, maxDepth);
    string bestMove = legalMoves[0].getChessNotation();
    int bestScoreSide = 0;

    for(int d = 1; d <= targetDepth; d++)
    {
        ctx.timedOut = false;
        int alpha = -INF_SCORE;
        int beta = INF_SCORE;
        if(d >= 4 && abs(bestScoreSide) < MATE_BOUND)
        {
            alpha = bestScoreSide - 60;
            beta = bestScoreSide + 60;
        }

        while(true)
        {
            ctx.orderMoves(board, legalMoves, 0, bestMove);

            string iterBestMove = "";
            int iterBestScore = -INF_SCORE;
            int curAlpha = alpha;
            int curBeta = beta;
            char (*b)[8] = board.getBoard();

            for(size_t moveIdx = 0; moveIdx < legalMoves.size(); moveIdx++)
            {
                if(d > 1 && ctx.checkTimeout())
                {
                    break;
                }

                Move& m = legalMoves[moveIdx];
                (void)b;
                BoardState st = board.saveState();
                board.makeMove(m);
                int score;
                if(moveIdx == 0)
                {
                    score = -ctx.negamax(board, d - 1, -curBeta, -curAlpha, 1, true);
                }
                else
                {
                    score = -ctx.negamax(board, d - 1, -curAlpha - 1, -curAlpha, 1, true);
                    if(!ctx.timedOut && score > curAlpha && score < curBeta)
                    {
                        score = -ctx.negamax(board, d - 1, -curBeta, -curAlpha, 1, true);
                    }
                }
                board.restoreState(st);

                if(d > 1 && ctx.timedOut)
                {
                    break;
                }

                if(score > iterBestScore)
                {
                    iterBestScore = score;
                    iterBestMove = m.getChessNotation();
                }
                if(score > curAlpha)
                {
                    curAlpha = score;
                }
            }

            if(d > 1 && ctx.timedOut)
            {
                break;
            }

            if(!iterBestMove.empty())
            {
                if(iterBestScore <= alpha && alpha > -INF_SCORE)
                {
                    alpha = -INF_SCORE;
                    bestMove = iterBestMove;
                    continue;
                }
                if(iterBestScore >= beta && beta < INF_SCORE)
                {
                    beta = INF_SCORE;
                    bestMove = iterBestMove;
                    continue;
                }

                bestMove = iterBestMove;
                bestScoreSide = iterBestScore;
            }
            break;
        }

        if(ctx.timedOut && d > 1)
        {
            break;
        }
        if(abs(bestScoreSide) >= MATE_BOUND)
        {
            break;
        }
    }

    board.restoreState(rootBackup);
    result.bestMove = bestMove;
    result.score = whiteTurn ? bestScoreSide : -bestScoreSide;
    result.nodes = ctx.nodes;
    return result;
}
