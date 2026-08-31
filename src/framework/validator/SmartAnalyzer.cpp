/*
 * SmartAnalyzer.cpp
 * Standalone, no dependency on ExerciseValidator — safe to merge with timed-para work.
 */
#include "SmartAnalyzer.h"
#include <QMap>
#include <QSet>
#include <QVector>
#include <QtMath>
#include <QRandomGenerator>
#include <QRegularExpression>

QMap<QString, SmartAnalyzer::KeyPos> SmartAnalyzer::s_pos;
QMap<QString, QPair<QString,QString>> SmartAnalyzer::s_finger;
QMap<QString, QString> SmartAnalyzer::s_baseToShift;
QMap<QString, QString> SmartAnalyzer::s_shiftToBase;
bool SmartAnalyzer::s_inited = false;

static void addRow(const QStringList &chars, double y, double x0, double dx=1.0){
    for(int i=0;i<chars.size();++i){
        SmartAnalyzer::KeyPos p{ x0 + i*dx, y };
        SmartAnalyzer::s_pos[chars[i]] = p;
        if(chars[i].size()==1 && chars[i][0].isLetter()){
            SmartAnalyzer::s_pos[chars[i].toUpper()] = p;
        }
    }
}
void SmartAnalyzer::ensureInited(){
    if(s_inited) return;
    s_inited=true;
    addRow(QStringList{"`","1","2","3","4","5","6","7","8","9","0","-","="}, 0, 0);
    addRow(QStringList{"q","w","e","r","t","y","u","i","o","p","[","]","\\"}, 1, 0.5);
    addRow(QStringList{"a","s","d","f","g","h","j","k","l",";","'"}, 2, 0.75);
    addRow(QStringList{"z","x","c","v","b","n","m",",",".","/"}, 3, 1.25);
    s_pos[" "] = {5.5, 4.0};
    s_pos["\n"] = {13.0, 2.0};

    auto addFinger=[&](const QString &ch, const QString &hand, const QString &finger){
        s_finger[ch]=qMakePair(hand,finger);
        if(ch.size()==1 && ch[0].isLetter())
            s_finger[ch.toUpper()]=qMakePair(hand,finger);
    };
    addFinger("`","L","LP"); addFinger("1","L","LP"); addFinger("q","L","LP"); addFinger("a","L","LP"); addFinger("z","L","LP");
    addFinger("2","L","LR"); addFinger("w","L","LR"); addFinger("s","L","LR"); addFinger("x","L","LR");
    addFinger("3","L","LM"); addFinger("e","L","LM"); addFinger("d","L","LM"); addFinger("c","L","LM");
    addFinger("4","L","LI"); addFinger("5","L","LI"); addFinger("r","L","LI"); addFinger("f","L","LI"); addFinger("v","L","LI"); addFinger("t","L","LI"); addFinger("g","L","LI"); addFinger("b","L","LI");
    addFinger("6","R","RI"); addFinger("7","R","RI"); addFinger("y","R","RI"); addFinger("h","R","RI"); addFinger("n","R","RI"); addFinger("u","R","RI"); addFinger("j","R","RI"); addFinger("m","R","RI");
    addFinger("8","R","RM"); addFinger("i","R","RM"); addFinger("k","R","RM"); addFinger(",","R","RM");
    addFinger("9","R","RR"); addFinger("o","R","RR"); addFinger("l","R","RR"); addFinger(".","R","RR");
    addFinger("0","R","RP"); addFinger("-","R","RP"); addFinger("=","R","RP"); addFinger("p","R","RP"); addFinger("[","R","RP"); addFinger("]","R","RP"); addFinger("\\","R","RP"); addFinger(";","R","RP"); addFinger("'","R","RP"); addFinger("/","R","RP");
    addFinger(" ","","TH"); addFinger("\n","R","RP");

    QMap<QString,QString> b2s{{"`","~"},{"1","!"},{"2","@"},{"3","#"},{"4","$"},{"5","%"},{"6","^"},{"7","&"},{"8","*"},{"9","("},{"0",")"},{"-","_"},{"=","+"},{"[","{"},{"]","}"},{"\\","|"},{";"," : "},{"'","\" "},{",","<"},{".",">"},{"/","?"}}; // fix later
    // clean entries: ";" -> ":" etc
    b2s.clear();
    b2s["`"]="~"; b2s["1"]="!"; b2s["2"]="@"; b2s["3"]="#"; b2s["4"]="$"; b2s["5"]="%"; b2s["6"]="^"; b2s["7"]="&"; b2s["8"]="*"; b2s["9"]="("; b2s["0"]=")"; b2s["-"]="_"; b2s["="]="+"; b2s["["]="{"; b2s["]"]="}"; b2s["\\"]="|"; b2s[";"]=":"; b2s["'"]="\""; b2s[","]="<"; b2s["."]=">"; b2s["/"]="?";
    s_baseToShift=b2s;
    for(auto it=b2s.begin(); it!=b2s.end(); ++it)
        s_shiftToBase[it.value()]=it.key();
}

