# === Custom-Nerd/Nerd-Engine Server Runner ===
# For: All users starting the Uvicorn backend (runs via WSL2 on Windows).

import os
import sys
import subprocess
import platform
import webbrowser
import socket
import datetime
import re
import shutil
import time
from pathlib import Path

# Import WSL functions from setup.py
try:
    from setup import (
        check_wsl_installed,
        check_ubuntu_setup_complete,
        windows_path_to_wsl
    )
except ImportError:
    # Fallback if setup.py is not available
    def check_wsl_installed(logger):
        return False, None
    def check_ubuntu_setup_complete(logger, distro="Ubuntu"):
        return False
    def windows_path_to_wsl(windows_path):
        path_str = str(windows_path).replace('\\', '/')
        if ':' in path_str:
            drive_letter = path_str[0].lower()
            path_str = path_str.replace(f'{drive_letter}:', f'/mnt/{drive_letter}')
        return path_str

# ------------------------------------------------------------------------------------
# IMPORTANT: Run the backend in a Linux environment (native Linux or WSL2 on Windows).
# Reason:
# The backend depends on Python packages that need native C/C++ compilation.
# On Windows, these often fail to build due to missing MSVC toolchains and POSIX
# headers, leading to errors for packages like:
#   - chroma-hnswlib
#   - greenlet
#   - httptools
#   - kiwisolver
#   - numpy (Meson-based)
#   - Levenshtein
#
# For macOS/Linux users:
#   - Run normally.
#
# For Windows users:
#   - Use WSL2 (Ubuntu) to run this script and the backend.
#   - This avoids Windows compiler issues and matches the supported Linux toolchain.
#
# TLDR: Use Linux/WSL2 to avoid Python build failures on Windows.
# ------------------------------------------------------------------------------------

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

    @staticmethod
    def print(text, color=RESET):
        if platform.system() == "Windows":
            print(text)
        else:
            print(f"{color}{text}{Colors.RESET}")

def open_browser_cross_platform(url_or_path, logger):
    """
    Open browser/URL cross-platform, handling WSL correctly.
    
    Rules:
    - WSL → Convert WSL path to Windows path, then open in browser
    - Windows native → cmd.exe start (handles both URLs and file paths)
    - macOS/Linux → webbrowser module
    
    Args:
        url_or_path: URL (http://...) or file path (file://... or absolute path)
        logger: Logger instance for output
    """
    is_wsl_env = bool(os.environ.get("WSL_DISTRO_NAME"))
    system = platform.system()
    # Only consider it WSL if we're on Linux platform AND have WSL_DISTRO_NAME
    # This prevents false detection on Windows native
    is_wsl = (system == "Linux") and is_wsl_env

    try:
        if is_wsl:
            # WSL: Convert file:// URL or WSL path to Windows path, then open in browser
            if url_or_path.startswith("file://"):
                # Extract path from file:// URL
                # file:///mnt/c/Users/... -> /mnt/c/Users/...
                path = url_or_path.replace("file://", "")
            else:
                path = url_or_path
            
            # Convert WSL path (/mnt/c/Users/...) to Windows path (C:\Users\...)
            if path.startswith("/mnt/"):
                # /mnt/c/Users/... -> C:\Users\...
                path_parts = [p for p in path.split("/") if p]  # Remove empty strings from split
                if len(path_parts) >= 2 and path_parts[0] == "mnt":
                    drive_letter = path_parts[1].upper()  # 'c' -> 'C'
                    windows_path = f"{drive_letter}:\\" + "\\".join(path_parts[2:])
                    # Use Windows start command to open HTML file in default browser
                    # The empty string after "start" tells Windows to use default handler
                    subprocess.Popen(["cmd.exe", "/c", "start", "", windows_path])
                    logger.log(f"✅ Opened index.html in browser: {windows_path}", Colors.GREEN)
                else:
                    logger.log(f"⚠️ Could not convert WSL path: {path}", Colors.YELLOW)
            elif path.startswith("http://") or path.startswith("https://"):
                # URL - use cmd.exe start to open in default browser
                subprocess.Popen(["cmd.exe", "/c", "start", "", path])
                logger.log(f"✅ Opened URL in browser: {path}", Colors.GREEN)
            else:
                # Assume it's already a Windows path or URL
                subprocess.Popen(["cmd.exe", "/c", "start", "", path])
                logger.log(f"✅ Opened in browser: {path}", Colors.GREEN)

        elif system == "Windows":
            # Windows native (not WSL)
            # Handle both file paths and URLs
            if url_or_path.startswith("file://"):
                # Convert file:// URL to Windows path
                # file:///C:/path/to/file.html -> C:\path\to\file.html
                path_str = url_or_path.replace("file:///", "").replace("/", "\\")
                # Remove leading slash if present (file:///C: -> C:)
                if path_str.startswith("\\"):
                    path_str = path_str[1:]
                subprocess.Popen(["cmd.exe", "/c", "start", "", path_str])
                logger.log(f"✅ Opened: {path_str}", Colors.GREEN)
            elif os.path.exists(url_or_path) or "\\" in url_or_path or (len(url_or_path) > 1 and url_or_path[1] == ":"):
                # It's a file path (absolute Windows path like C:\path\to\file.html)
                subprocess.Popen(["cmd.exe", "/c", "start", "", url_or_path])
                logger.log(f"✅ Opened: {url_or_path}", Colors.GREEN)
            else:
                # Regular URL (http://...)
                subprocess.Popen(["cmd.exe", "/c", "start", "", url_or_path])
                logger.log(f"✅ Opened: {url_or_path}", Colors.GREEN)

        else:
            # macOS / Linux native
            webbrowser.open(url_or_path)
            logger.log(f"✅ Opened: {url_or_path}", Colors.GREEN)

    except Exception as e:
        logger.log(f"⚠️ Failed to open browser automatically: {e}", Colors.YELLOW)
        logger.log(f"   Please open manually: {url_or_path}", Colors.CYAN)


