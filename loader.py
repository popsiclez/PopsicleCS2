import tempfile
import os
import sys
import subprocess
import atexit

LOADER_VERSION = "5"

# Try to import requests, fallback if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Global cleanup tracking
LOADER_TEMP_FILES = set()

def add_loader_temp_file(file_path):
    """Track temporary files created by loader for cleanup"""
    global LOADER_TEMP_FILES
    if file_path:
        LOADER_TEMP_FILES.add(file_path)

def cleanup_loader_temp_files():
    """Clean up all temporary files created by loader"""
    global LOADER_TEMP_FILES
    try:
        for temp_file in list(LOADER_TEMP_FILES):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"[LOADER CLEANUP] Removed: {temp_file}")
            except Exception as e:
                print(f"[LOADER CLEANUP] Error removing {temp_file}: {e}")
        LOADER_TEMP_FILES.clear()
    except Exception as e:
        print(f"[LOADER CLEANUP] Error during cleanup: {e}")

# Register cleanup handler
atexit.register(cleanup_loader_temp_files)

# Loader version


URL = "https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/script.pyw"
TITLE_URL = "https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/title.txt"
VERSION_URL = "https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/loaderversion.txt"
LOADED_SIGNAL_FILE = "script_loaded.signal"

def get_app_title():
    """Fetch application title from GitHub"""
    try:
        if HAS_REQUESTS:
            resp = requests.get(TITLE_URL, timeout=10)
            resp.raise_for_status()
            return resp.text.strip()
        else:
            # Fallback to urllib
            if sys.version_info[0] == 3:
                from urllib.request import urlopen
            else:
                from urllib2 import urlopen
            response = urlopen(TITLE_URL, timeout=10)
            return response.read().decode('utf-8').strip()
    except Exception:
        return "Popsicle CS2"  # Fallback title

def check_loader_version():
    """Check if loader version matches the remote version"""
    try:
        if HAS_REQUESTS:
            resp = requests.get(VERSION_URL, timeout=10)
            resp.raise_for_status()
            remote_version = resp.text.strip()
        else:
            # Fallback to urllib
            if sys.version_info[0] == 3:
                from urllib.request import urlopen
            else:
                from urllib2 import urlopen
            response = urlopen(VERSION_URL, timeout=10)
            remote_version = response.read().decode('utf-8').strip()
        
        return LOADER_VERSION == remote_version
    except Exception:
        # If we can't check version, assume it's okay to continue
        return True

def show_mode_selection():
    """Show mode selection in console and return selected mode"""
    try:
        app_title = get_app_title()
        print(f"\n{app_title} - Mode Selection")
        print("=" * 40)
        print("\nSelect mode:")
        print("1. LEGIT MODE")
        print("2. FULL MODE")
        
        while True:
            try:
                choice = input("\nEnter your choice (1 or 2): ").strip()
                if choice == "1":
                    print("\nLEGIT MODE selected!")
                    return "legit"
                elif choice == "2":
                    print("\nFULL MODE selected!")
                    return "full"
                else:
                    print("Invalid choice. Please enter 1 or 2.")
            except (KeyboardInterrupt, EOFError):
                print("\nSelection cancelled. Defaulting to FULL MODE.")
                return "full"
                
    except Exception as e:
        print(f"Error in mode selection: {e}")
        return "full"  # Ultimate fallback

