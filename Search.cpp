#include "Search.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <random>
#include <vector>

using namespace std;

namespace
{
const int INF_SCORE = 10000000;
const int MATE_SCORE = 100000;
const int TT_SIZE = 1 << 16; // 65536 entries

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

const int PAWN_PST[8][8] = {
    {0,  0,  0,  0,  0,  0,  0,  0},
    {50, 50, 50, 50, 50, 50, 50, 50},
    {10, 10, 20, 30, 30, 20, 10, 10},
    {5,  5, 10, 25, 25, 10,  5,  5},
    {0,  0,  0, 22, 22,  0,  0,  0},
    {5, -5,-10,  0,  0,-10, -5,  5},
    {5, 10, 10,-20,-20, 10, 10,  5},
    {0,  0,  0,  0,  0,  0,  0,  0}
};

const int KNIGHT_PST[8][8] = {
    {-50,-40,-30,-30,-30,-30,-40,-50},
    {-40,-20,  0,  0,  0,  0,-20,-40},
    {-30,  0, 10, 15, 15, 10,  0,-30},
    {-30,  5, 15, 20, 20, 15,  5,-30},
    {-30,  0, 15, 20, 20, 15,  0,-30},
    {-30,  5, 10, 15, 15, 10,  5,-30},
    {-40,-20,  0,  5,  5,  0,-20,-40},
    {-50,-40,-30,-30,-30,-30,-40,-50}
};

const int BISHOP_PST[8][8] = {
    {-20,-10,-10,-10,-10,-10,-10,-20},
    {-10,  0,  0,  0,  0,  0,  0,-10},
    {-10,  0,  5, 10, 10,  5,  0,-10},
    {-10,  5,  5, 10, 10,  5,  5,-10},
    {-10,  0, 10, 10, 10, 10,  0,-10},
    {-10, 10, 10, 10, 10, 10, 10,-10},
    {-10,  5,  0,  0,  0,  0,  5,-10},
    {-20,-10,-10,-10,-10,-10,-10,-20}
};

const int ROOK_PST[8][8] = {
    {0,  0,  0,  0,  0,  0,  0,  0},
    {5, 10, 10, 10, 10, 10, 10,  5},
    {-5, 0,  0,  0,  0,  0,  0, -5},
    {-5, 0,  0,  0,  0,  0,  0, -5},
    {-5, 0,  0,  0,  0,  0,  0, -5},
    {-5, 0,  0,  0,  0,  0,  0, -5},
    {-5, 0,  0,  0,  0,  0,  0, -5},
    {0,  0,  0,  5,  5,  0,  0,  0}
};

const int QUEEN_PST[8][8] = {
    {-20,-10,-10, -5, -5,-10,-10,-20},
    {-10,  0,  0,  0,  0,  0,  0,-10},
    {-10,  0,  5,  5,  5,  5,  0,-10},
    {-5,   0,  5,  5,  5,  5,  0, -5},
    {0,    0,  5,  5,  5,  5,  0, -5},
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
    {20,  20,  0,  0,  0,  0, 20, 20},
    {20,  30, 10,  0,  0, 10, 30, 20}
};

const int KING_END_PST[8][8] = {
    {-50,-40,-30,-20,-20,-30,-40,-50},
    {-30,-20,-10,  0,  0,-10,-20,-30},
    {-30,-10, 20, 30, 30, 20,-10,-30},
    {-30,-10, 30, 40, 40, 30,-10,-30},
    {-30,-10, 30, 40, 40, 30,-10,-30},
    {-30,-10, 20, 30, 30, 20,-10,-30},
    {-30,-30,  0,  0,  0,  0,-30,-30},
    {-50,-30,-30,-30,-30,-30,-30,-50}
};

int pieceValueCp(char piece)
{
    switch(tolower(piece))
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

int piecePst(char piece, int row, int col)
{
    int r = isupper(static_cast<unsigned char>(piece)) ? row : (7 - row);
    switch(tolower(piece))
    {
        case 'p': return PAWN_PST[r][col];
        case 'n': return KNIGHT_PST[r][col];
        case 'b': return BISHOP_PST[r][col];
        case 'r': return ROOK_PST[r][col];
        case 'q': return QUEEN_PST[r][col];
        default: return 0;
    }
}

int evaluateCentipawns(Board& chessboard)
{
    char (*b)[8] = chessboard.getBoard();
    int score = 0;
    int nonKingMat = 0;
    int wBishops = 0, bBishops = 0;
    int wkR = -1, wkC = -1, bkR = -1, bkC = -1;

    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            char p = b[r][c];
            if(p == ' ') continue;

            if(p == 'K') { wkR = r; wkC = c; continue; }
            if(p == 'k') { bkR = r; bkC = c; continue; }

            int val = pieceValueCp(p);
            int pst = piecePst(p, r, c);
            nonKingMat += val;

            if(isupper(static_cast<unsigned char>(p)))
            {
                score += val + pst;
                if(p == 'B') wBishops++;
            }
            else
            {
                score -= (val + pst);
                if(p == 'b') bBishops++;
            }
        }
    }