def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def build_log_file(base_dir, kind):
    logs_dir = base_dir / "logs" / kind
    logs_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    day = now.strftime("%d")
    mon = now.strftime("%b")
    year = now.strftime("%Y")
    hour = now.strftime("%I").lstrip("0") or "0"
    minute = now.strftime("%M")
    ampm = now.strftime("%p").lower()
    ts = f"{day}_{mon}_{year}_{hour}_{minute}_{ampm}"
    return logs_dir / f"{kind}_{ts}.log"


class RunLogger:
    def __init__(self, log_file_path):
        self.log_file = open(log_file_path, "w", encoding="utf-8")
        self.log_file.write(f"Run Log - Started at {datetime.datetime.now()}\n")
        self.log_file.write("=" * 50 + "\n")
        
        # Enable ANSI colors on Windows 10+ if available
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable ANSI escape sequence processing
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass  # If it fails, colors won't work but script will continue

    def log(self, text, color=None, end="\n"):
        # Print to console
        # If text already contains color codes, use them directly
        # Otherwise, apply the color parameter
        if color and Colors.CYAN not in text and Colors.YELLOW not in text and Colors.RED not in text and Colors.GREEN not in text:
            Colors.print(text, color)
        else:
            Colors.print(text)
        
        # Write to file (always strip ANSI codes for file)
        clean_text = strip_ansi(text)
        if end == "\n":
            timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
            self.log_file.write(f"{timestamp}{clean_text}\n")
        else:
            self.log_file.write(clean_text)
        self.log_file.flush()

    def raw(self, text):
        clean_text = strip_ansi(text)
        self.log_file.write(clean_text)
        self.log_file.flush()

    def close(self):
        self.log_file.write("\n" + "=" * 50 + "\n")
        self.log_file.write(f"Run Log - Finished at {datetime.datetime.now()}\n")
        self.log_file.close()