double SmartAnalyzer::distance(const QString &a, const QString &b){
    ensureInited();
    if(a.isEmpty()||b.isEmpty()) return 9.9;
    QString ca=a.left(1), cb=b.left(1);
    if(!s_pos.contains(ca)) ca=ca.toLower();
    if(!s_pos.contains(cb)) cb=cb.toLower();
    if(!s_pos.contains(ca)||!s_pos.contains(cb)) return 9.9;
    auto pa=s_pos[ca], pb=s_pos[cb];
    return qSqrt(qPow(pa.x-pb.x,2)+qPow(pa.y-pb.y,2));
}
bool SmartAnalyzer::adjacent(const QString &a, const QString &b){
    if(a.isEmpty()||b.isEmpty()) return false;
    if(a.toLower()==b.toLower()) return false;
    return distance(a,b) <= 1.42;
}
QPair<QString,QString> SmartAnalyzer::finger(const QString &ch){
    ensureInited();
    if(ch.isEmpty()) return qMakePair(QString(""),QString(""));
    QString c=ch.left(1);
    if(s_finger.contains(c)) return s_finger[c];
    if(s_finger.contains(c.toLower())) return s_finger[c.toLower()];
    return qMakePair(QString(""),QString(""));
}
bool SmartAnalyzer::isAdjacent(const QString &a, const QString &b){ return adjacent(a,b); }
double SmartAnalyzer::keyDistance(const QString &a, const QString &b){ return distance(a,b); }
QString SmartAnalyzer::fingerFor(const QString &ch){
    auto p=finger(ch);
    static QMap<QString,QString> names{{"LP","Left Pinky"},{"LR","Left Ring"},{"LM","Left Middle"},{"LI","Left Index"},{"RI","Right Index"},{"RM","Right Middle"},{"RR","Right Ring"},{"RP","Right Pinky"},{"TH","Thumb"}};
    if(names.contains(p.second)) return names[p.second] + " (" + p.first + ")";
    return p.second + " " + p.first;
}

