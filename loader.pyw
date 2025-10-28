import tempfile
import os
import sys
import subprocess
import atexit
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading

LOADER_VERSION = "1.1.2"

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
        
        # Clean up temp directory if it exists and is empty
        try:
            if os.path.exists(TEMP_DIR) and os.path.isdir(TEMP_DIR):
                # Check if directory is empty
                if not os.listdir(TEMP_DIR):
                    os.rmdir(TEMP_DIR)
                    print(f"[LOADER CLEANUP] Removed empty temp directory: {TEMP_DIR}")
        except Exception as e:
            print(f"[LOADER CLEANUP] Error removing temp directory: {e}")
    except Exception as e:
        print(f"[LOADER CLEANUP] Error during cleanup: {e}")

# Register cleanup handler
atexit.register(cleanup_loader_temp_files)

# Loader version


URL = "https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/script.pyw"
TITLE_URL = "https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/title.txt"
VERSION_URL = "https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/loaderversion.txt"
LOADED_SIGNAL_FILE = "script_loaded.signal"

# Temp directory for temporary files
TEMP_DIR = os.path.join(os.getcwd(), 'temp')
# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

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

def get_github_status():
    """Fetch current status from GitHub"""
    try:
        if HAS_REQUESTS:
            resp = requests.get('https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/status', timeout=10)
            resp.raise_for_status()
            return resp.text.strip()
        else:
            # Fallback to urllib
            if sys.version_info[0] == 3:
                from urllib.request import urlopen
            else:
                from urllib2 import urlopen
            response = urlopen('https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/status', timeout=10)
            return response.read().decode('utf-8').strip()
    except Exception:
        return "Unknown"  # Fallback status

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
        print("3. Skip - None")
        
        selected_commands = []
        
        while True:
            try:
                choice = input("\nEnter command numbers (comma-separated) or 3 to skip: ").strip()
                
                if choice == "3":
                    print("\nNo additional features selected.")
                    break
                
                # Parse comma-separated choices
                try:
                    choices = [int(x.strip()) for x in choice.split(',') if x.strip()]
                    valid_choices = []
                    
                    # Check if skip option (3) is included
                    if 3 in choices:
                        print("\nSkip option detected - no additional features selected.")
                        break
                    
                    for c in choices:
                        if c == 1:
                            selected_commands.append("debuglog")
                            valid_choices.append("debuglog")
                        elif c == 2:
                            selected_commands.append("tooltips")
                            valid_choices.append("tooltips")
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
                    print("\nDebug mode enabled!")
                    return True
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

def is_cs2_running():
    """Check if CS2 process is currently running"""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'cs2.exe' in proc.info['name'].lower():
                return True
        return False
    except ImportError:
        # Fallback method without psutil
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq cs2.exe'], 
                                  capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return 'cs2.exe' in result.stdout.lower()
        except Exception:
            return False

class LoaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        # Remove window decorations (title bar, minimize, maximize, close buttons)
        self.root.overrideredirect(True)
        self.selected_mode = None
        self.selected_commands = []
        self.debug_mode = False
        self.app_title = "Popsicle CS2"  # Default title
        self.github_status = "Unknown"  # Default status
        
        # Config variables
        self.preload_var = tk.BooleanVar()
        self.config_var = tk.StringVar()
        self.default_config_var = tk.BooleanVar()
        
        # Get the actual directory where the executable/script is located for configs
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            loader_directory = os.path.dirname(sys.executable)
        else:
            # If running as script
            loader_directory = os.path.dirname(os.path.abspath(__file__))
        
        self.configs_dir = os.path.join(loader_directory, 'configs')
        
        # Cancel functionality variables
        self.script_process = None
        self.is_launching = False
        self.is_cancelled = False
        self.can_cancel = False

        # Make window always on top
        self.root.attributes('-topmost', True)

        # Initialize UI
        self.setup_ui()
        self.load_app_title()
        self.load_github_status()

        # Make window draggable
        self._drag_data = {'x': 0, 'y': 0}
        self.root.bind('<ButtonPress-1>', self._start_move)
        self.root.bind('<B1-Motion>', self._do_move)

    def _start_move(self, event):
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def _do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_data['x'])
        y = self.root.winfo_y() + (event.y - self._drag_data['y'])
        self.root.geometry(f'+{x}+{y}')
        
    def setup_ui(self):
        # Configure main window
        self.root.title("Loader")
        self.root.resizable(False, True)  # Allow vertical resizing
        
        # Set initial size and center (will be resized after UI setup)
        self.root.geometry("480x790")
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        
        bg_color = "#131313"        # Deep black
        fg_color = "#ffffff"        # White text
        accent_color = "#ffffff"    # White accent
        secondary_color = "#ffffff" # White secondary
        border_color = "#333333"    # Border color for frames
        frame_bg_color = "#1A1A1A"  # Darker background for frames
        
        # Define consistent font
        default_font = ("Segoe UI", 10, "bold")
        title_font = ("Segoe UI", 18, "bold")
        section_font = ("Segoe UI", 12, "bold")
        button_font = ("Segoe UI", 12, "bold")
        
        # Get available configs
        if os.path.exists(self.configs_dir):
            self.config_files = [f for f in os.listdir(self.configs_dir) if f.endswith('.json') and f != 'autosave.json']
        else:
            self.config_files = []
        
        self.root.configure(bg=bg_color)
        
        # Configure ttk styles for modern look
        style.configure('TProgressbar', 
                       background=accent_color,      # Progress fill color
                       troughcolor=bg_color,         # Background color (matches window background)
                       borderwidth=0,                # Remove border
                       lightcolor=bg_color,          # Remove 3D effect
                       darkcolor=bg_color,           # Remove 3D effect
                       relief='flat')                # Remove outline from progress bar fill
        
        # Title label
        self.title_label = tk.Label(
            self.root,
            text="Loading...",
            font=title_font,
            bg=bg_color,
            fg=accent_color
        )
        self.title_label.pack(pady=(25, 10))
        
        # Combined version and status label (split for color)
        version_status_frame = tk.Frame(self.root, bg=bg_color)
        version_status_frame.pack(pady=(0, 0))
        self.version_label = tk.Label(
            version_status_frame,
            text=f"Version: {LOADER_VERSION}",
            font=default_font,
            bg=bg_color,
            fg="#ffffff"
        )
        self.version_label.pack(side="left")
        self.status_label_color = tk.Label(
            version_status_frame,
            text=" | ...",
            font=default_font,
            bg=bg_color,
            fg="#ffffff"
        )
        self.status_label_color.pack(side="left")

        # White horizontal separator line
        separator = tk.Frame(self.root, bg="#ffffff", height=2)
        separator.pack(fill="x", padx=70, pady=(18, 18))

        # Main frame
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Mode selection frame
        mode_frame = tk.LabelFrame(
            main_frame,
            text="Mode",
            font=section_font,
            bg=frame_bg_color,
            fg=fg_color,
            bd=0,
            relief="flat",
            highlightthickness=0,
            labelanchor="n"
        )
        mode_frame.pack(fill="x", pady=(0, 20))
        
        # Mode selection
        self.mode_var = tk.StringVar(value="full")
        
        style.configure('Modern.TRadiobutton', font=default_font, background=frame_bg_color, foreground=fg_color, borderwidth=0, focuscolor=frame_bg_color)
        style.map('Modern.TRadiobutton',
            focuscolor=[('active', frame_bg_color), ('!active', frame_bg_color)],
            bordercolor=[('active', frame_bg_color), ('!active', frame_bg_color)],
            background=[('active', frame_bg_color), ('!active', frame_bg_color), ('hover', frame_bg_color)],
            foreground=[('active', fg_color), ('!active', fg_color), ('hover', fg_color)]
        )
        legit_radio = ttk.Radiobutton(
            mode_frame,
            text="LEGIT MODE 🛡️",
            variable=self.mode_var,
            value="legit",
            style='Modern.TRadiobutton'
        )
        legit_radio.pack(anchor="w", padx=15, pady=8)

        full_radio = ttk.Radiobutton(
            mode_frame,
            text="FULL MODE ⚡",
            variable=self.mode_var,
            value="full",
            style='Modern.TRadiobutton'
        )
        full_radio.pack(anchor="w", padx=15, pady=8)
        
        # Features frame
        features_frame = tk.LabelFrame(
            main_frame,
            text="Commands",
            font=section_font,
            bg=frame_bg_color,
            fg=fg_color,
            bd=0,
            relief="flat",
            highlightthickness=0,
            labelanchor="n"
        )
        features_frame.pack(fill="x", pady=(0, 20))
        
        # Feature checkboxes
        self.debuglog_var = tk.BooleanVar()
        self.tooltips_var = tk.BooleanVar()
        
        style.configure('Modern.TCheckbutton', font=default_font, background=frame_bg_color, foreground=fg_color, borderwidth=0, focuscolor=frame_bg_color)
        style.map('Modern.TCheckbutton',
            focuscolor=[('active', frame_bg_color), ('!active', frame_bg_color)],
            bordercolor=[('active', frame_bg_color), ('!active', frame_bg_color)],
            background=[('active', frame_bg_color), ('!active', frame_bg_color), ('hover', frame_bg_color)],
            foreground=[('active', fg_color), ('!active', fg_color), ('hover', fg_color)]
        )
        
        # Configure combobox style
        style.configure('Modern.TCombobox', font=default_font, background=frame_bg_color, foreground=fg_color, fieldbackground=frame_bg_color, borderwidth=0, relief='flat', arrowcolor=fg_color)
        style.map('Modern.TCombobox',
            fieldbackground=[('readonly', frame_bg_color), ('hover', frame_bg_color)],
            background=[('hover', frame_bg_color)],
            selectbackground=[('readonly', frame_bg_color)],
            selectforeground=[('readonly', fg_color)]
        )
        debuglog_check = ttk.Checkbutton(
            features_frame,
            text="Debug Logging 📝",
            variable=self.debuglog_var,
            style='Modern.TCheckbutton'
        )
        debuglog_check.pack(anchor="w", padx=15, pady=6)

        tooltips_check = ttk.Checkbutton(
            features_frame,
            text="Tooltips 💡",
            variable=self.tooltips_var,
            style='Modern.TCheckbutton'
        )
        tooltips_check.pack(anchor="w", padx=15, pady=6)
        
        # Debug mode frame
        debug_frame = tk.LabelFrame(
            main_frame,
            text="Debug",
            font=section_font,
            bg=frame_bg_color,
            fg=fg_color,
            bd=0,
            relief="flat",
            highlightthickness=0,
            labelanchor="n"
        )
        debug_frame.pack(fill="x", pady=(0, 20))
        
        self.debug_var = tk.BooleanVar()
        debug_check = ttk.Checkbutton(
            debug_frame,
            text="Show Console Window 💻",
            variable=self.debug_var,
            style='Modern.TCheckbutton'
        )
        debug_check.pack(anchor="w", padx=15, pady=6)

        self.run_local_var = tk.BooleanVar()
        
        # Get the actual directory where the executable/script is located
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            loader_directory = os.path.dirname(sys.executable)
        else:
            # If running as script
            loader_directory = os.path.dirname(os.path.abspath(__file__))
            
        folder_name = os.path.basename(loader_directory)
        run_local_check = ttk.Checkbutton(
            debug_frame,
            text=f"Run Locally ({folder_name}\\script.pyw) 📁",
            variable=self.run_local_var,
            style='Modern.TCheckbutton'
        )
        run_local_check.pack(anchor="w", padx=15, pady=6)
        
        # Config frame
        config_frame = tk.LabelFrame(
            main_frame,
            text="Config",
            font=section_font,
            bg=frame_bg_color,
            fg=fg_color,
            bd=0,
            relief="flat",
            highlightthickness=0,
            labelanchor="n"
        )
        config_frame.pack(fill="x", pady=(0, 20))
        
        # Pre-load config checkbox
        preload_check = ttk.Checkbutton(
            config_frame,
            text="Pre-Load Config ⚙️",
            variable=self.preload_var,
            style='Modern.TCheckbutton',
            command=self.toggle_config_dropdown
        )
        preload_check.pack(anchor="w", padx=15, pady=6)
        
        # Default config checkbox
        self.default_config_check = ttk.Checkbutton(
            config_frame,
            text="Default Config 📋",
            variable=self.default_config_var,
            style='Modern.TCheckbutton',
            command=self.toggle_default_config
        )
        
        # Config dropdown
        self.config_label = tk.Label(
            config_frame,
            text="Select Config:",
            font=default_font,
            bg=frame_bg_color,
            fg=fg_color
        )
        
        self.config_combo = ttk.Combobox(
            config_frame,
            textvariable=self.config_var,
            values=self.config_files,
            state="readonly",
            font=default_font,
            style='Modern.TCombobox'
        )
        
        # Initially hide dropdown if preload is off
        if not self.preload_var.get():
            self.default_config_check.pack_forget()
            self.config_label.pack_forget()
            self.config_combo.pack_forget()
        else:
            self.default_config_check.pack(anchor="w", padx=15, pady=(0, 6))
            self.config_label.pack(anchor="w", padx=15, pady=(6, 2))
            self.config_combo.pack(anchor="w", padx=15, pady=(0, 6))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg=bg_color)
        status_frame.pack(fill="x", pady=(0, 15))
        
        self.status_label = tk.Label(
            status_frame,
            text="Waiting...",
            font=default_font,
            bg=bg_color,
            fg="#ffffff"
        )
        self.status_label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(
            status_frame,
            mode='determinate',
            length=350,
            style='TProgressbar',
            maximum=100
        )
        self.progress.pack(pady=(8, 0))
        
        # Button frame (centered at bottom, grid for equal width)
        button_frame = tk.Frame(main_frame, bg=bg_color)
        button_frame.pack(fill="x", pady=(8, 0))

        button_style = {
            'font': button_font,
            'bg': accent_color,
            'fg': "black",
            'activebackground': "#cccccc",
            'activeforeground': "black",
            'bd': 0,
            'cursor': "hand2",
            'relief': "flat",
            'width': 12,  # fixed width for both buttons
            'height': 2
        }

        self.launch_button = tk.Button(
            button_frame,
            text="Launch",
            command=self.launch_script,
            **button_style
        )
        exit_button = tk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit,
            **button_style
        )

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        self.launch_button.grid(row=0, column=0, padx=(40, 10), pady=0, sticky="ew")
        exit_button.grid(row=0, column=1, padx=(10, 40), pady=0, sticky="ew")
        
        # Resize window to fit initial content
        self.root.update_idletasks()
        required_height = self.root.winfo_reqheight()
        self.root.geometry(f"480x{required_height}")
        self.center_window()
        
    def toggle_config_dropdown(self):
        """Show/hide config dropdown based on preload checkbox state"""
        if self.preload_var.get():
            # Show default config checkbox, dropdown and label
            self.default_config_check.pack(anchor="w", padx=15, pady=(0, 6))
            self.config_label.pack(anchor="w", padx=15, pady=(6, 2))
            self.config_combo.pack(anchor="w", padx=15, pady=(0, 6))
            # Set default selection to first config if available
            if self.config_files and not self.config_var.get():
                self.config_var.set(self.config_files[0])
        else:
            # Hide default config checkbox, dropdown and label
            self.default_config_check.pack_forget()
            self.config_label.pack_forget()
            self.config_combo.pack_forget()
            # Clear selection when hiding
            self.config_var.set("")
            self.default_config_var.set(False)
        
        # Resize window to fit content while keeping current position
        self.root.update_idletasks()
        required_height = self.root.winfo_reqheight()
        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()
        self.root.geometry(f"480x{required_height}+{current_x}+{current_y}")
    
    def toggle_default_config(self):
        """Show/hide config dropdown based on default config checkbox state"""
        if self.default_config_var.get():
            # Hide config dropdown and label when default config is selected
            self.config_label.pack_forget()
            self.config_combo.pack_forget()
            # Clear selection when hiding
            self.config_var.set("")
        else:
            # Show config dropdown and label when default config is not selected
            self.config_label.pack(anchor="w", padx=15, pady=(6, 2))
            self.config_combo.pack(anchor="w", padx=15, pady=(0, 6))
            # Set default selection to first config if available
            if self.config_files and not self.config_var.get():
                self.config_var.set(self.config_files[0])
        
        # Resize window to fit content while keeping current position
        self.root.update_idletasks()
        required_height = self.root.winfo_reqheight()
        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()
        self.root.geometry(f"480x{required_height}+{current_x}+{current_y}")
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def load_app_title(self):
        """Load app title in background thread"""
        def load_title():
            try:
                title = get_app_title()
                self.root.after(0, lambda: self.update_title(title))
            except:
                pass
                
        thread = threading.Thread(target=load_title, daemon=True)
        thread.start()
        
    def load_github_status(self):
        """Load GitHub status in background thread"""
        def load_status():
            try:
                status = get_github_status()
                self.root.after(0, lambda: self.update_github_status(status))
            except:
                pass
                
        thread = threading.Thread(target=load_status, daemon=True)
        thread.start()
        
    def update_title(self, title):
        """Update the title in the UI"""
        self.app_title = title
        self.title_label.config(text=f"{title} Loader")
        self.root.title(f"{title} Loader")
        
    def update_github_status(self, status):
        """Update the GitHub status in the UI"""
        self.github_status = status
        # Set split label text and color
        self.version_label.config(text=f"Version: {LOADER_VERSION}", fg="#ffffff")
        if status.lower() == "online":
            status_text = " 🟢 - Online"
            status_color = "#00ff00"  # Green
            self.launch_button.config(state="normal")
        elif status.lower() == "offline":
            status_text = " 🔴 - Offline"
            status_color = "#ff3333"  # Red
            self.launch_button.config(state="disabled")
        else:
            status_text = f" Status: {status}"
            status_color = "#ffffff"
            self.launch_button.config(state="normal")
        self.status_label_color.config(text=status_text, fg=status_color)
        
    def on_closing(self):
        """Handle window close event"""
        self.root.quit()
        self.root.destroy()
        
    def update_status(self, text):
        """Update status text"""
        self.status_label.config(text=text)
        self.root.update()
        
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress['value'] = value
        self.root.update()
        
    def cancel_script(self):
        """Cancel the running script and its processes"""
        if not self.can_cancel:
            return
            
        self.is_cancelled = True
        self.update_status("Cancelling script...")
        
        try:
            # Create terminate signal file to signal script to shut down
            terminate_signal_file = os.path.join(TEMP_DIR, 'terminate_now.signal')
            try:
                with open(terminate_signal_file, 'w') as f:
                    f.write('terminate')
                add_loader_temp_file(terminate_signal_file)
            except Exception:
                pass
            
            # Wait a moment for graceful shutdown
            import time
            time.sleep(2)
            
            # Force terminate processes if still running
            try:
                import psutil
                # Find and terminate any python processes running our script
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'python' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and any('script.py' in str(arg) or 'tmp' in str(arg) for arg in cmdline):
                                proc.terminate()
                                try:
                                    proc.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except ImportError:
                # psutil not available, try alternative method
                try:
                    import subprocess
                    # Use taskkill to terminate python processes (less precise)
                    subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                                 capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(['taskkill', '/f', '/im', 'pythonw.exe'], 
                                 capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    pass
            
            # Clean up any remaining files
            cleanup_files = [
                'script_running.lock',
                'terminate_now.signal',
                'selected_mode.txt',
                'commands.txt',
                'script_loaded.signal',
                'keybind_cooldowns.json',
                'debug_console.lock'
            ]
            
            for filename in cleanup_files:
                filepath = os.path.join(TEMP_DIR, filename)
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
            
            self.update_status("Waiting...")
            self.update_progress(0)
            
        except Exception as e:
            self.update_status(f"Error cancelling script: {str(e)}")
        
        finally:
            # Reset button to launch state
            self.can_cancel = False
            self.is_launching = False
            self.is_cancelled = False
            
            # Set button state based on GitHub status
            if self.github_status.lower() == "disabled":
                button_state = "disabled"
            else:
                button_state = "normal"
                
            self.launch_button.config(text="Launch", command=self.launch_script, state=button_state)
        
    def launch_script(self):
        """Launch the main script with selected options"""
        if self.is_launching:
            return
            
        # Check if GitHub status allows launching
        if self.github_status.lower() == "disabled":
            messagebox.showerror(
                "Launch Disabled", 
                "Launching is currently disabled. Please check back later."
            )
            return
            
        # Change button to Cancel mode
        self.is_launching = True
        self.is_cancelled = False
        self.can_cancel = False  # Will be enabled during "Waiting for script to load" phase
        self.launch_button.config(text="Cancel", command=self.cancel_script, state="disabled")
        self.progress['value'] = 0
        
        # Get selections
        self.selected_mode = self.mode_var.get()
        self.debug_mode = self.debug_var.get()
        self.run_local = self.run_local_var.get()
        
        # Build commands list
        self.selected_commands = []
        if self.debuglog_var.get():
            self.selected_commands.append("debuglog")
        if self.tooltips_var.get():
            self.selected_commands.append("tooltips")
        
        # Launch in background thread
        thread = threading.Thread(target=self.launch_script_background, daemon=True)
        thread.start()
        
    def launch_script_background(self):
        """Background thread for launching script"""
        try:
            # Apply config if enabled and a config is selected
            if self.preload_var.get():
                self.root.after(0, lambda: self.update_status("Pre-Loading Config..."))
                self.root.after(0, lambda: self.update_progress(5))
                time.sleep(1.5)  # Add delay for config pre-loading stage
                try:
                    # Create selected_config.txt file with the selected config name or "default"
                    selected_config_file = os.path.join(TEMP_DIR, 'selected_config.txt')
                    if self.default_config_var.get():
                        selected_config = "default"
                    else:
                        selected_config = self.config_var.get()
                        if selected_config:
                            # Strip .json extension if present
                            if selected_config.endswith('.json'):
                                selected_config = selected_config[:-5]  # Remove .json (5 characters)
                    if selected_config:
                        import io
                        with io.open(selected_config_file, 'w', encoding='utf-8', newline='') as f:
                            f.write(selected_config)
                        add_loader_temp_file(selected_config_file)
                except Exception as e:
                    self.root.after(0, lambda: self.update_status(f"Config error: {str(e)}"))
                    self.root.after(0, lambda: self.update_progress(0))
                    self.root.after(0, lambda: self.reset_launch_button())
                    return
            
            # Check for cancellation
            if self.is_cancelled:
                return
                
            # Check loader version
            self.root.after(0, lambda: self.update_status("Checking loader version..."))
            self.root.after(0, lambda: self.update_progress(10))
            if not check_loader_version():
                self.root.after(0, lambda: self.update_status("Loader outdated, run setup again."))
                self.root.after(0, lambda: self.update_progress(0))
                self.root.after(0, lambda: self.reset_launch_button())
                return
            
            # Check for cancellation
            if self.is_cancelled:
                return
            
            # Get script content (either local or downloaded)
            script_content = None
            
            if self.run_local:
                # Try to load local script.pyw
                self.root.after(0, lambda: self.update_status("Loading local script..."))
                self.root.after(0, lambda: self.update_progress(30))
                
                # Get the actual directory where the executable/script is located
                if getattr(sys, 'frozen', False):
                    # If running as compiled executable
                    loader_directory = os.path.dirname(sys.executable)
                else:
                    # If running as script
                    loader_directory = os.path.dirname(os.path.abspath(__file__))
                
                local_script_path = os.path.join(loader_directory, 'script.pyw')
                try:
                    with open(local_script_path, 'r', encoding='utf-8') as f:
                        script_content = f.read()
                except (FileNotFoundError, IOError):
                    self.root.after(0, lambda: self.update_status("Script not found, try again."))
                    self.root.after(0, lambda: self.update_progress(0))
                    self.root.after(0, lambda: self.reset_launch_button())
                    return
            else:
                # Download script from GitHub
                self.root.after(0, lambda: self.update_status("Downloading script..."))
                self.root.after(0, lambda: self.update_progress(30))
                
                if HAS_REQUESTS:
                    try:
                        resp = requests.get(URL, timeout=15)
                        resp.raise_for_status()
                        script_content = resp.text
                    except Exception:
                        pass
                
                if script_content is None:
                    script_content = download_with_urllib(URL)
                
                if script_content is None:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Download Error", 
                        "Failed to download script. Please check your internet connection."
                    ))
                    self.root.after(0, lambda: self.reset_launch_button())
                    return
            
            # Check for cancellation
            if self.is_cancelled:
                return
            
            # Create temp file
            self.root.after(0, lambda: self.update_status("Preparing launch..."))
            self.root.after(0, lambda: self.update_progress(50))
            file_suffix = ".py" if self.debug_mode else ".pyw"
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix, mode='w', encoding='utf-8') as tmp:
                tmp.write(script_content)
                tmp_path = tmp.name
            
            add_loader_temp_file(tmp_path)
            
            # Create mode file
            mode_file = os.path.join(TEMP_DIR, 'selected_mode.txt')
            add_loader_temp_file(mode_file)
            try:
                import io
                with io.open(mode_file, 'w', encoding='utf-8', newline='') as f:
                    f.write(self.selected_mode)
            except Exception:
                pass
            
            # Create commands file
            commands_file = os.path.join(TEMP_DIR, 'commands.txt')
            add_loader_temp_file(commands_file)
            try:
                import io
                with io.open(commands_file, 'w', encoding='utf-8', newline='') as f:
                    for command in self.selected_commands:
                        f.write(command + '\n')
            except Exception:
                pass
            
            # Check for cancellation
            if self.is_cancelled:
                return
            
            # Find Python executable
            self.root.after(0, lambda: self.update_progress(60))
            python_exe = find_python_executable()
            if python_exe is None:
                self.root.after(0, lambda: messagebox.showerror(
                    "Python Error", 
                    "Could not find Python with required packages. Please run setup again."
                ))
                self.root.after(0, lambda: self.reset_launch_button())
                return
            
            # Check for cancellation
            if self.is_cancelled:
                return
            
            # Check if CS2 is running, if not wait for it
            if not is_cs2_running():
                self.root.after(0, lambda: self.update_status("Waiting for CS2.exe..."))
                self.root.after(0, lambda: self.update_progress(65))
                # Enable cancel button during CS2 waiting
                self.root.after(0, lambda: self.enable_cancel_button())
                
                # Wait for CS2 to start
                while not is_cs2_running():
                    if self.is_cancelled:
                        return
                    time.sleep(1)
                
                self.root.after(0, lambda: self.update_status("CS2.exe detected!"))
                time.sleep(0.5)  # Brief pause to show the detection message
            else:
                # Enable cancel button if CS2 is already running
                self.root.after(0, lambda: self.enable_cancel_button())
            
            # Clean up loaded signal file
            loaded_signal_path = os.path.join(TEMP_DIR, LOADED_SIGNAL_FILE)
            try:
                if os.path.exists(loaded_signal_path):
                    os.remove(loaded_signal_path)
            except OSError:
                pass
            
            # Launch script
            self.root.after(0, lambda: self.update_status("Launching script..."))
            self.root.after(0, lambda: self.update_progress(70))
            try:
                if self.debug_mode:
                    # Debug mode: always show console window in a new console
                    # Use cmd.exe /c start to open a new window and run the script with proper quoting
                    self.script_process = subprocess.Popen([
                        'cmd.exe', '/c', 'start', 'Debug Console', python_exe, tmp_path
                    ], creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=os.getcwd())
                else:
                    # Normal mode: hide console window
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                    if os.path.exists(pythonw_exe):
                        self.script_process = subprocess.Popen([pythonw_exe, tmp_path], startupinfo=startupinfo)
                    else:
                        self.script_process = subprocess.Popen([python_exe, tmp_path], startupinfo=startupinfo)
                
                # Wait for script to load
                self.root.after(0, lambda: self.update_status("Waiting for script to load..."))
                self.root.after(0, lambda: self.update_progress(80))
                while not os.path.exists(loaded_signal_path):
                    if self.is_cancelled:
                        return
                    time.sleep(0.5)
                
                # Disable cancel button after successful launch
                self.root.after(0, lambda: self.disable_cancel_button())
                
                # Success
                self.root.after(0, lambda: self.update_status("Script launched successfully!"))
                self.root.after(0, lambda: self.update_progress(100))
                
                # Clean up and exit
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                        if tmp_path in LOADER_TEMP_FILES:
                            LOADER_TEMP_FILES.remove(tmp_path)
                except OSError:
                    pass
                
                try:
                    if os.path.exists(loaded_signal_path):
                        os.remove(loaded_signal_path)
                except OSError:
                    pass
                
                # Close loader after short delay
                self.root.after(1000, self.root.quit)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Launch Error", 
                    f"Failed to launch script: {str(e)}"
                ))
                self.root.after(0, lambda: self.reset_launch_button())
                return
                
        except Exception as e:
            if not self.is_cancelled:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", 
                    f"An error occurred: {str(e)}"
                ))
                self.root.after(0, lambda: self.reset_launch_button())
        finally:
            if not self.is_cancelled:
                # Re-enable button and reset progress only if not cancelled
                self.root.after(0, lambda: self.reset_launch_button())
    
    def enable_cancel_button(self):
        """Enable the cancel button"""
        self.can_cancel = True
        self.launch_button.config(state="normal")
    
    def disable_cancel_button(self):
        """Disable the cancel button after successful launch"""
        self.can_cancel = False
        self.launch_button.config(state="disabled")
    
    def reset_launch_button(self):
        """Reset button back to launch mode"""
        self.is_launching = False
        self.is_cancelled = False
        self.can_cancel = False
        
        # Set button state based on GitHub status
        if self.github_status.lower() == "disabled":
            button_state = "disabled"
        else:
            button_state = "normal"
            
        self.launch_button.config(text="Launch", command=self.launch_script, state=button_state)
        self.update_progress(0)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    """Main entry point - now uses GUI instead of console"""
    try:
        # Create and run the GUI
        app = LoaderGUI()
        app.run()
    except Exception as e:
        # Fallback to console mode if GUI fails
        try:
            import tkinter
            # If tkinter import succeeds but GUI failed, show error
            print(f"GUI Error: {e}")
            print("Please check your display settings and try again.")
        except ImportError:
            # If tkinter not available, fall back to console mode
            print("GUI not available, falling back to console mode...")
            console_main()

