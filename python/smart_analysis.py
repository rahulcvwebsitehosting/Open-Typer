#!/usr/bin/env python3
"""
smart_analysis.py — Smart Typing Mistake Analyzer for Open-Typer
Analyzes *why* you make mistakes, not just *where*.

Features:
 - Per-letter / per-bigram mistake heatmap
 - Keyboard adjacency detection (QWERTY geometry)
 - Shift / Caps / Symbol diagnosis
 - Same-finger / same-hand & transposition detection
 - Similar-word confusion heuristic
 - Generates personalized drills focusing on weakest keys

Standalone — no Tk/Qt dependency.  Import from both Python front-ends and Qt (via py side) or reuse logic in C++.

Author: Muse Spark — for Rahul Shyam Open-Typer 5.3.x
"""

from __future__ import annotations
from collections import Counter, defaultdict
import math
import random
import re

# ---------------------------------------------------------------------------
# Keyboard geometry — QWERTY (US) with stagger.  Coordinates (x, y)
# ---------------------------------------------------------------------------
# Rows split with realistic stagger: numbers  y=0,  q-row y=1,  a-row y=2,  z-row y=3, space y=4
KEY_POS: dict[str, tuple[float, float]] = {}

def _add_row(chars, y, x0, dx=1.0):
    for i, ch in enumerate(chars):
        KEY_POS[ch] = (x0 + i * dx, y)
        # also map uppercase variant to same pos
        if ch.isalpha():
            KEY_POS[ch.upper()] = (x0 + i * dx, y)

# Row 0  ` 1 2 3 4 5 6 7 8 9 0 - =
_add_row(['`','1','2','3','4','5','6','7','8','9','0','-','='], y=0, x0=0)

# Row 1  q w e r t y u i o p [ ] \
_add_row(['q','w','e','r','t','y','u','i','o','p','[',']','\\'], y=1, x0=0.5)

# Row 2  a s d f g h j k l ; '
_add_row(['a','s','d','f','g','h','j','k','l',';','\''], y=2, x0=0.75)

# Row 3  z x c v b n m , . /
_add_row(['z','x','c','v','b','n','m',',','.','/'], y=3, x0=1.25)

# Space
KEY_POS[' '] = (5.5, 4.0)
KEY_POS['\n'] = (13.0, 2.0)  # Enter approx

# ---------------------------------------------------------------------------
# Finger / hand map
# ---------------------------------------------------------------------------
# finger ids: LP=left pinky, LR=left ring, LM=left middle, LI=left index, RI=right index, RM=right middle, RR=right ring, RP=right pinky, TH=thumb
FINGER_MAP: dict[str, tuple[str, str]] = {}  # char -> (hand, finger)
_hand_finger_table = {
    # left hand
    '`': ('L','LP'), '1': ('L','LP'), 'q': ('L','LP'), 'a': ('L','LP'), 'z': ('L','LP'),
    '2': ('L','LR'), 'w': ('L','LR'), 's': ('L','LR'), 'x': ('L','LR'),
    '3': ('L','LM'), 'e': ('L','LM'), 'd': ('L','LM'), 'c': ('L','LM'),
    '4': ('L','LI'), '5': ('L','LI'), 'r': ('L','LI'), 'f': ('L','LI'), 'v': ('L','LI'), 't': ('L','LI'), 'g': ('L','LI'), 'b': ('L','LI'),
    # right hand
    '6': ('R','RI'), '7': ('R','RI'), 'y': ('R','RI'), 'h': ('R','RI'), 'n': ('R','RI'), 'u': ('R','RI'), 'j': ('R','RI'), 'm': ('R','RI'),
    '8': ('R','RM'), 'i': ('R','RM'), 'k': ('R','RM'), ',': ('R','RM'),
    '9': ('R','RR'), 'o': ('R','RR'), 'l': ('R','RR'), '.': ('R','RR'),
    '0': ('R','RP'), '-': ('R','RP'), '=': ('R','RP'), 'p': ('R','RP'), '[': ('R','RP'), ']': ('R','RP'), '\\': ('R','RP'), ';': ('R','RP'), "'": ('R','RP'), '/': ('R','RP'),
    ' ': ('','TH'),
    '\n': ('R','RP'),
}
for ch, hf in _hand_finger_table.items():
    FINGER_MAP[ch] = hf
    FINGER_MAP[ch.upper()] = hf

