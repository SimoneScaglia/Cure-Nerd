# === Custom-Nerd/Nerd-Engine Backend Setup (All Platforms) ===
# For: All users (macOS, Linux, Windows via WSL2) running the initial backend installation.

import os
import sys
import subprocess
import platform
import shutil
import re
import datetime
from pathlib import Path

# ------------------------------------------------------------------------------------
# This setup script must run in a Linux environment (native Linux or WSL2 on Windows).
# Reason:
# The backend depends on Python packages that require native C/C++ compilation.
# On Windows, these packages frequently fail to build due to missing MSVC tools and
# incompatibilities with Windows' build toolchain.
#
# Libraries that commonly fail on Windows:
#   - chroma-hnswlib
#   - greenlet
#   - httptools
#   - kiwisolver
#   - numpy (Meson-based)
#   - Levenshtein
#
# Windows does not ship with the required compilers or POSIX headers. Installing
# Visual Studio Build Tools is unreliable and heavy, and many packages still do not
# support Windows builds.
#
# Because of this, run the backend inside a Linux environment.
#
# For macOS/Linux users:
#   - The script works natively. Just run: python3 setup.py
#
# For Windows users:
#   - FIRST: Run 'python presetup.py' to install and configure WSL2/Ubuntu
#   - THEN: Run 'python setup.py' (it will automatically run inside WSL2)
#   - This ensures full compatibility with Python build tools and avoids Windows
#     compiler issues entirely.
#
# Running inside WSL2/Ubuntu guarantees:
#   - GCC/Clang toolchain available
#   - build-essential support
#   - Stable wheels for all required packages
#   - Identical environment for all developers
#
# TLDR: 
#   - macOS/Linux: Run setup.py directly
#   - Windows: Run presetup.py first, then setup.py
# ------------------------------------------------------------------------------------

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    MAGENTA = '\033[95m'

def display_manual_instructions(logger, title, steps, color=Colors.CYAN):
    """Display beautiful, prominent manual instructions."""
    logger.log("", Colors.RESET)
    logger.log("╔" + "═" * 68 + "╗", Colors.BOLD + color)
    logger.log("║" + " " * 20 + title + " " * (48 - len(title)) + "║", Colors.BOLD + color)
    logger.log("╚" + "═" * 68 + "╝", Colors.BOLD + color)
    logger.log("", Colors.RESET)
    
    for i, step in enumerate(steps, 1):
        if isinstance(step, dict):
            step_title = step.get('title', f'Step {i}')
            step_commands = step.get('commands', [])
            step_notes = step.get('notes', [])
            
            logger.log(f"   {Colors.BOLD}{Colors.YELLOW}{i}️⃣  {step_title}{Colors.RESET}", Colors.RESET)
            if step_commands:
                for cmd in step_commands:
                    logger.log(f"      {Colors.BOLD}{Colors.GREEN}→{Colors.RESET} {Colors.CYAN}{cmd}{Colors.RESET}", Colors.RESET)
            if step_notes:
                for note in step_notes:
                    logger.log(f"      {Colors.YELLOW}•{Colors.RESET} {note}", Colors.RESET)
        else:
            logger.log(f"   {Colors.BOLD}{Colors.YELLOW}{i}️⃣  {step}{Colors.RESET}", Colors.RESET)
        logger.log("", Colors.RESET)
    
    logger.log("╔" + "═" * 68 + "╗", Colors.BOLD + Colors.MAGENTA)
    logger.log("║" + " " * 15 + "⚠️  READ THE STEPS ABOVE CAREFULLY ⚠️" + " " * 15 + "║", Colors.BOLD + Colors.MAGENTA)
    logger.log("╚" + "═" * 68 + "╝", Colors.BOLD + Colors.MAGENTA)
    logger.log("", Colors.RESET)


def display_ollama_manual_instructions(logger, platform_name):
    """
    Display manual installation steps for Ollama when the terminal install fails.
    Used as backup after a failed automated install attempt.
    """
    common_steps = [
        {
            "title": "Verify server and pull a model",
            "commands": [
                "ollama --version",
                "ollama serve           # if the server is not already running",
                "ollama pull llama3.2:1b",
                "curl http://localhost:11434/api/tags"
            ],
        },
        {
            "title": "Connect Custom-Nerd to Ollama",
            "commands": [
                "In customnerd-backend/variables.env set:",
                '  LLM="Ollama"',
                '  OLLAMA_MODEL="llama3.2:1b"',
                '  OLLAMA_BASE_URL="http://localhost:11434"',
                "Then use the Config page → Update Environment Configuration → Test Connection"
            ],
        },
    ]
    if platform_name == "Mac":
        steps = [
            {
                "title": "Option A — Install the macOS app",
                "commands": [
                    "Open https://ollama.com in your browser",
                    "Download the macOS app and move it to /Applications",
                    "Open the Ollama app once to start the local server"
                ],
            },
            {
                "title": "Option B — Terminal install",
                "commands": [
                    "Open the macOS Terminal app",
                    "Run: curl -fsSL https://ollama.com/install.sh | sh",
                ],
                "notes": [
                    "The script may ask for your macOS password — enter it when prompted.",
                ],
            },
        ] + common_steps
    elif platform_name == "Windows":
        steps = [
            {
                "title": "Install inside WSL (Ubuntu)",
                "commands": [
                    "Open PowerShell or CMD, run: wsl -d Ubuntu",
                    "Run: curl -fsSL https://ollama.com/install.sh | sh",
                    "Enter your Linux/sudo password if prompted.",
                ],
                "notes": [
                    "Ollama runs as a Linux app inside WSL. Use the same terminal session for ollama serve.",
                ],
            },
        ] + common_steps
    else:
        # Linux (native or WSL)
        steps = [
            {
                "title": "Install Ollama",
                "commands": [
                    "curl -fsSL https://ollama.com/install.sh | sh",
                ],
                "notes": [
                    "Enter your sudo password when prompted.",
                ],
            },
        ] + common_steps

    display_manual_instructions(logger, "📥 MANUAL OLLAMA INSTALLATION (Backup)", steps, color=Colors.CYAN)


def install_ollama_step(logger, platform_name, step_results, backend_dir):
    """
    Attempt to install Ollama via terminal. Runs actual install commands.
    If password is required, user enters it in the attached terminal.
    On failure, displays manual instructions as backup.
    Supports: Mac, Linux (native), Linux (WSL/Windows).
    """
    OLLAMA_MODEL_DEFAULT = "llama3.2:1b"

    # 1. Check if already installed
    ollama_path = shutil.which("ollama")
    if ollama_path:
        logger.log("", Colors.RESET)
        logger.log("✅ Ollama is already installed.", Colors.GREEN)
        logger.log(f"   Path: {ollama_path}", Colors.CYAN)
        # Still try to pull the default model if not present
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(backend_dir)
            )
            has_model = OLLAMA_MODEL_DEFAULT in (result.stdout or "") if result.returncode == 0 else False
        except Exception:
            has_model = False

        if not has_model:
            logger.log(f"   Pulling default model '{OLLAMA_MODEL_DEFAULT}'...", Colors.CYAN)
            try:
                run_command_with_output(
                    ["ollama", "pull", OLLAMA_MODEL_DEFAULT],
                    logger,
                    description=f"Pulling {OLLAMA_MODEL_DEFAULT}",
                    timeout=600,
                    cwd=str(backend_dir)
                )
                step_results.append(("Step 6: Ollama (optional)", "PASSED", f"Already installed, pulled {OLLAMA_MODEL_DEFAULT}"))
            except subprocess.CalledProcessError:
                step_results.append(("Step 6: Ollama (optional)", "WARNING", f"Model pull failed — run 'ollama pull {OLLAMA_MODEL_DEFAULT}' manually"))
        else:
            step_results.append(("Step 6: Ollama (optional)", "PASSED", "Already installed with default model"))
        return

    # 2. Not installed — try terminal install
    logger.log("", Colors.RESET)
    logger.log("🤖 Step 6: Optional — Install Ollama (local AI)", Colors.BLUE)
    logger.log("   Ollama lets you run AI models locally without API keys.", Colors.CYAN)
    logger.log("", Colors.RESET)

    if not sys.stdin.isatty():
        logger.log("⚠️ Non-interactive terminal — cannot run installer (may require password).", Colors.YELLOW)
        logger.log("   Skipping automated install. See manual steps below.", Colors.CYAN)
        display_ollama_manual_instructions(logger, platform_name)
        step_results.append(("Step 6: Ollama (optional)", "SKIPPED", "Non-interactive — install manually"))
        return

    logger.log("   Running: curl -fsSL https://ollama.com/install.sh | sh", Colors.CYAN)
    logger.log("   If prompted for a password, enter it in this terminal.", Colors.YELLOW)
    logger.log("", Colors.RESET)

    try:
        # Run with inherited stdin/stdout/stderr so user can type password
        proc = subprocess.run(
            ["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
            cwd=str(backend_dir),
            timeout=300,
        )
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, "curl | sh")
    except subprocess.TimeoutExpired:
        logger.log("❌ Ollama install timed out.", Colors.RED)
        display_ollama_manual_instructions(logger, platform_name)
        step_results.append(("Step 6: Ollama (optional)", "FAILED", "Install timed out"))
        return
    except subprocess.CalledProcessError as e:
        logger.log(f"❌ Ollama install failed (exit code {e.returncode}).", Colors.RED)
        display_ollama_manual_instructions(logger, platform_name)
        step_results.append(("Step 6: Ollama (optional)", "FAILED", "Install script failed"))
        return
    except Exception as e:
        logger.log(f"❌ Ollama install error: {e}", Colors.RED)
        display_ollama_manual_instructions(logger, platform_name)
        step_results.append(("Step 6: Ollama (optional)", "FAILED", str(e)))
        return

    # 3. Verify installation (check common install locations; PATH may not be updated in this session)
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        for candidate in ["/usr/local/bin/ollama", "/usr/bin/ollama"]:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                ollama_path = candidate
                break
    if not ollama_path:
        logger.log("❌ Ollama install completed but 'ollama' not found.", Colors.RED)
        logger.log("   Open a new terminal (PATH may need refresh) or run: export PATH=$PATH:/usr/local/bin", Colors.CYAN)
        display_ollama_manual_instructions(logger, platform_name)
        step_results.append(("Step 6: Ollama (optional)", "FAILED", "ollama not on PATH"))
        return

    logger.log("✅ Ollama installed successfully.", Colors.GREEN)
    logger.log(f"   Pulling default model '{OLLAMA_MODEL_DEFAULT}'...", Colors.CYAN)

    ollama_cmd = ollama_path if ollama_path else "ollama"
    try:
        run_command_with_output(
            [ollama_cmd, "pull", OLLAMA_MODEL_DEFAULT],
            logger,
            description=f"Pulling {OLLAMA_MODEL_DEFAULT}",
            timeout=600,
            cwd=str(backend_dir)
        )
        step_results.append(("Step 6: Ollama (optional)", "PASSED", f"Installed and pulled {OLLAMA_MODEL_DEFAULT}"))
    except subprocess.CalledProcessError:
        logger.log(f"⚠️ Model pull failed. Run manually: ollama pull {OLLAMA_MODEL_DEFAULT}", Colors.YELLOW)
        step_results.append(("Step 6: Ollama (optional)", "WARNING", "Installed; model pull failed — run manually"))


def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class Logger:
    def __init__(self, log_file_path):
        self.log_file = open(log_file_path, "w", encoding='utf-8')
        self.log_file.write(f"Setup Log - Started at {datetime.datetime.now()}\n")
        self.log_file.write("="*50 + "\n")
        
        # Enable ANSI colors on Windows 10+ if available
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable ANSI escape sequence processing
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass  # If it fails, colors won't work but script will continue
        
    def log(self, text, color=None, end='\n'):
        # Print to console
        # If text already contains color codes, use them directly
        # Otherwise, apply the color parameter
        if color and Colors.CYAN not in text and Colors.YELLOW not in text and Colors.RED not in text and Colors.GREEN not in text:
            # Text doesn't have embedded colors, apply the color parameter
            if platform.system() != "Windows":
                print(f"{color}{text}{Colors.RESET}", end=end)
            else:
                # On Windows, try to use colors (enabled in __init__)
                print(f"{color}{text}{Colors.RESET}", end=end)
        else:
            # Text has embedded colors or no color specified
            print(text, end=end)

        # Write to file (always strip ANSI codes for file)
        clean_text = strip_ansi(text)
        if end == '\n':
             timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
             self.log_file.write(f"{timestamp}{clean_text}\n")
        else:
             self.log_file.write(clean_text)
        self.log_file.flush()
    
    def raw_log(self, text):
        clean_text = strip_ansi(text)
        self.log_file.write(clean_text)
        self.log_file.flush()

    def close(self):
        self.log_file.write("\n" + "="*50 + "\n")
        self.log_file.write(f"Setup Log - Finished at {datetime.datetime.now()}\n")
        self.log_file.close()

