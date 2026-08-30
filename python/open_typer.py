#!/usr/bin/env python3
"""
Open-Typer 5.3.0 — Real Typing Tutor by Rahul Shyam
Tkinter implementation that mirrors the Qt/QML Open-Typer logic.
Pack parsing based on ConfigParser.cpp logic.
"""
import os, sys, time, webbrowser, random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Smart Analysis engine (isolated, does not disturb timed para) ---
try:
    # when run as `python -m python.open_typer` or `python open_typer.py`
    from python.smart_analysis import analyze_text, get_global_analyzer  # type: ignore
    SMART_AVAILABLE = True
except Exception:
    try:
        from smart_analysis import analyze_text, get_global_analyzer  # type: ignore
        SMART_AVAILABLE = True
    except Exception as _e:
        SMART_AVAILABLE = False
        analyze_text = None  # type: ignore
        def get_global_analyzer():  # type: ignore
            return None
        print(f"[SmartAnalysis] disabled: {_e}")

# --- Branding ---
VERSION = "5.3.2"
AUTHOR = "Rahul Shyam"
PORTFOLIO = "https://rahulshyam-portfolio.vercel.app/"
GITHUB = "https://github.com/rahulcvwebsitehosting/Open-Typer"
EMAIL = "rahulshyamcv@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/rahulshyamcivil/"
X_URL = "https://x.com/RahulShyamCv"
INSTA = "https://www.instagram.com/rahulcvjps/"
THREADS = "https://www.threads.net/@RahulCvJPS"
PHONE = "+91 73051 69964"
WA = "https://wa.me/917305169964"

# --- LiveChat 1000 most common words (sample 400 + blog flavor) ---
COMMON_WORDS = """the be to of and a in that have I it for not on with he as you do at this but his by from they we say her she or an will my one all would there their what so up out if about who get which go me when make can like time no just him know take people into year your good some could them see other than then now look only come its over think also back after use two how our work first well way even new want because any these give day most us is are was were has had been will would can could should may might must page self read give eat beauty mark does bring decide body some once got sit customer support chat live agent service business help team product sales marketing enterprise pricing integration shopify wordpress wix webflow whatsapp messenger mailchimp helpdesk inbox revenue ai agent text knowledge base tour features channels ecommerce education finance help center success blog partner api system status typing speed test words accuracy certificate time minute second paragraph course training lesson exercise history grade class pack keyboard layout language theme dark light font color custom timed words per minute characters per second error correct mistake word sentence text touch word count download instant scale social piece located solid inside was walk feel follow all week also were experience know want find learn practice muscle memory touch typing finger layout qwerty dvorak ergonomics speed test challenge course training certificate bronze silver gold ribbon medal level school grade adult professional dispatch advanced journey hello world quick brown fox jumps over lazy dog practice makes perfect typing tutor keyboard open typer civil engineering portfolio project blueprint neobrutalist ai gemini vercel firebase supabase react vite tailwind framer motion cloud run vision fallguard fabricscan autobom study sense civilog hostel planner sehatam tunnel viz buildflow resume crafter""".split()

CERT_THRESHOLDS = {
    "Gold": (350, 99.5),
    "Silver": (250, 98.5),
    "Bronze": (200, 96.5),
}

def wpm_calc(correct_chars, elapsed_sec):
    if elapsed_sec <=0:
        return 0
    return (correct_chars/5) / (elapsed_sec/60)

def cpm_calc(correct_chars, elapsed_sec):
    if elapsed_sec <=0:
        return 0
    return correct_chars / (elapsed_sec/60)

def cert_for(cpm, acc):
    for name in ["Gold","Silver","Bronze"]:
        cpm_thr, acc_thr = CERT_THRESHOLDS[name]
        if cpm >= cpm_thr and acc >= acc_thr:
            return name
    return None

def generate_random_words(num_words=50, word_pool=None):
    pool = word_pool or COMMON_WORDS
    return " ".join(random.choice(pool) for _ in range(num_words))

def generate_random_para(target_chars=300, source="words"):
    # source: "words" = LiveChat random words
    # "prose" = continuous pack prose
    # For words, generate until target_chars
    if source=="words":
        words=[]
        while len(" ".join(words)) < target_chars:
            words.append(random.choice(COMMON_WORDS))
        txt=" ".join(words)
        # Trim to target
        return txt[:target_chars].rsplit(" ",1)[0] if len(txt)>target_chars else txt
    else:
        # prose will be handled by caller concatenating pack texts
        return generate_random_words(target_chars//5)

def resource_path(relative):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, relative)

def find_packs_dir():
    candidates = [
        resource_path("res/packs"),
        resource_path("../res/packs"),
        os.path.join(os.path.dirname(__file__), "..", "..", "Open-Typer-master", "Open-Typer-master", "res", "packs"),
        r"C:\Users\saini\Downloads\Open-Typer-master\Open-Typer-master\res\packs",
        "res/packs",
        "../res/packs",
    ]
    for c in candidates:
        c = os.path.abspath(c)
        if os.path.isdir(c) and any(os.path.isfile(os.path.join(c, f)) for f in os.listdir(c)):
            # check has pack files
            if any(not f.endswith(".qrc") for f in os.listdir(c)):
                return c
    return None

def parse_pack_line(line):
    line=line.strip()
    if not line or line.startswith("#"):
        return None
    # Find space that separates attributes and text
    # Attributes are after ; until space
    try:
        # Find first space after ;
        semi = line.find(";")
        if semi==-1:
            return None
        space = line.find(" ", semi)
        if space==-1:
            # no text? maybe empty
            attrs = line[semi+1:]
            raw = ""
        else:
            attrs = line[semi+1:space]
            raw = line[space+1:]
        # attrs is like "120,60" or "120,60,wxo" etc
        parts = attrs.split(",")
        # repeatLimit = parts[0] if len>0, lineLength parts[1], desc parts[2] if exists
        # Find id part before :
        colon = line.find(":")
        if colon==-1:
            return None
        id_part = line[:colon]  # like "1.1.1"
        ids = id_part.split(".")
        if len(ids)!=3:
            return None
        lesson, sub, ex = map(int, ids)
        # repeat config before ;
        repeat_cfg = line[colon+1:semi]  # like "1,w" or "0,0"
        repeat_parts = repeat_cfg.split(",")
        repeat = repeat_parts[0]=="1"
        repeat_type = repeat_parts[1] if len(repeat_parts)>1 else ""
        # raw text may contain escaped \n? In ConfigParser generateText handles \n and repeating
        # For python, handle \n literally? In packs, raw uses actual text with spaces, not escaped
        # But generateText also handles repeating words if repeat
        # Simplify: if repeat and repeat_type=="w", we need to expand raw words to limit
        # For now, handle repeat
        text = generate_text(raw, repeat, repeat_type, int(parts[0]) if parts and parts[0].isdigit() else 0)
        # Also handle \n escapes in raw? ConfigParser: generateText also converts \\n to newline when not repeat
        # Our raw may contain literal "\n"?? Not in these packs, but handle
        text = text.replace("\\n", "\n")
        # Also line wrapping is done later by initExercise, but we will just return text for UI wrapping
        # desc is parts[2] if len>2 else ""
        desc = parts[2] if len(parts)>2 else ""
        return {
            "lesson": lesson,
            "sub": sub,
            "ex": ex,
            "repeat": repeat,
            "repeat_type": repeat_type,
            "limit": int(parts[0]) if parts[0].isdigit() else 120,
            "line_len": int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 60,
            "desc": desc,
            "raw": raw,
            "text": text
        }
    except Exception as e:
        print(f"parse error {line}: {e}")
        return None

def generate_text(rawText, repeat, repeatType, repeatLimit):
    if repeat and repeatType=="w":
        if not rawText:
            return ""
        words = rawText.split()
        if not words:
            return ""
        out=""
        i=0
        while True:
            nxt = words[i % len(words)]
            space = 1 if out else 0
            if len(out)+space+len(nxt) <= repeatLimit:
                if space:
                    out+=" "
                out+=nxt
            else:
                return out
            i+=1
            if i> len(words) and len(out)>=repeatLimit:
                break
        return out
    else:
        out=""
        i=0
        while i < len(rawText):
            if rawText[i]=="\\" and i+1 < len(rawText) and rawText[i+1]=="n":
                out+="\n"
                i+=2
            else:
                out+=rawText[i]
                i+=1
        return out

