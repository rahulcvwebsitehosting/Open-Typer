# Open-Typer Python — Real Typing App by Rahul Shyam

This is a **Tkinter** re-implementation of Open-Typer's typing logic, so the Windows exe *is* the typing tutor itself — not just a launcher.

- **File**: open_typer.py (676 lines) / ../Open-Typer-Typing-App.py
- **Version**: 5.3.0  •  **Author**: Rahul Shyam — https://rahulshyam-portfolio.vercel.app/
- **Packs**: loads real es/packs/* via ConfigParser logic (lesson/sub/ex, repeat, line_len, generateText)
- **Features**: Pack/Lesson/Sublesson/Exercise selectors, WPM/Accuracy/Time/Errors live, dark/light theme, history (last 5), custom .txt import (File → Open), next/prev/restart (Ctrl+R/N/P)

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

The released Open-Typer-5.3.0-Typing-App.exe (windowed, 11.5 MB) and .zip in [Releases](https://github.com/rahulcvwebsitehosting/Open-Typer/releases/tag/v5.3.0) are built from this source.

Original Qt/C++ build still available via qmake && make and GitHub Actions windows-build.yml.
