"""
Code Runner Module
"""
import subprocess
import time
import sys
import os
import traceback

from web_utils import _start_web_process, _open_browser_if_needed, _kill_process_tree, _is_port_open, _create_output_reader_thread


def execute_python_code(filepath, timeout=None, input_text=None):
    """
    Execute Python file as a subprocess, supporting input, capturing output, and proper timeout handling.
    """
    try:
        abs_filepath = os.path.abspath(filepath)

        if not os.path.exists(abs_filepath):
            return {"success": False, "error": f"file not found {abs_filepath}"}

        # Start subprocess (interactive)
        process = subprocess.Popen(
            [sys.executable, abs_filepath],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(abs_filepath),
            encoding='utf-8'
        )

        try:
            stdout, stderr = process.communicate(
                input=input_text,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            # Don't kill subprocess, only return current output in case debugging is needed
            process.kill()
            stdout, stderr = process.communicate()

            return {
                "success": False,
                "error": f"timeout {timeout} seconds",
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
                "filepath": abs_filepath
            }

        # Program exited normally = success
        return {
            "success": process.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode,
            "filepath": abs_filepath
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Execution exception: {str(e)}",
            "stdout": "",
            "stderr": traceback.format_exc(),
            "filepath": filepath
        }


# ---------------- Start Web Server ----------------
def run_web_server(filepath, open_browser=True, max_wait=15):
    abs_filepath = os.path.abspath(filepath)
    print(f"\nStarting web server: {abs_filepath}")

    process = _start_web_process(abs_filepath)
    output_lines = []
    _create_output_reader_thread(process, output_lines)

    default_ports = [5000, 8000, 8080, 3000, 8501]
    waited, poll = 0, 0.2
    server_url = None

    while waited < max_wait:
        if process.poll() is not None:
            return {"success": False, "error": "Server exited unexpectedly", "process": process,
                    "output_lines": output_lines}

        for p in default_ports:
            if _is_port_open("127.0.0.1", p):
                server_url = f"http://127.0.0.1:{p}"
                break
        if server_url:
            break

        time.sleep(poll)
        waited += poll

    if not server_url:
        return {"success": False, "error": "Server did not start in time", "process": process,
                "output_lines": output_lines}

    _open_browser_if_needed(server_url, open_browser)
    return {"success": True, "process": process, "url": server_url, "output_lines": output_lines}


# ---------------- Run main.py ----------------
def run_main_web_app(main_path, open_browser=True, run_timeout=None, result_container=None):
    if result_container is None:
        result_container = {}

    server_info = run_web_server(main_path, open_browser=open_browser)
    result_container["server_process"] = server_info.get("process")
    result_container["server_output"] = server_info.get("output_lines", [])
    result_container["server_url"] = server_info.get("url")

    if not server_info["success"]:
        result_container["server_error"] = server_info.get("error", "failed to run web server")
        return False

    process = server_info["process"]
    output_lines = server_info["output_lines"]
    server_url = server_info.get("url")

    print(f"Server running at: {server_url}")
    print("Press Ctrl+C to stop the server.")

    last_len = 0
    start_time = time.time()

    try:
        while True:
            # capture new output
            new_lines = output_lines[last_len:]
            last_len = len(output_lines)
            for i, line in enumerate(new_lines):
                if "Traceback (most recent call last)" in line:
                    tb = "\n".join(new_lines[i:])
                    result_container["server_error"] = tb
                    _kill_process_tree(process)
                    return False

            # Subprocess exited unexpectedly
            if process.poll() is not None:
                if "server_error" not in result_container:
                    result_container["server_error"] = "Web server stopped unexpectedly"
                return False

            # Timeout stop
            if run_timeout and time.time() - start_time > run_timeout:
                print(f"Server ran for {run_timeout}s, stopping...")
                _kill_process_tree(process)
                return True

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nCtrl+C pressed, stopping server...")
        if process.poll() is None:
            _kill_process_tree(process)
        return True


def run_main_as_console_app(main_path, run_timeout=None):
    """
    Run main.py as a real console application, preserving user interaction while capturing exception information.
    """
    import tempfile

    print("\n" + "=" * 60)
    print("run main.py")
    print("=" * 60)

    abs_main = os.path.abspath(main_path)
    cwd = os.path.dirname(abs_main)

    # temp file capture stderr
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as err_file:
        process = subprocess.Popen(
            [sys.executable, abs_main],
            cwd=cwd,
            stdin=None,  # Inherit current console
            stdout=None,  # Inherit current console
            stderr=err_file  # Write stderr to temporary file
        )

        start_time = time.time()

        try:
            while True:
                ret = process.poll()
                if ret is not None:
                    # Program exited, read stderr
                    err_file.seek(0)
                    stderr_content = err_file.read()

                    return {
                        "success": (ret == 0),
                        "returncode": ret,
                        "stdout": "",  # Direct console output
                        "stderr": stderr_content,
                        "error": None if ret == 0 else "failed to run",
                        "filepath": abs_main
                    }

                if run_timeout and (time.time() - start_time) > run_timeout:
                    process.kill()
                    err_file.seek(0)
                    stderr_content = err_file.read()

                    return {
                        "success": False,
                        "error": f"time out{run_timeout}seconds. terminate now",
                        "stdout": "",
                        "stderr": stderr_content,
                        "returncode": None,
                        "filepath": abs_main
                    }

                time.sleep(0.1)

        except Exception as e:
            process.kill()
            err_file.seek(0)
            stderr_content = err_file.read()

            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": stderr_content,
                "returncode": None,
                "filepath": abs_main
            }