FINGER_NAME = {
    'LP': 'Left Pinky', 'LR': 'Left Ring', 'LM': 'Left Middle', 'LI': 'Left Index',
    'RI': 'Right Index', 'RM': 'Right Middle', 'RR': 'Right Ring', 'RP': 'Right Pinky',
    'TH': 'Thumb'
}

# ---------------------------------------------------------------------------
# Shift pairs — base -> shifted, and reverse
# ---------------------------------------------------------------------------
BASE_TO_SHIFT = {'`':'~','1':'!','2':'@','3':'#','4':'$','5':'%','6':'^','7':'&','8':'*','9':'(','0':')','-':'_','=':'+','[':'{',']':'}','\\':'|',';':':',"'":'"',',':'<','.':'>','/':'?'}
SHIFT_TO_BASE = {v:k for k,v in BASE_TO_SHIFT.items()}
# For shifted detection we need also letter case: lower -> upper via Shift or Caps
# ---------------------------------------------------------------------------

def _pos(c: str):
    """return (x,y) or None"""
    if not c:
        return None
    # normalize to single char; take first char
    c0 = c[0]
    return KEY_POS.get(c0) or KEY_POS.get(c0.lower())

def distance(c1: str, c2: str) -> float:
    p1 = _pos(c1)
    p2 = _pos(c2)
    if not p1 or not p2:
        return 9.9
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def is_adjacent(c1: str, c2: str, thresh: float = 1.42) -> bool:
    """True if keys are neighbors on QWERTY."""
    if not c1 or not c2:
        return False
    if c1.lower() == c2.lower():
        return False
    d = distance(c1.lower(), c2.lower())
    return 0 < d <= thresh

def finger_of(c: str):
    return FINGER_MAP.get(c) or FINGER_MAP.get(c.lower()) or ('','')

def same_hand(c1: str, c2: str) -> bool:
    h1,_ = finger_of(c1)
    h2,_ = finger_of(c2)
    return h1 != '' and h1 == h2

def same_finger(c1: str, c2: str) -> bool:
    return finger_of(c1) == finger_of(c2) and finger_of(c1) != ('','')

# Precompute adjacency sets for quick lookup
_ADJ_MAP: dict[str, set] = {}
for ch in list(KEY_POS.keys()):
    if len(ch)!=1:
        continue
    s=set()
    for other in list(KEY_POS.keys()):
        if len(other)!=1:
            continue
        if is_adjacent(ch, other):
            s.add(other.lower())
            s.add(other)
    _ADJ_MAP[ch] = s
    _ADJ_MAP[ch.lower()] = s

def neighbors_of(ch: str) -> set:
    return _ADJ_MAP.get(ch, set()) | _ADJ_MAP.get(ch.lower(), set())

# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------
CATEGORY_ADJACENT = "adjacent_key"
CATEGORY_SHIFT_CASE = "shift_case"
CATEGORY_SHIFT_SYMBOL = "shift_symbol"
CATEGORY_TRANSPOSITION = "transposition"
CATEGORY_OMISSION = "omission"
CATEGORY_INSERTION = "insertion"
CATEGORY_DOUBLE = "double_letter"
CATEGORY_OTHER = "other"