def show_commands_selection():
    """Show commands selection menu and return list of selected commands"""
    try:
        print("\nAvailable commands:")
        print("1. debuglog - Enable logging to debug_log.txt")
        print("2. tooltips - Enable tooltips")
        print("3. fov - Enable FOV slider in misc")
        print("4. Skip - None")
        
        selected_commands = []
        
        while True:
            try:
                choice = input("\nEnter command numbers (comma-separated) or 4 to skip: ").strip()
                
                if choice == "4":
                    print("\nNo additional features selected.")
                    break
                
                # Parse comma-separated choices
                try:
                    choices = [int(x.strip()) for x in choice.split(',') if x.strip()]
                    valid_choices = []
                    
                    # Check if skip option (4) is included
                    if 4 in choices:
                        print("\nSkip option detected - no additional features selected.")
                        break
                    
                    for c in choices:
                        if c == 1:
                            selected_commands.append("debuglog")
                            valid_choices.append("debuglog")
                        elif c == 2:
                            selected_commands.append("tooltips")
                            valid_choices.append("tooltips")
                        elif c == 3:
                            selected_commands.append("fov")
                            valid_choices.append("fov")
                        else:
                            print(f"Invalid choice: {c}")
                    
                    if valid_choices:
                        print(f"\nSelected features: {', '.join(valid_choices)}")
                        break
                    else:
                        print("No valid choices selected. Please try again.")
                        
                except ValueError:
                    print("Invalid input format. Please enter numbers separated by commas.")
                    
            except (KeyboardInterrupt, EOFError):
                print("\nSelection cancelled. No additional features selected.")
                break
        
        return selected_commands
        
    except Exception as e:
        print(f"Error in commands selection: {e}")
        return []  # Return empty list on error

def show_debug_prompt():
    """Show debug menu prompt and return debug mode choice"""
    try: 
        print("Launch with debug menu?")
        print("1. Yes")
        print("2. No")
        
        while True:
            try:
                choice = input("\nEnter your choice (1 or 2): ").strip()
                if choice == "1":
                    # Password protection for debug mode
                    attempts = 3
                    while attempts > 0:
                        password = input("Enter password for debug mode: ").strip()
                        if password == "bert":
                            print("\nDebug mode enabled!")
                            return True
                        else:
                            attempts -= 1
                            if attempts > 0:
                                print(f"Incorrect password. {attempts} attempts remaining.")
                            else:
                                print("Too many incorrect attempts. Defaulting to normal mode.")
                                return False
                elif choice == "2":
                    print("\nNormal mode selected!")
                    return False
                else:
                    print("Invalid choice. Please enter 1 or 2.")
            except (KeyboardInterrupt, EOFError):
                print("\nSelection cancelled. Defaulting to normal mode.")
                return False
                
    except Exception as e:
        print(f"Error in debug selection: {e}")
        return False  # Ultimate fallback

def download_with_urllib(url):
    """Fallback download method using built-in urllib"""
    try:
        if sys.version_info[0] == 3:
            from urllib.request import urlopen
            from urllib.error import URLError
        else:
            from urllib2 import urlopen, URLError
        
        response = urlopen(url, timeout=15)
        return response.read().decode('utf-8')
    except Exception:
        return None

def find_python_executable():
    """Find the Python executable with required packages installed"""
    possible_paths = [
        os.path.join(os.environ.get('LocalAppData', ''), 'Programs', 'Python', 'Python313', 'python.exe'),
        os.path.join(os.environ.get('LocalAppData', ''), 'Programs', 'Python', 'Python312', 'python.exe'),
        os.path.join(os.environ.get('LocalAppData', ''), 'Programs', 'Python', 'Python311', 'python.exe'),
        'python.exe',
        'python',
    ]
    
    for python_path in possible_paths:
        try:
            # Test if python exists and has required packages (hidden window)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run([python_path, '-c', 'import keyboard, requests, pymem, pynput, PySide6, numpy, PIL, pyautogui'], 
                                  capture_output=True, text=True, timeout=10, startupinfo=startupinfo)
            if result.returncode == 0:
                return python_path
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    return None