def load_packs(packs_dir):
    packs={}
    if not packs_dir or not os.path.isdir(packs_dir):
        return packs
    for fname in os.listdir(packs_dir):
        if fname.endswith(".qrc"):
            continue
        fpath=os.path.join(packs_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                lines=f.readlines()
            entries=[]
            for l in lines:
                p=parse_pack_line(l)
                if p:
                    entries.append(p)
            if entries:
                packs[fname]=entries
        except Exception as e:
            print(f"Failed load {fname}: {e}")
    return packs

class TimedParaDialog(tk.Toplevel):
    """Dialog for Para + Time Limit — inspired by typing.com (1/3/5 min) / LiveChat (60s) / Typewizz (1 min cert)"""
    def __init__(self, parent, packs):
        super().__init__(parent)
        self.title("Paragraph Time Attack — Open-Typer")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(parent); self.grab_set()
        self.result=None
        self.packs=packs
        frm=ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Para + Time Limit — Typing Speed Test", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(frm, text="Like typing.com (1/3/5 min) • LiveChat (60s random words) • Typewizz (1 min cert)", font=("Segoe UI", 8), foreground="#64748b").pack(anchor="w")
        # Time
        tf=ttk.LabelFrame(frm, text="Time limit", padding=8)
        tf.pack(fill="x", pady=8)
        self.time_var=tk.StringVar(value="60s")
        times=["15s","30s","60s","2m30s","3 min","5 min","10 min","Custom"]
        self.time_combo=ttk.Combobox(tf, values=times, textvariable=self.time_var, state="readonly", width=12)
        self.time_combo.pack(side="left")
        self.time_combo.bind("<<ComboboxSelected>>", self._on_time)
        self.custom_min=tk.IntVar(value=1); self.custom_sec=tk.IntVar(value=0)
        cf=ttk.Frame(tf); cf.pack(side="left", padx=12)
        ttk.Label(cf, text="Min:").pack(side="left")
        ttk.Spinbox(cf, from_=0, to=60, textvariable=self.custom_min, width=4, state="disabled").pack(side="left", padx=4)
        ttk.Label(cf, text="Sec:").pack(side="left")
        ttk.Spinbox(cf, from_=0, to=59, textvariable=self.custom_sec, width=4, state="disabled").pack(side="left", padx=4)
        self.custom_frame=cf
        # Source
        sf=ttk.LabelFrame(frm, text="Paragraph source", padding=8)
        sf.pack(fill="x", pady=8)
        self.source_var=tk.StringVar(value="Paragraph Prose (Typewizz continuous)")
        sources=["Random Words — 1000 common (LiveChat)", "Paragraph Prose (Typewizz continuous)", "Current Exercise (pack)", "Custom File"]
        self.source_combo=ttk.Combobox(sf, values=sources, textvariable=self.source_var, state="readonly", width=40)
        self.source_combo.pack(fill="x")
        # Length
        lf=ttk.LabelFrame(frm, text="Paragraph length", padding=8)
        lf.pack(fill="x", pady=8)
        self.len_var=tk.StringVar(value="Medium — ~300 chars (60s)")
        lens=["Short — ~150 chars (15-30s)", "Medium — ~300 chars (60s)", "Long — ~600 chars (2-5 min)", "Full Page — ~1000 chars (no timer)"]
        self.len_combo=ttk.Combobox(lf, values=lens, textvariable=self.len_var, state="readonly", width=40)
        self.len_combo.pack(fill="x")
        ttk.Label(lf, text="For 60s at 60 WPM you need ~300 chars. Long ensures you won't run out.", font=("Segoe UI", 7), foreground="#64748b").pack(anchor="w", pady=(4,0))
        # Buttons
        bf=ttk.Frame(frm); bf.pack(fill="x", pady=12)
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bf, text="Start Test ➤", style="Accent.TButton", command=self._on_ok).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._on_ok())
        # Center
        self.update_idletasks(); x=parent.winfo_x()+(parent.winfo_width()-self.winfo_width())//2; y=parent.winfo_y()+(parent.winfo_height()-self.winfo_height())//2; self.geometry(f"+{x}+{y}")

    def _on_time(self, e=None):
        is_custom = self.time_var.get()=="Custom"
        state="normal" if is_custom else "disabled"
        for w in self.custom_frame.winfo_children():
            if isinstance(w, ttk.Spinbox):
                w.config(state=state)

    def _on_ok(self):
        # parse time
        mapping={"15s":15,"30s":30,"60s":60,"2m30s":150,"3 min":180,"5 min":300,"10 min":600}
        t=self.time_var.get()
        if t=="Custom":
            secs=self.custom_min.get()*60+self.custom_sec.get()
            if secs<5:
                messagebox.showwarning("Invalid", "Custom time must be >=5 seconds")
                return
        else:
            secs=mapping.get(t,60)
        # length
        len_map={"Short — ~150 chars (15-30s)":150,"Medium — ~300 chars (60s)":300,"Long — ~600 chars (2-5 min)":600,"Full Page — ~1000 chars (no timer)":1000}
        target=len_map.get(self.len_var.get(),300)
        # if Full Page -> untimed
        if "Full Page" in self.len_var.get():
            secs=0
        source=self.source_var.get()
        self.result=(secs, source, target)
        self.destroy()

    def get(self):
        self.wait_window()
        return self.result