QVariantMap SmartAnalyzer::classify(const QString &exp, const QString &got, const QString &prev, const QString &next){
    ensureInited();
    QVariantMap out;
    out["expected"]=exp; out["typed"]=got;
    if(exp==got){ out["category"]="correct"; out["reason"]=""; out["suggestion"]=""; return out; }
    // case swap
    if(exp.toLower()==got.toLower() && exp!=got){
        if(exp[0].isUpper() && got[0].isLower()){
            out["category"]="shift_case";
            out["reason"]=QString("Typed lowercase '%1' but expected uppercase '%2'. Missed Shift (or Caps Lock off).").arg(got, exp);
            out["suggestion"]=QString("Hold Shift with opposite hand for '%1'.").arg(exp);
            return out;
        } else {
            out["category"]="shift_case";
            out["reason"]=QString("Typed uppercase '%1' but expected lowercase '%2'. Accidental Shift / Caps Lock on.").arg(got, exp);
            out["suggestion"]=QString("Check Caps Lock. Release Shift for '%1'.").arg(exp);
            return out;
        }
    }
    if(s_shiftToBase.contains(exp) && s_shiftToBase[exp]==got){
        out["category"]="shift_symbol";
        out["reason"]=QString("Expected symbol '%1' (Shift + '%2') but typed '%2' without Shift.").arg(exp, got);
        out["suggestion"]=QString("Hold Shift + '%1' → '%2'.").arg(got, exp);
        return out;
    }
    if(s_shiftToBase.contains(got) && s_shiftToBase[got]==exp){
        out["category"]="shift_symbol";
        out["reason"]=QString("Expected '%1' but typed shifted '%2' (Shift + '%1').").arg(exp, got);
        out["suggestion"]=QString("Release Shift for '%1'.").arg(exp);
        return out;
    }
    if(s_baseToShift.contains(exp) && s_baseToShift[exp]==got){
        out["category"]="shift_symbol";
        out["reason"]=QString("Expected '%1' but held Shift and typed '%2'.").arg(exp, got);
        out["suggestion"]=QString("Don't hold Shift for '%1'.").arg(exp);
        return out;
    }
    if(s_baseToShift.contains(got) && s_baseToShift[got]==exp){
        out["category"]="shift_symbol";
        out["reason"]=QString("Expected '%1' (Shift layer) but typed base '%2'. Hold Shift!").arg(exp, got);
        out["suggestion"]=QString("Shift + '%1' → '%2'.").arg(got, exp);
        return out;
    }
    if(adjacent(exp, got)){
        double d=distance(exp,got);
        auto fe=finger(exp), fg=finger(got);
        bool sf = (fe==fg);
        out["category"]="adjacent_key";
        out["reason"]=QString("'%1' is next to '%2' on QWERTY (dist %3). %4 — likely wrong finger / fat-finger.")
                         .arg(got, exp).arg(d,0,'f',1).arg(sf ? "Same finger" : "Different finger");
        out["suggestion"]=QString("Focus on '%1' — %2. Slow down.").arg(exp, fingerFor(exp));
        out["distance"]=d;
        return out;
    }
    if(prev==exp || next==exp){
        out["category"]="double_letter";
        out["reason"]=QString("Double-letter near '%1'. Rhythm slip.").arg(exp);
        out["suggestion"]=QString("Practice double '%1' with steady rhythm.").arg(exp.toLower());
        return out;
    }
    out["category"]="other";
    out["reason"]=QString("Typed '%1' instead of '%2'. Similar-word / reading error.").arg(got, exp);
    out["suggestion"]=QString("Practice words with '%1'.").arg(exp);
    return out;
}
QVariantMap SmartAnalyzer::classifySingle(const QString &exp, const QString &got){
    return classify(exp, got, "", "");
}
QString SmartAnalyzer::wordAt(const QString &text, int pos){
    if(pos<0||pos>=text.size()) return "";
    int s=pos, e=pos;
    while(s>0 && (text[s-1].isLetterOrNumber() || text[s-1]=='\'' || text[s-1]=='-')) s--;
    while(e < text.size() && (text[e].isLetterOrNumber() || text[e]=='\'' || text[e]=='-')) e++;
    return text.mid(s, e-s);
}

static QStringList commonPool(){
    return QStringList{"the","be","to","of","and","a","in","that","have","I","it","for","not","on","with","he","as","you","do","at","this","but","his","by","from","they","we","say","her","she","or","an","will","my","one","all","would","there","their","what","so","up","out","if","about","who","get","which","go","me","when","make","can","like","time","no","just","him","know","take","people","into","year","your","good","some","could","them","see","other","than","then","now","look","only","come","its","over","think","also","back","after","use","two","how","our","work","first","well","way","even","new","want","because","any","these","give","day","most","us","quick","brown","fox","jumps","over","lazy","dog","practice","typing","keyboard","shift","letter","adjacent","finger","memory","touch","words","error","correct","speed","words","certificate","training","lesson","exercise","pack","custom","timed","minute","second","paragraph","course","history","grade","class","qwerty","open","typer","civil","engineering","project","blueprint","ai","gemini","vercel"};
}