def main():
    try:
        # Set console window title
        try:
            import ctypes
            app_title = get_app_title()
            ctypes.windll.kernel32.SetConsoleTitleW(f"{app_title} Loader")
        except:
            pass
        
        # Check loader version silently
        if not check_loader_version():
            print("Loader outdated, run setup again.")
            input("Press any key to exit...")
            return
        
        # Show mode selection dialog
        selected_mode = show_mode_selection()
        
        # Show commands selection
        selected_commands = show_commands_selection()
        
        # Show debug menu prompt (separate from commands)
        debug_mode = show_debug_prompt()
        
        print(f"\nSelected mode: {selected_mode.upper()}")
        if selected_commands:
            print(f"Selected features: {', '.join(selected_commands)}")
        else:
            print("No additional features selected")
        if debug_mode:
            print("Debug mode: ENABLED (console visible)")
        else:
            print("Debug mode: DISABLED (hidden)")
        print("Starting script...")
        
        # Exit if no mode selected
        if selected_mode is None:
            return
        
        # Download script using available method
        script_content = None
        if HAS_REQUESTS:
            try:
                resp = requests.get(URL, timeout=15)
                resp.raise_for_status()
                script_content = resp.text
            except Exception as e:
                pass
        
        # Fallback to urllib if requests failed or unavailable
        if script_content is None:
            script_content = download_with_urllib(URL)
        
        if script_content is None:
            return
        
        # Save to temp file with appropriate extension based on debug mode
        file_suffix = ".py" if debug_mode else ".pyw"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix, mode='w', encoding='utf-8') as tmp:
            tmp.write(script_content)
            tmp_path = tmp.name
        
        # Track temp file for cleanup
        add_loader_temp_file(tmp_path)
        
        # Create mode file to communicate with script
        mode_file = os.path.join(os.getcwd(), 'selected_mode.txt')
        add_loader_temp_file(mode_file)  # Track mode file for cleanup
        try:
            with open(mode_file, 'w') as f:
                f.write(selected_mode)
        except Exception as e:
            pass
        
        # Create commands file to communicate selected features with script
        commands_file = os.path.join(os.getcwd(), 'commands.txt')
        add_loader_temp_file(commands_file)  # Track commands file for cleanup
        try:
            with open(commands_file, 'w') as f:
                for command in selected_commands:
                    f.write(command + '\n')
        except Exception as e:
            pass
        
        # Find Python executable
        python_exe = find_python_executable()
        if python_exe is None:
            return
        
        # Clean up any existing loaded signal file
        loaded_signal_path = os.path.join(os.getcwd(), LOADED_SIGNAL_FILE)
        try:
            if os.path.exists(loaded_signal_path):
                os.remove(loaded_signal_path)
        except OSError:
            pass
        
        # Run script using system Python
        try:
            if debug_mode:
                # Debug mode: show console window using python.exe
                startupinfo = None  # Don't hide the console
                subprocess.Popen([python_exe, tmp_path], startupinfo=startupinfo)
            else:
                # Normal mode: hide console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # Use pythonw.exe instead of python.exe to avoid console window
                pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                if os.path.exists(pythonw_exe):
                    # Start the script in a non-blocking way
                    subprocess.Popen([pythonw_exe, tmp_path], startupinfo=startupinfo)
                else:
                    # Start the script in a non-blocking way
                    subprocess.Popen([python_exe, tmp_path], startupinfo=startupinfo)
            
            # Wait for script to signal it's fully loaded
            import time
            wait_interval = 0.5  # Check every 0.5 seconds
            waited_time = 0
            
            while True:
                if os.path.exists(loaded_signal_path):
                    print("Script confirmed loaded! Cleaning up and closing loader...")
                    break
                time.sleep(wait_interval)
                waited_time += wait_interval
            
            # Clean up temp file after script has confirmed it's loaded
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    if tmp_path in LOADER_TEMP_FILES:
                        LOADER_TEMP_FILES.remove(tmp_path)
            except OSError:
                pass
            
            # Clean up loaded signal file
            try:
                if os.path.exists(loaded_signal_path):
                    os.remove(loaded_signal_path)
            except OSError:
                pass
            
            # Exit the loader completely
            sys.exit(0)
                
        except Exception as e:
            # Only clean up on error
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    if tmp_path in LOADER_TEMP_FILES:
                        LOADER_TEMP_FILES.remove(tmp_path)
            except OSError:
                pass
            sys.exit(1)
                
    except Exception as e:
        pass

if __name__ == "__main__":
    main()