def run_command_with_output(cmd, logger, timeout=None, description="", cwd=None):
    """
    Run a subprocess command and display output in real-time with [Internal Check] prefix.
    Returns: (returncode, stdout, stderr)
    """
    import threading
    import queue
    
    if description:
        logger.log(f"   {description}", Colors.CYAN)
    
    # Show the command being run with visual separator
    cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
    logger.log("", Colors.RESET)
    logger.log("   " + "─" * 70, Colors.CYAN)
    logger.log(f"   {Colors.CYAN}┌─ [Internal Check] ────────────────────────────────────────────────┐{Colors.RESET}", Colors.RESET)
    logger.log(f"   {Colors.CYAN}│{Colors.RESET} Running: {cmd_str}", Colors.RESET)
    logger.log(f"   {Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.RESET}", Colors.RESET)
    logger.log("", Colors.RESET)
    
    stdout_lines = []
    stderr_lines = []
    stdout_queue = queue.Queue()
    stderr_queue = queue.Queue()
    
    def read_output(pipe, queue_obj, lines_list):
        """Read from pipe and put lines in queue and list."""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    lines_list.append(line)
                    queue_obj.put(line)
            queue_obj.put(None)  # Signal end
        except Exception:
            queue_obj.put(None)
        finally:
            pipe.close()
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd
        )
        
        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_queue, stdout_lines))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_queue, stderr_lines))
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Display output in real-time
        stdout_done = False
        stderr_done = False
        
        while not (stdout_done and stderr_done):
            # Check stdout
            try:
                line = stdout_queue.get_nowait()
                if line is None:
                    stdout_done = True
                else:
                    # Indent internal check output for visual distinction
                    logger.log(f"   {Colors.CYAN}│{Colors.RESET} {line.rstrip()}", Colors.RESET)
            except queue.Empty:
                pass
            
            # Check stderr
            try:
                line = stderr_queue.get_nowait()
                if line is None:
                    stderr_done = True
                else:
                    # Indent internal check stderr output (errors/warnings)
                    logger.log(f"   {Colors.CYAN}│{Colors.RESET} {Colors.YELLOW}{line.rstrip()}{Colors.RESET}", Colors.RESET)
            except queue.Empty:
                pass
            
            # Check if process is done
            if process.poll() is not None:
                # Process finished, read remaining output
                import time
                time.sleep(0.1)  # Give threads time to finish reading
                # Drain remaining queues
                while True:
                    try:
                        line = stdout_queue.get_nowait()
                        if line is None:
                            stdout_done = True
                            break
                        logger.log(f"   {Colors.CYAN}│{Colors.RESET} {line.rstrip()}", Colors.RESET)
                    except queue.Empty:
                        break
                
                while True:
                    try:
                        line = stderr_queue.get_nowait()
                        if line is None:
                            stderr_done = True
                            break
                        logger.log(f"   {Colors.CYAN}│{Colors.RESET} {Colors.YELLOW}{line.rstrip()}{Colors.RESET}", Colors.RESET)
                    except queue.Empty:
                        break
                break
            
            import time
            time.sleep(0.05)  # Small delay to avoid busy waiting
        
        # Wait for process to complete
        returncode = process.wait(timeout=timeout)
        
        # Wait for threads to finish
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
        
        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)
        
        # Close the visual box
        logger.log("", Colors.RESET)
        status_color = Colors.GREEN if returncode == 0 else Colors.RED
        status_icon = "✓" if returncode == 0 else "✗"
        logger.log(f"   {Colors.CYAN}┌─ [Internal Check] Result ─────────────────────────────────────────┐{Colors.RESET}", Colors.RESET)
        logger.log(f"   {Colors.CYAN}│{Colors.RESET} {status_icon} Exit code: {status_color}{returncode}{Colors.RESET}", Colors.RESET)
        logger.log(f"   {Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.RESET}", Colors.RESET)
        logger.log("", Colors.RESET)
        
        # Create exception with stdout/stderr attached for better error handling
        exception = None
        if returncode != 0:
            # Include stdout and stderr in the exception for better error handling
            # This allows callers to check for success indicators even on non-zero exit codes
            # For apt-get, exit code 100 is often a false positive (terminal warnings like TCSAFLUSH)
            raise subprocess.CalledProcessError(returncode, cmd, stdout, stderr)
        
        return returncode, stdout, stderr
        
    except subprocess.TimeoutExpired:
        process.kill()
        logger.log(f"   {Colors.CYAN}┌─ [Internal Check] Error ──────────────────────────────────────────┐{Colors.RESET}", Colors.RESET)
        logger.log(f"   {Colors.CYAN}│{Colors.RESET} ✗ Command timed out after {timeout} seconds", Colors.RESET)
        logger.log(f"   {Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.RESET}", Colors.RESET)
        logger.log("", Colors.RESET)
        raise
    except Exception as e:
        logger.log(f"   {Colors.CYAN}┌─ [Internal Check] Error ──────────────────────────────────────────┐{Colors.RESET}", Colors.RESET)
        # Format error message nicely - show command as readable string instead of list
        if isinstance(e, subprocess.CalledProcessError):
            cmd_str = " ".join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
            error_msg = f"Command '{cmd_str}' returned non-zero exit status {e.returncode}"
            logger.log(f"   {Colors.CYAN}│{Colors.RESET} ✗ {error_msg}", Colors.RESET)
        else:
            logger.log(f"   {Colors.CYAN}│{Colors.RESET} ✗ Error running command: {e}", Colors.RESET)
        logger.log(f"   {Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.RESET}", Colors.RESET)
        logger.log("", Colors.RESET)
        raise

def run_command(cmd, logger, cwd=None):
    """Legacy wrapper for backward compatibility."""
    try:
        run_command_with_output(cmd, logger, description=f"Running: {' '.join(cmd)}", cwd=cwd)
    except subprocess.CalledProcessError as e:
        raise