def classify_single(exp: str, typed: str, prev_exp: str = "", next_exp: str = "") -> dict:
    """
    Classify a single-character substitution exp -> typed.
    Returns {category, reason, suggestion, distance, same_finger, same_hand}
    """
    if exp == typed:
        return {"category": "correct", "reason": "", "suggestion": ""}

    # Case / shift-symbol checks first (highest explanatory power)
    # 1) Pure case swap (e.g., 'a' -> 'A' or 'A' -> 'a')
    if exp.lower() == typed.lower() and exp != typed:
        if exp.isupper() and typed.islower():
            return {
                "category": CATEGORY_SHIFT_CASE,
                "reason": f"You typed lowercase '{typed}' but expected uppercase '{exp}'. Missed Shift (or Caps Lock off).",
                "suggestion": f"Hold Shift with opposite hand while typing '{exp}'. Practice capital '{exp}' in words.",
                "distance": 0,
                "same_finger": False,
                "same_hand": False,
            }
        else:
            return {
                "category": CATEGORY_SHIFT_CASE,
                "reason": f"You typed uppercase '{typed}' but expected lowercase '{exp}'. Accidental Shift or Caps Lock on.",
                "suggestion": f"Check Caps Lock. Practice keeping Shift released for '{exp}'.",
                "distance": 0,
                "same_finger": False,
                "same_hand": False,
            }

    # 2) Symbol shift miss: exp is shifted symbol, typed is its base ( ! -> 1 )
    if exp in SHIFT_TO_BASE and typed == SHIFT_TO_BASE[exp]:
        return {
            "category": CATEGORY_SHIFT_SYMBOL,
            "reason": f"Expected symbol '{exp}' (Shift + '{typed}') but you typed '{typed}' without Shift.",
            "suggestion": f"Hold Shift + '{typed}' to get '{exp}'. Drill: '{typed} {exp} {typed}{exp}'",
            "distance": 0,
            "same_finger": False,
            "same_hand": False,
        }
    if typed in SHIFT_TO_BASE and exp == SHIFT_TO_BASE[typed]:
        # typed shifted but expected base -> accidental shift
        return {
            "category": CATEGORY_SHIFT_SYMBOL,
            "reason": f"Expected '{exp}' but you typed shifted '{typed}' (Shift + '{exp}') by mistake.",
            "suggestion": f"Release Shift when typing '{exp}'. Drill '{exp}' in isolation.",
            "distance": 0,
            "same_finger": False,
            "same_hand": False,
        }
    # Also direct map: exp is base, typed is its shift, or vice versa
    if BASE_TO_SHIFT.get(exp) == typed:
        return {
            "category": CATEGORY_SHIFT_SYMBOL,
            "reason": f"Expected '{exp}' but you held Shift and typed '{typed}'.",
            "suggestion": f"Don't hold Shift for '{exp}'. Practice distinguishing '{exp}' vs '{typed}'.",
            "distance": 0,
            "same_finger": False,
            "same_hand": False,
        }
    if BASE_TO_SHIFT.get(typed) == exp:
        return {
            "category": CATEGORY_SHIFT_SYMBOL,
            "reason": f"Expected '{exp}' (Shift layer) but you typed base '{typed}'. Hold Shift!",
            "suggestion": f"Shift + '{typed}' → '{exp}'. Repeat 10×.",
            "distance": 0,
            "same_finger": False,
            "same_hand": False,
        }

    # 3) Adjacent key (fat finger)
    if is_adjacent(exp, typed):
        d = distance(exp, typed)
        hf_exp = finger_of(exp)
        hf_typed = finger_of(typed)
        sf = hf_exp == hf_typed
        sh = same_hand(exp, typed)
        hand_msg = "same hand" if sh else "different hand"
        finger_msg = "same finger" if sf else f"{FINGER_NAME.get(hf_exp[1],'')} vs {FINGER_NAME.get(hf_typed[1],'')}"
        return {
            "category": CATEGORY_ADJACENT,
            "reason": f"'{typed}' is next to '{exp}' on QWERTY (distance {d:.1f}). Likely {finger_msg} ({hand_msg}) — wrong finger / fat-finger.",
            "suggestion": f"Slow down on '{exp}'. Focus on precise finger placement: '{exp}' is {FINGER_NAME.get(hf_exp[1],'?')} ({hf_exp[0] or '?'} hand).",
            "distance": d,
            "same_finger": sf,
            "same_hand": sh,
        }

    # 4) Double-letter confusion (omission or doubling)
    if prev_exp == exp or next_exp == exp:
        # expected double letter like "tt" — maybe you missed one or added extra
        return {
            "category": CATEGORY_DOUBLE,
            "reason": f"Double-letter pattern around '{exp}' (e.g., '{prev_exp}{exp}{next_exp}'). Timing/rhythm slip.",
            "suggestion": f"Practice words with double '{exp.lower()}': drills like '..{exp.lower()*3} ..'. Keep steady rhythm.",
            "distance": distance(exp, typed),
            "same_finger": same_finger(exp, typed),
            "same_hand": same_hand(exp, typed),
        }

    # Fallback — other / similar word etc.
    return {
        "category": CATEGORY_OTHER,
        "reason": f"Typed '{typed}' instead of '{exp}'. No simple keyboard explanation — likely similar-word confusion / reading error.",
        "suggestion": f"Practice words with '{exp}' — focus on reading ahead.",
        "distance": distance(exp, typed),
        "same_finger": same_finger(exp, typed),
        "same_hand": same_hand(exp, typed),
    }

# ---------------------------------------------------------------------------
# Word-level heuristics
# ---------------------------------------------------------------------------
def _word_at(text: str, pos: int) -> str:
    """Return word containing pos (alnum+apostrophe)."""
    if not text or pos <0 or pos>=len(text):
        return ""
    # find boundaries
    start = pos
    while start>0 and (text[start-1].isalnum() or text[start-1] in "'-"):
        start -=1
    end = pos
    while end < len(text) and (text[end].isalnum() or text[end] in "'-"):
        end+=1
    return text[start:end]

# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------
class SmartReport:
    """Result container — dict-like but typed."""
    def __init__(self):
        self.total_chars = 0
        self.errors = 0
        self.accuracy = 100.0
        self.letter_stats: dict[str, dict] = {}   # char -> {total, mistakes, acc}
        self.bigram_stats: Counter = Counter()
        self.worst_letters: list[tuple[str, dict]] = []  # [(char, stats), ...] sorted
        self.worst_bigrams: list[tuple[str, int]] = []
        self.category_counts: Counter = Counter()
        self.detailed: list[dict] = []  # per mistake
        self.finger_stats: Counter = Counter()
        self.hand_stats: Counter = Counter()
        self.word_errors: list[dict] = []
        self.suggestions: list[str] = []
        self.drill_text: str = ""
        self.keyboard_heatmap: dict[str, float] = {}  # char -> error rate 0..1
        self.explanations: list[str] = []
        self.summary: str = ""

    def to_dict(self):
        return {
            "total_chars": self.total_chars,
            "errors": self.errors,
            "accuracy": self.accuracy,
            "letter_stats": self.letter_stats,
            "worst_letters": self.worst_letters,
            "worst_bigrams": self.worst_bigrams,
            "category_counts": dict(self.category_counts),
            "detailed": self.detailed,
            "finger_stats": dict(self.finger_stats),
            "hand_stats": dict(self.hand_stats),
            "word_errors": self.word_errors,
            "suggestions": self.suggestions,
            "drill_text": self.drill_text,
            "keyboard_heatmap": self.keyboard_heatmap,
            "explanations": self.explanations,
            "summary": self.summary,
        }

def _generate_drill(worst_letters: list[tuple[str, dict]], num_words: int = 40, word_pool: list[str] | None = None) -> str:
    """Build a personalized drill paragraph focused on worst_letters."""
    if not worst_letters:
        return ""
    letters = [ch for ch,_ in worst_letters[:5]]
    # Filter pool to words containing any of those letters; fallback to generated nonsense bigrams
    if word_pool is None:
        # minimal встроенный pool — reused from open_typer if available
        try:
            from open_typer import COMMON_WORDS as _pool  # type: ignore
            word_pool = _pool
        except Exception:
            word_pool = ["the","and","you","with","have","this","will","your","can","about","would","there","their","what","said","each","which","she","how","time","will","way","many","then","them","write","would","like","so","these","her","long","make","thing","see","him","two","has","look","more","day","could","go","come","did","number","sound","no","most","people","my","over","know","water","than","call","first","who","may","down","side","been","now","find","any","new","work","part","take","get","place","made","live","where","after","back","little","only","round","man","year","came","show","every","good","me","give","our","under","name","very","through","just","form","sentence","great","think","say","help","low","line","differ","turn","cause","much","mean","before","move","right","boy","old","too","same","tell","does","set","three","want","air","well","also","play","small","end","put","home","read","hand","port","large","spell","add","even","land","here","must","big","high","such","follow","act","why","ask","men","change","went","light","kind","off","need","house","picture","try","us","again","animal","point","mother","world","near","build","self","earth","father","head","stand","own","page","should","country","found","answer","school","grow","study","still","learn","plant","cover","food","sun","four","between","state","keep","eye","never","last","let","thought","city","tree","cross","farm","hard","start","might","story","saw","far","sea","draw","left","late","run","dont","while","press","close","night","real","life","few","north","book","carry","took","science","eat","room","friend","began","idea","fish","mountain","stop","once","base","hear","horse","cut","sure","watch","color","face","wood","main","open","seem","together","next","white","children","begin","got","walk","example","ease","paper","group","always","music","those","both","mark","often","letter","until","mile","river","car","feet","care","second","book","carry","took","science","eat","room","friend","began","idea","fish","mountain","stop","once","base","hear","horse","cut","sure","watch","color","face","wood","main","open","seem","together","next","white","children","begin","got","walk","example","ease","paper","group","always","music","those","both","mark","often","letter","until","mile","river","car","feet","care","second"]

        except Exception:
            word_pool = ["apple","error","test","typing","keyboard","practice","shift","letter","adjacent","finger"]
        # ensure we have at least some words containing worst letters
    candidates = [w for w in word_pool if any(ch.lower() in w.lower() for ch in letters)]
    if len(candidates) < 20:
        candidates = word_pool
    # generate paragraph: 50% focused words, 50% random to keep natural
    out=[]
    for _ in range(num_words):
        if random.random() < 0.75 and candidates:
            out.append(random.choice(candidates))
        else:
            out.append(random.choice(word_pool))
    # inject targeted bigrams: e.g., "aa ee rr"
    if len(letters) >= 2:
        targeted_bigrams = [f"{a}{b}" for a in letters[:3] for b in letters[:3] if a!=b][:6]
        # interleave every 7 words
        for i in range(0, len(out), 7):
            if targeted_bigrams:
                out.insert(i, random.choice(targeted_bigrams))
    # also add isolated repeat drills at head: "jjj kkk"
    prefix = " ".join(ch.lower()*4 for ch in letters[:3])
    return prefix + "  " + " ".join(out)

