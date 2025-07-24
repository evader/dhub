import sys
import os
import platform
import shutil
from pathlib import Path
from datetime import datetime
import tempfile

# Universal, native-first bootstrapper for JEMAI AGI OS

# --- GITHUB CREDENTIALS FOR CANVAS AUTOSYNC ---
# --- GITHUB CREDENTIALS FOR CANVAS AUTOSYNC ---
GITHUB_USERNAME = "evader"
# Active token for evaderbot - rotate if compromised
GITHUB_PAT = "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"  # evaderbot PAT
# Or use classic PAT if needed:
# GITHUB_PAT = "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"
# Or use fine-grained PAT:
# GITHUB_PAT = "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"
GITHUB_REMOTE = f"https://{GITHUB_USERNAME}:{GITHUB_PAT}@github.com/evader/dhub.git"
# ---------------------------------------------
# ---------------------------------------------

# No Docker. No black box. Pure Python. Modular. Extensible.

LOG_FILE = Path.cwd() / 'jemai_bootstrap.log'
CREATED_FILES = []

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    if LOG_FILE not in CREATED_FILES:
        CREATED_FILES.append(LOG_FILE)

def detect_platform():
    os_name = platform.system()
    os_release = platform.release()
    arch = platform.machine()
    python_version = sys.version.split()[0]
    is_admin = False
    try:
        if os_name == 'Windows':
            is_admin = os.getuid() == 0 if hasattr(os, 'getuid') else False
        else:
            is_admin = os.geteuid() == 0
    except Exception:
        pass
    log(f"Platform: {os_name} {os_release} ({arch}), Python {python_version}, Admin: {is_admin}")
    return {
        'os': os_name,
        'release': os_release,
        'arch': arch,
        'python_version': python_version,
        'is_admin': is_admin
    }

def check_space():
    root = Path('/') if os.name != 'nt' else Path(os.environ['SYSTEMDRIVE'] + '\\')
    total, used, free = shutil.disk_usage(root)
    log(f"Disk space on {root}: {free // (2**30)}GB free / {total // (2**30)}GB total")
    return {'root': str(root), 'total': total, 'used': used, 'free': free}

def active_jobs():
    # Process inspection not supported in some restricted/sandboxed environments.
    # This function now simply notifies and does not attempt process listing if unsupported.
    try:
        # Only attempt if not in restricted envs (like emscripten)
        if hasattr(os, 'popen') and sys.platform not in ['emscripten', 'wasi']:
            running = []
            if platform.system() == 'Windows':
                # List running processes, check for ssh.exe or robocopy etc
                try:
                    for proc in os.popen('tasklist').read().splitlines():
                        if any(tool in proc.lower() for tool in ['ssh', 'robocopy', 'scp']):
                            running.append(proc)
                except Exception:
                    pass
            else:
                try:
                    for proc in os.popen('ps -A -o command').read().splitlines():
                        if any(tool in proc.lower() for tool in ['ssh', 'rsync', 'scp']):
                            running.append(proc)
                except Exception:
                    pass
            if running:
                log(f"Active transfer/processes detected: {running}")
            else:
                log("No active SSH/xfer jobs detected.")
            return running
        else:
            log("Process inspection not supported in this environment.")
            return []
    except Exception:
        log("Error: Could not check running processes due to environment limitations.")
        return []

def scan_for_created_files():
    log('--- Scanning for files created by jemai_bootstrap.py ---')
    found = []
    # Check current working dir
    cwd = Path.cwd()
    for file in cwd.iterdir():
        if file.name.startswith('jemai_') and file.is_file():
            found.append(file)
    # Check temp dirs
    tempdirs = [tempfile.gettempdir()]
    if platform.system() == 'Windows':
        tempdirs.append(os.environ.get('TEMP', ''))
        tempdirs.append(os.environ.get('TMP', ''))
    for tempdir in tempdirs:
        if tempdir and Path(tempdir).exists():
            for file in Path(tempdir).glob('jemai_*'):
                if file.is_file():
                    found.append(file)
    for file in found:
        log(f'Found created file: {file}')
    if not found:
        log('No jemai-related files found in temp or CWD.')
    return found

def main():
    log('==== JEMAI Universal Bootstrapper (Native, No Docker) ===='\
        '\nStarting environment detection...')
    env = detect_platform()
    space = check_space()
    jobs = active_jobs()
    scan_for_created_files()
    log('Bootstrap scan complete.')
    log('Summary:')
    log(f"OS: {env['os']} {env['release']} ({env['arch']}) | Python {env['python_version']} | Admin: {env['is_admin']}")
    log(f"Disk: {space['free']//(2**30)}GB free")
    log(f"Active Jobs: {len(jobs)}")
    print('\nDONE. See jemai_bootstrap.log for full output. Extend this script to add more modules/services.\n')

def print_logfile():
    log_path = Path('jemai_bootstrap.log')
    if log_path.exists():
        print("===== jemai_bootstrap.log =====")
        with open(log_path, 'r', encoding='utf-8') as f:
            print(f.read())
        print("===== end of log =====")  # Fixed unterminated string error
    else:
        print("No jemai_bootstrap.log file found.")

def force_git_remote():
    """Sets the git remote to use credentials for autosync in stateless environments (like canvas)"""
    import subprocess
    try:
        if (Path.cwd() / '.git').exists():
            subprocess.run(["git", "remote", "set-url", "origin", GITHUB_REMOTE], check=True)
    except Exception as e:
        print(f"Could not set remote with credentials: {e}")

def autosync_to_github():
    """
    Adds, commits, and pushes changes to the current git repo if possible.
    Only runs if git is available and the repo is initialized.
    """
    import subprocess
    try:
        if (Path.cwd() / '.git').exists():
            force_git_remote()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Auto-sync at {now}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Auto-sync to GitHub: success.")
        else:
            print("Auto-sync skipped: not a git repo.")
    except subprocess.CalledProcessError as e:
        print(f"Auto-sync to GitHub failed: {e}")
    except Exception as e:
        print(f"Auto-sync error: {e}")

def setup_autopull_agent():
    """Creates and launches an auto-pull agent (Windows only) to keep local repo in sync."""
    import subprocess
    agent_path = Path('jemai_autopull.bat')
    # Create the batch file if it doesn't exist
    if not agent_path.exists():
        with open(agent_path, 'w') as bat:
            bat.write("""@echo off
cd /d %~dp0
:loop
git pull
timeout /t 30 >nul
goto loop
""")
        log(f"[Agent Setup] jemai_autopull.bat created.")
    # Check if agent is already running
    try:
        result = subprocess.check_output('tasklist', shell=True).decode()
        if 'jemai_autopull.bat' in result:
            log('[Agent Setup] Auto-pull agent already running.')
            print('[Agent Setup] Auto-pull agent already running.')
        else:
            # Launch the agent in a detached window
            subprocess.Popen(['start', 'jemai_autopull.bat'], shell=True)
            log('[Agent Setup] Auto-pull agent started.')
            print('[Agent Setup] Auto-pull agent started.')
    except Exception as e:
        log(f'[Agent Setup] Could not check/start agent: {e}')
        print(f'[Agent Setup] Could not check/start agent: {e}')

if __name__ == '__main__':
    main()
    print_logfile()
    autosync_to_github()
    # Setup the agent once (Windows only):
    if platform.system() == 'Windows':
        setup_autopull_agent()