QString SmartAnalyzer::generateDrill(const QVariantList &worstLetters, int wordCount){
    ensureInited();
    if(worstLetters.isEmpty()) return "";
    QStringList letters;
    for(auto &v: worstLetters){
        if(v.type()==QVariant::List){
            auto lst=v.toList();
            if(!lst.isEmpty()) letters << lst[0].toString().toLower();
        } else if(v.type()==QVariant::String){
            letters << v.toString().toLower();
        } else if(v.type()==QVariant::Map){
            auto m=v.toMap();
            if(m.contains("letter")) letters << m["letter"].toString().toLower();
            else if(m.contains("char")) letters << m["char"].toString().toLower();
        }
        if(letters.size()>=5) break;
    }
    if(letters.isEmpty()) return "";
    auto pool=commonPool();
    QStringList candidates;
    for(auto &w: pool){ for(auto &ch: letters){ if(w.contains(ch, Qt::CaseInsensitive)){ candidates<<w; break; } } }
    if(candidates.size()<20) candidates=pool;
    QStringList out;
    QString prefix;
    for(int i=0;i<qMin(3, letters.size());++i) prefix += letters[i].repeated(4) + " ";
    for(int i=0;i<wordCount;++i){
        if(QRandomGenerator::global()->bounded(100) < 75 && !candidates.isEmpty())
            out << candidates[QRandomGenerator::global()->bounded(candidates.size())];
        else
            out << pool[QRandomGenerator::global()->bounded(pool.size())];
        if(i%7==0 && letters.size()>=2){
            QString bg = letters[QRandomGenerator::global()->bounded(letters.size())] + letters[QRandomGenerator::global()->bounded(letters.size())];
            if(bg[0]!=bg[1]) out.insert(out.size()-1, bg);
        }
    }
    return prefix + "  " + out.join(" ");
}