def console_main():
    """Fallback console-based loader (original implementation)"""
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
        
        # Check GitHub status
        github_status = get_github_status()
        print(f"Status: {github_status}")
        
        if github_status.lower() == "disabled":
            print("Launching is currently disabled. Please check back later.")
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
        print("Loading...")
        
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
        mode_file = os.path.join(TEMP_DIR, 'selected_mode.txt')
        add_loader_temp_file(mode_file)  # Track mode file for cleanup
        try:
            import io
            with io.open(mode_file, 'w', encoding='utf-8', newline='') as f:
                f.write(selected_mode)
        except Exception as e:
            pass
        
        # Create commands file to communicate selected features with script
        commands_file = os.path.join(TEMP_DIR, 'commands.txt')
        add_loader_temp_file(commands_file)  # Track commands file for cleanup
        try:
            import io
            with io.open(commands_file, 'w', encoding='utf-8', newline='') as f:
                for command in selected_commands:
                    f.write(command + '\n')
        except Exception as e:
            pass
        
        # Find Python executable
        python_exe = find_python_executable()
        if python_exe is None:
            return
        
        # Check if CS2 is running, if not wait for it
        if not is_cs2_running():
            print("Waiting for CS2.exe...")
            while not is_cs2_running():
                time.sleep(1)
            print("CS2.exe detected!")
        
        # Clean up any existing loaded signal file
        loaded_signal_path = os.path.join(TEMP_DIR, LOADED_SIGNAL_FILE)
        try:
            if os.path.exists(loaded_signal_path):
                os.remove(loaded_signal_path)
        except OSError:
            pass
        
        # Run script using system Python
        try:
            if debug_mode:
                # Debug mode: always show console window in a new console
                # Use cmd to start a new console window that runs the script
                cmd_command = f'start "Debug Console" cmd /k "{python_exe}" "{tmp_path}"'
                subprocess.Popen(cmd_command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
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