def analyze_text(target: str, typed: str, word_pool: list[str] | None = None) -> SmartReport:
    """
    Main entry.  Compares target vs typed char-by-char (like Tk validator),
    plus advanced detection for transpositions & length mismatches.

    Returns SmartReport.
    """
    rep = SmartReport()
    if not target:
        return rep
    n = len(target)
    m = len(typed)
    rep.total_chars = n
    # Align: we compare up to min(n,m) char-by-char; remainder counts as omissions/insertions
    counter_total: Counter = Counter()
    counter_mistake: Counter = Counter()
    bigram_total: Counter = Counter()
    bigram_mistake: Counter = Counter()
    # For finger/hand
    finger_counter: Counter = Counter()
    hand_counter: Counter = Counter()

    # Detect transpositions: we will scan; if i and i+1 are swapped we count one transposition rather than two adjacent errors
    detailed = []
    i=0
    while i < min(n, m):
        exp = target[i]
        got = typed[i]
        # counters
        low = exp.lower()
        if exp != '\n' and exp != ' ':
            counter_total[low] += 1
            # bigram
            if i>0:
                bg = (target[i-1].lower()+low)
                bigram_total[bg]+=1

        if exp != got:
            # Check transposition: need i+1 within both strings and cross-match
            if i+1 < min(n,m) and target[i] == typed[i+1] and target[i+1] == typed[i]:
                # transposition of two chars
                exp2 = target[i+1]
                rep.category_counts[CATEGORY_TRANSPOSITION] += 1  # count as one event
                d = distance(exp, typed[i])  # distance not really
                # record as one detailed entry covering both positions
                detailed.append({
                    "pos": i,
                    "expected": exp+exp2,
                    "typed": got+typed[i+1],
                    "category": CATEGORY_TRANSPOSITION,
                    "reason": f"Swapped adjacent letters '{exp+exp2}' → '{got+typed[i+1]}'. Words with similar letters close together are easy to transpose — slow down on bigrams.",
                    "suggestion": f"Drill bigram '{exp+exp2}' slowly: type '{exp+exp2} {exp+exp2} {exp+exp2}' 10× with steady rhythm.",
                    "finger": FINGER_NAME.get(finger_of(exp)[1],""),
                    "hand": finger_of(exp)[0],
                })
                # update per-letter mistakes for both chars
                counter_mistake[exp.lower()] +=1
                counter_mistake[exp2.lower()] +=1
                if i>0:
                    bigram_mistake[target[i-1].lower()+low]+=1
                    bigram_mistake[low+exp2.lower()]+=1
                hand, finger = finger_of(exp)
                if hand:
                    hand_counter[hand]+=1
                    finger_counter[finger]+=1
                hand, finger = finger_of(exp2)
                if hand:
                    hand_counter[hand]+=1
                    finger_counter[finger]+=1
                # also account for word confusion
                w_exp = _word_at(target, i)
                w_got = _word_at(typed, i)
                if w_exp and w_got and w_exp != w_got:
                    rep.word_errors.append({"pos": i, "expected_word": w_exp, "typed_word": w_got, "reason": "transposition inside word"})
                i+=2
                continue
            else:
                # single char substitution
                cls = classify_single(exp, got,
                                      prev_exp=target[i-1] if i>0 else "",
                                      next_exp=target[i+1] if i+1<n else "")
                rep.category_counts[cls["category"]] += 1
                # per-letter
                counter_mistake[low]+=1
                if i>0:
                    bigram_mistake[target[i-1].lower()+low]+=1
                # finger/hand from expected char
                hand, finger = finger_of(exp)
                if hand:
                    hand_counter[hand]+=1
                    finger_counter[finger]+=1
                # word context
                w_exp = _word_at(target, i)
                w_got = _word_at(typed, i)
                # if word differs and both are plausible, add note
                word_note = ""
                if w_exp and w_got and w_exp.lower() != w_got.lower():
                    word_note = f" (word: expected '{w_exp}' but typed '{w_got}')"
                detailed.append({
                    "pos": i,
                    "expected": exp,
                    "typed": got,
                    "category": cls["category"],
                    "reason": cls["reason"] + word_note,
                    "suggestion": cls["suggestion"],
                    "distance": cls.get("distance", 0),
                    "same_finger": cls.get("same_finger", False),
                    "same_hand": cls.get("same_hand", False),
                    "finger": FINGER_NAME.get(finger_of(exp)[1],""),
                    "hand": finger_of(exp)[0],
                })
                if w_exp and w_exp!=w_got:
                    rep.word_errors.append({"pos": i, "expected_word": w_exp, "typed_word": w_got, "reason": cls["reason"]})
        i+=1

    # Omissions / insertions for length mismatch
    if m < n:
        # omitted suffix
        for j in range(m, n):
            exp = target[j]
            if exp in ("\n"," "):
                continue
            low = exp.lower()
            counter_mistake[low]+=1
            counter_total[low]+=1
            rep.category_counts[CATEGORY_OMISSION] += 1
            hand, finger = finger_of(exp)
            if hand:
                hand_counter[hand]+=1
                finger_counter[finger]+=1
            detailed.append({
                "pos": j,
                "expected": exp,
                "typed": "(missing)",
                "category": CATEGORY_OMISSION,
                "reason": f"Missing character '{exp}' at end. Did you stop early or delete too much?",
                "suggestion": "Practice completing the line — don't rush the finish.",
                "finger": FINGER_NAME.get(finger_of(exp)[1],""),
                "hand": finger_of(exp)[0],
            })
    elif m > n:
        for j in range(n, m):
            got = typed[j]
            if got in ("\n"," "):
                continue
            rep.category_counts[CATEGORY_INSERTION]+=1
            detailed.append({
                "pos": j,
                "expected": "(none)",
                "typed": got,
                "category": CATEGORY_INSERTION,
                "reason": f"Extra character '{got}' beyond expected text. Likely double-press or didn't stop.",
                "suggestion": "Watch for extra key presses — lift fingers after each tap.",
                "finger": FINGER_NAME.get(finger_of(got)[1],""),
                "hand": finger_of(got)[0],
            })

    rep.errors = len([d for d in detailed if d["category"]!="correct"])
    # Because transposition counts as 1 detailed but 2 letter mistakes, we already accounted. For accuracy we need mistake chars:
    mistake_chars = sum(counter_mistake.values())
    rep.accuracy = max(0.0, (n - mistake_chars)/ max(1,n) * 100.0)
    rep.detailed = detailed
    rep.finger_stats = finger_counter
    rep.hand_stats = hand_counter

    # letter stats
    letter_stats = {}
    for ch, tot in counter_total.items():
        mis = counter_mistake.get(ch, 0)
        acc = (tot - mis)/ tot * 100 if tot else 100
        letter_stats[ch] = {"total": tot, "mistakes": mis, "accuracy": acc, "error_rate": mis/max(1,tot)}
    # also include letters that only appear as mistakes but no total? already counted via suffix; for heatmap need include all a-z
    for ch in map(chr, range(ord('a'), ord('z')+1)):
        if ch not in letter_stats:
            # if never typed but maybe neighbor errors? check if ch had mistakes via adjacency? not needed
            # but include with 0 totals for heatmap completeness
            mis = counter_mistake.get(ch, 0)
            if mis>0:
                letter_stats[ch] = {"total": 0, "mistakes": mis, "accuracy": 0.0, "error_rate": 1.0}

    rep.letter_stats = letter_stats
    # worst letters sorted by error_rate then mistakes
    worst = sorted(letter_stats.items(), key=lambda kv: (kv[1]["error_rate"], kv[1]["mistakes"]), reverse=True)
    # filter to only those with mistakes>0
    worst = [kv for kv in worst if kv[1]["mistakes"]>0]
    rep.worst_letters = worst[:7]  # top 7

    # worst bigrams
    bg_err = []
    for bg, tot in bigram_total.items():
        mis = bigram_mistake.get(bg,0)
        if mis>0:
            bg_err.append((bg, mis, mis/tot))
    bg_err_sorted = sorted(bg_err, key=lambda x: (x[1], x[2]), reverse=True)
    rep.worst_bigrams = [(bg, cnt) for bg,cnt,_ in bg_err_sorted[:5]]
    # also single omitted bigrams?

    # keyboard heatmap = error_rate per char (0..1)
    hm = {}
    max_mis = max((v["mistakes"] for v in letter_stats.values()), default=1)
    for ch, st in letter_stats.items():
        # normalized by worst
        hm[ch] = st["error_rate"]  # 0..1
        # also consider absolute for intensity
    # include shift symbols/punct too where mistakes happened
    for ch in set(counter_mistake.keys()):
        if ch not in hm:
            hm[ch] = 1.0
    rep.keyboard_heatmap = hm

    # suggestions
    suggestions: list[str] = []
    if not worst:
        suggestions.append("Flawless! No mistakes detected. Try a harder paragraph or increase time limit to push speed.")
    else:
        top_chars = ", ".join(f"'{ch}' ({st['mistakes']}/{st['total']} errors, {st['accuracy']:.0f}% acc)" for ch, st in worst[:3])
        suggestions.append(f"Focus letters: {top_chars}. These are your weakest keys.")

        # category based suggestions
        cnt_adj = rep.category_counts.get(CATEGORY_ADJACENT, 0)
        cnt_shift_case = rep.category_counts.get(CATEGORY_SHIFT_CASE, 0)
        cnt_shift_sym = rep.category_counts.get(CATEGORY_SHIFT_SYMBOL, 0)
        cnt_trans = rep.category_counts.get(CATEGORY_TRANSPOSITION, 0)
        cnt_double = rep.category_counts.get(CATEGORY_DOUBLE, 0)
        cnt_other = rep.category_counts.get(CATEGORY_OTHER, 0)

        if cnt_adj >= 2:
            # find most common adjacent offending pair
            adj_samples = [d for d in detailed if d["category"]==CATEGORY_ADJACENT][:2]
            ex = ", ".join(f"'{d['expected']}'→'{d['typed']}'" for d in adj_samples)
            suggestions.append(f"Keyboard adjacency: {cnt_adj} errors are neighboring keys ({ex}). Example '{ex}': slow down, ensure correct finger reaches. Try tactile drills with isolated keys.")
        if cnt_shift_case >=1:
            suggestions.append(f"Shift/Caps: {cnt_shift_case} case errors. You {'forget Shift for capitals' if any('Missed Shift' in d['reason'] for d in detailed) else 'hit Shift accidentally'}. Practice: type \"Aa Bb Cc\" repeatedly, checking Shift with opposite hand.")
            # caps lock heuristic
            missed = sum(1 for d in detailed if d["category"]==CATEGORY_SHIFT_CASE and "Missed" in d["reason"])
            accidental = cnt_shift_case - missed
            if missed >=2 and accidental==0:
                suggestions.append("All case errors are missing capitals → likely Caps Lock off but you forget Shift. Drill capitals at sentence starts.")
            elif accidental >=2 and missed==0:
                suggestions.append("Caps Lock may be ON (all accidental capitals). Tap Caps Lock to turn off and practice lowercases.")
        if cnt_shift_sym>=1:
            syms = ", ".join(set(d["expected"] for d in detailed if d["category"]==CATEGORY_SHIFT_SYMBOL))
            suggestions.append(f"Symbol Shift: {cnt_shift_sym} errors on symbols {syms}. Symbols need Shift + base key. Drill each: type \"1 ! 1 !\" / \"; : ; :\" etc.")
        if cnt_trans>=1:
            suggestions.append(f"Transpositions: {cnt_trans} swapped letters. Caused by similar bigrams close together (e.g., 'teh' vs 'the'). Practice rhythm: type bigrams slowly and evenly.")
        if cnt_double>=1:
            suggestions.append(f"Double letters: {cnt_double} slips on repeated letters. Keep even timing on doubles — don't rush the second tap.")
        # hand/finger imbalance
        if hand_counter:
            total_hand = sum(hand_counter.values())
            left = hand_counter.get('L',0)
            right = hand_counter.get('R',0)
            if total_hand>0:
                left_pct = left/total_hand*100
                if left_pct >= 65:
                    suggestions.append(f"Left hand dominant errors ({left_pct:.0f}% left). Your left hand ({FINGER_NAME.get('LI','')} etc.) needs precision work.")
                elif left_pct <= 35:
                    suggestions.append(f"Right hand dominant errors ({100-left_pct:.0f}% right). Focus right-hand drills (y, u, i, o, p, h, j, k, l).")
        if finger_counter:
            worst_finger = finger_counter.most_common(1)[0]
            freq = worst_finger[0]
            cnt = worst_finger[1]
            if cnt >=2:
                suggestions.append(f"Weakest finger: {FINGER_NAME.get(freq,'?')} ({cnt} errors). Isolate drills for that finger's keys.")
        # bigram suggestion
        if rep.worst_bigrams:
            bg_txt = ", ".join(f"'{bg}' ({cnt} slips)" for bg,cnt in rep.worst_bigrams[:2])
            suggestions.append(f"Tricky sequences: {bg_txt}. Practice these bigrams in words.")

        # generic
        suggestions.append("Tip: Type 10% slower and aim for 98%+ accuracy — speed follows accuracy. Use 'Practice Drill' below for targeted reps.")

    rep.suggestions = suggestions

    # drill text
    rep.drill_text = _generate_drill(worst, word_pool=word_pool) if worst else ""

    # explanations list
    rep.explanations = [d["reason"] for d in detailed]

    # summary
    if rep.errors ==0:
        rep.summary = "Perfect! No mistakes."
    else:
        top = ", ".join(f"{k}={v}" for k,v in rep.category_counts.most_common(3))
        worst_letter_str = ", ".join(ch for ch,_ in worst[:3]) if worst else "?"
        rep.summary = f"{rep.errors} mistake(s) — Accuracy {rep.accuracy:.1f}%. Categories: {top}. Weakest: {worst_letter_str}."

    return rep