    if(wBishops >= 2) score += 30;
    if(bBishops >= 2) score -= 30;

    bool endgame = (nonKingMat <= 2600);
    if(wkR >= 0)
    {
        score += endgame ? KING_END_PST[wkR][wkC] : KING_MID_PST[wkR][wkC];
    }
    if(bkR >= 0)
    {
        score -= endgame ? KING_END_PST[7 - bkR][bkC] : KING_MID_PST[7 - bkR][bkC];
    }

    return score;
}

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

struct SearchContext
{
    vector<TTEntry> tt;
    string killers[64][2];
    long long nodes = 0;
    chrono::steady_clock::time_point deadline;
    bool hasDeadline = false;
    bool timedOut = false;

    SearchContext() : tt(TT_SIZE) {}

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

    void recordKiller(int ply, const string& moveStr)
    {
        if(ply < 0 || ply >= 64) return;
        if(killers[ply][0] != moveStr)
        {
            killers[ply][1] = killers[ply][0];
            killers[ply][0] = moveStr;
        }
    }

    void orderMoves(Board& chessboard, vector<Move>& moves, int ply, const string& ttMove)
    {
        char (*b)[8] = chessboard.getBoard();
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
                sc = 1000000;
            }
            else
            {
                int sr = m.getStartRow(), scCol = m.getStartCol();
                int er = m.getEndRow(), ecCol = m.getEndCol();
                char attacker = b[sr][scCol];
                char victim = b[er][ecCol];

                bool isEp = (tolower(attacker) == 'p' && scCol != ecCol && victim == ' ');
                if(victim != ' ')
                {
                    sc = 10000 + pieceValueCp(victim) * 10 - pieceValueCp(attacker) / 10;
                }
                else if(isEp)
                {
                    sc = 10000 + 1000 - 10;
                }

                char promo = m.getPromotionPiece();
                if(promo != ' ')
                {
                    sc += 9000 + pieceValueCp(promo);
                }

                if(sc == 0 && ply >= 0 && ply < 64)
                {
                    if(notation == killers[ply][0]) sc = 5000;
                    else if(notation == killers[ply][1]) sc = 4500;
                }

                if(tolower(attacker) == 'k' && abs(ecCol - scCol) == 2)
                {
                    sc += 60;
                }

                sc += piecePst(attacker, er, ecCol) - piecePst(attacker, sr, scCol);
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
        if(checkTimeout()) return evaluateCentipawns(chessboard);

        bool whiteTurn = chessboard.getWhiteTurn();
        if(chessboard.isInsufficientMaterial() || chessboard.isFiftyMoveDraw())
        {
            return 0;
        }

        bool inCheck = chessboard.isKinginCheck(whiteTurn);
        vector<Move> moves = chessboard.generateLegalMoves(whiteTurn);
        if(moves.empty())
        {
            if(inCheck)
            {
                int mateVal = MATE_SCORE + max(0, 20 - ply);
                return whiteTurn ? -mateVal : mateVal;
            }
            return 0;
        }

        int standPat = evaluateCentipawns(chessboard);
        if(qDepth <= 0 && !inCheck)
        {
            return standPat;
        }

        int best = standPat;
        if(!inCheck)
        {
            if(whiteTurn)
            {
                if(standPat >= beta) return standPat;
                alpha = max(alpha, standPat);
            }
            else
            {
                if(standPat <= alpha) return standPat;
                beta = min(beta, standPat);
            }
        }
        else
        {
            best = whiteTurn ? -INF_SCORE : INF_SCORE;
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
            bool isCapture = (b[er][ecCol] != ' ') ||
                             (tolower(b[sr][scCol]) == 'p' && scCol != ecCol);
            bool isPromo = (m.getPromotionPiece() != ' ');
            if(isCapture || isPromo)
            {
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
                        if(chessboard.isKinginCheck(nextWhite))
                        {
                            int mateVal = MATE_SCORE + max(0, 19 - ply);
                            score = nextWhite ? -mateVal : mateVal;
                        }
                        else
                        {
                            score = 0;
                        }
                    }
                    else
                    {
                        score = evaluateCentipawns(chessboard);
                    }
                }
            }
            else
            {
                score = quiescence(chessboard, alpha, beta, qDepth - 1, ply + 1);
            }
            chessboard.restoreState(st);

            if(timedOut) return best;

