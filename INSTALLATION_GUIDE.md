# Installation Guide

Simple setup guide for Custom-Nerd/Nerd-Engine on Windows, macOS, and Linux.

> **💡 Tip:** If you encounter errors during installation, try using ChatGPT or Gemini - they are really helpful for debugging installation issues!

## Table of Contents

- [Quick Steps](#quick-steps) - Fast installation for experienced users
- [Detailed Steps](#detailed-steps) - Step-by-step guide with explanations

---

## Quick Steps

**Windows:**
1. `python3 presetup.py` (as Administrator; may fail first time - let it complete, restart, then run again)
2. Open new terminal → `wsl -d Ubuntu`
3. `cd Downloads/customnerd-main/customnerd-main`
4. `python3 setup.py`
5. `python3 run.py`

**macOS/Linux:**
1. `cd ~/Downloads/customnerd-main`
2. `python3 setup.py`
3. `python3 run.py`

---

## Detailed Steps

## What You Need

- Python 3.11 or 3.12 (download from [python.org](https://www.python.org/downloads/release/python-3119/))
  - **macOS:** Download macOS 64-bit universal2 installer
  - **Windows:** Download Python install manager
  - **Linux:** Download XZ compressed source tarball or use your distribution's package manager
- Internet connection

**Windows Installation Note:** When installing Python on Windows, a terminal window will appear during the installation process. When prompted, type `y` and press Enter for:
  - Adding Python to PATH
  - Installing Cython

This is important for the installation to work correctly!

---

## Step 1: Download and Extract

1. Download the project file (it will be a `.zip` file)
2. Extract it:
   - **Windows:** Right-click the file → "Extract All"
   - **macOS:** Double-click the file
   - **Linux:** Right-click → "Extract Here" or use `unzip customnerd.zip` in terminal

---

## Step 2: Open Terminal

**macOS:**
- Press `Cmd + Space`, type "Terminal", press Enter

**Linux:**
- Press `Ctrl + Alt + T`

**Windows:**
- Press `Windows Key + X` → Click "Windows PowerShell (Admin)"
- Or press `Windows Key`, type "PowerShell", right-click it → "Run as Administrator"

---

## Step 3: Go to Your Project Folder

Type this command (replace `YourUsername` with your actual username on Windows):

**Windows:**
```
cd Downloads\customnerd-main\customnerd-main
```

**macOS/Linux:**
```
cd ~/Downloads/customnerd-main/customnerd-main
```

---

## Step 4: Windows Only - Install WSL2

**Skip this step if you're on macOS or Linux.**

Run this command:
```
python3 presetup.py
```

**⚠️ Important:** `presetup.py` might fail the first time - this is normal! Let the installation run completely, then restart your system. After restarting, run `python3 presetup.py` again.

This will install WSL2 and Ubuntu. You may need to restart your computer.

When it finishes, open a **new** terminal window and run:
```
wsl -d Ubuntu
```

Then go to your project:
```
cd /mnt/c/Users/YourUsername/Downloads/customnerd-main
```

---

## Step 4.5: Windows/WSL Only - Install Python 3.11 and wslu

**Skip this step if you're on macOS or Linux.**

WSL comes with Python 3.12 by default, but we need Python 3.11 for better compatibility. Run these commands inside WSL:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

Also install `wslu` for automatic browser window opening:

```bash
sudo apt update
sudo apt install wslu
```

**Note:** You can keep both Python 3.11 and 3.12 installed - we'll use Python 3.11 specifically for this project.

**Note:** The `setup.py` script will automatically install these if they're missing, but you can install them manually if you prefer.

---

## Step 5: Run Setup

**Windows (inside WSL):**
```
python3 setup.py
```

**macOS/Linux:**
```
python3 setup.py
```

**⏰ Important:** `setup.py` will take a couple of hours to complete. Please wait patiently - this is normal! The script is downloading and installing many packages, which takes time.

**You may need to type in the terminal twice:** (1) Use existing venv? → say yes. (2) Password for Ollama (last step).

Wait for it to finish. Do not interrupt the process.

**Note:** If `setup.py` fails on the first run, don't worry! This is common. Check what failed in the error messages, fix any issues (if needed), and run the script again. The script will resume from where it left off and fix most issues automatically.

**Troubleshooting:** If you encounter errors, try using ChatGPT or Gemini - they are really helpful for debugging installation issues!

---

## Step 6: Start the Server

**Windows (inside WSL):**
```
python3 run.py
```

**macOS/Linux:**
```
python3 run.py
```

The server will start at `http://localhost:8000`

---

## Configure Your API Keys

1. Open the file: `customnerd-backend/variables.env`
2. Add one of: `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY` (required). Set `LLM="OpenAI"`, `LLM="Gemini"`, or `LLM="Claude"` to match the key you added.
3. Save the file

---

## Logs

All installation logs are automatically saved in the `logs/` folder:
- `logs/presetup/` - Logs from `presetup.py` (Windows only)
- `logs/setup/` - Logs from `setup.py`
- `logs/run/` - Logs from `run.py`

Log files are named with the date and time (e.g., `setup_24_Dec_2025_8_26_pm.log`). If you encounter errors, check these logs for detailed information.

---