def is_port_free(port):
    """Return True if the port is free, False if something is already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


def kill_process_on_port(port, logger):
    """
    Find and kill the process listening on the given port.
    Returns True if a process was killed and port is now free, False otherwise.
    """
    system = platform.system()
    pids = []
    try:
        if system in ("Darwin", "Linux"):
            # lsof -i :8000 -t returns PIDs only
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        elif system == "Windows":
            # netstat -ano | findstr :8000
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in (result.stdout or "").splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.append(pid)
            pids = list(dict.fromkeys(pids))  # dedupe
    except Exception as e:
        logger.log(f"⚠️ Could not find process on port {port}: {e}", Colors.YELLOW)
        return False

    if not pids:
        return False

    for pid in pids:
        try:
            if system in ("Darwin", "Linux"):
                subprocess.run(["kill", "-9", pid], capture_output=True, timeout=5)
            else:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=5)
            logger.log(f"   Killed process {pid}", Colors.CYAN)
        except Exception:
            pass

    time.sleep(1)
    return is_port_free(port)


def run_setup_wizard(base_dir, logger):
    """Run the setup.py script if the virtual environment is missing."""
    setup_script = base_dir / "setup.py"
    if not setup_script.exists():
        logger.log(f"❌ First-time setup required, but {setup_script} is missing.", Colors.RED)
        sys.exit(1)

    logger.log("🛠️ First-time setup detected. Running setup.py ...", Colors.YELLOW)
    try:
        subprocess.check_call([sys.executable, str(setup_script)])
    except subprocess.CalledProcessError:
        logger.log("❌ Setup failed. Please review the errors above and retry.", Colors.RED)
        sys.exit(1)



def run_health_checks(backend_dir, venv_python, logger):
    logger.log("🏥 Running Pre-flight Health Checks...", Colors.BLUE)
    
    # 1. Check for main.py
    main_py = backend_dir / "main.py"
    if not main_py.exists():
        logger.log(f"❌ Critical Error: 'main.py' not found in {backend_dir}", Colors.RED)
        return False
    logger.log("✅ main.py found", Colors.GREEN)

    # 2. Check if venv python works
    try:
        subprocess.check_call([str(venv_python), "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.log("✅ Virtual environment Python executable is functional", Colors.GREEN)
    except Exception:
        logger.log("❌ Critical Error: Virtual environment Python is not working!", Colors.RED)
        return False

    # 3. Check if Uvicorn is installed in venv
    try:
        subprocess.check_call([str(venv_python), "-m", "uvicorn", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.log("✅ Uvicorn is installed correctly", Colors.GREEN)
    except subprocess.CalledProcessError:
        logger.log("⚠️ Uvicorn is NOT installed in the virtual environment.", Colors.YELLOW)
        logger.log("🔧 Attempting to install uvicorn...", Colors.CYAN)
        
        try:
            # Determine pip command - prefer python -m pip for better compatibility
            install_cmd = [str(venv_python), "-m", "pip", "install", "uvicorn"]
            
            # Show command with visual separator
            cmd_str = " ".join(install_cmd)
            logger.log("", Colors.RESET)
            logger.log("   " + "─" * 70, Colors.CYAN)
            logger.log(f"   {Colors.CYAN}┌─ [Internal Check] ────────────────────────────────────────────────┐{Colors.RESET}", Colors.RESET)
            logger.log(f"   {Colors.CYAN}│{Colors.RESET} Running: {cmd_str}", Colors.RESET)
            logger.log(f"   {Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.RESET}", Colors.RESET)
            logger.log("", Colors.RESET)
            
            result = subprocess.run(
                install_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
                cwd=str(backend_dir)
            )
            
            # Display output
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.log(f"   {Colors.CYAN}│{Colors.RESET} {line.rstrip()}", Colors.RESET)
            
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.log(f"   {Colors.CYAN}│{Colors.RESET} {Colors.YELLOW}{line.rstrip()}{Colors.RESET}", Colors.RESET)
            
            # Close box
            status_color = Colors.GREEN if result.returncode == 0 else Colors.RED
            status_icon = "✓" if result.returncode == 0 else "✗"
            logger.log("", Colors.RESET)
            logger.log(f"   {Colors.CYAN}┌─ [Internal Check] Result ─────────────────────────────────────────┐{Colors.RESET}", Colors.RESET)
            logger.log(f"   {Colors.CYAN}│{Colors.RESET} {status_icon} Exit code: {status_color}{result.returncode}{Colors.RESET}", Colors.RESET)
            logger.log(f"   {Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.RESET}", Colors.RESET)
            logger.log("", Colors.RESET)
            
            if result.returncode == 0:
                logger.log("✅ Uvicorn installed successfully", Colors.GREEN)
                # Verify installation
                try:
                    subprocess.check_call([str(venv_python), "-m", "uvicorn", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.log("✅ Uvicorn verified and ready", Colors.GREEN)
                except subprocess.CalledProcessError:
                    logger.log("⚠️ Uvicorn installation completed but verification failed.", Colors.YELLOW)
                    logger.log("   Please run 'python3 setup.py' to fix dependencies.", Colors.YELLOW)
                    return False
            else:
                logger.log("❌ Failed to install uvicorn automatically.", Colors.RED)
                logger.log(f"   Error: {result.stderr[:200] if result.stderr else 'Unknown error'}", Colors.YELLOW)
                logger.log("   Please run 'python3 setup.py' to fix dependencies.", Colors.YELLOW)
                return False
        except subprocess.TimeoutExpired:
            logger.log("⏱️ Uvicorn installation timed out.", Colors.YELLOW)
            logger.log("   Please run 'python3 setup.py' to fix dependencies.", Colors.YELLOW)
            return False
        except Exception as e:
            logger.log(f"❌ Error installing uvicorn: {e}", Colors.RED)
        logger.log("   Please run 'python3 setup.py' to fix dependencies.", Colors.YELLOW)
        return False

    # 4. Check if Port 8000 is free; if busy, try to kill and retry
    if not is_port_free(8000):
        logger.log("⚠️ Port 8000 is busy. Killing existing process and retrying...", Colors.YELLOW)
        if kill_process_on_port(8000, logger):
            logger.log("✅ Freed port 8000, continuing...", Colors.GREEN)
        else:
            logger.log("❌ Port 8000 is still busy. Close the existing server or pick another port.", Colors.RED)
            return False
    else:
        logger.log("✅ Port 8000 is available", Colors.GREEN)
    
    return True

def main():
    base_dir = Path(__file__).parent.absolute()
    log_file_path = build_log_file(base_dir, "run")
    logger = RunLogger(log_file_path)
    logger.log(f"📝 Logging run output to: {log_file_path}", Colors.YELLOW)

    try:
        logger.log("🚀 Starting Uvicorn Server...", Colors.RESET)

        # 1. Detect OS
        os_name = platform.system()
        if os_name == "Darwin":
            platform_name = "Mac"
        elif os_name == "Linux":
            platform_name = "Linux"
        elif os_name == "Windows":
            platform_name = "Windows"
            logger.log("🪟 Running on Windows...", Colors.RESET)
            logger.log("", Colors.RESET)
            
            # Check if we're already running inside WSL
            is_wsl = bool(os.environ.get('WSL_DISTRO_NAME'))
            if is_wsl:
                wsl_distro = os.environ.get('WSL_DISTRO_NAME', 'Unknown')
                # Verify it's Ubuntu specifically
                if 'ubuntu' in wsl_distro.lower() or 'Ubuntu' in wsl_distro:
                    logger.log(f"✅ Already running inside WSL2 (Ubuntu: {wsl_distro}). Proceeding...", Colors.GREEN)
                else:
                    logger.log(f"⚠️ Running inside WSL2 but distribution is '{wsl_distro}', not Ubuntu.", Colors.YELLOW)
                    logger.log("   This script is optimized for Ubuntu. Proceeding anyway...", Colors.CYAN)
                logger.log("", Colors.RESET)
            else:
                # We're on Windows but NOT in WSL - ask user to manually enter WSL
                logger.log("🔍 Detected Windows outside WSL.", Colors.BLUE)
                logger.log("", Colors.RESET)
                
                script_path = Path(__file__).absolute()
                distro = "Ubuntu"  # Default to Ubuntu
                
                # Check for WSL2 installation
                try:
                    wsl_installed, detected_distro = check_wsl_installed(logger)
                    
                    if not wsl_installed:
                        logger.log("", Colors.RESET)
                        logger.log("❌ WSL2 is not installed.", Colors.RED)
                        logger.log("", Colors.RESET)
                        logger.log("📋 To set up WSL2, run:", Colors.CYAN)
                        logger.log("", Colors.RESET)
                        logger.log("   python presetup.py", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        logger.log("Or manually install WSL2:", Colors.CYAN)
                        logger.log("   1. Open PowerShell as Administrator", Colors.YELLOW)
                        logger.log("   2. Run: wsl --install", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        sys.exit(1)
                    
                    if detected_distro:
                        distro = detected_distro
                    
                    if not detected_distro:
                        logger.log("", Colors.RESET)
                        logger.log("⚠️ WSL is installed but Ubuntu distribution not found.", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        logger.log("📋 To install Ubuntu, run:", Colors.CYAN)
                        logger.log("", Colors.RESET)
                        logger.log("   python presetup.py", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        logger.log("Or manually install Ubuntu:", Colors.CYAN)
                        logger.log("   wsl --install -d Ubuntu", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        sys.exit(1)
                    
                    # Verify Ubuntu is ready
                    if not check_ubuntu_setup_complete(logger, distro):
                        logger.log("", Colors.RESET)
                        logger.log("⚠️ Ubuntu is installed but needs initial user setup.", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        logger.log("📋 To complete Ubuntu setup, run:", Colors.CYAN)
                        logger.log("", Colors.RESET)
                        logger.log("   python presetup.py", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        logger.log("Or manually complete Ubuntu setup:", Colors.CYAN)
                        logger.log("   1. Launch Ubuntu: wsl -d Ubuntu", Colors.YELLOW)
                        logger.log("   2. Create your username and password when prompted", Colors.YELLOW)
                        logger.log("   3. Wait for Ubuntu to finish initializing", Colors.YELLOW)
                        logger.log("   4. Run this script again", Colors.YELLOW)
                        logger.log("", Colors.RESET)
                        sys.exit(1)
                    
                    # Convert Windows paths to WSL paths
                    wsl_base_dir = windows_path_to_wsl(base_dir)
                    script_filename = script_path.name
                    
                    logger.log("", Colors.RESET)
                    logger.log("=" * 50, Colors.GREEN)
                    logger.log("📋 MANUAL WSL ENTRY REQUIRED", Colors.GREEN)
                    logger.log("=" * 50, Colors.GREEN)
                    logger.log("", Colors.RESET)
                    logger.log("✅ WSL2 and Ubuntu are ready!", Colors.GREEN)
                    logger.log("", Colors.RESET)
                    logger.log("📋 Please run the following commands manually:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("   1. Open a new terminal/PowerShell window", Colors.YELLOW)
                    logger.log(f"   2. Run: wsl -d {distro}", Colors.YELLOW)
                    logger.log(f"   3. Navigate to your project: cd Downloads/customnerd-main/customnerd-main/", Colors.YELLOW)
                    logger.log("      (Path may vary depending on where you downloaded the project)", Colors.CYAN)
                    logger.log(f"   4. Run: python3 {script_filename}", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    sys.exit(0)
                    
                except FileNotFoundError:
                    # WSL command not found - WSL is not installed
                    logger.log("", Colors.RESET)
                    logger.log("❌ WSL2 is not installed.", Colors.RED)
                    logger.log("", Colors.RESET)
                    logger.log("📋 To set up WSL2, run:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("   python presetup.py", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    logger.log("Or manually install WSL2:", Colors.CYAN)
                    logger.log("   1. Open PowerShell as Administrator", Colors.YELLOW)
                    logger.log("   2. Run: wsl --install", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    sys.exit(1)
                except Exception as e:
                    # If check fails, provide manual instructions
                    logger.log("", Colors.RESET)
                    logger.log("⚠️ Could not verify WSL2 setup.", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    logger.log("📋 Please run the following commands manually:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("   1. Open a new terminal/PowerShell window", Colors.YELLOW)
                    logger.log(f"   2. Run: wsl -d {distro}", Colors.YELLOW)
                    wsl_base_dir = windows_path_to_wsl(base_dir)
                    script_filename = script_path.name
                    logger.log(f"   3. Navigate to your project: cd {wsl_base_dir}", Colors.YELLOW)
                    logger.log(f"   4. Run: python3 {script_filename}", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    sys.exit(1)
        else:
            logger.log("❌ Unsupported OS detected!", Colors.RED)
            sys.exit(1)

        logger.log(f"🖥️ Detected Platform: {platform_name}", Colors.RESET)

        # 2. Check Python version compatibility and prefer Python 3.11 on WSL
        python_executable = sys.executable
        is_wsl = bool(os.environ.get('WSL_DISTRO_NAME'))
        
        if is_wsl:
            try:
                python311_check = subprocess.run(
                    ["python3.11", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if python311_check.returncode == 0:
                    python_executable = "python3.11"
                    logger.log("✅ Using Python 3.11 (recommended for WSL)", Colors.GREEN)
            except Exception:
                pass  # Fall back to default python
        
        try:
            # Check version of the executable we'll use
            version_check = subprocess.run(
                [python_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if version_check.returncode == 0:
                version_str = version_check.stdout.strip()
                logger.log(f"🐍 {version_str}", Colors.CYAN)
                if "3.12" in version_str:
                    logger.log("⚠️ Python 3.12 detected - some packages may have compatibility issues", Colors.YELLOW)
                elif "3.11" in version_str:
                    logger.log("✅ Python 3.11 detected - excellent compatibility!", Colors.GREEN)
        except Exception:
            pass  # Non-critical check
        
        logger.log("", Colors.RESET)

        # 3. Check and navigate to backend directory
        # Assuming script is run from customnerd/ directory
        
        backend_dir = base_dir / "customnerd-backend"

        if not backend_dir.exists():
            logger.log("❌ Error: 'customnerd-backend' directory not found!", Colors.RED)
            sys.exit(1)

        # 3. Locate virtual environment (auto-run setup if missing)
        venv_dir = backend_dir / "nerd_engine_venv"
        if not venv_dir.exists():
            run_setup_wizard(base_dir, logger)

        if platform_name == "Windows":
            venv_python = venv_dir / "Scripts" / "python.exe"
            venv_pip = venv_dir / "Scripts" / "pip.exe"
        else:
            venv_python = venv_dir / "bin" / "python"
            venv_pip = venv_dir / "bin" / "pip"

        if not venv_python.exists():
            logger.log(f"❌ Virtual environment not found at {venv_dir}. Please run setup.py first.", Colors.RED)
            sys.exit(1)
        
        logger.log("🔗 Found virtual environment...", Colors.RESET)

        # Note: Windows-specific pywin32 is not needed when running in WSL2
        # If we're here and platform_name is Windows, we're already inside WSL2
        
        # Run Health Checks
        if not run_health_checks(backend_dir, venv_python, logger):
            logger.log("\n❌ Health checks failed. Aborting server start.", Colors.RED)
            sys.exit(1)
        
        logger.log("\n✅ All systems go! Starting engine...", Colors.GREEN)

        # 4. Show stop instruction
        if platform_name == "Mac":
            stop_key = "Cmd+C"
        else:
            stop_key = "Ctrl+C"
        logger.log(f"💡 Press {stop_key} to stop the server", Colors.CYAN)
        logger.log("", Colors.RESET)

        # 5. Start uvicorn server with a success URL waiter
        logger.log("🌐 Starting server with hot reload...", Colors.RESET)
        logger.log("⏳ Starting server... This may take a few moments.", Colors.RESET)
        logger.log("✨ Waiting for: 'Application startup complete'", Colors.RESET)
        print()

        os.chdir(backend_dir)
        cmd = [str(venv_python), "-m", "uvicorn", "main:app", "--reload"]

        success_url_opened = False
        try:
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as proc:
                for line in proc.stdout:
                    # Stream uvicorn output to console and log
                    print(line, end="")
                    logger.raw(line)

                    # Once startup completes, open browser only once
                    if (not success_url_opened) and ("Application startup complete" in line):
                        success_url_opened = True
                        system = platform.system()
                        
                        # All platforms: Open index.html file
                        index_html_path = base_dir / "customnerd-website" / "index.html"
                        if index_html_path.exists():
                            logger.log("🌐 Opening index.html...", Colors.BLUE)
                            is_wsl = bool(os.environ.get("WSL_DISTRO_NAME")) and system == "Linux"
                            
                            if is_wsl:
                                # WSL: Use path conversion method (works without wslu/wslview)
                                wsl_path = str(index_html_path.absolute())
                                open_browser_cross_platform(wsl_path, logger)
                            elif system == "Windows":
                                # Windows native: Pass absolute path directly (not file:// URL)
                                open_browser_cross_platform(str(index_html_path.absolute()), logger)
                            else:
                                # macOS/Linux native: Use file:// URL
                                file_url = f"file://{index_html_path.absolute()}"
                                open_browser_cross_platform(file_url, logger)
                            
                            # Show manual path in case browser didn't open
                            logger.log("", Colors.RESET)
                            logger.log("💡 If index.html didn't open automatically, open it manually:", Colors.CYAN)
                            logger.log(f"   {index_html_path.absolute()}", Colors.YELLOW)
                            logger.log("", Colors.RESET)
                        else:
                            logger.log(f"⚠️ index.html not found at {index_html_path}", Colors.YELLOW)
                            logger.log("   Backend is running at http://localhost:8000", Colors.CYAN)
                            # Fallback to localhost if index.html not found
                            open_browser_cross_platform("http://localhost:8000", logger)

                proc.wait()
        except KeyboardInterrupt:
            logger.log("\nServer stopped by user.", Colors.YELLOW)
        logger.log(f"📁 Logs saved to: {log_file_path}", Colors.BLUE)
    except KeyboardInterrupt:
        try:
            logger.log("\nOperation cancelled.", Colors.YELLOW)
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            logger.close()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)