            if(whiteTurn)
            {
                best = max(best, score);
                alpha = max(alpha, best);
                if(alpha >= beta) break;
            }
            else
            {
                best = min(best, score);
                beta = min(beta, best);
                if(beta <= alpha) break;
            }
        }

        return best;
    }

    int alphaBeta(Board& chessboard, int depth, int alpha, int beta, int ply)
    {
        nodes++;
        if(checkTimeout()) return evaluateCentipawns(chessboard);

        bool whiteTurn = chessboard.getWhiteTurn();
        if(chessboard.isInsufficientMaterial() || chessboard.isFiftyMoveDraw())
        {
            return 0;
        }

        if(depth <= 0)
        {
            return quiescence(chessboard, alpha, beta, 4, ply);
        }

        BoardState curState = chessboard.saveState();
        uint64_t key = ZOBRIST.hash(curState);
        TTEntry& entry = tt[key & (TT_SIZE - 1)];
        string ttMove;

        if(entry.flag != TT_EMPTY && entry.key == key)
        {
            ttMove = entry.bestMove;
            if(entry.depth >= depth)
            {
                if(entry.flag == TT_EXACT) return entry.score;
                if(entry.flag == TT_LOWER && entry.score >= beta) return entry.score;
                if(entry.flag == TT_UPPER && entry.score <= alpha) return entry.score;
            }
        }

        vector<Move> moves = chessboard.generateLegalMoves(whiteTurn);
        if(moves.empty())
        {
            if(chessboard.isKinginCheck(whiteTurn))
            {
                int mateVal = MATE_SCORE + depth * 10 + max(0, 20 - ply);
                return whiteTurn ? -mateVal : mateVal;
            }
            return 0;
        }

        orderMoves(chessboard, moves, ply, ttMove);

        int origAlpha = alpha;
        int origBeta = beta;
        int bestScore = whiteTurn ? -INF_SCORE : INF_SCORE;
        string bestLocalMove;
        char (*b)[8] = chessboard.getBoard();

        for(auto& m : moves)
        {
            bool isCapture = (b[m.getEndRow()][m.getEndCol()] != ' ');
            BoardState st = chessboard.saveState();
            chessboard.makeMove(m);
            int score = alphaBeta(chessboard, depth - 1, alpha, beta, ply + 1);
            chessboard.restoreState(st);

            if(timedOut) return bestScore;

            if(whiteTurn)
            {
                if(score > bestScore)
                {
                    bestScore = score;
                    bestLocalMove = m.getChessNotation();
                }
                alpha = max(alpha, bestScore);
                if(alpha >= beta)
                {
                    if(!isCapture && m.getPromotionPiece() == ' ')
                    {
                        recordKiller(ply, m.getChessNotation());
                    }
                    break;
                }
            }
            else
            {
                if(score < bestScore)
                {
                    bestScore = score;
                    bestLocalMove = m.getChessNotation();
                }
                beta = min(beta, bestScore);
                if(beta <= alpha)
                {
                    if(!isCapture && m.getPromotionPiece() == ' ')
                    {
                        recordKiller(ply, m.getChessNotation());
                    }
                    break;
                }
            }
        }

        if(!timedOut && !bestLocalMove.empty())
        {
            entry.key = key;
            entry.depth = depth;
            entry.score = bestScore;
            if(bestScore <= origAlpha) entry.flag = TT_UPPER;
            else if(bestScore >= origBeta) entry.flag = TT_LOWER;
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

    SearchContext ctx;
    if(timeLimitMs > 0)
    {
        ctx.hasDeadline = true;
        ctx.deadline = chrono::steady_clock::now() + chrono::milliseconds(timeLimitMs);
    }

    int targetDepth = max(1, maxDepth);
    string bestMove = legalMoves[0].getChessNotation();
    int bestScore = 0;

    for(int d = 1; d <= targetDepth; d++)
    {
        ctx.timedOut = false;
        ctx.orderMoves(board, legalMoves, 0, bestMove);

        string iterBestMove = "";
        int iterBestScore = whiteTurn ? -INF_SCORE : INF_SCORE;
        int alpha = -INF_SCORE;
        int beta = INF_SCORE;

        for(auto& m : legalMoves)
        {
            if(d > 1 && ctx.checkTimeout())
            {
                break;
            }

            BoardState st = board.saveState();
            board.makeMove(m);
            int score = ctx.alphaBeta(board, d - 1, alpha, beta, 1);
            board.restoreState(st);

            if(d > 1 && ctx.timedOut)
            {
                break;
            }

            if(whiteTurn)
            {
                if(score > iterBestScore)
                {
                    iterBestScore = score;
                    iterBestMove = m.getChessNotation();
                }
                alpha = max(alpha, iterBestScore);
            }
            else
            {
                if(score < iterBestScore)
                {
                    iterBestScore = score;
                    iterBestMove = m.getChessNotation();
                }
                beta = min(beta, iterBestScore);
            }
        }

        if(!ctx.timedOut && !iterBestMove.empty())
        {
            bestMove = iterBestMove;
            bestScore = iterBestScore;
            if(abs(bestScore) >= MATE_SCORE - 100)
            {
                break;
            }
        }
        else if(d > 1)
        {
            break;
        }
    }

    board.restoreState(rootBackup);
    result.bestMove = bestMove;
    result.score = bestScore;
    result.nodes = ctx.nodes;
    return result;
}