QVariantMap SmartAnalyzer::analyze(const QString &target, const QString &typed){
    ensureInited();
    QVariantMap rep;
    int n=target.size(), m=typed.size();
    if(n==0){ rep["errors"]=0; rep["accuracy"]=100; return rep; }
    QMap<QString,int> total, mistake;
    QMap<QString,int> bigramTotal, bigramMist;
    QMap<QString,int> catCount;
    QVariantList detailed;
    QMap<QString,int> fingerCount, handCount;
    QVariantList wordErrors;
    int pos=0;
    int i=0;
    int minLen=qMin(n,m);
    while(i < minLen){
        QString exp=target.mid(i,1), got=typed.mid(i,1);
        QString low=exp.toLower();
        if(exp!="\n" && exp!=" ") { total[low]++; if(i>0) bigramTotal[target.mid(i-1,1).toLower()+low]++; }
        if(exp!=got){
            // transposition check
            if(i+1 < minLen && target.mid(i,1)==typed.mid(i+1,1) && target.mid(i+1,1)==typed.mid(i,1)){
                QString exp2=target.mid(i+1,1);
                catCount["transposition"]++;
                QVariantMap d; d["pos"]=i; d["expected"]=exp+exp2; d["typed"]=got+typed.mid(i+1,1);
                d["category"]="transposition";
                d["reason"]=QString("Swapped '%1' → '%2'. Similar bigrams close together.").arg(exp+exp2, got+typed.mid(i+1,1));
                d["suggestion"]=QString("Drill '%1' slowly.").arg(exp+exp2);
                detailed.append(d);
                mistake[low]++; mistake[exp2.toLower()]++;
                auto fe=finger(exp); if(!fe.first.isEmpty()){ handCount[fe.first]++; fingerCount[fe.second]++; }
                auto fe2=finger(exp2); if(!fe2.first.isEmpty()){ handCount[fe2.first]++; fingerCount[fe2.second]++; }
                QString w1=wordAt(target,i), w2=wordAt(typed,i);
                if(!w1.isEmpty() && w1!=w2){ QVariantMap we; we["expected_word"]=w1; we["typed_word"]=w2; wordErrors.append(we); }
                i+=2; continue;
            } else {
                QString prev = i>0 ? target.mid(i-1,1) : "";
                QString nxt = i+1<n ? target.mid(i+1,1) : "";
                auto cls=classify(exp, got, prev, nxt);
                QString cat=cls["category"].toString();
                catCount[cat]++;
                mistake[low]++;
                if(i>0) bigramMist[target.mid(i-1,1).toLower()+low]++;
                auto fe=finger(exp); if(!fe.first.isEmpty()){ handCount[fe.first]++; fingerCount[fe.second]++; }
                QVariantMap d; d["pos"]=i; d["expected"]=exp; d["typed"]=got;
                d["category"]=cat; d["reason"]=cls["reason"]; d["suggestion"]=cls["suggestion"];
                if(cls.contains("distance")) d["distance"]=cls["distance"];
                detailed.append(d);
                QString w1=wordAt(target,i), w2=wordAt(typed,i);
                if(!w1.isEmpty() && w1!=w2){ QVariantMap we; we["expected_word"]=w1; we["typed_word"]=w2; wordErrors.append(we); }
            }
        }
        i++;
    }
    if(m < n){
        for(int j=m;j<n;++j){
            QString exp=target.mid(j,1);
            if(exp=="\n"||exp==" ") continue;
            QString low=exp.toLower(); mistake[low]++; total[low]++; catCount["omission"]++;
            auto fe=finger(exp); if(!fe.first.isEmpty()){ handCount[fe.first]++; fingerCount[fe.second]++; }
            QVariantMap d; d["pos"]=j; d["expected"]=exp; d["typed"]="(missing)"; d["category"]="omission"; d["reason"]=QString("Missing '%1' — early stop.").arg(exp); d["suggestion"]="Complete the line.";
            detailed.append(d);
        }
    } else if(m > n){
        for(int j=n;j<m;++j){
            QString got=typed.mid(j,1);
            if(got=="\n"||got==" ") continue;
            catCount["insertion"]++;
            QVariantMap d; d["pos"]=j; d["expected"]="(none)"; d["typed"]=got; d["category"]="insertion"; d["reason"]=QString("Extra '%1'.").arg(got); d["suggestion"]="Lift fingers.";
            detailed.append(d);
        }
    }
    int mistakeChars=0; for(auto it=mistake.begin(); it!=mistake.end(); ++it) mistakeChars+=it.value();
    double acc = qMax(0.0, (n - mistakeChars) / double(qMax(1,n)) * 100.0);
    // letter stats
    QVariantList worstLetters;
    QMap<double, QString> sorted; // error_rate -> char (approx, handle collisions by tiny offset)
    QVariantMap letterStats;
    for(auto it=total.begin(); it!=total.end(); ++it){
        QString ch=it.key(); int tot=it.value(); int mis=mistake.value(ch,0);
        double rate = mis / double(qMax(1,tot));
        double accCh = (tot-mis)/double(tot)*100;
        QVariantMap st; st["total"]=tot; st["mistakes"]=mis; st["accuracy"]=accCh; st["error_rate"]=rate;
        letterStats[ch]=st;
        if(mis>0) sorted.insert(rate + mis*1e-9, ch); // stable sort
    }
    // include letters that only had mistakes via omission
    for(auto it=mistake.begin(); it!=mistake.end(); ++it){ if(!letterStats.contains(it.key())){ QVariantMap st; st["total"]=0; st["mistakes"]=it.value(); st["accuracy"]=0; st["error_rate"]=1; letterStats[it.key()]=st; sorted.insert(1.0 + it.value()*1e-9, it.key()); } }
    // iterate sorted descending top 7
    auto keys=sorted.keys();
    std::sort(keys.begin(), keys.end(), std::greater<double>());
    for(int k=0;k<qMin(7, keys.size());++k){
        QString ch=sorted[keys[k]];
        QVariantMap entry; entry["letter"]=ch; entry["stats"]=letterStats[ch].toMap();
        worstLetters.append(entry);
    }
    // worst bigrams
    QVariantList worstBigrams;
    QMap<QString,int> bgErr;
    for(auto it=bigramTotal.begin(); it!=bigramTotal.end(); ++it){
        int mis=bigramMist.value(it.key(),0);
        if(mis>0) bgErr[it.key()]=mis;
    }
    // sort by mis descending
    QStringList bgKeys=bgErr.keys();
    std::sort(bgKeys.begin(), bgKeys.end(), [&](const QString &a, const QString &b){ return bgErr[a] > bgErr[b]; });
    for(int k=0;k<qMin(5, bgKeys.size());++k){ QVariantMap e; e["bigram"]=bgKeys[k]; e["count"]=bgErr[bgKeys[k]]; worstBigrams.append(e); }

    // heatmap
    QVariantMap heat;
    for(auto it=letterStats.begin(); it!=letterStats.end(); ++it){
        auto st=it.value().toMap();
        heat[it.key()] = st["error_rate"];
    }
    // suggestions
    QVariantList sugg;
    if(worstLetters.isEmpty()){
        sugg.append("Flawless! No mistakes. Try harder paragraph or longer time limit.");
    } else {
        QStringList topChars;
        for(int k=0;k<qMin(3, worstLetters.size());++k){ auto m=worstLetters[k].toMap(); topChars << "'" + m["letter"].toString() + "'"; }
        sugg.append(QString("Focus letters: %1. These are your weakest keys.").arg(topChars.join(", ")));
        if(catCount.value("adjacent_key",0) >=2) sugg.append(QString("Keyboard adjacency: %1 neighbour-key slips — slow down, ensure correct finger.").arg(catCount["adjacent_key"]));
        if(catCount.value("shift_case",0) >=1) sugg.append("Shift/Caps: case errors — you forget Shift for capitals or Caps Lock is on. Practice \"Aa Bb Cc\" with opposite hand Shift.");
        if(catCount.value("shift_symbol",0) >=1) sugg.append("Symbol Shift: errors on symbols needing Shift (e.g., '1' vs '!'). Drill \"1 ! 1 !\" / \"; : ; :\".");
        if(catCount.value("transposition",0) >=1) sugg.append("Transpositions: swapped letters due to near bigrams. Practice rhythm evenly.");
        if(catCount.value("double_letter",0) >=1) sugg.append("Double letters: rhythm slip on repeated letters. Keep even timing.");
        // hand imbalance
        int left=handCount.value("L",0), right=handCount.value("R",0), tot=left+right;
        if(tot>0){
            double leftPct=left*100.0/tot;
            if(leftPct>=65) sugg.append(QString("Left hand dominant (%1% left). Drill left-hand keys.").arg(int(leftPct)));
            else if(leftPct<=35) sugg.append(QString("Right hand dominant (%1% right). Drill right-hand keys.").arg(int(100-leftPct)));
        }
        if(!worstBigrams.isEmpty()){
            QStringList bgs; for(int k=0;k<qMin(2, worstBigrams.size());++k) bgs << "'" + worstBigrams[k].toMap()["bigram"].toString() + "'";
            sugg.append(QString("Tricky sequences: %1. Practice these bigrams.").arg(bgs.join(", ")));
        }
        sugg.append("Tip: Type 10% slower for 98%+ accuracy — speed follows accuracy.");
    }
    QString drill = generateDrill(worstLetters);
    QString summary;
    if(mistakeChars==0) summary="Perfect! No mistakes.";
    else {
        QStringList cats; for(auto it=catCount.begin(); it!=catCount.end(); ++it) cats << it.key() + "=" + QString::number(it.value());
        QString wl; for(int k=0;k<qMin(3, worstLetters.size());++k) wl += worstLetters[k].toMap()["letter"].toString() + (k<2?",":"");
        summary = QString("%1 mistake(s) — %2% acc. Cats: %3. Weak: %4").arg(detailed.size()).arg(acc,0,'f',1).arg(cats.join(", ")).arg(wl);
    }

    rep["total_chars"]=n; rep["errors"]=detailed.size(); rep["mistakeChars"]=mistakeChars; rep["accuracy"]=acc;
    rep["letterStats"]=letterStats; rep["worstLetters"]=worstLetters; rep["worstBigrams"]=worstBigrams;
    rep["categoryCounts"]=QVariant::fromValue(catCount); rep["detailed"]=detailed; rep["fingerStats"]=QVariant::fromValue(fingerCount); rep["handStats"]=QVariant::fromValue(handCount);
    rep["wordErrors"]=wordErrors; rep["suggestions"]=sugg; rep["drillText"]=drill; rep["keyboardHeat"]=heat; rep["summary"]=summary;
    return rep;
}
