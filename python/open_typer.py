#!/usr/bin/env python3
"""
Open-Typer 5.3.0 — Real Typing Tutor by Rahul Shyam
Tkinter implementation that mirrors the Qt/QML Open-Typer logic.
Pack parsing based on ConfigParser.cpp logic.
"""
import os, sys, time, webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Branding ---
VERSION = "5.3.0"
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

class TypingApp(tk.Tk):
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

        ctrl.columnconfigure(8, weight=1)

        # Stats bar
        stats = tk.Frame(self, bg="#e2e8f0", height=34)
        stats.pack(fill="x", padx=10, pady=(0,6))
        stats.pack_propagate(False)
        self.wpm_var=tk.StringVar(value="WPM: 0")
        self.acc_var=tk.StringVar(value="Accuracy: 100%")
        self.time_var=tk.StringVar(value="Time: 00:00")
        self.err_var=tk.StringVar(value="Errors: 0")
        for var in [self.wpm_var, self.acc_var, self.time_var, self.err_var]:
            tk.Label(stats, textvariable=var, bg="#e2e8f0", fg="#0f172a", font=("Consolas", 10, "bold")).pack(side="left", padx=16, pady=6)
        self.progress_var=tk.StringVar(value="Idle")
        tk.Label(stats, textvariable=self.progress_var, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9)).pack(side="right", padx=12)

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
        filem.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filem)
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
        # Check completion
        if current == target and len(target)>0:
            self._on_complete()
        # Also handle if typed longer than target -> extra errors
        if len(current) > len(target):
            self.err_var.set(f"Errors: {errs} (+{len(current)-len(target)} extra)")

    def _update_stats(self):
        typed=self.typed
        errs=self.errors
        total=len(self.current_text) if self.current_text else 1
        elapsed = time.time()-self.start_time if self.start_time else 0
        # Accuracy
        acc = max(0, (typed - errs) / max(1, typed) * 100) if typed>0 else 100
        self.acc_var.set(f"Accuracy: {acc:.1f}%")
        self.err_var.set(f"Errors: {errs}")
        # WPM: (correct chars /5) / minutes
        correct = max(0, typed - errs)
        minutes = elapsed/60 if elapsed>0 else 1/60
        wpm = (correct/5) / minutes if minutes>0 else 0
        # But if not started, wpm 0
        if self.start_time is None:
            wpm=0
        self.wpm_var.set(f"WPM: {wpm:.0f}")
        # Progress
        pct = min(100, typed/len(self.current_text)*100) if self.current_text else 0
        self.progress_var.set(f"Lesson {self.current_lesson} • Sub {self.current_sub} • Ex {self.current_ex} — {pct:.0f}%  —  {len(self.current_text)} chars")

    def _update_timer(self):
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
        # Add to history
        hist = f"{self.current_pack} L{self.current_lesson}.{self.current_sub}.{self.current_ex} — WPM {wpm:.0f} Acc {acc:.1f}% Time {int(elapsed//60):02d}:{int(elapsed%60):02d}"
        self.history.insert(0, hist)
        self.history=self.history[:5]
        self.history_label.config(text="\n".join(self.history) if self.history else "—")
        # Show dialog
        msg = f"Exercise completed!\n\nPack: {self.current_pack}\nLesson {self.current_lesson} • Sublesson {self.current_sub} • Exercise {self.current_ex}\n\nWPM: {wpm:.0f}\nAccuracy: {acc:.1f}%\nErrors: {self.errors}\nTime: {int(elapsed//60):02d}:{int(elapsed%60):02d}\n\nNext exercise?"
        if messagebox.askyesno("Completed", msg):
            self._nav(1)
        else:
            # stay but allow restart
            pass

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
