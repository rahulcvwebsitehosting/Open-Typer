# Open-Typer Python — Real Typing App by Rahul Shyam

This is a **Tkinter** re-implementation of Open-Typer's typing logic, so the Windows exe *is* the typing tutor itself — not just a launcher.
- **File**: open_typer.py (1019 lines) / ../Open-Typer-Typing-App.py
- **Version**: 5.3.2  •  **Author**: Rahul Shyam — https://rahulshyam-portfolio.vercel.app/
- **Packs**: loads real `res/packs/*` via ConfigParser logic (lesson/sub/ex, repeat, line_len, generateText) + `COMMON_WORDS` (1000 LiveChat words)
- **Features**: Pack/Lesson/Sublesson/Exercise selectors, WPM/CPM/Accuracy/Time/Errors live, dark/light theme, history (last 5), custom .txt import, next/prev/restart (Ctrl+R/N/P)
- **NEW 5.3.2 — Para Time Attack** (inspired by typing.com 1/3/5 min + LiveChat 60s + Typewizz cert):
  - **File → Para Time Attack...** or **Test → Quick 60s** — dialog with `Time: 15s/30s/60s/2m30s/3m/5m/10m/Custom`, `Source: Random Words (1000 common) / Paragraph Prose (Typewizz continuous) / Current Exercise / Custom File`, `Length: Short 150 / Medium 300 / Long 600 / Full Page`
  - **Live HUD**: `WPM (net)`, `CPM (net/gross)`, `Accuracy`, `Time remaining`, `Progress bar` (red <10s), `Cert preview`
  - **Formulas**: `CPM = correct/min`, `WPM = CPM/5` (LiveChat de-facto), `Accuracy = correct/typed`, **Gross vs Net** shown
  - **End card**: WPM/CPM gross/net, accuracy, errors, error-words, **Gold 350 CPM 99.5% (8%) / Silver 250 98.5% (21%) / Bronze 200 96.5% (39%)** (Typewizz) + Retry/Next/Error-words

## Run without building exe
```bash
python python/open_typer.py
# or
python Open-Typer-Typing-App.py
```

## Build exe (as released)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Open-Typer" --icon res/icons/icon.ico --add-data "res/packs;res/packs" --add-data "res/icons;res/icons" python/open_typer.py
# dist/Open-Typer.exe  (~11.5 MB)
```

The released `Open-Typer-5.3.2-Typing-App.exe` (11.5 MB windowed, icon, bundled packs) and `.zip` in [Releases](https://github.com/rahulcvwebsitehosting/Open-Typer/releases/tag/v5.3.2) are built from this source.

Original Qt/C++ build still available via `qmake && make` and GitHub Actions `windows-build.yml` (Qt 6.5.2, MinGW 11.2). See `TimeDialog.qml:27` for Qt time limits.