# ── Smart Analysis Dialog — isolated from timed-para logic ─────────
class SmartAnalysisDialog(tk.Toplevel):
    """Shows which letters you flub most + *why* (adjacent key / Shift / caps / transposition)."""
    def __init__(self, parent, target: str, typed: str, elapsed: float = 0):
        super().__init__(parent)
        self.title("🧠 Smart Analysis — Why You Make Mistakes")
        self.geometry("860x680")
        self.minsize(780, 620)
        self.transient(parent)
        self.grab_set()
        self.target = target
        self.typed = typed
        self.elapsed = elapsed

        # header
        hdr = tk.Frame(self, bg="#0f172a", height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🧠 Smart Mistake Analysis", fg="white", bg="#0f172a", font=("Segoe UI", 13, "bold")).pack(side="left", padx=14, pady=8)
        tk.Label(hdr, text="reads which letters you miss + diagnoses keyboard pattern & shift/caps", fg="#93c5fd", bg="#0f172a", font=("Segoe UI", 8)).pack(side="left")

        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)

        # compute report
        if SMART_AVAILABLE and analyze_text:
            try:
                self.report = analyze_text(target, typed)
            except Exception as e:
                messagebox.showerror("Analysis error", str(e))
                self.report = None
        else:
            # fallback mini analysis without smart_analysis module (should not happen)
            self.report = None

        if not self.report or not target:
            ttk.Label(outer, text="Not enough data — finish an exercise first.").pack(pady=40)
            ttk.Button(outer, text="Close", command=self.destroy).pack()
            return

        # Summary bar
        acc = self.report.accuracy if hasattr(self.report, 'accuracy') else self.report.get('accuracy', 0)
        errs = self.report.errors if hasattr(self.report, 'errors') else self.report.get('errors', 0)
        summ = self.report.summary if hasattr(self.report, 'summary') else self.report.get('summary','')
        sum_fr = tk.Frame(outer, bg="#eff6ff", bd=1, relief="solid")
        sum_fr.pack(fill="x", pady=(0,8))
        tk.Label(sum_fr, text=f"Accuracy {acc:.1f}%   Errors: {errs}   Time: {elapsed:.1f}s", bg="#eff6ff", fg="#0f172a", font=("Consolas", 10, "bold")).pack(side="left", padx=10, pady=6)
        tk.Label(sum_fr, text=summ[:90], bg="#eff6ff", fg="#475569", font=("Segoe UI", 8)).pack(side="left", padx=8)

        # Notebook tabs
        nb = ttk.Notebook(outer)
        nb.pack(fill="both", expand=True)

        # --- Tab 1: Worst letters ---
        tab1 = ttk.Frame(nb, padding=10)
        nb.add(tab1, text="  🔤 Worst Letters  ")
        self._build_worst_tab(tab1)

        # --- Tab 2: Why? (category breakdown) ---
        tab2 = ttk.Frame(nb, padding=10)
        nb.add(tab2, text="  🔍 Why You Mistake  ")
        self._build_why_tab(tab2)

        # --- Tab 3: Keyboard heatmap ---
        tab3 = ttk.Frame(nb, padding=8)
        nb.add(tab3, text="  ⌨ Keyboard Pattern  ")
        self._build_keyboard_tab(tab3)

        # --- Tab 4: Suggestions + Drill ---
        tab4 = ttk.Frame(nb, padding=10)
        nb.add(tab4, text="  💡 Practice Drill  ")
        self._build_drill_tab(tab4)

        # bottom buttons
        bf = ttk.Frame(outer)
        bf.pack(fill="x", pady=(8,0))
        ttk.Button(bf, text="📋 Copy Summary", command=self._copy_summary).pack(side="left", padx=4)
        ttk.Button(bf, text="Close", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bf, text="★ Practice Drill →", style="Accent.TButton", command=self._start_drill).pack(side="right", padx=4)
        self.bind("<Escape>", lambda e: self.destroy())
        # store parent for drill launch
        self._parent_app = parent

    def _build_worst_tab(self, parent):
        r = self.report
        wl = r.worst_letters if hasattr(r,'worst_letters') else r.get('worst_letters',[])
        if not wl:
            ttk.Label(parent, text="No letter mistakes — perfect run! 🎉", font=("Segoe UI", 11)).pack(pady=20)
            return
        # header
        ttk.Label(parent, text="Letters you miss most (error rate)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,6))
        # canvas bar chart
        cv = tk.Canvas(parent, height=180, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        cv.pack(fill="x", pady=4)
        # compute max
        max_rate = max(s["error_rate"] for _,s in wl) if wl else 1
        max_mis = max(s["mistakes"] for _,s in wl) if wl else 1
        w = 760
        bar_h = 22
        y0=10
        for idx,(ch, st) in enumerate(wl):
            rate = st["error_rate"]
            mis = st["mistakes"]
            tot = st["total"]
            acc = st["accuracy"]
            bar_w = int((rate/max_rate)* 520) if max_rate>0 else 0
            y = y0 + idx*(bar_h+8)
            # label
            cv.create_text(14, y+bar_h//2, text=f"'{ch}'", anchor="w", font=("Consolas", 11, "bold"), fill="#0f172a")
            # bar bg
            cv.create_rectangle(60, y, 580, y+bar_h, fill="#f1f5f9", outline="#e2e8f0")
            # bar fill color by severity
            col = "#ef4444" if rate>0.4 else "#f97316" if rate>0.2 else "#eab308"
            cv.create_rectangle(60, y, 60+bar_w, y+bar_h, fill=col, outline="")
            cv.create_text(62, y+bar_h//2, text=f" {rate*100:.0f}%", anchor="w", font=("Segoe UI", 8, "bold"), fill="white" if bar_w>40 else "#0f172a")
            # stats
            cv.create_text(590, y+bar_h//2, text=f"{mis}/{tot}  {acc:.0f}% acc", anchor="w", font=("Segoe UI", 8), fill="#475569")
            if y+bar_h > 170:
                break
        # table of worst bigrams
        worst_bg = r.worst_bigrams if hasattr(r,'worst_bigrams') else r.get('worst_bigrams',[])
        if worst_bg:
            ttk.Label(parent, text="Tricky bigrams (two-letter sequences you flub):", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10,2))
            ttk.Label(parent, text=", ".join(f"'{bg}' ({cnt}×)" for bg,cnt in worst_bg), font=("Consolas", 9), foreground="#334155", wraplength=740, justify="left").pack(anchor="w")
        # finger/hand
        hand = r.hand_stats if hasattr(r,'hand_stats') else r.get('hand_stats',{})
        finger = r.finger_stats if hasattr(r,'finger_stats') else r.get('finger_stats',{})
        if hand:
            left = hand.get('L',0); right = hand.get('R',0); tot = left+right or 1
            ttk.Label(parent, text=f"Hand balance: Left {left} ({left/tot*100:.0f}%)  •  Right {right} ({right/tot*100:.0f}%)", font=("Segoe UI", 8), foreground="#64748b").pack(anchor="w", pady=(6,0))
        if finger:
            worst_f = max(finger, key=lambda k: finger[k]) if finger else None
            if worst_f:
                names = {"LP":"Left Pinky","LR":"Left Ring","LM":"Left Middle","LI":"Left Index","RI":"Right Index","RM":"Right Middle","RR":"Right Ring","RP":"Right Pinky"}
                ttk.Label(parent, text=f"Weakest finger: {names.get(worst_f, worst_f)} ({finger[worst_f]} errors)", font=("Segoe UI", 8, "bold"), foreground="#0f172a").pack(anchor="w")

    def _build_why_tab(self, parent):
        r = self.report
        cat = r.category_counts if hasattr(r,'category_counts') else r.get('category_counts',{})
        detailed = r.detailed if hasattr(r,'detailed') else r.get('detailed',[])
        if not detailed:
            ttk.Label(parent, text="No mistakes to diagnose.").pack(pady=20)
            return
        # category counts bar-like list
        ttk.Label(parent, text="Root cause breakdown — *why* each mistake happened:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,6))
        label_map = {
            "adjacent_key": "⌨ Adjacent / fat-finger (neighbour key)",
            "shift_case": "⇧ Shift / Caps (wrong case)",
            "shift_symbol": "⇧ Symbol Shift (e.g., '1' vs '!')",
            "transposition": "⇄ Transposition (swapped letters)",
            "double_letter": "⧉ Double-letter timing",
            "omission": "∅ Omission / early stop",
            "insertion": "＋ Insertion / double-press",
            "other": "？ Other / reading error"
        }
        total = sum(cat.values()) or 1
        for k in ["adjacent_key","shift_case","shift_symbol","transposition","double_letter","omission","insertion","other"]:
            v = cat.get(k,0)
            if v==0:
                continue
            pct = v/total*100
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label_map.get(k,k), width=42, font=("Segoe UI", 9)).pack(side="left")
            # mini bar
            cv = tk.Canvas(row, width=140, height=14, bg="white", highlightthickness=0)
            cv.pack(side="left", padx=4)
            cv.create_rectangle(0,0, int(pct/100*140),14, fill="#0ea5e9" if k=="adjacent_key" else "#8b5cf6" if "shift" in k else "#f59e0b" if k=="transposition" else "#94a3b8", outline="")
            ttk.Label(row, text=f"{v} ({pct:.0f}%)", font=("Consolas", 9, "bold")).pack(side="left", padx=6)

        # scrollable detailed list
        ttk.Label(parent, text="Each mistake explained:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10,4))
        txt = tk.Text(parent, wrap="word", height=14, font=("Segoe UI", 9), bg="white", relief="solid", bd=1, padx=8, pady=6)
        txt.pack(fill="both", expand=True)
        for d in detailed[:18]:
            pos = d.get('pos',0)
            exp = d.get('expected','')
            got = d.get('typed','')
            why = d.get('reason','')
            cat_s = d.get('category','')
            txt.insert("end", f"• pos {pos}: '{exp}' → '{got}'  [{cat_s}]\n", "hdr")
            txt.insert("end", f"   {why}\n")
            sug = d.get('suggestion','')
            if sug:
                txt.insert("end", f"   → {sug}\n")
            txt.insert("end", "\n")
        txt.tag_config("hdr", font=("Consolas", 9, "bold"), foreground="#0f172a")
        txt.config(state="disabled")

    def _build_keyboard_tab(self, parent):
        r = self.report
        hm = r.keyboard_heatmap if hasattr(r,'keyboard_heatmap') else r.get('keyboard_heatmap',{})
        ttk.Label(parent, text="QWERTY heatmap — red = you hit this key wrong often. Darker = worse.", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(parent, text="Tip: Adjacent-key errors happen when two keys are ~1 key apart. Shift errors = missed Shift for capitals/symbols.", font=("Segoe UI", 8), foreground="#64748b", wraplength=720, justify="left").pack(anchor="w", pady=(2,6))
        cv = tk.Canvas(parent, bg="#f8fafc", highlightthickness=1, highlightbackground="#cbd5e1", height=220)
        cv.pack(fill="x", pady=4)
        # draw keyboard schematic: 4 rows
        rows = [
            list("`1234567890-="),
            list("qwertyuiop[]\\"),
            list("asdfghjkl;'"),
            list("zxcvbnm,./"),
        ]
        x0, y0 = 12, 12
        key_w, key_h, gap = 44, 36, 6
        row_xoff = [0, 22, 32, 54]
        for ri, row in enumerate(rows):
            y = y0 + ri*(key_h+gap)
            x = x0 + row_xoff[ri]
            for ch in row:
                rate = hm.get(ch, 0) or hm.get(ch.lower(), 0)
                # color intensity
                if rate >= 0.4:
                    col = "#dc2626"
                    fg = "white"
                elif rate >= 0.2:
                    col = "#f87171"
                    fg = "white"
                elif rate >= 0.08:
                    col = "#fee2e2"
                    fg = "#7f1d1d"
                elif rate > 0:
                    col = "#fffbeb"
                    fg = "#92400e"
                else:
                    col = "white"
                    fg = "#334155"
                cv.create_rectangle(x, y, x+key_w, y+key_h, fill=col, outline="#cbd5e1", width=1)
                lab = ch.upper() if ch.isalpha() else ch
                cv.create_text(x+key_w//2, y+key_h//2 -2, text=lab, font=("Consolas", 10, "bold"), fill=fg)
                if rate>0:
                    cv.create_text(x+key_w//2, y+key_h-7, text=f"{rate*100:.0f}%", font=("Segoe UI", 6), fill=fg)
                x += key_w+gap
        # space bar
        cv.create_rectangle(220, y0+4*(key_h+gap), 520, y0+4*(key_h+gap)+key_h, fill="white" if hm.get(' ',0)==0 else "#fee2e2", outline="#cbd5e1")
        cv.create_text(370, y0+4*(key_h+gap)+key_h//2, text="SPACE", font=("Segoe UI", 9, "bold"), fill="#334155")
        # legend
        leg_y = y0+4*(key_h+gap)+key_h+16
        for i,(col, txt_) in enumerate([("white","0%"), ("#fffbeb","1-8%"), ("#fee2e2","8-20%"), ("#f87171","20-40%"), ("#dc2626",">40%")]):
            lx = x0 + i*110
            cv.create_rectangle(lx, leg_y, lx+18, leg_y+12, fill=col, outline="#cbd5e1")
            cv.create_text(lx+24, leg_y+6, text=txt_, anchor="w", font=("Segoe UI", 8), fill="#475569")
        # finger hint
        ttk.Label(parent, text="If errors cluster on one finger/hand, that finger needs isolated drills (see Practice Drill tab).", font=("Segoe UI", 8), foreground="#64748b").pack(anchor="w", pady=(6,0))

    def _build_drill_tab(self, parent):
        r = self.report
        sugg = r.suggestions if hasattr(r,'suggestions') else r.get('suggestions',[])
        drill = r.drill_text if hasattr(r,'drill_text') else r.get('drill_text','')
        ttk.Label(parent, text="Personalized suggestions:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        for s in sugg:
            # bullet
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=2, anchor="w")
            tk.Canvas(row, width=6, height=6, bg="#0ea5e9", highlightthickness=0).pack(side="left", padx=(4,6), pady=4)
            lbl = tk.Label(row, text=s, font=("Segoe UI", 9), wraplength=720, justify="left", bg=parent.cget("background") if hasattr(parent,"cget") else "#f0f0f0")
            lbl.pack(side="left", fill="x", expand=True, anchor="w")
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(parent, text="Your custom drill (focuses on weakest letters):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(parent, text="Copy or click 'Practice Drill →' to load this drill as a custom exercise.", font=("Segoe UI", 8), foreground="#64748b").pack(anchor="w")
        txt = tk.Text(parent, wrap="word", height=6, font=("Consolas", 11), bg="#fffbeb", relief="solid", bd=1, padx=8, pady=8)
        txt.pack(fill="both", expand=True, pady=4)
        txt.insert("1.0", drill if drill else "No drill — perfect run. Try longer paragraph.")
        txt.config(state="disabled")
        self._drill_text_widget = txt
        self._drill_raw = drill

    def _copy_summary(self):
        r = self.report
        summ = r.summary if hasattr(r,'summary') else r.get('summary','')
        sugg = r.suggestions if hasattr(r,'suggestions') else r.get('suggestions',[])
        txt = f"Open-Typer Smart Analysis\nTarget: {repr(self.target[:60])}\nTyped : {repr(self.typed[:60])}\n{summ}\n\n" + "\n".join(f"- {s}" for s in sugg)
        self.clipboard_clear()
        self.clipboard_append(txt)
        messagebox.showinfo("Copied", "Summary copied to clipboard.")

    def _start_drill(self):
        if not self._drill_raw:
            messagebox.showinfo("No drill", "No weaknesses to drill — try a harder text.")
            return
        # ask parent app to load drill as custom exercise
        app = self._parent_app
        try:
            # create synthetic pack entry like custom file does
            custom_name = "Smart Drill — Weak Letters"
            entry = {"lesson":1,"sub":1,"ex":1,"text": self._drill_raw,"raw": self._drill_raw,"desc":"Smart drill","limit":120,"line_len":60,"repeat":False,"repeat_type":""}
            # inject into packs
            if hasattr(app, 'packs'):
                app.packs[custom_name] = [entry]
                app.pack_names = sorted(app.packs.keys())
                if hasattr(app, 'pack_combo'):
                    app.pack_combo["values"] = app.pack_names
                app.current_pack = custom_name
                if hasattr(app,'pack_var'):
                    app.pack_var.set(custom_name)
                app.current_lesson=1; app.current_sub=1; app.current_ex=1
                if hasattr(app,'_refresh_combos'):
                    app._refresh_combos()
                if hasattr(app,'_load_exercise'):
                    app._load_exercise()
            messagebox.showinfo("Drill loaded", f"Loaded drill for weakest letters:\n\n{self._drill_raw[:120]}...")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Failed", str(e))



    def __init__(self, packs):
        super().__init__()
        self.packs=packs
        self.pack_names=sorted(packs.keys())
        if not self.pack_names:
            messagebox.showerror("No packs", "No lesson packs found. Place res/packs beside exe or use File→Open")
            self.pack_names=["en_US-default-A"]
            self.packs={"en_US-default-A": [{"lesson":1,"sub":1,"ex":1,"text":"ff jj ff jj","raw":"ff jj","desc":"","limit":120,"line_len":60}]}
        self.title(f"Open-Typer {VERSION} — by {AUTHOR}")
        try:
            self.iconbitmap(resource_path("res/icons/icon.ico"))
        except:
            pass
        self.geometry("920x700")
        self.minsize(860,600)
        # theme
        self.is_dark=False
        self.style=ttk.Style()
        try:
            self.style.theme_use("clam")
        except: pass
        self.configure(bg="#f5f5f5")
        self.current_text=""
        self.current_entry=""
        self.start_time=None
        self.errors=0
        self.typed=0
        self.history=[]
        # Timed Para mode (LiveChat / Typewizz / typing.com)
        self.is_timed_para=False
        self.time_limit=0
        self.time_remaining=0
        self.timer_job=None
        self.timed_source=""
        # Smart Analysis — cumulative across session
        self.smart_session_reports=[]
        self.last_smart_report=None
        self.current_pack=self.pack_names[0]
        self.current_lesson=1
        self.current_sub=1
        self.current_ex=1
        self._build_ui()
        self._load_exercise()
        self.bind("<Key>", self._global_key)

    def _build_ui(self):
        # Top branding bar
        top = tk.Frame(self, bg="#0f172a", height=56)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)
        tk.Label(top, text="⌨ Open-Typer", fg="white", bg="#0f172a", font=("Segoe UI", 16, "bold")).pack(side="left", padx=16, pady=8)
        tk.Label(top, text=f"v{VERSION}  •  by {AUTHOR}", fg="#93c5fd", bg="#0f172a", font=("Segoe UI", 9)).pack(side="left", pady=8)
        # Portfolio button
        btnf = tk.Frame(top, bg="#0f172a")
        btnf.pack(side="right", padx=12)
        for txt, url in [("Portfolio", PORTFOLIO), ("GitHub", GITHUB), ("About", None)]:
            b = tk.Button(btnf, text=txt, bg="#1e40af" if txt=="Portfolio" else "#1e293b", fg="white", relief="flat", padx=10, pady=4, font=("Segoe UI", 9, "bold"), cursor="hand2", command=lambda u=url, t=txt: self._open_top(t,u))
            b.pack(side="left", padx=4)
            b.bind("<Enter>", lambda e, b=b: b.config(bg="#2563eb"))
            b.bind("<Leave>", lambda e, b=b, t=txt: b.config(bg="#1e40af" if t=="Portfolio" else "#1e293b"))

        # Controls frame
        ctrl = ttk.Frame(self, padding=10)
        ctrl.pack(fill="x")
        # Pack selector
        ttk.Label(ctrl, text="Pack:").grid(row=0, column=0, sticky="w", padx=4)
        self.pack_var=tk.StringVar(value=self.current_pack)
        self.pack_combo=ttk.Combobox(ctrl, textvariable=self.pack_var, values=self.pack_names, state="readonly", width=22)
        self.pack_combo.grid(row=0, column=1, padx=4)
        self.pack_combo.bind("<<ComboboxSelected>>", self._on_pack_change)

        ttk.Label(ctrl, text="Lesson:").grid(row=0, column=2, padx=4)
        self.lesson_var=tk.StringVar()
        self.lesson_combo=ttk.Combobox(ctrl, textvariable=self.lesson_var, state="readonly", width=8)
        self.lesson_combo.grid(row=0, column=3, padx=4)
        self.lesson_combo.bind("<<ComboboxSelected>>", self._on_lesson_change)

        ttk.Label(ctrl, text="Sublesson:").grid(row=0, column=4, padx=4)
        self.sub_var=tk.StringVar()
        self.sub_combo=ttk.Combobox(ctrl, textvariable=self.sub_var, state="readonly", width=10)
        self.sub_combo.grid(row=0, column=5, padx=4)
        self.sub_combo.bind("<<ComboboxSelected>>", self._on_sub_change)

        ttk.Label(ctrl, text="Exercise:").grid(row=0, column=6, padx=4)
        self.ex_var=tk.StringVar()
        self.ex_combo=ttk.Combobox(ctrl, textvariable=self.ex_var, state="readonly", width=8)
        self.ex_combo.grid(row=0, column=7, padx=4)
        self.ex_combo.bind("<<ComboboxSelected>>", self._on_ex_change)

        # Buttons
        bf = ttk.Frame(ctrl)
        bf.grid(row=0, column=8, padx=10)
        ttk.Button(bf, text="⟳ Restart", command=self._restart).pack(side="left", padx=2)
        ttk.Button(bf, text="‹ Prev", command=lambda: self._nav(-1)).pack(side="left", padx=2)
        ttk.Button(bf, text="Next ›", command=lambda: self._nav(1)).pack(side="left", padx=2)
        ttk.Button(bf, text="Theme", command=self._toggle_theme).pack(side="left", padx=2)
        # Timed Para Attack (typing.com / LiveChat / Typewizz)
        ttk.Button(bf, text="⏱ Para Time Attack", command=self._start_timed_para_dialog).pack(side="left", padx=6)
        # Smart Analysis — isolated (does not interfere with timed para)
        ttk.Button(bf, text="🧠 Smart Analysis", command=self._show_smart_analysis).pack(side="left", padx=6)

        ctrl.columnconfigure(8, weight=1)

        # Stats bar — WPM/CPM/Accuracy/Time/Errors (LiveChat dual + Typewizz cert)
        stats = tk.Frame(self, bg="#e2e8f0", height=34)
        stats.pack(fill="x", padx=10, pady=(0,6))
        stats.pack_propagate(False)
        self.wpm_var=tk.StringVar(value="WPM: 0")
        self.cpm_var=tk.StringVar(value="CPM: 0")
        self.acc_var=tk.StringVar(value="Acc: 100%")
        self.time_var=tk.StringVar(value="Time: 00:00")
        self.err_var=tk.StringVar(value="Errors: 0")
        for var in [self.wpm_var, self.cpm_var, self.acc_var, self.time_var, self.err_var]:
            tk.Label(stats, textvariable=var, bg="#e2e8f0", fg="#0f172a", font=("Consolas", 10, "bold")).pack(side="left", padx=10, pady=6)
        self.progress_var=tk.StringVar(value="Idle")
        tk.Label(stats, textvariable=self.progress_var, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9)).pack(side="right", padx=12)
        # Progress bar for timed mode (Typewizz countdown)
        self.time_progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.time_progress.pack(fill="x", padx=10, pady=(0,4))

        # Main text area
        mid = tk.Frame(self, bg="#f5f5f5")
        mid.pack(fill="both", expand=True, padx=10, pady=6)

        # Target text display (read-only Text with tags)
        self.display = tk.Text(mid, wrap="word", font=("Consolas", 16), height=5, bg="white", fg="#0f172a", relief="solid", bd=1, padx=12, pady=12, spacing1=4, spacing3=4)
        self.display.pack(fill="x", pady=(0,8))
        self.display.config(state="disabled")
        self.display.tag_config("correct", foreground="#16a34a")
        self.display.tag_config("incorrect", foreground="white", background="#ef4444", underline=True)
        self.display.tag_config("current", background="#dbeafe", foreground="#1e40af")
        self.display.tag_config("pending", foreground="#94a3b8")
        self.display.tag_config("error_word", background="#fef3c7")

        # Input area
        inp_frame = tk.Frame(mid, bg="#f5f5f5")
        inp_frame.pack(fill="both", expand=True)
        tk.Label(inp_frame, text="Type here:", bg="#f5f5f5", fg="#475569", font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
        self.input = tk.Text(inp_frame, wrap="word", font=("Consolas", 16), height=5, bg="white", fg="#0f172a", insertbackground="#0f172a", relief="solid", bd=1, padx=12, pady=12, undo=False)
        self.input.pack(fill="both", expand=True, pady=4)
        self.input.bind("<KeyRelease>", self._on_input)
        self.input.bind("<KeyPress>", self._on_keypress)
        # Prevent paste of large text? Allow
        # History / tips
        hist_frame = tk.Frame(mid, bg="#f5f5f5")
        hist_frame.pack(fill="x", pady=(8,0))
        tk.Label(hist_frame, text="History (last 5):", bg="#f5f5f5", fg="#64748b", font=("Segoe UI", 8)).pack(anchor="w")
        self.history_label = tk.Label(hist_frame, text="—", bg="#f5f5f5", fg="#475569", font=("Consolas", 8), justify="left", anchor="w")
        self.history_label.pack(fill="x")

        # Bottom status
        bottom = tk.Frame(self, bg="#0f172a", height=28)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)
        tk.Label(bottom, text=f"© 2021-2026 {AUTHOR}  •  GPL-3.0  •  {GITHUB}  •  {EMAIL}  •  {PHONE}", fg="#94a3b8", bg="#0f172a", font=("Segoe UI", 8)).pack(side="left", padx=10, pady=4)
        tk.Label(bottom, text="Designed & engineered with precision", fg="#60a5fa", bg="#0f172a", font=("Segoe UI", 8, "italic")).pack(side="right", padx=10)

        # Menu
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="Open custom text file...", command=self._open_custom)
        filem.add_command(label="Restart exercise", command=self._restart)
        filem.add_separator()
        filem.add_command(label="Para Time Attack...  (1/3/5 min)", command=self._start_timed_para_dialog)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filem)
        testm = tk.Menu(menubar, tearoff=0)
        testm.add_command(label="Paragraph Time Attack...  ⏱", command=self._start_timed_para_dialog)
        testm.add_command(label="Quick 60s — Random Words (LiveChat)", command=lambda: self._quick_timed(60, "Random Words — 1000 common (LiveChat)", 300))
        testm.add_command(label="Quick 60s — Paragraph Prose (Typewizz)", command=lambda: self._quick_timed(60, "Paragraph Prose (Typewizz continuous)", 300))
        testm.add_command(label="3 min — Paragraph Prose", command=lambda: self._quick_timed(180, "Paragraph Prose (Typewizz continuous)", 600))
        menubar.add_cascade(label="Test", menu=testm)
        # Analysis menu — isolated from Test menu (no conflict)
        analysism = tk.Menu(menubar, tearoff=0)
        analysism.add_command(label="🧠 Smart Analysis — This Exercise", command=self._show_smart_analysis)
        analysism.add_command(label="📊 Session Overview (all exercises)", command=self._show_session_analysis)
        analysism.add_separator()
        analysism.add_command(label="★ Practice Weak Letters (Drill)", command=self._practice_weak_letters)
        menubar.add_cascade(label="Analysis", menu=analysism)
        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(label="About Open-Typer...", command=self._show_about)
        helpm.add_command(label="Portfolio", command=lambda: webbrowser.open(PORTFOLIO))
        helpm.add_command(label="GitHub", command=lambda: webbrowser.open(GITHUB))
        menubar.add_cascade(label="Help", menu=helpm)
        self.config(menu=menubar)

        # Update combos initially
        self._refresh_combos()

    def _open_top(self, txt, url):
        if txt=="About":
            self._show_about()
        elif url:
            webbrowser.open(url)

    def _refresh_combos(self):
        # Populate lesson/sub/ex based on current pack
        entries = self.packs.get(self.current_pack, [])
        lessons = sorted(set(e["lesson"] for e in entries))
        self.lesson_combo["values"]=lessons
        if self.current_lesson not in lessons and lessons:
            self.current_lesson=lessons[0]
        self.lesson_var.set(str(self.current_lesson))
        # sublessons for lesson
        subs = sorted(set(e["sub"] for e in entries if e["lesson"]==self.current_lesson))
        sub_names = {1:"Touch",2:"Words",3:"Sentences",4:"Text"}
        sub_labels = [f"{s} - {sub_names.get(s, f'Sublesson {s}')}" for s in subs]
        self.sub_map = dict(zip(sub_labels, subs))
        self.sub_rev = {v:k for k,v in self.sub_map.items()}
        self.sub_combo["values"]=sub_labels
        if self.current_sub not in subs and subs:
            self.current_sub=subs[0]
        self.sub_var.set(self.sub_rev.get(self.current_sub, ""))
        # exercises
        exs = sorted(set(e["ex"] for e in entries if e["lesson"]==self.current_lesson and e["sub"]==self.current_sub))
        self.ex_combo["values"]=exs
        if self.current_ex not in exs and exs:
            self.current_ex=exs[0]
        self.ex_var.set(str(self.current_ex))

    def _on_pack_change(self, e):
        self.current_pack=self.pack_var.get()
        # reset to first lesson
        entries=self.packs[self.current_pack]
        self.current_lesson=min(set(en["lesson"] for en in entries))
        self.current_sub=min(set(en["sub"] for en in entries if en["lesson"]==self.current_lesson))
        self.current_ex=1
        self._refresh_combos()
        self._load_exercise()

    def _on_lesson_change(self, e):
        try:
            self.current_lesson=int(self.lesson_var.get())
        except: return
        # refresh subs
        entries=self.packs[self.current_pack]
        subs=sorted(set(en["sub"] for en in entries if en["lesson"]==self.current_lesson))
        if self.current_sub not in subs:
            self.current_sub=subs[0] if subs else 1
        exs=sorted(set(en["ex"] for en in entries if en["lesson"]==self.current_lesson and en["sub"]==self.current_sub))
        self.current_ex=exs[0] if exs else 1
        self._refresh_combos()
        self._load_exercise()

    def _on_sub_change(self, e):
        label=self.sub_var.get()
        self.current_sub=self.sub_map.get(label, 1)
        entries=self.packs[self.current_pack]
        exs=sorted(set(en["ex"] for en in entries if en["lesson"]==self.current_lesson and en["sub"]==self.current_sub))
        self.current_ex=exs[0] if exs else 1
        self._refresh_combos()
        self._load_exercise()

    def _on_ex_change(self, e):
        try:
            self.current_ex=int(self.ex_var.get())
        except: return
        self._load_exercise()

    def _nav(self, delta):
        entries=self.packs[self.current_pack]
        # Get sorted list of tuples
        tuples=sorted((en["lesson"], en["sub"], en["ex"]) for en in entries)
        try:
            idx=tuples.index((self.current_lesson, self.current_sub, self.current_ex))
        except:
            idx=0
        idx = max(0, min(len(tuples)-1, idx+delta))
        self.current_lesson, self.current_sub, self.current_ex = tuples[idx]
        self._refresh_combos()
        self._load_exercise()

    def _load_exercise(self):
        # Cancel timed mode if active
        if self.timer_job:
            try: self.after_cancel(self.timer_job)
            except: pass
            self.timer_job=None
        self.is_timed_para=False
        self.time_limit=0
        self.time_remaining=0
        self.time_progress.config(value=0)
        entries=self.packs.get(self.current_pack, [])
        found=None
        for en in entries:
            if en["lesson"]==self.current_lesson and en["sub"]==self.current_sub and en["ex"]==self.current_ex:
                found=en
                break
        if not found and entries:
            found=entries[0]
        if not found:
            self.current_text=""
            return
        # Apply line wrapping like ConfigParser::initExercise (simple word wrap at line_len)
        raw = found["text"]
        line_len = found["line_len"]
        # Do wrapping
        self.current_text = self._wrap_text(raw, line_len)
        # Also get desc for title
        desc = found.get("desc","")
        # Update display
        self.display.config(state="normal")
        self.display.delete("1.0","end")
        self.display.insert("1.0", self.current_text)
        # Tag all as pending initially
        self.display.tag_add("pending", "1.0", "end")
        self.display.tag_remove("correct", "1.0", "end")
        self.display.tag_remove("incorrect", "1.0", "end")
        self.display.tag_remove("current", "1.0", "end")
        # Highlight first char as current
        if self.current_text:
            self.display.tag_add("current", "1.0", "1.1")
            self.display.tag_remove("pending", "1.0", "1.1")
        self.display.config(state="disabled")
        # Reset input
        self.input.delete("1.0","end")
        self.input.focus_set()
        self.start_time=None
        self.errors=0
        self.typed=0
        self.progress_var.set(f"Lesson {self.current_lesson} • Sublesson {self.current_sub} • Exercise {self.current_ex}  —  {desc} — {len(self.current_text)} chars")
        self._update_stats()
        self.after(200, self._update_timer)

    # === Timed Para Time Attack — typing.com 1/3/5 min + LiveChat 60s + Typewizz 1 min cert ===
    def _start_timed_para_dialog(self):
        dlg=TimedParaDialog(self, self.packs)
        res=dlg.get()
        if res:
            secs, source, target = res
            self._quick_timed(secs, source, target)

    def _quick_timed(self, secs, source, target):
        self._start_timed_para(secs, source, target)

    def _start_timed_para(self, time_limit, source, target_chars):
        # Cancel previous
        if self.timer_job:
            try: self.after_cancel(self.timer_job)
            except: pass
        # Generate paragraph
        para=""
        if "Random Words" in source:
            para=generate_random_para(target_chars, "words")
        elif "Paragraph Prose" in source:
            # Concatenate pack prose until target
            entries=[]
            for lst in self.packs.values():
                for en in lst:
                    # Only Text sublessons (4) are prose-like
                    if en["sub"]==4 or en["sub"]==3:
                        entries.append(en["text"])
            if entries:
                # shuffle and join
                random.shuffle(entries)
                para=""
                for e in entries:
                    if len(para)+len(e)+1 <= target_chars:
                        para+= (" " if para else "")+e
                    else:
                        break
                if not para:
                    para=entries[0][:target_chars]
            else:
                para=generate_random_para(target_chars, "words")
        elif "Current Exercise" in source:
            # Use current exercise text repeated to target
            entries=self.packs.get(self.current_pack, [])
            cur=None
            for en in entries:
                if en["lesson"]==self.current_lesson and en["sub"]==self.current_sub and en["ex"]==self.current_ex:
                    cur=en; break
            base=cur["text"] if cur else "The quick brown fox jumps over the lazy dog. "
            para=""
            while len(para) < target_chars:
                para+= (" " if para else "")+base
            para=para[:target_chars].rsplit(" ",1)[0]
        elif "Custom File" in source:
            path=filedialog.askopenfilename(title="Open para text", filetypes=[("Text","*.txt"),("All","*.*")])
            if path and os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        txt=f.read().strip().replace("\r","").replace("\n"," ")
                    para=txt[:target_chars] if target_chars< len(txt) else txt
                except Exception as e:
                    messagebox.showerror("Error", str(e)); return
            else:
                return
        else:
            para=generate_random_para(target_chars, "words")

        # Wrap at 60 (like livechat paragraph)
        self.current_text=self._wrap_text(para, 60)
        self.is_timed_para=True
        self.time_limit=time_limit  # 0 = untimed (typing.com Page Test)
        self.time_remaining=time_limit
        self.timed_source=source
        # Update display
        self.display.config(state="normal")
        self.display.delete("1.0","end")
        self.display.insert("1.0", self.current_text)
        self.display.tag_add("pending","1.0","end")
        self.display.tag_remove("correct","1.0","end")
        self.display.tag_remove("incorrect","1.0","end")
        self.display.tag_remove("current","1.0","end")
        if self.current_text:
            self.display.tag_add("current","1.0","1.1")
            self.display.tag_remove("pending","1.0","1.1")
        self.display.config(state="disabled")
        self.input.delete("1.0","end")
        self.input.focus_set()
        self.start_time=None
        self.errors=0
        self.typed=0
        self.time_progress.config(maximum=max(1,time_limit) if time_limit else 100, value=0)
        if time_limit==0:
            self.progress_var.set(f"Para — {source} — Full Page — {len(self.current_text)} chars (no timer)")
            self.time_var.set("Time: --:--")
        else:
            mins, secs = divmod(time_limit,60)
            self.progress_var.set(f"⏱ Para Time Attack — {source} — {mins:02d}:{secs:02d} — {len(self.current_text)} chars")
            self.time_var.set(f"Time: {mins:02d}:{secs:02d}")
        self._update_stats()
        self.after(200, self._update_timer)
        # Focus

    def _tick_timed(self):
        if not self.is_timed_para or self.time_limit==0 or self.start_time is None:
            return
        elapsed=time.time()-self.start_time
        remaining=max(0, self.time_limit - elapsed)
        self.time_remaining=remaining
        mins, secs = divmod(int(remaining),60)
        self.time_var.set(f"Time: {mins:02d}:{secs:02d}")
        # progress bar: elapsed / limit
        pct = min(100, elapsed/self.time_limit*100) if self.time_limit else 0
        self.time_progress.config(value=elapsed)
        # color red when <10s
        if remaining<=10 and remaining>0:
            self.time_progress.config(style="red.Horizontal.TProgressbar")
        if remaining<=0:
            self._on_complete_timed(timeout=True)
        else:
            self.timer_job=self.after(100, self._tick_timed)

    def _on_complete_timed(self, timeout=False):
        if self.timer_job:
            try: self.after_cancel(self.timer_job)
            except: pass
            self.timer_job=None
        elapsed=time.time()-self.start_time if self.start_time else self.time_limit
        if timeout:
            elapsed=self.time_limit
        # Correct chars
        target=self.current_text
        typed_text=self.input.get("1.0","end-1c")
        correct=sum(1 for a,b in zip(typed_text, target) if a==b)
        # For timeout, typed may be less than target; correct is up to typed length
        typed_len=len(typed_text)
        # For LiveChat / Typewizz, CPM/WPM based on correct chars
        cpm = cpm_calc(correct, elapsed)
        cpm_gross = cpm_calc(typed_len, elapsed)
        wpm = wpm_calc(correct, elapsed)
        wpm_gross = wpm_calc(typed_len, elapsed)
        acc = (correct/typed_len*100) if typed_len else 100
        cert=cert_for(cpm, acc)
        # Error words
        target_words=target.split()
        typed_words=typed_text.split()
        err_words=sum(1 for a,b in zip(typed_words, target_words) if a!=b)
        # --- Smart Analysis for timed para (isolated) ---
        try:
            if SMART_AVAILABLE and analyze_text and typed_text and target:
                rep = analyze_text(target, typed_text)
                self.last_smart_report = rep
                self.smart_session_reports.append(rep)
                self._last_typed = typed_text
                self._last_target = target
        except Exception as e:
            print(f"[SmartAnalysis timed] {e}")
        hist=f"⏱ PARA {self.time_limit}s {self.timed_source[:12]} — WPM {wpm:.0f} (gross {wpm_gross:.0f}) CPM {cpm:.0f} Acc {acc:.1f}% Err {self.errors} Cert {cert or '—'}"
        self.history.insert(0, hist)
        self.history=self.history[:5]
        self.history_label.config(text="\n".join(self.history))
        # Build certificate message like Typewizz
        cert_msg=""
        if cert:
            cert_msg=f"\nCertificate: {cert} ✅\n"
            if cert=="Gold": cert_msg+="Gold: 350 CPM 99.5% — top 8%\n"
            elif cert=="Silver": cert_msg+="Silver: 250 CPM 98.5% — top 21%\n"
            else: cert_msg+="Bronze: 200 CPM 96.5% — top 39%\n"
        else:
            # Show next threshold
            cert_msg="\nCertificate: —\nNext: Bronze 200 CPM 96.5%\n"
        # Smart hint
        smart_hint=""
        try:
            if self.last_smart_report:
                rr=self.last_smart_report
                worst = rr.worst_letters if hasattr(rr,'worst_letters') else rr.get('worst_letters',[])
                cat = rr.category_counts if hasattr(rr,'category_counts') else rr.get('category_counts',{})
                if worst:
                    top = ", ".join(ch for ch,_ in worst[:3])
                    top_cat = max(cat, key=lambda k: cat[k]) if cat else ""
                    label_map = {"adjacent_key":"adjacent keys","shift_case":"Shift/Caps","shift_symbol":"Symbol Shift","transposition":"swapped letters"}
                    smart_hint = f"\n🧠 Smart: weakest → {top}  •  {label_map.get(top_cat, top_cat)}\n"
        except Exception:
            pass
        msg = f"{'Time up!' if timeout else 'Completed!'}\n\nSource: {self.timed_source}\nTime limit: {self.time_limit}s  Elapsed: {int(elapsed//60):02d}:{int(elapsed%60):02d}\nChars: {typed_len}/{len(target)} (correct {correct})\n\nWPM: {wpm:.0f} (gross {wpm_gross:.0f})\nCPM: {cpm:.0f} (gross {cpm_gross:.0f})\nAccuracy: {acc:.1f}%\nErrors: {self.errors}  Error words: {err_words}{smart_hint}\n{cert_msg}\nRetry?"
        # If errors, offer smart analysis first
        if self.errors>0 and SMART_AVAILABLE and self.last_smart_report:
            if messagebox.askyesno("Time Attack Completed — Smart Analysis", msg + "\nOpen Smart Analysis?"):
                try:
                    SmartAnalysisDialog(self, target, typed_text, elapsed)
                except Exception as e:
                    messagebox.showerror("Smart Analysis", str(e))
                if messagebox.askyesno("Retry?", "Retry same Time Attack (new para)?"):
                    self._start_timed_para(self.time_limit, self.timed_source, len(self.current_text))
                    return
                else:
                    self.is_timed_para=False
                    self.time_progress.config(value=0)
                    self._load_exercise()
                    return
        if messagebox.askyesno("Time Attack Completed", msg):
            # Restart same para with same settings but new random para
            self._start_timed_para(self.time_limit, self.timed_source, len(self.current_text))
        else:
            self.is_timed_para=False
            self.time_progress.config(value=0)
            self._load_exercise()

    def _wrap_text(self, text, line_len):
        # Mimic ConfigParser::initExercise word wrap
        words=text.replace("\n"," \n ").split(" ")
        out=""
        line_pos=0
        first=True
        for w in words:
            if w=="\n":
                out+="\n"
                line_pos=0
                first=True
                continue
            if w=="":
                continue
            l=len(w)
            if line_pos + l + (0 if first else 1) > line_len:
                out+="\n"
                line_pos=0
                first=True
            if not first and line_pos>0:
                out+=" "
                line_pos+=1
            out+=w
            line_pos+=l
            first=False
        return out

    def _on_keypress(self, event):
        if self.start_time is None and event.char and event.keysym not in ("BackSpace","Shift_L","Shift_R","Control_L","Control_R","Alt_L","Alt_R"):
            self.start_time=time.time()
            if self.is_timed_para and self.time_limit>0:
                self._tick_timed()

    def _on_input(self, event=None):
        # Get current input text (strip trailing newline added by Text widget)
        current = self.input.get("1.0","end-1c")
        # Remove possible extra newline at end
        # Compare to target
        target = self.current_text
        # Update display tags
        self.display.config(state="normal")
        # Clear all
        self.display.tag_remove("correct","1.0","end")
        self.display.tag_remove("incorrect","1.0","end")
        self.display.tag_remove("current","1.0","end")
        self.display.tag_remove("pending","1.0","end")

        typed_len=len(current)
        errs=0
        for i,ch in enumerate(target):
            idx = f"1.0+{i}c"
            nxt = f"1.0+{i+1}c"
            if i < typed_len:
                if current[i]==ch:
                    self.display.tag_add("correct", idx, nxt)
                else:
                    self.display.tag_add("incorrect", idx, nxt)
                    errs+=1
            elif i==typed_len:
                self.display.tag_add("current", idx, nxt)
            else:
                self.display.tag_add("pending", idx, nxt)
        self.display.config(state="disabled")
        self.errors=errs
        self.typed=typed_len
        self._update_stats()
        # Check completion — for timed para, finish early if paragraph completed before timeout
        if self.is_timed_para:
            if current == target and len(target)>0:
                self._on_complete_timed(timeout=False)
                return
        else:
            if current == target and len(target)>0:
                self._on_complete()
                return
        # Also handle if typed longer than target -> extra errors
        if len(current) > len(target):
            self.err_var.set(f"Errors: {errs} (+{len(current)-len(target)} extra)")

    def _update_stats(self):
        typed=self.typed
        errs=self.errors
        total=len(self.current_text) if self.current_text else 1
        elapsed = time.time()-self.start_time if self.start_time else 0
        # Accuracy (typing.com / LiveChat)
        acc = max(0, (typed - errs) / max(1, typed) * 100) if typed>0 else 100
        self.acc_var.set(f"Acc: {acc:.1f}%")
        self.err_var.set(f"Errors: {errs}")
        # WPM/CPM — Gross vs Net (LiveChat de-facto: WPM = corrected CPM /5)
        correct = max(0, typed - errs)
        minutes = elapsed/60 if elapsed>0 else 1/60
        wpm = (correct/5) / minutes if minutes>0 else 0
        cpm = correct / minutes if minutes>0 else 0
        cpm_gross = typed / minutes if minutes>0 else 0
        if self.start_time is None:
            wpm=0; cpm=0; cpm_gross=0
        self.wpm_var.set(f"WPM: {wpm:.0f}")
        try:
            self.cpm_var.set(f"CPM: {cpm:.0f} ({cpm_gross:.0f} gross)")
        except:
            pass
        # Progress — lesson mode vs timed para
        if self.is_timed_para and self.time_limit>0:
            # Show remaining + cert hint (Typewizz)
            elapsed = time.time()-self.start_time if self.start_time else 0
            remaining = max(0, self.time_limit - elapsed)
            mins, secs = divmod(int(remaining),60)
            # cert preview
            cur_cpm = cpm
            cert = cert_for(cur_cpm, acc) if typed>0 else None
            cert_txt = f" • {cert} ✅" if cert else ""
            self.progress_var.set(f"⏱ PARA {self.time_limit}s {self.timed_source[:18]} — {remaining:.0f}s left — {typed}/{len(self.current_text)} chars{cert_txt}")
        else:
            pct = min(100, typed/len(self.current_text)*100) if self.current_text else 0
            if self.is_timed_para and self.time_limit==0:
                self.progress_var.set(f"Para — Full Page — {typed}/{len(self.current_text)} chars — {pct:.0f}%")
            else:
                self.progress_var.set(f"Lesson {self.current_lesson} • Sub {self.current_sub} • Ex {self.current_ex} — {pct:.0f}%  —  {len(self.current_text)} chars")

    def _update_timer(self):
        if self.is_timed_para and self.time_limit>0:
            if self.start_time:
                elapsed=time.time()-self.start_time
                remaining=max(0, self.time_limit - elapsed)
                mins, secs = divmod(int(remaining),60)
                self.time_var.set(f"Time: {mins:02d}:{secs:02d} / {self.time_limit//60:02d}:{self.time_limit%60:02d}")
                self._update_stats()
                # progress bar handled in _tick_timed
            else:
                mins, secs = divmod(self.time_limit,60)
                self.time_var.set(f"Time: {mins:02d}:{secs:02d}")
            self.after(200, self._update_timer)
            return
        if self.start_time:
            elapsed=time.time()-self.start_time
            mins=int(elapsed//60)
            secs=int(elapsed%60)
            self.time_var.set(f"Time: {mins:02d}:{secs:02d}")
            self._update_stats()
        else:
            self.time_var.set("Time: 00:00")
        self.after(200, self._update_timer)

    def _restart(self):
        self._load_exercise()

    def _on_complete(self):
        elapsed=time.time()-self.start_time if self.start_time else 0
        correct=max(0, self.typed - self.errors)
        acc=(self.typed - self.errors)/max(1,self.typed)*100 if self.typed else 100
        wpm=(correct/5)/(elapsed/60) if elapsed>0 else 0
        # --- Smart Analysis — compute for this exercise (non-intrusive) ---
        typed_text=self.input.get("1.0","end-1c") if hasattr(self,'input') else ""
        target_text=self.current_text
        try:
            if SMART_AVAILABLE and analyze_text and typed_text and target_text:
                rep = analyze_text(target_text, typed_text)
                self.last_smart_report = rep
                self.smart_session_reports.append(rep)
                # also push to global analyzer
        except Exception as e:
            print(f"[SmartAnalysis] compute failed: {e}")
            rep=None
        # Add to history
        hist = f"{self.current_pack} L{self.current_lesson}.{self.current_sub}.{self.current_ex} — WPM {wpm:.0f} Acc {acc:.1f}% Time {int(elapsed//60):02d}:{int(elapsed%60):02d}"
        self.history.insert(0, hist)
        self.history=self.history[:5]
        self.history_label.config(text="\n".join(self.history) if self.history else "—")
        # Show dialog — include smart hint without disturbing flow
        smart_hint=""
        try:
            if self.last_smart_report:
                rr=self.last_smart_report
                worst = rr.worst_letters if hasattr(rr,'worst_letters') else rr.get('worst_letters',[])
                cat = rr.category_counts if hasattr(rr,'category_counts') else rr.get('category_counts',{})
                if worst:
                    top = ", ".join(ch for ch,_ in worst[:3])
                    top_cat = max(cat, key=lambda k: cat[k]) if cat else ""
                    label_map = {"adjacent_key":"adjacent-key fat-finger","shift_case":"Shift/Caps","shift_symbol":"Symbol Shift","transposition":"swapped letters","double_letter":"double-letter","other":"reading"}
                    smart_hint = f"\n🧠 Smart: weakest → {top}  •  main cause: {label_map.get(top_cat, top_cat) or '—'}\n   See Analysis → Smart Analysis for why & drill."
                else:
                    smart_hint="\n🧠 Smart: Perfect! No weak letters."
        except Exception:
            pass
        msg = f"Exercise completed!\n\nPack: {self.current_pack}\nLesson {self.current_lesson} • Sublesson {self.current_sub} • Exercise {self.current_ex}\n\nWPM: {wpm:.0f}\nAccuracy: {acc:.1f}%\nErrors: {self.errors}\nTime: {int(elapsed//60):02d}:{int(elapsed%60):02d}{smart_hint}\n\nNext exercise?"
        # Offer smart analysis if errors
        if self.errors>0 and SMART_AVAILABLE:
            if messagebox.askyesno("Completed — Smart Analysis available", msg + "\n\nOpen Smart Analysis? (diagnoses adjacent keys / Shift)"):
                self._show_smart_analysis(last=True)
                # after dialog, ask next
                if messagebox.askyesno("Next?", "Go to next exercise?"):
                    self._nav(1)
                return
        if messagebox.askyesno("Completed", msg):
            self._nav(1)
        else:
            pass

    # ── Smart Analysis helpers — isolated from timed-para ─────────
    def _show_smart_analysis(self, last=False):
        """Open SmartAnalysisDialog for current exercise or last completed."""
        target = self.current_text
        typed = ""
        elapsed = time.time()-self.start_time if self.start_time else 0
        try:
            typed = self.input.get("1.0","end-1c")
        except: typed=""
        # If exercise is completed and we have last report's texts, prefer those when 'last' flag and typed==target (cleared)
        if last and self.last_smart_report is not None:
            # try to use the report's drill? Actually dialog recomputes from current target/typed,
            # but if current input is empty after completion, we need to use last typed captured at completion.
            # We capture typed before nav; for simplicity, if typed is short (<5) and we have a cached report, show cached report via dialog override.
            # We'll just pass the last report's drill by reconstructing target/typed from report? Instead pass current typed if empty show message.
            if len(typed) < 5 and hasattr(self,'_last_typed') and self._last_typed:
                typed = self._last_typed
                target = self._last_target if hasattr(self,'_last_target') else target
        # Also store last for fallback
        self._last_typed = typed
        self._last_target = target
        if not typed or len(typed.strip())<1:
            # if no typed yet, but we have a last report, show that report's dialog by re-feeding its texts
            if self.last_smart_report is not None:
                # reconstruct from last typed/target saved
                pass
            else:
                messagebox.showinfo("Smart Analysis", "Type something first — then open Smart Analysis to see weakest letters & why.")
                return
        # require at least 5 chars vs target or we show still
        if len(typed) < 3 and not target:
            messagebox.showinfo("Smart Analysis", "Not enough data yet. Complete at least a few words.")
            return
        try:
            dlg = SmartAnalysisDialog(self, target, typed, elapsed)
        except Exception as e:
            messagebox.showerror("Smart Analysis failed", str(e))

    def _show_session_analysis(self):
        """Aggregated view across session — worst letters overall."""
        if not SMART_AVAILABLE:
            messagebox.showinfo("Smart Analysis", "Engine not available.")
            return
        try:
            ga = get_global_analyzer()
        except Exception:
            ga=None
        # fallback to local session reports
        reports = getattr(self,'smart_session_reports',[])
        if not reports and (ga is None or not getattr(ga,'reports',[])):
            messagebox.showinfo("Session Analysis", "No exercises completed yet. Finish one exercise to build session stats.")
            return
        # Build aggregated stats from global analyzer if available, else local
        if ga and getattr(ga,'reports',[]):
            worst = ga.aggregated_worst(topn=7)
            total_mis = sum(ga.mistake_counter.values())
            total = sum(ga.total_counter.values())
            acc = ga.overall_accuracy()
        else:
            # aggregate locally
            from collections import Counter
            tc=Counter(); mc=Counter()
            for r in reports:
                wl = r.worst_letters if hasattr(r,'worst_letters') else r.get('worst_letters',[])
                ls = r.letter_stats if hasattr(r,'letter_stats') else r.get('letter_stats',{})
                for ch,st in ls.items():
                    tc[ch]+=st.get('total',0)
                    mc[ch]+=st.get('mistakes',0)
            # worst
            tmp=[]
            for ch, tot in tc.items():
                mis=mc.get(ch,0)
                if mis:
                    tmp.append((ch, {"total":tot,"mistakes":mis,"accuracy": (tot-mis)/tot*100 if tot else 0, "error_rate": mis/max(1,tot)}))
            tmp.sort(key=lambda kv: (kv[1]["error_rate"], kv[1]["mistakes"]), reverse=True)
            worst=tmp[:7]
            total=sum(tc.values()); total_mis=sum(mc.values()); acc=(total-total_mis)/max(1,total)*100 if total else 100
        if not worst:
            messagebox.showinfo("Session Analysis", "No letter mistakes in this session — excellent!")
            return
        # Simple dialog showing aggregated worst
        win=tk.Toplevel(self)
        win.title("📊 Session Smart Analysis — All Exercises")
        win.geometry("560x420")
        win.transient(self); win.grab_set()
        ttk.Label(win, text="Session Overview — weakest letters across all exercises", font=("Segoe UI", 11, "bold"), padding=12).pack(anchor="w")
        ttk.Label(win, text=f"Overall accuracy {acc:.1f}%   Total errors {total_mis}/{total}", font=("Consolas", 10), padding=(12,0,12,8)).pack(anchor="w")
        fr=ttk.Frame(win, padding=10)
        fr.pack(fill="both", expand=True)
        for idx,(ch,st) in enumerate(worst):
            row=ttk.Frame(fr)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"'{ch}'", font=("Consolas", 12, "bold"), width=6).pack(side="left")
            pct=st["error_rate"]*100
            bar=tk.Canvas(row, width=260, height=16, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
            bar.pack(side="left", padx=6)
            bar.create_rectangle(0,0, int(pct/100*260),16, fill="#ef4444" if pct>30 else "#f97316" if pct>15 else "#facc15", outline="")
            ttk.Label(row, text=f"{st['mistakes']}/{st['total']}  {st['accuracy']:.0f}% acc", font=("Segoe UI", 9)).pack(side="left", padx=8)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)
        win.bind("<Escape>", lambda e: win.destroy())

    def _practice_weak_letters(self):
        """Generate drill from last or session worst and load as custom exercise."""
        if not SMART_AVAILABLE:
            messagebox.showinfo("Practice Drill", "Smart engine not available.")
            return
        # Prefer last report, else session aggregate
        rep=self.last_smart_report
        if rep is None:
            # try global
            try:
                ga=get_global_analyzer()
                worst=ga.aggregated_worst() if ga else []
                drill=""
                if worst:
                    # generate drill via analyze_text helper
                    from smart_analysis import _generate_drill  # type: ignore
                    drill=_generate_drill(worst)  # type: ignore
                if not drill:
                    messagebox.showinfo("Drill", "Finish an exercise first to detect weak letters.")
                    return
                # load drill
                self._load_drill_text(drill)
                return
            except Exception as e:
                messagebox.showerror("Drill error", str(e)); return
        # rep available
        drill = rep.drill_text if hasattr(rep,'drill_text') else rep.get('drill_text','') if isinstance(rep, dict) else ""
        if not drill:
            # generate on fly
            try:
                worst = rep.worst_letters if hasattr(rep,'worst_letters') else rep.get('worst_letters',[])
                from smart_analysis import _generate_drill  # type: ignore
                drill=_generate_drill(worst)
            except Exception:
                drill=""
        if not drill:
            messagebox.showinfo("Drill", "No weak letters — you’re perfect! Try a harder pack.")
            return
        self._load_drill_text(drill)

    def _load_drill_text(self, drill: str):
        custom_name="Smart Drill — Weak Letters"
        entry={"lesson":1,"sub":1,"ex":1,"text": drill,"raw": drill,"desc":"Smart drill","limit":120,"line_len":60,"repeat":False,"repeat_type":""}
        self.packs[custom_name]=[entry]
        self.pack_names=sorted(self.packs.keys())
        self.pack_combo["values"]=self.pack_names
        self.current_pack=custom_name
        self.pack_var.set(custom_name)
        self.current_lesson=1; self.current_sub=1; self.current_ex=1
        self._refresh_combos()
        self._load_exercise()
        messagebox.showinfo("Drill loaded", f"Drill for weakest letters loaded ({len(drill)} chars).\n\n{drill[:140]}...")

    def _open_custom(self):
        path=filedialog.askopenfilename(title="Open custom text", filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                txt=f.read().strip()
            if not txt:
                messagebox.showwarning("Empty", "File is empty")
                return
            # Create a synthetic pack entry
            custom_name=f"Custom — {os.path.basename(path)}"
            # Split into words and create a single exercise
            # Use current pack's line_len if exists else 60
            # Add to packs
            entry={"lesson":1,"sub":1,"ex":1,"text":txt,"raw":txt,"desc":"Custom","limit":120,"line_len":60,"repeat":False,"repeat_type":""}
            self.packs[custom_name]=[entry]
            self.pack_names=sorted(self.packs.keys())
            self.pack_combo["values"]=self.pack_names
            self.current_pack=custom_name
            self.pack_var.set(custom_name)
            self.current_lesson=1
            self.current_sub=1
            self.current_ex=1
            self._refresh_combos()
            self._load_exercise()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _show_about(self):
        win=tk.Toplevel(self)
        win.title(f"About Open-Typer {VERSION}")
        win.geometry("520x420")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        # Content
        frm=tk.Frame(win, padx=20, pady=20, bg="white")
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text="Open-Typer", font=("Segoe UI", 18, "bold"), bg="white", fg="#0f172a").pack(anchor="w")
        tk.Label(frm, text=f"Version {VERSION}  •  Revision {self._get_rev()}", bg="white", fg="#475569").pack(anchor="w")
        tk.Label(frm, text="", bg="white").pack()
        # Source
        def link(label, url):
            l=tk.Label(frm, text=label, fg="#2563eb", bg="white", cursor="hand2", font=("Segoe UI", 9, "underline"))
            l.pack(anchor="w", pady=1)
            l.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        link(f"Source code: {GITHUB}", GITHUB)
        tk.Label(frm, text=f"Copyright © 2021-2026 {AUTHOR}", bg="white", fg="#0f172a", font=("Segoe UI", 9)).pack(anchor="w", pady=(10,0))
        tk.Label(frm, text="Published with the GNU General Public License.", bg="white", fg="#64748b", font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(frm, text="", bg="white").pack()
        link(f"Designed & developed by Rahul S  →  {PORTFOLIO}", PORTFOLIO)
        link(f"GitHub: {GITHUB}", GITHUB)
        link(f"Email: {EMAIL}", f"mailto:{EMAIL}")
        link(f"Phone: {PHONE}  →  {WA}", WA)
        tk.Label(frm, text="LinkedIn  •  X  •  Instagram  •  Threads", bg="white", fg="#0f172a", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8,0))
        row=tk.Frame(frm, bg="white")
        row.pack(anchor="w")
        for txt,url in [("LinkedIn",LINKEDIN),("X @RahulShyamCv",X_URL),("Instagram",INSTA),("Threads",THREADS)]:
            l=tk.Label(row, text=txt, fg="#2563eb", bg="white", cursor="hand2", font=("Segoe UI", 8, "underline"))
            l.pack(side="left", padx=6)
            l.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        tk.Label(frm, text="", bg="white").pack()
        ttk.Button(frm, text="Close", command=win.destroy).pack(pady=10)
        win.bind("<Escape>", lambda e: win.destroy())
        win.focus_set()

    def _get_rev(self):
        try:
            import subprocess
            rev=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=os.path.dirname(__file__) if os.path.dirname(__file__) else ".", stderr=subprocess.DEVNULL).decode().strip()
            return rev[:7]
        except:
            return "5.3.0"

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            bg, fg, ebg, tbg = "#0f172a", "#e2e8f0", "#1e293b", "#1e293b"
        else:
            bg, fg, ebg, tbg = "#f5f5f5", "#0f172a", "white", "#ffffff"
        self.configure(bg=bg)
        try:
            self.display.config(bg=ebg, fg=fg, insertbackground=fg)
            self.input.config(bg=ebg, fg=fg, insertbackground=fg)
        except:
            pass

    def _global_key(self, event):
        # Ctrl+R restart, Ctrl+N next etc
        if event.state & 0x4: # Ctrl
            if event.keysym.lower()=="r":
                self._restart()
            elif event.keysym.lower()=="n":
                self._nav(1)
            elif event.keysym.lower()=="p":
                self._nav(-1)

def main():
    packs_dir=find_packs_dir()
    packs=load_packs(packs_dir)
    # If no packs found, create demo pack like TypeArena
    if not packs:
        demo_text="ff jj ff jj jjfj djjj jjdf dfjf fdjd ddfj fdfd jjdf jjjd dfdj jdjf dffd jddd fdjj"
        packs={"Demo (no packs found)": [{"lesson":1,"sub":1,"ex":1,"text":demo_text,"raw":demo_text,"desc":"Demo","limit":120,"line_len":60}]}
    app=TypingApp(packs)
    app.mainloop()

if __name__=="__main__":
    main()
