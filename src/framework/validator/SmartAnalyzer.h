/*
 * SmartAnalyzer.h — Keyboard-aware mistake diagnosis for Open-Typer
 * Does NOT modify ExerciseValidator; standalone so timed-para patch is untouched.
 *
 * Analyses *why* mistakes happen:
 *  - adjacent keys on QWERTY (≈1.4 distance)
 *  - missed / accidental Shift (caps, symbols like !/1, :/;)
 *  - transposition (swapped letters "teh"→"the")
 *  - double-letter rhythm
 *  - word-level confusion (similar words)
 *
 * Exposed to QML as OpenTyper.Validator.SmartAnalyzer
 */
#ifndef SMARTANALYZER_H
#define SMARTANALYZER_H

#include <QObject>
#include <QVariantMap>
#include <QVariantList>
#include <QMap>
#include <QPair>

class SmartAnalyzer : public QObject
{
    Q_OBJECT
public:
    explicit SmartAnalyzer(QObject *parent = nullptr) : QObject(parent) {}

    enum Category {
        AdjacentKey = 0,
        ShiftCase = 1,
        ShiftSymbol = 2,
        Transposition = 3,
        DoubleLetter = 4,
        Omission = 5,
        Insertion = 6,
        Other = 7
    };
    Q_ENUM(Category)

    // Main entry: target vs typed -> report map
    Q_INVOKABLE QVariantMap analyze(const QString &target, const QString &typed);

    // Drill text for worst letters
    Q_INVOKABLE QString generateDrill(const QVariantList &worstLetters, int wordCount = 40);

    // Static helpers exposed for QML debugging
    Q_INVOKABLE bool isAdjacent(const QString &a, const QString &b);
    Q_INVOKABLE double keyDistance(const QString &a, const QString &b);
    Q_INVOKABLE QString fingerFor(const QString &ch);
    Q_INVOKABLE QVariantMap classifySingle(const QString &expected, const QString &typed);

private:
    struct KeyPos { double x, y; };
    static QMap<QString, KeyPos> s_pos;
    static QMap<QString, QPair<QString,QString>> s_finger; // char -> (hand,finger)
    static QMap<QString, QString> s_baseToShift;
    static QMap<QString, QString> s_shiftToBase;
    static bool s_inited;
    static void ensureInited();
    static double distance(const QString &a, const QString &b);
    static bool adjacent(const QString &a, const QString &b);
    static QPair<QString,QString> finger(const QString &ch);
    static QVariantMap classify(const QString &exp, const QString &got, const QString &prev, const QString &next);
    static QString wordAt(const QString &text, int pos);
};

#endif // SMARTANALYZER_H