# ---------------------------------------------------------------------------
# Aggregate / history (persistent per-user)
# ---------------------------------------------------------------------------
class GlobalAnalyzer:
    """Accumulates letter stats across multiple exercises (in-memory)."""
    def __init__(self):
        self.total_counter: Counter = Counter()
        self.mistake_counter: Counter = Counter()
        self.reports: list[SmartReport] = []
        self.bigram_counter: Counter = Counter()
        self.bigram_mistakes: Counter = Counter()

    def add_report(self, rep: SmartReport):
        self.reports.append(rep)
        for ch, st in rep.letter_stats.items():
            self.total_counter[ch] += st["total"]
            self.mistake_counter[ch] += st["mistakes"]
        for bg, cnt in rep.worst_bigrams:
            self.bigram_mistakes[bg]+=cnt

    def aggregated_worst(self, topn=7):
        stats=[]
        for ch, tot in self.total_counter.items():
            mis = self.mistake_counter.get(ch,0)
            if mis==0:
                continue
            acc = (tot-mis)/tot*100 if tot else 0
            stats.append((ch, {"total": tot, "mistakes": mis, "accuracy": acc, "error_rate": mis/max(1,tot)}))
        stats.sort(key=lambda kv: (kv[1]["error_rate"], kv[1]["mistakes"]), reverse=True)
        return stats[:topn]

    def overall_accuracy(self):
        tot = sum(self.total_counter.values())
        mis = sum(self.mistake_counter.values())
        return (tot-mis)/max(1,tot)*100

