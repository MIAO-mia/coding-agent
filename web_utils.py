"""
Web-related utility functions
"""
import socket
import subprocess
import threading
import webbrowser
import sys
import os
import psutil


def _start_web_process(abs_filepath):
    return subprocess.Popen(
        [sys.executable, abs_filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # stderr merged into stdout
        text=True,
        encoding='utf-8',
        bufsize=1,
        cwd=os.path.dirname(abs_filepath)
    )

# ---------------- Port detection ----------------
def _is_port_open(host, port, timeout=0.2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

# ---------------- Real-time output reading ----------------
def _create_output_reader_thread(process, output_lines):
    def read_output():
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.rstrip()
                output_lines.append(line)
                print(line, flush=True)
    t = threading.Thread(target=read_output, daemon=True)
    t.start()
    return t

# ---------------- Browser opening ----------------
def _open_browser_if_needed(url, open_browser):
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"can't open browser: {e}")

# ---------------- Process termination ----------------
def _kill_process_tree(proc):
    try:
        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        pass

