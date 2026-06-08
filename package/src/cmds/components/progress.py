import os
import sys
import threading
import time

# . -> .. -> ... -> .. -> .
DOT_FRAMES = ["   ", ".  ", ".. ", "...", ".. ", ".  "]

DIM = "\033[2m"
RESET = "\033[0m"
CLEAR_LINE = "\033[2K"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

class ProgressBar:
    def __init__(self, total: int):
        self._total = total
        self._current = 0
        self._lock = threading.Lock()
        self._stopped = False
        self._dot_frame = 0
        self._pending_logs: list[str] = []
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.flush()
        self._thread.start()

    def log(self, msg: str):
        with self._lock:
            self._pending_logs.append(msg)

    def advance(self, amount: int = 1):
        with self._lock:
            self._current = min(self._current + amount, self._total)

    def stop(self):
        with self._lock:
            self._stopped = True
        self._thread.join()
        sys.stdout.write(f"\r{CLEAR_LINE}")
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()

    def _render(self):
        with self._lock:
            current = self._current
            total = self._total
            pending = self._pending_logs[:]
            self._pending_logs.clear()
            dots = DOT_FRAMES[self._dot_frame % len(DOT_FRAMES)]
            self._dot_frame += 1

        pct = int((current / total) * 100) if total > 0 else 0

        for msg in pending:
            sys.stdout.write(f"\r{CLEAR_LINE}{DIM}{msg}{RESET}\n")
            sys.stdout.flush()

        try:
            cols = os.get_terminal_size().columns
        except OSError:
            cols = 80

        pct_str = f"{pct}%"
        left = f"Building{dots}"
        gap = cols - len(left) - len(pct_str)
        if gap < 1:
            gap = 1
        sys.stdout.write(f"\r{CLEAR_LINE}{left}{' ' * gap}{pct_str}")
        sys.stdout.flush()

    def _loop(self):
        while True:
            self._render()
            time.sleep(0.18)
            with self._lock:
                if self._stopped:
                    break

def countBuildWork(
    sourceDir: str | None,
    pluginDir: str,
    ignoreAbsPaths: set,
    compileLevel: int | None,
    obfuscation: list | None,
    checkAstFlag: bool,
) -> int:
    total = 0 # setup phase
    total += 3
    pyFiles = 0
    
    if sourceDir and os.path.isdir(sourceDir):
        for root, dirs, files in os.walk(sourceDir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(".py"):
                    absPath = os.path.join(root, file)
                    if os.path.normpath(absPath) not in ignoreAbsPaths:
                        pyFiles += 1
    totalFiles = 0
    
    for root, dirs, files in os.walk(pluginDir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        totalFiles += len(files)

    if checkAstFlag:
        total += pyFiles
    if obfuscation is not None:
        total += pyFiles
    if compileLevel is not None:
        total += pyFiles * 2
    total += totalFiles + 2
    return max(total, 1)