# Singleton for convenience
_global = GlobalAnalyzer()
def get_global_analyzer() -> GlobalAnalyzer:
    return _global

# ---------------------------------------------------------------------------
# Convenience: one-liner API for UI
# ---------------------------------------------------------------------------
def quick_analysis(target: str, typed: str) -> dict:
    """Return dict suitable for JSON/QML."""
    rep = analyze_text(target, typed)
    # also feed global
    try:
        get_global_analyzer().add_report(rep)
    except Exception:
        pass
    return rep.to_dict()

# ---------------------------------------------------------------------------
# Test / CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        ("hello world", "hwllo world"),  # adjacent? e->w? actually e vs w adjacent
        ("Hello World", "hello world"),  # shift case
        ("Test 123! @", "Test 1231 @"),  # shift symbol ! -> 1
        ("the quick brown", "teh quick borwn"),  # transposition
        ("apple banana", "aple banana"),  # double omission
        ("QWERTYUIOP", "QWERTYUIOP"),  # perfect
    ]
    for tgt, typ in tests:
        print(f"\nTarget: {tgt!r}\nTyped : {typ!r}")
        r = analyze_text(tgt, typ)
        print(f"  {r.summary}")
        for d in r.detailed:
            print(f"    {d['expected']!r}→{d['typed']!r}  {d['category']}  | {d['reason']}")
        print(f"  Suggestions: {r.suggestions[0] if r.suggestions else ''}")
        print(f"  Drill: {r.drill_text[:60]}")