def check_wsl_catastrophic_failure(logger, distro="Ubuntu"):
    """Check if WSL is experiencing catastrophic failure errors."""
    try:
        result = subprocess.run(
            ["wsl", "-d", distro, "echo", "test"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check for catastrophic failure error messages
        error_output = result.stderr.lower() if result.stderr else ""
        stdout_output = result.stdout.lower() if result.stdout else ""
        combined_output = error_output + stdout_output
        
        if ("catastrophic failure" in combined_output or 
            "e_unexpected" in combined_output or
            "wsl/service" in combined_output):
            return True
        
        # Also check return code - catastrophic failures often return non-zero
        if result.returncode != 0 and ("catastrophic" in combined_output or "unexpected" in combined_output):
            return True
            
        return False
    except Exception:
        # If we can't even run the command, it might be a catastrophic failure
        return True

def check_ubuntu_setup_complete(logger, distro="Ubuntu"):
    """Check if Ubuntu WSL has completed initial user setup."""
    try:
        # First check for catastrophic failure
        if check_wsl_catastrophic_failure(logger, distro):
            logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
            logger.log("", Colors.RESET)
            logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
            logger.log("", Colors.RESET)
            logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
            logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
            logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
            logger.log("   4. Run this script again", Colors.YELLOW)
            logger.log("", Colors.RESET)
            logger.log("Or run: python presetup.py", Colors.CYAN)
            logger.log("", Colors.RESET)
            return False
        
        # Try to run a simple command in Ubuntu to check if it's ready
        result = subprocess.run(
            ["wsl", "-d", distro, "whoami"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check stderr for catastrophic failure messages
        error_output = result.stderr.lower() if result.stderr else ""
        if "catastrophic failure" in error_output or "e_unexpected" in error_output:
            logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
            logger.log("", Colors.RESET)
            logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
            logger.log("", Colors.RESET)
            logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
            logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
            logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
            logger.log("   4. Run this script again", Colors.YELLOW)
            logger.log("", Colors.RESET)
            logger.log("Or run: python presetup.py", Colors.CYAN)
            logger.log("", Colors.RESET)
            return False
        
        if result.returncode == 0 and result.stdout.strip():
            username = result.stdout.strip()
            logger.log(f"✅ Ubuntu setup complete (user: {username})", Colors.GREEN)
            return True
        else:
            # If whoami fails, Ubuntu might not be set up
            logger.log("⚠️ Ubuntu appears to be installed but user setup may be incomplete", Colors.YELLOW)
            return False
    except subprocess.TimeoutExpired:
        logger.log("⏱️ Ubuntu is responding slowly. It may be waiting for initial setup.", Colors.YELLOW)
        return False
    except Exception as e:
        error_str = str(e).lower()
        # Check if the exception message contains catastrophic failure indicators
        if "catastrophic" in error_str or "e_unexpected" in error_str:
            logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
            logger.log("", Colors.RESET)
            logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
            logger.log("", Colors.RESET)
            logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
            logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
            logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
            logger.log("   4. Run this script again", Colors.YELLOW)
            logger.log("", Colors.RESET)
            logger.log("Or run: python presetup.py", Colors.CYAN)
            logger.log("", Colors.RESET)
            return False
        # If we can't run commands, Ubuntu might need initial setup
        logger.log(f"⚠️ Could not verify Ubuntu setup: {e}", Colors.YELLOW)
        return False

def get_ubuntu_distro_name(logger):
    """Extract the exact Ubuntu distribution name from WSL list."""
    try:
        result = subprocess.run(
            ["wsl", "--list", "--verbose"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                # Look for Ubuntu distributions (Ubuntu, Ubuntu-22.04, Ubuntu-24.04, etc.)
                # Skip header lines and lines with asterisks (default distro marker)
                line_lower = line.lower()
                if 'ubuntu' in line_lower and 'no installed distributions' not in line_lower:
                    # Extract the distribution name (first word)
                    parts = line.split()
                    if parts:
                        distro_name = parts[0]
                        logger.log(f"📋 Found Ubuntu distribution: {distro_name}", Colors.CYAN)
                        return distro_name
        return None  # No Ubuntu found
    except Exception as e:
        logger.log(f"⚠️ Could not determine Ubuntu distribution name: {e}", Colors.YELLOW)
        return None

def check_wsl_installed(logger):
    """Check if WSL2 is installed and available."""
    try:
        # Check if wsl command exists
        result = subprocess.run(
            ["wsl", "--status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Check WSL version
            version_result = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            logger.log("✅ WSL is installed", Colors.GREEN)
            
            # Check for Ubuntu distribution
            list_result = subprocess.run(
                ["wsl", "--list", "--verbose"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Get the exact Ubuntu distribution name
            ubuntu_distro = get_ubuntu_distro_name(logger)
            
            if ubuntu_distro:
                logger.log(f"✅ Ubuntu distribution found: {ubuntu_distro}", Colors.GREEN)
                
                # Check if Ubuntu setup is complete using the exact name
                if not check_ubuntu_setup_complete(logger, ubuntu_distro):
                    logger.log("", Colors.RESET)
                    logger.log("⚠️ Ubuntu needs initial setup!", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    logger.log("📋 Setup Instructions:", Colors.CYAN)
                    logger.log(f"   1. Launch Ubuntu from Start Menu or run: wsl -d {ubuntu_distro}", Colors.YELLOW)
                    logger.log("   2. Ubuntu will prompt you to create a username", Colors.YELLOW)
                    logger.log("   3. Enter your desired username (lowercase, no spaces)", Colors.YELLOW)
                    logger.log("   4. Enter and confirm your password", Colors.YELLOW)
                    logger.log("   5. Wait for Ubuntu to finish initializing", Colors.YELLOW)
                    logger.log("   6. Run this script again", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    return True, ubuntu_distro  # Return True but user needs to complete setup
                
                return True, ubuntu_distro
            else:
                logger.log("⚠️ Ubuntu distribution not found. Will install it.", Colors.YELLOW)
                return True, None
        return False, None
    except FileNotFoundError:
        logger.log("❌ WSL is not installed", Colors.RED)
        return False, None
    except Exception as e:
        logger.log(f"⚠️ Error checking WSL: {e}", Colors.YELLOW)
        return False, None

def find_installed_python_versions_macos(logger):
    """Find all Python versions installed via Homebrew on macOS."""
    versions = []
    try:
        result = subprocess.run(
            ["brew", "list", "--formula"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'python@' in line:
                    versions.append(line.strip())
        return versions
    except Exception:
        return []

def switch_to_python311_macos(logger):
    """Automatically switch to Python 3.11 on macOS using Homebrew."""
    logger.log("", Colors.RESET)
    logger.log("=" * 60, Colors.BLUE)
    logger.log("🔄 Switching to Python 3.11 (macOS)", Colors.BLUE)
    logger.log("=" * 60, Colors.BLUE)
    logger.log("", Colors.RESET)
    
    # Step 1: Check if Homebrew is installed
    logger.log("Step 1/6: Checking Homebrew...", Colors.BLUE)
    try:
        subprocess.run(["brew", "--version"], capture_output=True, check=True, timeout=5)
        logger.log("✅ Homebrew found", Colors.GREEN)
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.log("❌ Homebrew not found. Please install it first:", Colors.RED)
        logger.log("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"", Colors.YELLOW)
        return False
    
    # Step 2: Check if Python 3.11 is installed
    logger.log("", Colors.RESET)
    logger.log("Step 2/6: Checking for Python 3.11...", Colors.BLUE)
    python311_installed = False
    try:
        result = subprocess.run(
            ["brew", "list", "python@3.11"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            python311_installed = True
            logger.log("✅ Python 3.11 is installed", Colors.GREEN)
        else:
            logger.log("⚠️ Python 3.11 not found. Installing...", Colors.YELLOW)
            logger.log("   This may take a few minutes...", Colors.CYAN)
            install_result = subprocess.run(
                ["brew", "install", "python@3.11"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=600
            )
            if install_result.returncode == 0:
                python311_installed = True
                logger.log("✅ Python 3.11 installed successfully", Colors.GREEN)
            else:
                logger.log("❌ Failed to install Python 3.11", Colors.RED)
                logger.log("   Please install manually: brew install python@3.11", Colors.YELLOW)
                return False
    except Exception as e:
        logger.log(f"❌ Error checking/installing Python 3.11: {e}", Colors.RED)
        return False
    
    # Step 3: Find all installed Python versions
    logger.log("", Colors.RESET)
    logger.log("Step 3/6: Finding installed Python versions...", Colors.BLUE)
    installed_versions = find_installed_python_versions_macos(logger)
    if installed_versions:
        logger.log(f"   Found: {', '.join(installed_versions)}", Colors.CYAN)
    else:
        logger.log("   No other Python versions found via Homebrew", Colors.CYAN)
    
    # Step 4: Unlink all Python versions
    logger.log("", Colors.RESET)
    logger.log("Step 4/6: Unlinking all Python versions...", Colors.BLUE)
    versions_to_unlink = ["python@3.14", "python@3.13", "python@3.12", "python@3.11", "python@3.10"]
    for version in versions_to_unlink:
        try:
            result = subprocess.run(
                ["brew", "unlink", version],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.log(f"   ✅ Unlinked {version}", Colors.GREEN)
            # Don't log error if version doesn't exist
        except Exception:
            pass
    
    # Step 5: Link Python 3.11
    logger.log("", Colors.RESET)
    logger.log("Step 5/6: Linking Python 3.11...", Colors.BLUE)
    try:
        result = subprocess.run(
            ["brew", "link", "python@3.11", "--overwrite", "--force"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            logger.log("✅ Python 3.11 linked successfully", Colors.GREEN)
        else:
            logger.log(f"⚠️ Link command had warnings: {result.stderr[:200]}", Colors.YELLOW)
    except Exception as e:
        logger.log(f"⚠️ Error linking Python 3.11: {e}", Colors.YELLOW)
    
    # Step 6: Create universal python3 symlink
    logger.log("", Colors.RESET)
    logger.log("Step 6/6: Creating python3 symlink...", Colors.BLUE)
    homebrew_bin = "/opt/homebrew/bin"
    python311_bin = "/opt/homebrew/opt/python@3.11/bin/python3.11"
    python3_symlink = f"{homebrew_bin}/python3"
    
    try:
        # Remove existing symlink if it exists
        if os.path.exists(python3_symlink) or os.path.islink(python3_symlink):
            os.remove(python3_symlink)
        
        # Create new symlink
        os.symlink(python311_bin, python3_symlink)
        logger.log("✅ python3 symlink created", Colors.GREEN)
    except PermissionError:
        logger.log("⚠️ Permission denied. Trying with sudo...", Colors.YELLOW)
        try:
            subprocess.run(
                ["sudo", "ln", "-sf", python311_bin, python3_symlink],
                check=True,
                timeout=10
            )
            logger.log("✅ python3 symlink created (with sudo)", Colors.GREEN)
        except Exception as e:
            logger.log(f"⚠️ Could not create symlink: {e}", Colors.YELLOW)
            logger.log("   You may need to create it manually:", Colors.CYAN)
            logger.log(f"   ln -s {python311_bin} {python3_symlink}", Colors.YELLOW)
    except Exception as e:
        logger.log(f"⚠️ Could not create symlink: {e}", Colors.YELLOW)
    
    # Verify the switch
    logger.log("", Colors.RESET)
    logger.log("🔍 Verifying Python version...", Colors.BLUE)
    try:
        # Use the new python3 to check version
        result = subprocess.run(
            [python3_symlink, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            logger.log(f"✅ {version_str}", Colors.GREEN)
            if "3.11" in version_str:
                logger.log("", Colors.RESET)
                logger.log("✅ Successfully switched to Python 3.11!", Colors.GREEN)
                logger.log("", Colors.RESET)
                logger.log("💡 Important: Restart your terminal or run:", Colors.CYAN)
                logger.log("   hash -r", Colors.YELLOW)
                logger.log("   source ~/.zshrc  # or ~/.bashrc", Colors.YELLOW)
                logger.log("", Colors.RESET)
                logger.log("   Then run this script again.", Colors.CYAN)
                return True
            else:
                logger.log("⚠️ Python version is not 3.11. Please check manually.", Colors.YELLOW)
                return False
    except Exception as e:
        logger.log(f"⚠️ Could not verify Python version: {e}", Colors.YELLOW)
        return False

def check_python_version(logger):
    """Check Python version and warn about Python 3.12 compatibility issues (Windows only)."""
    try:
        version_info = sys.version_info
        major = version_info.major
        minor = version_info.minor
        platform_name = platform.system()
        is_wsl = bool(os.environ.get('WSL_DISTRO_NAME'))
        
        logger.log(f"🐍 Python version: {major}.{minor}.{version_info.micro}", Colors.CYAN)
        
        # Check for Python 3.14+ (incompatible with many packages)
        if major == 3 and minor >= 14:
            logger.log("", Colors.RESET)
            logger.log("❌ Python 3.14+ detected - INCOMPATIBLE!", Colors.RED)
            logger.log("   Python 3.14 has breaking changes that cause package incompatibilities.", Colors.YELLOW)
            logger.log("   Known issues: httpcore, httpx, and other packages fail to import.", Colors.YELLOW)
            logger.log("   Required: Use Python 3.11 or 3.12 instead.", Colors.CYAN)
            logger.log("", Colors.RESET)
            logger.log("=" * 60, Colors.BLUE)
            logger.log("📥 Installation Guide", Colors.BLUE)
            logger.log("=" * 60, Colors.BLUE)
            logger.log("", Colors.RESET)
            
            if platform_name == "Darwin":
                logger.log("🍎 macOS - Python 3.14+ detected", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log("Would you like to automatically switch to Python 3.11? (y/n): ", Colors.YELLOW)
                try:
                    if sys.stdin.isatty():
                        response = input().strip().lower()
                    else:
                        # Non-interactive mode - default to no
                        response = 'n'
                        logger.log("   Non-interactive mode: defaulting to 'n'", Colors.CYAN)
                except (EOFError, KeyboardInterrupt):
                    # Non-interactive mode - default to no
                    response = 'n'
                    logger.log("   Non-interactive mode: defaulting to 'n'", Colors.CYAN)
                if response == 'y' or response == 'yes':
                    if switch_to_python311_macos(logger):
                        logger.log("", Colors.RESET)
                        logger.log("✅ Python version switched! Please restart your terminal and run this script again.", Colors.GREEN)
                        sys.exit(0)
                    else:
                        logger.log("", Colors.RESET)
                        logger.log("❌ Failed to switch Python version automatically.", Colors.RED)
                        logger.log("", Colors.RESET)
                        display_manual_instructions(
                            logger,
                            "📥 MANUAL INSTALLATION STEPS",
                            [
                                {
                                    'title': 'Install Python 3.11',
                                    'commands': ['brew install python@3.11']
                                },
                                {
                                    'title': 'Run setup with Python 3.11',
                                    'commands': ['python3.11 setup.py']
                                }
                            ]
                        )
                        sys.exit(1)
                else:
                    logger.log("", Colors.RESET)
                    logger.log("📥 Manual Installation Steps:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("Step 1/2: Install Python 3.11", Colors.YELLOW)
                    logger.log("   brew install python@3.11", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("Step 2/2: Run setup with Python 3.11", Colors.YELLOW)
                    logger.log("   python3.11 setup.py", Colors.RESET)
                    sys.exit(1)
            elif platform_name == "Linux" or is_wsl:
                logger.log("🐧 Linux/WSL - Installation Steps:", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log("Step 1/2: Install Python 3.11", Colors.YELLOW)
                logger.log("   sudo apt-get update", Colors.RESET)
                logger.log("   sudo apt-get install python3.11 python3.11-venv python3.11-pip", Colors.RESET)
                logger.log("", Colors.RESET)
                logger.log("Step 2/2: Run setup with Python 3.11", Colors.YELLOW)
                logger.log("   python3.11 setup.py", Colors.RESET)
            elif platform_name == "Windows":
                logger.log("🪟 Windows - Installation Steps:", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log("Step 1/2: Download and Install Python 3.11", Colors.YELLOW)
                logger.log("   1. Download from: https://www.python.org/downloads/release/python-3119/", Colors.BLUE)
                logger.log("   2. Download 'Windows installer (64-bit)'", Colors.RESET)
                logger.log("   3. Run the installer", Colors.RESET)
                logger.log("   4. During installation, check 'Add Python to PATH'", Colors.RESET)
                logger.log("", Colors.RESET)
                logger.log("Step 2/2: Run setup with Python 3.11", Colors.YELLOW)
                logger.log("   python3.11 setup.py", Colors.RESET)
            
            logger.log("", Colors.RESET)
            logger.log("=" * 60, Colors.BLUE)
            logger.log("", Colors.RESET)
            logger.log("❌ Setup cannot continue with Python 3.14+. Please install Python 3.11.", Colors.RED)
            sys.exit(1)
        
        # Only restrict Python 3.12+ on Windows/WSL, allow on macOS and Linux
        elif major == 3 and minor >= 12:
            if platform_name == "Windows" or (platform_name == "Linux" and is_wsl):
                logger.log("", Colors.RESET)
                logger.log("⚠️ Python 3.12+ detected on Windows/WSL", Colors.YELLOW)
                logger.log("   Some packages may have compatibility issues with Python 3.12+ on Windows.", Colors.YELLOW)
                logger.log("   Recommended: Use Python 3.11 for best compatibility.", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log("=" * 60, Colors.BLUE)
                logger.log("📥 Installation & Uninstallation Guide", Colors.BLUE)
                logger.log("=" * 60, Colors.BLUE)
                logger.log("", Colors.RESET)
                
                if is_wsl or (platform_name == "Linux" and is_wsl):
                    logger.log("🐧 Linux / WSL2 (Ubuntu) Instructions:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("Step 1/3: Install Python 3.11", Colors.YELLOW)
                    logger.log("   sudo apt-get update", Colors.RESET)
                    logger.log("   sudo apt-get install python3.11 python3.11-venv python3.11-pip", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("Step 2/3: (Optional) Uninstall current Python 3.12", Colors.YELLOW)
                    logger.log("   sudo apt-get remove python3.12 python3.12-venv python3.12-pip", Colors.RESET)
                    logger.log("   sudo apt-get autoremove", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("Step 3/3: Run setup with Python 3.11", Colors.YELLOW)
                    logger.log("   python3.11 setup.py", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("💡 Note: You can keep both versions installed and just use python3.11 for this project.", Colors.CYAN)
                    
                elif platform_name == "Windows":
                    logger.log("🪟 Windows Instructions:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("Step 1/3: Download and Install Python 3.11", Colors.YELLOW)
                    logger.log("   1. Download from: https://www.python.org/downloads/release/python-3119/", Colors.BLUE)
                    logger.log("   2. Download 'Windows installer (64-bit)'", Colors.RESET)
                    logger.log("   3. Run the installer", Colors.RESET)
                    logger.log("   4. During installation, check 'Add Python to PATH'", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("Step 2/3: (Optional) Uninstall current Python 3.12", Colors.YELLOW)
                    logger.log("   1. Open Settings > Apps > Installed apps", Colors.RESET)
                    logger.log("   2. Search for 'Python 3.12'", Colors.RESET)
                    logger.log("   3. Click Uninstall", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("Step 3/3: Run setup with Python 3.11", Colors.YELLOW)
                    logger.log("   python3.11 setup.py", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("💡 Note: On Windows, we recommend using WSL2 instead.", Colors.CYAN)
                    logger.log("   Run this script from Windows and it will use WSL2 automatically.", Colors.CYAN)
                
                logger.log("", Colors.RESET)
                logger.log("=" * 60, Colors.BLUE)
                logger.log("", Colors.RESET)
                
                # Check if stdin is interactive (tty)
                # If not interactive (e.g., automated WSL entry), auto-continue
                if not sys.stdin.isatty() or is_wsl:
                    # Non-interactive mode or WSL - auto-continue
                    logger.log("⚠️ Auto-continuing with Python 3.12+ (non-interactive mode or WSL)...", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                else:
                    # Interactive mode - prompt user
                    try:
                        response = input("Continue with Python 3.12+ anyway? (y/n): ").strip().lower()
                        if response != 'y' and response != 'yes':
                            logger.log("", Colors.RESET)
                            logger.log("Setup cancelled. Please install Python 3.11 and try again.", Colors.YELLOW)
                            logger.log("", Colors.RESET)
                            logger.log("📚 Quick Reference Links:", Colors.CYAN)
                            logger.log("   Python 3.11 Downloads: https://www.python.org/downloads/release/python-3119/", Colors.BLUE)
                            logger.log("   Python Docs: https://docs.python.org/3.11/", Colors.BLUE)
                            sys.exit(0)
                    except (EOFError, KeyboardInterrupt):
                        # If input fails (non-interactive), auto-continue
                        logger.log("⚠️ Non-interactive mode detected. Continuing with Python 3.12+...", Colors.YELLOW)
                        logger.log("", Colors.RESET)
            elif platform_name == "Darwin":
                # macOS - Python 3.12 works but 3.11 is recommended
                logger.log("⚠️ Python 3.12+ detected on macOS", Colors.YELLOW)
                logger.log("   Python 3.12 works, but Python 3.11 is recommended for best compatibility.", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log("Would you like to switch to Python 3.11? (y/n): ", Colors.YELLOW)
                try:
                    if sys.stdin.isatty():
                        response = input().strip().lower()
                    else:
                        # Non-interactive mode - default to no
                        response = 'n'
                        logger.log("   Non-interactive mode: defaulting to 'n'", Colors.CYAN)
                except (EOFError, KeyboardInterrupt):
                    # Non-interactive mode - default to no
                    response = 'n'
                    logger.log("   Non-interactive mode: defaulting to 'n'", Colors.CYAN)
                if response == 'y' or response == 'yes':
                    if switch_to_python311_macos(logger):
                        logger.log("", Colors.RESET)
                        logger.log("✅ Python version switched! Please restart your terminal and run this script again.", Colors.GREEN)
                        sys.exit(0)
                    else:
                        logger.log("", Colors.RESET)
                        logger.log("⚠️ Failed to switch automatically. Continuing with Python 3.12...", Colors.YELLOW)
                else:
                    logger.log("   Continuing with Python 3.12...", Colors.CYAN)
            elif platform_name == "Linux" and not is_wsl:
                # Native Linux - Python 3.12 is fine, just log it
                logger.log("✅ Python 3.12+ detected on Linux - compatible!", Colors.GREEN)
        elif major == 3 and minor == 11:
            logger.log("✅ Python 3.11 detected - excellent compatibility!", Colors.GREEN)
        elif major == 3 and minor < 11:
            logger.log("⚠️ Python 3.10 or earlier detected", Colors.YELLOW)
            logger.log("   Python 3.11+ is recommended for best compatibility.", Colors.CYAN)
            logger.log("", Colors.RESET)
            
            if platform_name == "Darwin":
                logger.log("🍎 macOS - Would you like to automatically switch to Python 3.11? (y/n): ", Colors.CYAN)
                try:
                    if sys.stdin.isatty():
                        response = input().strip().lower()
                    else:
                        # Non-interactive mode - default to no
                        response = 'n'
                        logger.log("   Non-interactive mode: defaulting to 'n'", Colors.CYAN)
                except (EOFError, KeyboardInterrupt):
                    # Non-interactive mode - default to no
                    response = 'n'
                    logger.log("   Non-interactive mode: defaulting to 'n'", Colors.CYAN)
                if response == 'y' or response == 'yes':
                    if switch_to_python311_macos(logger):
                        logger.log("", Colors.RESET)
                        logger.log("✅ Python version switched! Please restart your terminal and run this script again.", Colors.GREEN)
                        sys.exit(0)
                    else:
                        logger.log("", Colors.RESET)
                        logger.log("❌ Failed to switch Python version automatically.", Colors.RED)
                        logger.log("", Colors.RESET)
                        display_manual_instructions(
                            logger,
                            "📥 MANUAL INSTALLATION STEPS",
                            [
                                {
                                    'title': 'Install Python 3.11',
                                    'commands': ['brew install python@3.11']
                                },
                                {
                                    'title': 'Run setup with Python 3.11',
                                    'commands': ['python3.11 setup.py']
                                }
                            ]
                        )
                        sys.exit(1)
                else:
                    logger.log("", Colors.RESET)
                    logger.log("📥 Manual Installation Steps:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("Step 1/2: Install Python 3.11", Colors.YELLOW)
                    logger.log("   brew install python@3.11", Colors.RESET)
                    logger.log("", Colors.RESET)
                    logger.log("Step 2/2: Run setup with Python 3.11", Colors.YELLOW)
                    logger.log("   python3.11 setup.py", Colors.RESET)
                    sys.exit(1)
            elif platform_name == "Linux" or is_wsl:
                display_manual_instructions(
                    logger,
                    "📥 INSTALLATION STEPS",
                    [
                        {
                            'title': 'Install Python 3.11',
                            'commands': [
                                'sudo apt-get update',
                                'sudo apt-get install python3.11 python3.11-venv python3.11-pip'
                            ]
                        },
                        {
                            'title': 'Run setup with Python 3.11',
                            'commands': ['python3.11 setup.py']
                        }
                    ]
                )
                sys.exit(1)
            else:
                display_manual_instructions(
                    logger,
                    "📥 INSTALLATION STEPS",
                    [
                        {
                            'title': 'Download and Install Python 3.11',
                            'commands': ['https://www.python.org/downloads/release/python-3119/'],
                            'notes': [
                                'During installation, check "Add Python to PATH"'
                            ]
                        },
                        {
                            'title': 'Run setup with Python 3.11',
                            'commands': ['python3.11 setup.py']
                        }
                    ]
                )
                sys.exit(1)
        
        return True
    except Exception as e:
        logger.log(f"⚠️ Could not check Python version: {e}", Colors.YELLOW)
        return True  # Continue anyway

def install_wsl2(logger):
    """Install WSL2 and Ubuntu on Windows."""
    logger.log("", Colors.RESET)
    logger.log("=" * 60, Colors.BLUE)
    logger.log("🔧 Installing WSL2 and Ubuntu", Colors.BLUE)
    logger.log("=" * 60, Colors.BLUE)
    logger.log("", Colors.RESET)
    
    logger.log("📥 This will install WSL2 and Ubuntu. This may take 5-10 minutes.", Colors.YELLOW)
    logger.log("   You may be prompted for administrator privileges.", Colors.CYAN)
    logger.log("", Colors.RESET)
    
    try:
        # Step 1: Enable WSL feature
        logger.log("Step 1/3: Enabling WSL feature...", Colors.BLUE)
        try:
            result = subprocess.run(
                ["dism.exe", "/online", "/enable-feature", "/featurename:Microsoft-Windows-Subsystem-Linux", "/all", "/norestart"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.log("✅ WSL feature enabled", Colors.GREEN)
            else:
                logger.log("⚠️ WSL feature may already be enabled or requires admin", Colors.YELLOW)
        except Exception as e:
            logger.log(f"⚠️ Could not enable WSL feature: {e}", Colors.YELLOW)
            logger.log("   You may need to run this script as Administrator", Colors.CYAN)
        
        # Step 2: Enable Virtual Machine Platform
        logger.log("", Colors.RESET)
        logger.log("Step 2/3: Enabling Virtual Machine Platform...", Colors.BLUE)
        try:
            result = subprocess.run(
                ["dism.exe", "/online", "/enable-feature", "/featurename:VirtualMachinePlatform", "/all", "/norestart"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.log("✅ Virtual Machine Platform enabled", Colors.GREEN)
            else:
                logger.log("⚠️ Virtual Machine Platform may already be enabled", Colors.YELLOW)
        except Exception as e:
            logger.log(f"⚠️ Could not enable Virtual Machine Platform: {e}", Colors.YELLOW)
        
        # Step 3: Install WSL2 and Ubuntu
        logger.log("", Colors.RESET)
        logger.log("Step 3/3: Installing WSL2 and Ubuntu...", Colors.BLUE)
        logger.log("   This will download Ubuntu (~200MB) and may take several minutes.", Colors.CYAN)
        
        try:
            # Use wsl --install to install WSL2 and Ubuntu
            result = subprocess.run(
                ["wsl", "--install", "-d", "Ubuntu"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                logger.log("✅ WSL2 and Ubuntu installed successfully!", Colors.GREEN)
                logger.log("", Colors.RESET)
                logger.log("⚠️ IMPORTANT: A restart may be required.", Colors.YELLOW)
                logger.log("   After restart, Ubuntu will be available.", Colors.CYAN)
                logger.log("   Then run this script again.", Colors.CYAN)
                return True
            else:
                logger.log("⚠️ Installation command completed with warnings", Colors.YELLOW)
                logger.log("   Check the output above for details.", Colors.CYAN)
                if "restart" in result.stdout.lower() or "restart" in result.stderr.lower():
                    logger.log("", Colors.RESET)
                    logger.log("🔄 RESTART REQUIRED", Colors.BOLD + Colors.YELLOW)
                    logger.log("   Please restart your computer and run this script again.", Colors.CYAN)
                return False
        except subprocess.TimeoutExpired:
            logger.log("⏱️ Installation is taking longer than expected.", Colors.YELLOW)
            logger.log("   This is normal. Please wait for it to complete.", Colors.CYAN)
            return False
        except Exception as e:
            logger.log(f"❌ Error during installation: {e}", Colors.RED)
            logger.log("", Colors.RESET)
            logger.log("💡 Manual Installation Steps:", Colors.CYAN)
            logger.log("   1. Open PowerShell as Administrator", Colors.YELLOW)
            logger.log("   2. Run: wsl --install", Colors.YELLOW)
            logger.log("   3. Restart your computer", Colors.YELLOW)
            logger.log("   4. After restart, Ubuntu will launch automatically", Colors.YELLOW)
            logger.log("   5. Set up your Ubuntu username and password", Colors.YELLOW)
            logger.log("   6. Run this script again", Colors.YELLOW)
            return False
            
    except Exception as e:
        logger.log(f"❌ Failed to install WSL2: {e}", Colors.RED)
        return False

def windows_path_to_wsl(windows_path):
    """Convert Windows path to WSL path."""
    # Convert C:\Users\... to /mnt/c/Users/...
    path_str = str(windows_path).replace('\\', '/')
    # Remove any leading/trailing whitespace
    path_str = path_str.strip()
    # Handle absolute Windows paths (C:/, D:/, etc.)
    if ':' in path_str and len(path_str) > 1:
        # Extract drive letter (first character before colon)
        parts = path_str.split(':', 1)
        if len(parts) == 2:
            drive_letter = parts[0].lower()
            remaining_path = parts[1].lstrip('/').lstrip('\\')
            # Construct WSL path
            path_str = f'/mnt/{drive_letter}/{remaining_path}'
            # Normalize path separators
            path_str = path_str.replace('\\', '/')
            # Remove duplicate slashes
            while '//' in path_str:
                path_str = path_str.replace('//', '/')
    return path_str

def run_in_wsl(script_path, base_dir, logger, distro="Ubuntu"):
    """Run the setup script inside WSL2."""
    logger.log("", Colors.RESET)
    logger.log("=" * 60, Colors.BLUE)
    logger.log("🐧 Running Setup Inside WSL2 (Ubuntu)", Colors.BLUE)
    logger.log("=" * 60, Colors.BLUE)
    logger.log("", Colors.RESET)
    
    # Convert Windows paths to WSL paths
    wsl_script_path = windows_path_to_wsl(script_path)
    wsl_base_dir = windows_path_to_wsl(base_dir)
    
    logger.log(f"📁 Windows path: {base_dir}", Colors.CYAN)
    logger.log(f"📁 WSL path: {wsl_base_dir}", Colors.CYAN)
    logger.log("", Colors.RESET)
    
    # Check if Ubuntu setup is complete first
    logger.log("🔍 Verifying Ubuntu is ready...", Colors.BLUE)
    if not check_ubuntu_setup_complete(logger, distro):
        logger.log("", Colors.RESET)
        logger.log("❌ Ubuntu needs initial user setup before proceeding.", Colors.RED)
        logger.log("", Colors.RESET)
        logger.log("📋 Please complete Ubuntu setup:", Colors.CYAN)
        logger.log(f"   1. Launch Ubuntu: wsl -d {distro}", Colors.YELLOW)
        logger.log("   2. Create your username and password when prompted", Colors.YELLOW)
        logger.log("   3. Wait for Ubuntu to finish initializing", Colors.YELLOW)
        logger.log("   4. Run this script again", Colors.YELLOW)
        return False
    
    # Check if Python3 is available in WSL
    logger.log("🔍 Checking Python3 in WSL...", Colors.BLUE)
    try:
        # First check Python version
        version_result = subprocess.run(
            ["wsl", "-d", distro, "python3", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if version_result.returncode == 0:
            version_str = version_result.stdout.strip()
            logger.log(f"✅ Found {version_str}", Colors.GREEN)
            
            # Check if it's Python 3.12
            if "3.12" in version_str:
                logger.log("⚠️ Python 3.12 detected in WSL", Colors.YELLOW)
                logger.log("   Some packages may have compatibility issues.", Colors.YELLOW)
                logger.log("   Consider installing Python 3.11: sudo apt-get install python3.11", Colors.CYAN)
        else:
            logger.log("⚠️ Python3 not found in WSL. Installing...", Colors.YELLOW)
            subprocess.run(
                ["wsl", "-d", distro, "sudo", "apt-get", "update"],
                timeout=60
            )
            # Try to install Python 3.11 first, fallback to default python3
            install_result = subprocess.run(
                ["wsl", "-d", distro, "sudo", "apt-get", "install", "-y", "python3.11", "python3.11-venv", "python3.11-pip", "build-essential"],
                capture_output=True,
                timeout=300
            )
            if install_result.returncode != 0:
                # Fallback to default python3
                subprocess.run(
                    ["wsl", "-d", distro, "sudo", "apt-get", "install", "-y", "python3", "python3-venv", "python3-pip", "build-essential"],
                    timeout=300
                )
            logger.log("✅ Python3 installed in WSL", Colors.GREEN)
            
            # Install wslu (provides wslview command for opening files in Windows browser)
            logger.log("", Colors.RESET)
            logger.log("🔍 Installing wslu (for wslview command)...", Colors.BLUE)
            try:
                wslu_result = subprocess.run(
                    ["wsl", "-d", distro, "sudo", "apt-get", "install", "-y", "wslu"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if wslu_result.returncode == 0:
                    logger.log("✅ wslu installed successfully", Colors.GREEN)
                else:
                    logger.log("⚠️ wslu installation failed (may not be available in this Ubuntu version)", Colors.YELLOW)
                    logger.log("   You can install it manually: sudo apt install wslu", Colors.CYAN)
            except Exception as e:
                logger.log(f"⚠️ Could not install wslu: {e}", Colors.YELLOW)
                logger.log("   You can install it manually: sudo apt install wslu", Colors.CYAN)
    except subprocess.TimeoutExpired:
        logger.log("⏱️ Python3 check timed out. Ubuntu may be slow to respond.", Colors.YELLOW)
        logger.log("   This might indicate Ubuntu needs initial setup.", Colors.CYAN)
        return False
    except Exception as e:
        logger.log(f"⚠️ Could not check/install Python3: {e}", Colors.YELLOW)
        logger.log("   Ubuntu may need initial user setup. Please run: wsl -d Ubuntu", Colors.CYAN)
        return False
    
    logger.log("", Colors.RESET)
    logger.log("🚀 Executing setup script in WSL2...", Colors.BLUE)
    logger.log("", Colors.RESET)
    
    # Run the setup script inside WSL
    try:
        cmd = [
            "wsl", "-d", distro,
            "bash", "-c",
            f"cd {wsl_base_dir} && python3 {wsl_script_path}"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        error_output = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output, end='')
                logger.raw_log(output)
                # Check for catastrophic failure in output (now includes both stdout and stderr)
                if "catastrophic failure" in output.lower() or "e_unexpected" in output.lower():
                    error_output = output
                    # Immediately detect and handle catastrophic failure
                    logger.log("", Colors.RESET)
                    logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
                    logger.log("", Colors.RESET)
                    logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
                    logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
                    logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
                    logger.log("   4. Run this script again", Colors.YELLOW)
                    logger.log("", Colors.RESET)
                    logger.log("Or run: python presetup.py", Colors.CYAN)
                    logger.log("", Colors.RESET)
                    # Wait for process to finish before returning
                    process.wait()
                    return False
        
        rc = process.poll()
        if rc != 0:
            # Check if it's a catastrophic failure
            if error_output and ("catastrophic failure" in error_output.lower() or "e_unexpected" in error_output.lower()):
                logger.log("", Colors.RESET)
                logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
                logger.log("", Colors.RESET)
                logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
                logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
                logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
                logger.log("   4. Run this script again", Colors.YELLOW)
                logger.log("", Colors.RESET)
                logger.log("Or run: python presetup.py", Colors.CYAN)
                logger.log("", Colors.RESET)
                return False
            raise subprocess.CalledProcessError(rc, cmd)
        
        return True
    except subprocess.CalledProcessError as e:
        # Check error output for catastrophic failure
        error_str = str(e).lower()
        if "catastrophic" in error_str or "e_unexpected" in error_str:
            logger.log("", Colors.RESET)
            logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
            logger.log("", Colors.RESET)
            logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
            logger.log("", Colors.RESET)
            logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
            logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
            logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
            logger.log("   4. Run this script again", Colors.YELLOW)
            logger.log("", Colors.RESET)
            logger.log("Or run: python presetup.py", Colors.CYAN)
            logger.log("", Colors.RESET)
            return False
        logger.log(f"❌ Setup failed in WSL2: {e}", Colors.RED)
        return False
    except Exception as e:
        error_str = str(e).lower()
        # Check if the exception message contains catastrophic failure indicators
        if "catastrophic" in error_str or "e_unexpected" in error_str:
            logger.log("", Colors.RESET)
            logger.log("❌ WSL is experiencing a catastrophic failure error.", Colors.RED)
            logger.log("", Colors.RESET)
            logger.log("📋 To fix this, you need to unregister and reinstall Ubuntu:", Colors.CYAN)
            logger.log("", Colors.RESET)
            logger.log("   1. Run: wsl --unregister Ubuntu", Colors.YELLOW)
            logger.log("   2. Run: wsl --install -d Ubuntu", Colors.YELLOW)
            logger.log("   3. After Ubuntu launches, create your username and password", Colors.YELLOW)
            logger.log("   4. Run this script again", Colors.YELLOW)
            logger.log("", Colors.RESET)
            logger.log("Or run: python presetup.py", Colors.CYAN)
            logger.log("", Colors.RESET)
            return False
        logger.log(f"❌ Error running setup in WSL2: {e}", Colors.RED)
        return False

def main():
    base_dir = Path(__file__).parent.absolute()
    logs_dir = base_dir / "logs" / "setup"
    logs_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now()
    day = now.strftime("%d")
    mon = now.strftime("%b")
    year = now.strftime("%Y")
    hour = now.strftime("%I").lstrip("0") or "0"
    minute = now.strftime("%M")
    ampm = now.strftime("%p").lower()
    ts = f"{day}_{mon}_{year}_{hour}_{minute}_{ampm}"
    log_file_path = logs_dir / f"setup_{ts}.log"
    logger = Logger(log_file_path)
    
    try:
        logger.log("🚀 Welcome to the Custom-Nerd/Nerd-Engine Backend Setup Wizard!", Colors.BLUE)
        logger.log(f"📝 Logging setup progress to: {log_file_path}", Colors.YELLOW)
        logger.log("", Colors.RESET)
        logger.log("⏰ IMPORTANT: This setup will take a couple of hours to complete.", Colors.YELLOW)
        logger.log("   Please wait patiently - this is normal! The script is downloading", Colors.CYAN)
        logger.log("   and installing many packages, which takes time.", Colors.CYAN)
        logger.log("   Do not interrupt the process.", Colors.CYAN)
        logger.log("", Colors.RESET)
        logger.log("💡 TIP: If setup.py fails on the first run, don't worry!", Colors.YELLOW)
        logger.log("   Check what failed in the error messages above, fix any issues,", Colors.CYAN)
        logger.log("   and run the script again. The script will resume from where it left off.", Colors.CYAN)
        logger.log("", Colors.RESET)
        logger.log("✨ Let's get your environment up and running...", Colors.RESET)
        logger.log("", Colors.RESET)
        logger.log("📌 You may need to type in the terminal twice:", Colors.CYAN)
        logger.log("   1) Use existing venv? → say yes.", Colors.RESET)
        logger.log("   2) Password for Ollama (last step).", Colors.RESET)
        logger.log("", Colors.RESET)

        # 1. Detect OS and Platform
        os_name = platform.system()
        is_wsl = bool(os.environ.get('WSL_DISTRO_NAME'))
        
        if os_name == "Darwin":
            platform_name = "Mac"
            logger.log("🍎 Running on macOS...", Colors.RESET)
        elif os_name == "Linux":
            platform_name = "Linux"
            if is_wsl:
                wsl_distro = os.environ.get('WSL_DISTRO_NAME', 'Unknown')
                if 'ubuntu' in wsl_distro.lower() or 'Ubuntu' in wsl_distro:
                    logger.log(f"🐧 Running on Linux (WSL2 - Ubuntu: {wsl_distro})...", Colors.GREEN)
                else:
                    logger.log(f"🐧 Running on Linux (WSL2 - {wsl_distro})...", Colors.YELLOW)
                    logger.log("   This script is optimized for Ubuntu. Proceeding anyway...", Colors.CYAN)
                
                # Check for Python 3.11 and install if needed
                logger.log("", Colors.RESET)
                logger.log("🔍 Checking for Python 3.11 (recommended for WSL)...", Colors.BLUE)
                python311_available = False
                try:
                    python311_check = subprocess.run(
                        ["python3.11", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if python311_check.returncode == 0:
                        python311_available = True
                        logger.log("✅ Python 3.11 is available", Colors.GREEN)
                    else:
                        logger.log("⚠️ Python 3.11 not found. Installing...", Colors.YELLOW)
                        # Check if sudo can run without password (non-interactive)
                        sudo_check = subprocess.run(
                            ["sudo", "-n", "true"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if sudo_check.returncode == 0:
                            # Sudo doesn't require password, safe to install
                            logger.log("   Updating package lists...", Colors.CYAN)
                            apt_update = subprocess.run(
                                ["sudo", "apt", "update"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=120
                            )
                            logger.log("   Installing Python 3.11 and dependencies...", Colors.CYAN)
                            python311_install = subprocess.run(
                                ["sudo", "apt-get", "install", "-y", "python3.11", "python3.11-venv", "python3.11-dev"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=300
                            )
                            if python311_install.returncode == 0:
                                python311_available = True
                                logger.log("✅ Python 3.11 installed successfully", Colors.GREEN)
                            else:
                                logger.log("⚠️ Python 3.11 installation failed. Continuing with default Python...", Colors.YELLOW)
                                logger.log("   You can install it manually: sudo apt install python3.11 python3.11-venv python3.11-dev", Colors.CYAN)
                        else:
                            logger.log("⚠️ Python 3.11 not found. Skipping installation (requires password).", Colors.YELLOW)
                            logger.log("   You can install it manually:", Colors.CYAN)
                            logger.log("   sudo apt update", Colors.CYAN)
                            logger.log("   sudo apt install python3.11 python3.11-venv python3.11-dev", Colors.CYAN)
                except Exception as e:
                    logger.log(f"⚠️ Could not check/install Python 3.11: {e}", Colors.YELLOW)
                    logger.log("   Continuing with default Python...", Colors.CYAN)
                
                # Install wslu (provides wslview command for opening files in Windows browser)
                logger.log("", Colors.RESET)
                logger.log("🔍 Checking for wslu (optional - for opening files in Windows browser)...", Colors.BLUE)
                try:
                    # Check if wslview command exists
                    wslview_check = subprocess.run(
                        ["which", "wslview"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if wslview_check.returncode == 0:
                        logger.log("✅ wslu is already installed", Colors.GREEN)
                    else:
                        # Check if sudo can run without password (non-interactive)
                        sudo_check = subprocess.run(
                            ["sudo", "-n", "true"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if sudo_check.returncode == 0:
                            # Sudo doesn't require password, safe to install
                            logger.log("⚠️ wslu not found. Installing...", Colors.YELLOW)
                            # Update package lists first
                            apt_update = subprocess.run(
                                ["sudo", "apt", "update"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=120
                            )
                            wslu_result = subprocess.run(
                                ["sudo", "apt-get", "install", "-y", "wslu"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=120
                            )
                            if wslu_result.returncode == 0:
                                logger.log("✅ wslu installed successfully", Colors.GREEN)
                            else:
                                logger.log("⚠️ wslu installation failed (may not be available in this Ubuntu version)", Colors.YELLOW)
                                logger.log("   You can install it manually: sudo apt install wslu", Colors.CYAN)
                        else:
                            # Sudo requires password - skip installation to avoid blocking
                            logger.log("⚠️ wslu not found. Skipping installation (requires password).", Colors.YELLOW)
                            logger.log("   This is optional. You can install it manually later:", Colors.CYAN)
                            logger.log("   sudo apt update && sudo apt install wslu", Colors.CYAN)
                except Exception as e:
                    logger.log(f"⚠️ Could not check wslu: {e}", Colors.YELLOW)
                    logger.log("   This is optional. You can install it manually: sudo apt install wslu", Colors.CYAN)
            else:
                logger.log("🐧 Running on Linux...", Colors.RESET)
        elif os_name == "Windows":
            platform_name = "Windows"
            logger.log("🪟 Running on Windows...", Colors.RESET)
            logger.log("", Colors.RESET)
            
            # Check if we're already running inside WSL
            if is_wsl:
                wsl_distro = os.environ.get('WSL_DISTRO_NAME', 'Unknown')
                # Verify it's Ubuntu specifically
                if 'ubuntu' in wsl_distro.lower() or 'Ubuntu' in wsl_distro:
                    logger.log(f"✅ Already running inside WSL2 (Ubuntu: {wsl_distro}). Proceeding with setup...", Colors.GREEN)
                else:
                    logger.log(f"⚠️ Running inside WSL2 but distribution is '{wsl_distro}', not Ubuntu.", Colors.YELLOW)
                    logger.log("   This script is optimized for Ubuntu. Proceeding anyway...", Colors.CYAN)
                
                # Check for Python 3.11 and install if needed
                logger.log("", Colors.RESET)
                logger.log("🔍 Checking for Python 3.11 (recommended for WSL)...", Colors.BLUE)
                python311_available = False
                try:
                    python311_check = subprocess.run(
                        ["python3.11", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if python311_check.returncode == 0:
                        python311_available = True
                        logger.log("✅ Python 3.11 is available", Colors.GREEN)
                    else:
                        logger.log("⚠️ Python 3.11 not found. Installing...", Colors.YELLOW)
                        # Check if sudo can run without password (non-interactive)
                        sudo_check = subprocess.run(
                            ["sudo", "-n", "true"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if sudo_check.returncode == 0:
                            # Sudo doesn't require password, safe to install
                            logger.log("   Updating package lists...", Colors.CYAN)
                            apt_update = subprocess.run(
                                ["sudo", "apt", "update"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=120
                            )
                            logger.log("   Installing Python 3.11 and dependencies...", Colors.CYAN)
                            python311_install = subprocess.run(
                                ["sudo", "apt-get", "install", "-y", "python3.11", "python3.11-venv", "python3.11-dev"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=300
                            )
                            if python311_install.returncode == 0:
                                python311_available = True
                                logger.log("✅ Python 3.11 installed successfully", Colors.GREEN)
                            else:
                                logger.log("⚠️ Python 3.11 installation failed. Continuing with default Python...", Colors.YELLOW)
                                logger.log("   You can install it manually: sudo apt install python3.11 python3.11-venv python3.11-dev", Colors.CYAN)
                        else:
                            logger.log("⚠️ Python 3.11 not found. Skipping installation (requires password).", Colors.YELLOW)
                            logger.log("   You can install it manually:", Colors.CYAN)
                            logger.log("   sudo apt update", Colors.CYAN)
                            logger.log("   sudo apt install python3.11 python3.11-venv python3.11-dev", Colors.CYAN)
                except Exception as e:
                    logger.log(f"⚠️ Could not check/install Python 3.11: {e}", Colors.YELLOW)
                    logger.log("   Continuing with default Python...", Colors.CYAN)
                
                # Install wslu (provides wslview command for opening files in Windows browser)
                logger.log("", Colors.RESET)
                logger.log("🔍 Checking for wslu (optional - for opening files in Windows browser)...", Colors.BLUE)
                try:
                    # Check if wslview command exists
                    wslview_check = subprocess.run(
                        ["which", "wslview"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if wslview_check.returncode == 0:
                        logger.log("✅ wslu is already installed", Colors.GREEN)
                    else:
                        # Check if sudo can run without password (non-interactive)
                        sudo_check = subprocess.run(
                            ["sudo", "-n", "true"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if sudo_check.returncode == 0:
                            # Sudo doesn't require password, safe to install
                            logger.log("⚠️ wslu not found. Installing...", Colors.YELLOW)
                            # Update package lists first
                            apt_update = subprocess.run(
                                ["sudo", "apt", "update"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=120
                            )
                            wslu_result = subprocess.run(
                                ["sudo", "apt-get", "install", "-y", "wslu"],
                                capture_output=True,
                                text=True,
                                stdin=subprocess.DEVNULL,
                                timeout=120
                            )
                            if wslu_result.returncode == 0:
                                logger.log("✅ wslu installed successfully", Colors.GREEN)
                            else:
                                logger.log("⚠️ wslu installation failed (may not be available in this Ubuntu version)", Colors.YELLOW)
                                logger.log("   You can install it manually: sudo apt install wslu", Colors.CYAN)
                        else:
                            # Sudo requires password - skip installation to avoid blocking
                            logger.log("⚠️ wslu not found. Skipping installation (requires password).", Colors.YELLOW)
                            logger.log("   This is optional. You can install it manually later:", Colors.CYAN)
                            logger.log("   sudo apt update && sudo apt install wslu", Colors.CYAN)
                except Exception as e:
                    logger.log(f"⚠️ Could not check wslu: {e}", Colors.YELLOW)
                    logger.log("   This is optional. You can install it manually: sudo apt install wslu", Colors.CYAN)
                
                logger.log("", Colors.RESET)
            else:
                # We're on Windows but NOT in WSL - automatically enter WSL and run setup
                logger.log("🔍 Detected Windows outside WSL. Entering WSL2...", Colors.BLUE)
                logger.log("", Colors.RESET)
                
                script_path = Path(__file__).absolute()
                
                # Get the exact Ubuntu distribution name
                wsl_installed, distro = check_wsl_installed(logger)
                if not distro:
                    distro = "Ubuntu"  # Default fallback
                
                # Check if WSL is installed
                    if not wsl_installed:
                        logger.log("", Colors.RESET)
                        logger.log("❌ WSL2 is not installed.", Colors.RED)
                        logger.log("", Colors.RESET)
                        logger.log("📋 To set up WSL2, run:", Colors.CYAN)
                        logger.log("", Colors.RESET)
                        logger.log("   python presetup.py", Colors.YELLOW)
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
                        sys.exit(1)
                    
                # Convert Windows paths to WSL paths
                    wsl_base_dir = windows_path_to_wsl(base_dir)
                
                logger.log("", Colors.RESET)
                logger.log("=" * 50, Colors.GREEN)
                logger.log("📋 MANUAL WSL ENTRY REQUIRED", Colors.GREEN)
                logger.log("=" * 50, Colors.GREEN)
                logger.log("", Colors.RESET)
                logger.log("✅ WSL2 and Ubuntu are ready!", Colors.GREEN)
                logger.log("", Colors.RESET)
                logger.log("📋 Please run the following commands manually:", Colors.CYAN)
                logger.log("", Colors.RESET)
                logger.log(f"   1. Open a new terminal/PowerShell window", Colors.YELLOW)
                logger.log(f"   2. Run: wsl -d {distro}", Colors.YELLOW)
                logger.log(f"   3. Navigate to your project: cd Downloads/customnerd-main/customnerd-main/", Colors.YELLOW)
                logger.log("      (Path may vary depending on where you downloaded the project)", Colors.CYAN)
                logger.log(f"   4. Run: python3.11 setup.py", Colors.YELLOW)
                logger.log("      (Use python3.11 instead of python3 to ensure Python 3.11 is used)", Colors.CYAN)
                logger.log("", Colors.RESET)
                sys.exit(0)
        else:
            logger.log("❌ Unsupported OS detected!", Colors.RED)
            sys.exit(1)

        # 2. Check Python version compatibility
        logger.log("🔍 Checking Python version...", Colors.BLUE)
        step_results = []  # Track step results: [(step_name, status, message)]
        
        try:
            check_python_version(logger)
            step_results.append(("Step 1: Check Python version", "PASSED", "Python version compatible"))
        except SystemExit:
            # User chose to exit or version incompatible
            step_results.append(("Step 1: Check Python version", "FAILED", "Python version incompatible or user cancelled"))
            raise
        except Exception as e:
            step_results.append(("Step 1: Check Python version", "WARNING", f"Check completed with warnings: {e}"))
        logger.log("", Colors.RESET)

        # 3. Check and navigate to backend directory
        # Assuming script is run from customnerd/ directory
        backend_dir = base_dir / "customnerd-backend"

        if not backend_dir.exists():
            logger.log(f"❌ '{backend_dir.name}' directory not found!", Colors.RED)
            step_results.append(("Step 2: Verify backend directory", "FAILED", f"Directory not found: {backend_dir.name}"))
            sys.exit(1)
        
        step_results.append(("Step 2: Verify backend directory", "PASSED", f"Found: {backend_dir.name}"))
        os.chdir(backend_dir)
        
        # 4. Check if virtual environment already exists
        venv_dir = backend_dir / "nerd_engine_venv"
        venv_exists = venv_dir.exists() or venv_dir.is_symlink()
        venv_created = False  # Initialize flag
        
        if venv_exists:
            logger.log("", Colors.RESET)
            logger.log("🔍 Checking existing virtual environment...", Colors.BLUE)
            
            # Determine actual venv location (in case it's a symlink)
            if venv_dir.is_symlink():
                venv_actual_dir = venv_dir.resolve()
                logger.log(f"✅ Found existing virtual environment (symlink)", Colors.GREEN)
                logger.log(f"   Location: {venv_dir} -> {venv_actual_dir}", Colors.CYAN)
            else:
                venv_actual_dir = venv_dir
                logger.log(f"✅ Found existing virtual environment", Colors.GREEN)
                logger.log(f"   Location: {venv_dir}", Colors.CYAN)
            
            # Check if venv is valid
            if platform_name == "Windows":
                venv_python = venv_actual_dir / "Scripts" / "python.exe"
            else:
                venv_python = venv_actual_dir / "bin" / "python"
            
            venv_valid = venv_python.exists() if venv_actual_dir.exists() else False
            
            if venv_valid:
                logger.log("✅ Virtual environment is valid and ready to use", Colors.GREEN)
                logger.log("", Colors.RESET)
                logger.log("💡 Options:", Colors.CYAN)
                logger.log("   1. Use existing virtual environment (recommended)", Colors.RESET)
                logger.log("   2. Recreate virtual environment (will delete existing one)", Colors.RESET)
                logger.log("", Colors.RESET)
                
                # Check if we're in interactive mode
                if sys.stdin.isatty() and not is_wsl:
                    try:
                        response = input("Use existing virtual environment? (y/n) [y]: ").strip().lower()
                        if response == '' or response == 'y' or response == 'yes':
                            logger.log("✅ Using existing virtual environment", Colors.GREEN)
                            logger.log("", Colors.RESET)
                            venv_created = True  # Skip creation
                        else:
                            logger.log("🗑️ Will recreate virtual environment...", Colors.YELLOW)
                            # Remove existing venv
                            if venv_dir.is_symlink():
                                venv_dir.unlink()
                            elif venv_dir.exists():
                                import shutil
                                shutil.rmtree(venv_dir)
                            logger.log("✅ Removed existing virtual environment", Colors.GREEN)
                            venv_exists = False  # Will create new one
                    except (EOFError, KeyboardInterrupt):
                        # Non-interactive - use existing
                        logger.log("✅ Using existing virtual environment (non-interactive mode)", Colors.GREEN)
                        venv_created = True
                else:
                    # Non-interactive or WSL - use existing
                    logger.log("✅ Using existing virtual environment (non-interactive mode)", Colors.GREEN)
                    logger.log("", Colors.RESET)
                    venv_created = True  # Skip creation
            else:
                logger.log("⚠️ Existing virtual environment appears to be invalid or corrupted", Colors.YELLOW)
                logger.log("   Will recreate it...", Colors.CYAN)
                # Remove invalid venv
                if venv_dir.is_symlink():
                    venv_dir.unlink()
                elif venv_dir.exists():
                    import shutil
                    shutil.rmtree(venv_dir)
                logger.log("✅ Removed invalid virtual environment", Colors.GREEN)
                venv_exists = False  # Will create new one
        
        # 5. Create virtual environment (if needed)
        if not venv_exists or not venv_created:
            # Check if we're on a Windows mount - venv can't be created on Windows filesystems
            backend_path_str = str(backend_dir)
            is_windows_mount = backend_path_str.startswith('/mnt/') and len(backend_path_str) > 5 and backend_path_str[5].isalpha()
            
            if is_windows_mount:
                # Create venv in Linux-native location (home directory)
                import getpass
                username = getpass.getuser()
                venv_storage_dir = Path.home() / ".local" / "share" / "venvs" / "customnerd"
                venv_storage_dir.mkdir(parents=True, exist_ok=True)
                
                # Create a unique venv name based on project path hash
                import hashlib
                project_hash = hashlib.md5(backend_path_str.encode()).hexdigest()[:8]
                venv_actual_dir = venv_storage_dir / f"nerd_engine_venv_{project_hash}"
                venv_dir = backend_dir / "nerd_engine_venv"  # Symlink target
                
                logger.log("", Colors.RESET)
                logger.log("⚠️ Project is on Windows filesystem mount (/mnt/c/...)", Colors.YELLOW)
                logger.log("   Virtual environments cannot be created on Windows filesystems in WSL.", Colors.CYAN)
                logger.log(f"   Creating venv in Linux-native location: {venv_actual_dir}", Colors.CYAN)
                logger.log(f"   Will create symlink: {venv_dir} -> {venv_actual_dir}", Colors.CYAN)
                logger.log("", Colors.RESET)
            else:
                # Normal Linux filesystem - create venv in project directory
                venv_dir = backend_dir / "nerd_engine_venv"
                venv_actual_dir = venv_dir
            
            logger.log("⏳ Creating virtual environment...", Colors.RESET)
            
            # Prefer Python 3.11 on WSL if available
            python_executable = sys.executable
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
                        logger.log("✅ Using Python 3.11 for virtual environment (recommended for WSL)", Colors.GREEN)
                except Exception:
                    pass  # Fall back to default python
            
            max_retries = 3  # First attempt + one retry after fixing
            
            for attempt in range(max_retries):
                try:
                    # Use venv_actual_dir for creation (Linux-native location if on Windows mount)
                    returncode, stdout, stderr = run_command_with_output(
                        [python_executable, "-m", "venv", str(venv_actual_dir)],
                        logger,
                        description="Creating virtual environment",
                        cwd=str(backend_dir)
                    )
                    
                    if returncode == 0:
                        venv_created = True
                        # If on Windows mount, create symlink
                        if is_windows_mount:
                            # Remove existing symlink or directory if it exists
                            if venv_dir.exists() or venv_dir.is_symlink():
                                if venv_dir.is_symlink():
                                    venv_dir.unlink()
                                else:
                                    import shutil
                                    shutil.rmtree(venv_dir)
                            # Create symlink
                            venv_dir.symlink_to(venv_actual_dir)
                            logger.log(f"✅ Created symlink: {venv_dir} -> {venv_actual_dir}", Colors.GREEN)
                        step_results.append(("Step 3: Create virtual environment", "PASSED", f"Created: {venv_dir.name}"))
                        break
                    else:
                        # This should not happen as run_command_with_output raises on non-zero
                        # But handle it just in case
                        error_output = (stderr + stdout).lower() if stderr or stdout else ""
                        full_error = (stderr + stdout) if stderr or stdout else ""
                        
                        # Detect all possible venv/ensurepip errors
                        is_venv_error = (
                            "ensurepip is not available" in error_output or
                            "no module named ensurepip" in error_output or
                            "python3-venv" in error_output or
                            ("python" in error_output and "venv" in error_output and "not available" in error_output) or
                            ("venv" in error_output and "failed" in error_output)
                        )
                except subprocess.CalledProcessError as e:
                    # run_command_with_output raises CalledProcessError on non-zero exit
                    # The error output was already logged by run_command_with_output
                    
                    # Check if it's a Windows mount permission error
                    error_output = ""
                    try:
                        # Try to get stderr from the exception
                        if hasattr(e, 'stderr') and e.stderr:
                            error_output = e.stderr.lower()
                        elif hasattr(e, 'stdout') and e.stdout:
                            error_output = e.stdout.lower()
                        elif hasattr(e, 'output') and e.output:
                            error_output = str(e.output).lower()
                    except:
                        pass
                    
                    # Also try to get error from the exception string
                    try:
                        error_msg = str(e).lower()
                        if error_msg and not error_output:
                            error_output = error_msg
                    except:
                        error_msg = ""
                    
                    # Check for Windows mount permission errors
                    is_windows_mount_error = (
                        "operation not permitted" in error_output or
                        "errno 1" in error_output or
                        "/mnt/" in str(venv_actual_dir).lower()
                    )
                    
                    if is_windows_mount_error and not is_windows_mount:
                        # We're on Windows mount but didn't detect it - switch to Linux-native location
                        logger.log("", Colors.RESET)
                        logger.log("⚠️ Detected Windows filesystem mount issue!", Colors.YELLOW)
                        logger.log("   Virtual environments cannot be created on Windows filesystems.", Colors.CYAN)
                        logger.log("   Switching to Linux-native venv location...", Colors.CYAN)
                        logger.log("", Colors.RESET)
                        
                        # Recalculate with Windows mount detection
                        is_windows_mount = True
                        import getpass
                        username = getpass.getuser()
                        venv_storage_dir = Path.home() / ".local" / "share" / "venvs" / "customnerd"
                        venv_storage_dir.mkdir(parents=True, exist_ok=True)
                        
                        import hashlib
                        project_hash = hashlib.md5(str(backend_dir).encode()).hexdigest()[:8]
                        venv_actual_dir = venv_storage_dir / f"nerd_engine_venv_{project_hash}"
                        venv_dir = backend_dir / "nerd_engine_venv"
                        
                        # Retry with new location
                        continue
                    
                    # For venv creation, if it fails, it's almost always a missing python3-venv issue
                    # So we'll assume it's a venv error and try to fix it
                    is_venv_error = True
                    
                    # Try to get more specific error info if available
                    if not error_msg:
                        try:
                            error_msg = str(e).lower()
                        except:
                            error_msg = error_output if error_output else ""
                    
                    if "ensurepip" in error_msg or "venv" in error_msg or "python3-venv" in error_output:
                        is_venv_error = True
                    
                    if is_venv_error:
                        logger.log("", Colors.RESET)
                        logger.log("⚠️ Virtual environment creation failed - missing Python tooling", Colors.YELLOW)
                        logger.log("   Detected: Ubuntu 24.04 (Noble) minimal Python installation", Colors.CYAN)
                        logger.log("   Attempting to fix automatically...", Colors.CYAN)
                        logger.log("", Colors.RESET)
                        
                        # Only attempt fixes on Linux/WSL (not Windows)
                        if platform_name != "Windows":
                            try:
                                # ============================================================
                                # STEP 1: Check and fix APT cache corruption (if present)
                                # ============================================================
                                logger.log("🔍 Step 1/3: Checking APT cache integrity...", Colors.BLUE)
                                check_apt_returncode, check_apt_stdout, check_apt_stderr = run_command_with_output(
                                    ["sudo", "apt", "update"],
                                    logger,
                                    description="Checking APT cache",
                                    timeout=60
                                )
                                
                                apt_cache_corrupted = False
                                if check_apt_returncode != 0:
                                    apt_error = (check_apt_stderr + check_apt_stdout).lower() if check_apt_stderr or check_apt_stdout else ""
                                    if "unable to parse package file" in apt_error or "package cache file is corrupted" in apt_error:
                                        apt_cache_corrupted = True
                                        logger.log("", Colors.RESET)
                                        logger.log("⚠️ APT cache is corrupted. Fixing...", Colors.YELLOW)
                                        
                                        # Hard reset APT cache
                                        logger.log("   Removing corrupted package lists...", Colors.CYAN)
                                        run_command_with_output(
                                            ["sudo", "rm", "-rf", "/var/lib/apt/lists/*"],
                                            logger,
                                            description="Removing corrupted APT lists",
                                            timeout=30
                                        )
                                        
                                        logger.log("   Cleaning APT cache...", Colors.CYAN)
                                        run_command_with_output(
                                            ["sudo", "apt", "clean"],
                                            logger,
                                            description="Cleaning APT cache",
                                            timeout=30
                                        )
                                        
                                        logger.log("   Updating APT cache...", Colors.CYAN)
                                        run_command_with_output(
                                            ["sudo", "apt", "update"],
                                            logger,
                                            description="Updating APT after cache clean",
                                            timeout=120
                                        )
                                        logger.log("✅ APT cache fixed", Colors.GREEN)
                                else:
                                    logger.log("✅ APT cache is healthy", Colors.GREEN)
                                
                                # ============================================================
                                # STEP 2: Enable universe repository (required for python3-full)
                                # ============================================================
                                logger.log("", Colors.RESET)
                                logger.log("🔍 Step 2/3: Ensuring universe repository is enabled...", Colors.BLUE)
                                logger.log("   (Universe repo is disabled by default in WSL minimal images)", Colors.CYAN)
                                
                                # Try to enable universe repository (idempotent - safe to run multiple times)
                                # Ubuntu 24.04 uses different file structure, so we just try to add it
                                logger.log("   Enabling universe repository...", Colors.CYAN)
                                try:
                                    # Use subprocess.run directly instead of run_command_with_output
                                    # because add-apt-repository may return non-zero even when successful
                                    add_repo_result = subprocess.run(
                                        ["sudo", "add-apt-repository", "-y", "universe"],
                                        capture_output=True,
                                        text=True,
                                        timeout=60,
                                        stdin=subprocess.DEVNULL
                                    )
                                    
                                    # Check output to see if it succeeded or was already enabled
                                    output = (add_repo_result.stdout + add_repo_result.stderr).lower()
                                    if add_repo_result.returncode == 0:
                                        logger.log("✅ Universe repository enabled", Colors.GREEN)
                                    elif "already" in output or "exists" in output or "no change" in output:
                                        logger.log("✅ Universe repository already enabled", Colors.GREEN)
                                    else:
                                        # Even if it failed, continue - repository might already be enabled
                                        logger.log("⚠️ Could not verify universe repository status, but continuing...", Colors.YELLOW)
                                        logger.log("   (Repository may already be enabled)", Colors.CYAN)
                                except subprocess.TimeoutExpired:
                                    logger.log("⚠️ Repository check timed out, but continuing...", Colors.YELLOW)
                                except Exception as e:
                                    logger.log(f"⚠️ Error checking universe repository: {e}", Colors.YELLOW)
                                    logger.log("   Continuing anyway - repository may already be enabled", Colors.CYAN)
                                
                                # Update APT after enabling universe
                                logger.log("   Updating package lists...", Colors.CYAN)
                                run_command_with_output(
                                    ["sudo", "apt", "update"],
                                    logger,
                                    description="Updating APT after enabling universe",
                                    timeout=120
                                )
                                
                                # ============================================================
                                # STEP 3: Install python3-full (solves everything)
                                # ============================================================
                                python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                                logger.log("", Colors.RESET)
                                logger.log(f"🔍 Step 3/3: Installing python3-full (Python {python_version})...", Colors.BLUE)
                                logger.log("   This package includes:", Colors.CYAN)
                                logger.log("   • venv module", Colors.RESET)
                                logger.log("   • ensurepip module", Colors.RESET)
                                logger.log("   • pip", Colors.RESET)
                                logger.log("   • Full Python standard library", Colors.RESET)
                                logger.log("   (Recommended solution for Ubuntu 24.04 Noble)", Colors.CYAN)
                                logger.log("", Colors.RESET)
                                
                                # Try to install python3-full
                                # Note: apt-get may return exit code 100 even on success due to terminal warnings
                                install_returncode = None
                                install_stdout = ""
                                install_stderr = ""
                                try:
                                    install_returncode, install_stdout, install_stderr = run_command_with_output(
                                        ["sudo", "apt-get", "install", "-y", "python3-full"],
                                        logger,
                                        description="Installing python3-full",
                                        timeout=300
                                    )
                                except subprocess.CalledProcessError as e:
                                    # Capture output even if exit code is non-zero
                                    install_returncode = e.returncode
                                    # Try to get stdout/stderr from the exception if available
                                    if hasattr(e, 'stdout') and e.stdout:
                                        install_stdout = e.stdout
                                    if hasattr(e, 'stderr') and e.stderr:
                                        install_stderr = e.stderr
                                    # If we don't have output from exception, we'll check via venv module
                                
                                # Check if installation actually succeeded
                                # apt-get can return non-zero exit codes (like 100) even on success
                                # if there are non-critical warnings (e.g., terminal settings, TCSAFLUSH errors)
                                install_output = (install_stdout + install_stderr).lower() if install_stdout or install_stderr else ""
                                installation_succeeded = (
                                    install_returncode == 0 or
                                    "setting up python3-full" in install_output or
                                    "setting up python3.12-full" in install_output or
                                    "python3-full is already the newest version" in install_output or
                                    "python3.12-full" in install_output and ("setting up" in install_output or "unpacking" in install_output) or
                                    (install_returncode == 100 and ("setting up" in install_output or "unpacking" in install_output))
                                )
                                
                                # Also verify by checking if python3-venv module is available
                                # This is the most reliable check - if venv works, installation succeeded
                                if not installation_succeeded or install_returncode != 0:
                                    try:
                                        check_venv = subprocess.run(
                                            ["python3", "-m", "venv", "--help"],
                                            stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL,
                                            timeout=5
                                        )
                                        if check_venv.returncode == 0:
                                            installation_succeeded = True
                                            logger.log("", Colors.RESET)
                                            logger.log("✅ Verified: python3-venv module is available (installation succeeded)", Colors.GREEN)
                                    except:
                                        pass
                                
                                if installation_succeeded:
                                    logger.log("", Colors.RESET)
                                    logger.log("✅ python3-full installed successfully", Colors.GREEN)
                                    logger.log("   All Python tooling is now available!", Colors.CYAN)
                                    logger.log("", Colors.RESET)
                                    logger.log("🔄 Retrying virtual environment creation...", Colors.BLUE)
                                    logger.log("", Colors.RESET)
                                    continue  # Retry venv creation
                                else:
                                    # Installation failed - try version-specific venv package as fallback
                                    install_error = (install_stderr + install_stdout).lower() if install_stderr or install_stdout else ""
                                    
                                    # Try installing version-specific python3-venv package
                                    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                                    venv_package = f"python3.{sys.version_info.minor}-venv"
                                    
                                    logger.log("", Colors.RESET)
                                    logger.log(f"⚠️ python3-full installation failed, trying {venv_package}...", Colors.YELLOW)
                                    logger.log("", Colors.RESET)
                                
                                venv_install_returncode, venv_install_stdout, venv_install_stderr = run_command_with_output(
                                    ["sudo", "apt-get", "install", "-y", venv_package],
                                    logger,
                                    description=f"Installing {venv_package}",
                                    timeout=300
                                )
                                
                                # Check if installation actually succeeded
                                venv_install_output = (venv_install_stdout + venv_install_stderr).lower() if venv_install_stdout or venv_install_stderr else ""
                                venv_installation_succeeded = (
                                    venv_install_returncode == 0 or
                                    f"setting up {venv_package}" in venv_install_output or
                                    f"{venv_package} is already the newest version" in venv_install_output or
                                    "0 upgraded, 0 newly installed" in venv_install_output and venv_package in venv_install_output
                                )
                                
                                # Also verify by checking if python3-venv module is available
                                if not venv_installation_succeeded:
                                    try:
                                        check_venv = subprocess.run(
                                            ["python3", "-m", "venv", "--help"],
                                            stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL,
                                            timeout=5
                                        )
                                        if check_venv.returncode == 0:
                                            venv_installation_succeeded = True
                                    except:
                                        pass
                                
                                if venv_installation_succeeded:
                                    logger.log("", Colors.RESET)
                                    logger.log(f"✅ {venv_package} installed successfully", Colors.GREEN)
                                    logger.log("", Colors.RESET)
                                    logger.log("🔄 Retrying virtual environment creation...", Colors.BLUE)
                                    logger.log("", Colors.RESET)
                                    continue  # Retry venv creation
                                
                                    # Both installations failed - provide comprehensive help
                                    logger.log("", Colors.RESET)
                                    logger.log("❌ Failed to install python3-full and version-specific venv package", Colors.RED)
                                    
                                    # Check for specific error patterns
                                    if "no installation candidate" in install_error or "has no installation candidate" in install_error:
                                        logger.log("", Colors.RESET)
                                        logger.log("💡 Issue: Package not found in repositories", Colors.YELLOW)
                                        logger.log("   This usually means:", Colors.CYAN)
                                        logger.log("   • Universe repository is still not enabled", Colors.RESET)
                                        logger.log("   • APT cache needs updating", Colors.RESET)
                                    elif "unable to parse" in install_error or "corrupted" in install_error:
                                        logger.log("", Colors.RESET)
                                        logger.log("💡 Issue: APT cache still corrupted", Colors.YELLOW)
                                    
                                    display_manual_instructions(
                                        logger,
                                        "📋 MANUAL INSTALLATION STEPS",
                                        [
                                            {
                                                'title': 'Fix APT cache (if corrupted)',
                                                'commands': [
                                                    'sudo rm -rf /var/lib/apt/lists/*',
                                                    'sudo apt clean',
                                                    'sudo apt update'
                                                ]
                                            },
                                            {
                                                'title': 'Enable universe repository',
                                                'commands': [
                                                    'sudo add-apt-repository universe',
                                                    'sudo apt update'
                                                ]
                                            },
                                            {
                                                'title': 'Install Python tooling',
                                                'commands': [
                                                'sudo apt install -y python3-full',
                                                '# Or if python3-full fails, try version-specific:',
                                                f'sudo apt install -y python3.{sys.version_info.minor}-venv'
                                                ]
                                            },
                                            {
                                                'title': 'Verify installation',
                                                'commands': [
                                                    'python3 -m venv test_venv  # Should work now',
                                                    'rm -rf test_venv'
                                                ]
                                            },
                                            {
                                                'title': 'Run this script again',
                                                'commands': [
                                                    'python3 setup.py'
                                                ]
                                            }
                                        ]
                                    )
                                    step_results.append(("Step 3: Create virtual environment", "FAILED", "python3-full installation failed"))
                                    sys.exit(1)
                            except Exception as e:
                                logger.log("", Colors.RESET)
                                # Format error message nicely - show command as readable string instead of list
                                if isinstance(e, subprocess.CalledProcessError):
                                    cmd_str = " ".join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
                                    error_msg = f"Command '{cmd_str}' returned non-zero exit status {e.returncode}"
                                    logger.log(f"❌ Error during Python tooling installation: {error_msg}", Colors.RED)
                                else:
                                    logger.log(f"❌ Error during Python tooling installation: {e}", Colors.RED)
                                logger.log("", Colors.RESET)
                                logger.log("💡 Please follow manual installation steps above", Colors.CYAN)
                                if isinstance(e, subprocess.CalledProcessError):
                                    cmd_str = " ".join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
                                    step_results.append(("Step 3: Create virtual environment", "FAILED", f"Installation error: Command '{cmd_str}' failed"))
                                else:
                                    step_results.append(("Step 3: Create virtual environment", "FAILED", f"Installation error: {e}"))
                                sys.exit(1)
                        else:
                            logger.log("", Colors.RESET)
                            logger.log("❌ Cannot install Python tooling on Windows", Colors.RED)
                            logger.log("   Please install it manually in your WSL environment:", Colors.YELLOW)
                            logger.log("", Colors.RESET)
                            logger.log("   1. Activate WSL: wsl -d Ubuntu", Colors.CYAN)
                            logger.log("   2. Run: sudo apt install -y python3-full", Colors.CYAN)
                            logger.log("   3. Then run this script again", Colors.CYAN)
                            step_results.append(("Step 3: Create virtual environment", "FAILED", "Windows platform - install in WSL"))
                            sys.exit(1)
                    else:
                        # Different error - don't retry, show error
                        logger.log("", Colors.RESET)
                        logger.log("❌ Virtual environment creation failed with unexpected error", Colors.RED)
                        # Get error message from exception
                        error_msg = str(e)
                        if error_msg:
                            logger.log("", Colors.RESET)
                            logger.log("Error details:", Colors.YELLOW)
                            # Show error but truncate if too long
                            error_preview = error_msg[:1000] if len(error_msg) > 1000 else error_msg
                            logger.log(error_preview, Colors.RESET)
                            if len(error_msg) > 1000:
                                logger.log(f"\n   ... (truncated, {len(error_msg) - 1000} more characters)", Colors.RESET)
                        step_results.append(("Step 3: Create virtual environment", "FAILED", "Unexpected error"))
                        sys.exit(1)
        
        if not venv_created:
            logger.log("", Colors.RESET)
            logger.log("❌ Failed to create virtual environment after all retries.", Colors.RED)
            step_results.append(("Step 3: Create virtual environment", "FAILED", "Failed to create virtual environment"))
            sys.exit(1)

        # 5. Determine paths for venv python and pip
        if platform_name == "Windows":
            venv_python = venv_dir / "Scripts" / "python.exe"
            venv_pip = venv_dir / "Scripts" / "pip.exe"
        else:
            venv_python = venv_dir / "bin" / "python"
            venv_pip = venv_dir / "bin" / "pip"

        if not venv_python.exists():
            logger.log(f"❌ Could not find python executable at {venv_python}", Colors.RED)
            sys.exit(1)

        # 6. Install Requirements
        logger.log("📦 Installing Python packages from requirements.txt...", Colors.RESET)
        requirements_file = backend_dir / "requirements.txt"
        
        failed_pkgs = []
        installed_count = 0
        
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
            
            total_packages = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                logger.log(f"🔄 Installing {line}...", Colors.YELLOW)
                try:
                    run_command([str(venv_pip), "install", line], logger, cwd=str(backend_dir))
                    installed_count += 1
                except subprocess.CalledProcessError:
                    failed_pkgs.append(line)
        else:
            logger.log("⚠️ requirements.txt not found!", Colors.YELLOW)
            step_results.append(("Step 4: Install packages", "FAILED", "requirements.txt not found"))
            total_packages = 0

        # 7. Retry installation of failed packages without version
        still_failed_pkgs = []
        retry_success_count = 0
        for pkg in failed_pkgs:
            pkg_name = pkg.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
            logger.log(f"🔄 Retrying installation of {pkg_name}...", Colors.YELLOW)
            try:
                run_command([str(venv_pip), "install", pkg_name], logger, cwd=str(backend_dir))
                logger.log(f"✅ Successfully installed {pkg_name} without version.", Colors.GREEN)
                retry_success_count += 1
                installed_count += 1
            except subprocess.CalledProcessError:
                logger.log(f"❌ Failed to install {pkg_name} again.", Colors.RED)
                still_failed_pkgs.append(pkg_name)
        
        if requirements_file.exists():
            if not still_failed_pkgs:
                step_results.append(("Step 4: Install packages", "PASSED", f"Installed {installed_count}/{total_packages} packages"))
            else:
                step_results.append(("Step 4: Install packages", "WARNING", f"Installed {installed_count}/{total_packages} packages, {len(still_failed_pkgs)} failed"))

        # 8. Create variables.env file
        logger.log("🔧 Generating environment variables file...", Colors.RESET)
        env_content = """LLM="OpenAI"
NCBI_API_KEY=""
OPENAI_API_KEY=""
GEMINI_API_KEY=""
OLLAMA_MODEL="llama3.2:1b"
OLLAMA_BASE_URL="http://localhost:11434"
ELSEVIER_API_KEY=""
SPRINGER_API_KEY=""
WILEY_API_KEY=""
ENTREZ_EMAIL=""
OXFORD_API_KEY=""
OXFORD_APP_HEADER=""
GNEWS_API_KEY=""
NEWS_API_KEY=""
GUARDIAN_API_KEY=""
ADS_API_TOKEN=""
"""
        env_file = backend_dir / "variables.env"
        try:
            with open(env_file, "w") as f:
                f.write(env_content)
            step_results.append(("Step 5: Generate environment file", "PASSED", f"Created: {env_file.name}"))
        except Exception as e:
            step_results.append(("Step 5: Generate environment file", "FAILED", f"Error: {e}"))
            logger.log(f"⚠️ Could not create environment file: {e}", Colors.YELLOW)

        # 6. Optional: Install Ollama (Mac, Linux, WSL)
        # Runs terminal install; if password required, user enters it in this session.
        # On failure, shows manual instructions as backup.
        install_ollama_step(logger, platform_name, step_results, backend_dir)

        # 9. Display summary
        logger.log("", Colors.RESET)
        logger.log("=" * 70, Colors.BLUE)
        logger.log("📊 Setup Summary", Colors.BLUE)
        logger.log("=" * 70, Colors.BLUE)
        logger.log("", Colors.RESET)
        
        passed_steps = [s for s in step_results if s[1] == "PASSED"]
        failed_steps = [s for s in step_results if s[1] == "FAILED"]
        warning_steps = [s for s in step_results if s[1] == "WARNING"]
        
        if passed_steps:
            logger.log("✅ Steps Completed Successfully:", Colors.GREEN)
            for step_name, status, message in passed_steps:
                logger.log(f"   ✓ {step_name}", Colors.GREEN)
                if message:
                    logger.log(f"     → {message}", Colors.CYAN)
            logger.log("", Colors.RESET)
        
        if warning_steps:
            logger.log("⚠️ Steps with Warnings:", Colors.YELLOW)
            for step_name, status, message in warning_steps:
                logger.log(f"   ⚠ {step_name}", Colors.YELLOW)
                if message:
                    logger.log(f"     → {message}", Colors.CYAN)
            logger.log("", Colors.RESET)
        
        if failed_steps:
            logger.log("❌ Steps Failed:", Colors.RED)
            for step_name, status, message in failed_steps:
                logger.log(f"   ✗ {step_name}", Colors.RED)
                if message:
                    logger.log(f"     → {message}", Colors.YELLOW)
            logger.log("", Colors.RESET)
        
        logger.log("=" * 70, Colors.BLUE)
        logger.log("", Colors.RESET)
        
        # 10. Show result
        if not still_failed_pkgs:
            logger.log("")
            logger.log("✅ All packages installed successfully!", Colors.GREEN)
            logger.log("🚀 You're ready to start the server:", Colors.BLUE)
            logger.log("    python3 run.py", Colors.RESET)
        else:
            logger.log("")
            display_manual_instructions(
                logger,
                "⚠️ MANUAL PACKAGE INSTALLATION REQUIRED",
                [
                    {
                        'title': 'Navigate to backend directory',
                        'commands': ['cd customnerd-backend']
                    },
                    {
                        'title': 'Activate your virtual environment',
                        'commands': [
                            'nerd_engine_venv\\Scripts\\activate' if platform_name == "Windows" 
                            else 'source nerd_engine_venv/bin/activate'
                        ]
                    },
                    {
                        'title': 'Manually install the failed packages',
                        'commands': [f'pip3 install {pkg}' for pkg in still_failed_pkgs]
                    },
                    {
                        'title': 'Start the server',
                        'commands': ['python3 run.py']
                    }
                ]
            )

        # Final message
        logger.log("")
        logger.log("✨ Setup Complete! Tip of the Day:", Colors.GREEN)
        logger.log("👉 Never forget to hydrate and commit your code! 💧💻", Colors.YELLOW)
        logger.log(f"📁 Logs saved to: {log_file_path}", Colors.BLUE)
        
    finally:
        logger.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)

