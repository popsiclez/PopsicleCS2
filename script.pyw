#4
VERSION = "4"
STARTUP_ENABLED = True
            
import threading
import keyboard
import os
import sys
import json
import time
import atexit
import signal
import tempfile
import glob
                                                                                  
import random
import threading
import multiprocessing
import ctypes
import colorsys
import math
              
import requests
import pymem
import pymem.process
from pynput.mouse import Controller, Button
import numpy as np
from PIL import ImageGrab
import pyautogui
           
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import QFileSystemWatcher, QCoreApplication, QTimer
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
                 
import win32api
import win32con
import win32gui
import signal
from datetime import datetime

CONSOLE_CREATED = False

# Global variables for cleanup tracking
TEMPORARY_FILES = set()  # Track all temporary files created
CLEANUP_REGISTERED = False  # Track if cleanup handlers are registered
PROCESSES_LIST = []  # Track all spawned processes for cleanup

LOG_FILE = None
original_stdout = None
original_stderr = None

class LogRedirector:
    """Redirect stdout/stderr to both file and console"""
    def __init__(self, log_file, original_stream):
        self.log_file = log_file
        self.original_stream = original_stream
        
    def write(self, text):

        if self.original_stream:
            try:
                self.original_stream.write(text)
                self.original_stream.flush()
            except:
                pass
        

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(text)
                f.flush()
        except:
            pass
    
    def flush(self):
        if self.original_stream:
            try:
                self.original_stream.flush()
            except:
                pass

def setup_logging():
    """Setup logging to redirect all print statements to debug_log.txt"""
    global original_stdout, original_stderr, LOG_FILE
    

    if LOG_FILE is not None:
        print("[DEBUG] Logging already setup, skipping")
        return
    

    LOG_FILE = os.path.join(os.getcwd(), 'debug_log.txt')
    add_temporary_file(LOG_FILE)  # Track for cleanup
    

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    

    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"=== Popsicle CS2 Debug Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write("All console output will be logged here\n\n")
    except:
        pass
    

    sys.stdout = LogRedirector(LOG_FILE, original_stdout)
    sys.stderr = LogRedirector(LOG_FILE, original_stderr)

def cleanup_logging():
    """Restore original stdout/stderr"""
    global original_stdout, original_stderr, LOG_FILE
    try:
        if LOG_FILE:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Session ended - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except:
        pass
    
    if original_stdout:
        sys.stdout = original_stdout
    if original_stderr:
        sys.stderr = original_stderr
    

    LOG_FILE = None

def cleanup_all_temporary_files():
    """Comprehensive cleanup of all temporary files created by the script"""
    global TEMPORARY_FILES, PROCESSES_LIST
    
    try:
        print("[CLEANUP] Starting comprehensive cleanup...")
        
        # 1. Terminate all spawned processes first
        if PROCESSES_LIST:
            print(f"[CLEANUP] Terminating {len(PROCESSES_LIST)} processes...")
            for i, p in enumerate(PROCESSES_LIST):
                try:
                    if hasattr(p, 'is_alive') and p.is_alive():
                        print(f"[CLEANUP] Terminating process {i+1}")
                        p.terminate()
                        p.join(2)  # Wait up to 2 seconds
                        if p.is_alive():
                            p.kill()
                            p.join(1)
                except Exception as e:
                    print(f"[CLEANUP] Error terminating process {i+1}: {e}")
        
        # 2. Clean up tracked temporary files
        files_cleaned = 0
        if TEMPORARY_FILES:
            print(f"[CLEANUP] Cleaning {len(TEMPORARY_FILES)} tracked temporary files...")
            for temp_file in list(TEMPORARY_FILES):
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        files_cleaned += 1
                        print(f"[CLEANUP] Removed: {temp_file}")
                except Exception as e:
                    print(f"[CLEANUP] Error removing {temp_file}: {e}")
        
        # 3. Clean up standard temporary files
        standard_temp_files = [
            LOCK_FILE,
            TERMINATE_SIGNAL_FILE,
            KEYBIND_COOLDOWNS_FILE,
            CONSOLE_LOCK_FILE,
            MODE_FILE,
            os.path.join(os.getcwd(), 'debug_log.txt'),
            os.path.join(os.getcwd(), 'panic_shutdown.signal')
        ]
        
        print("[CLEANUP] Cleaning standard temporary files...")
        for temp_file in standard_temp_files:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                    files_cleaned += 1
                    print(f"[CLEANUP] Removed: {temp_file}")
            except Exception as e:
                print(f"[CLEANUP] Error removing {temp_file}: {e}")
        
        # 4. Clean up any orphaned .signal files
        try:
            import glob
            signal_files = glob.glob(os.path.join(os.getcwd(), '*.signal'))
            if signal_files:
                print(f"[CLEANUP] Cleaning {len(signal_files)} signal files...")
                for signal_file in signal_files:
                    try:
                        os.remove(signal_file)
                        files_cleaned += 1
                        print(f"[CLEANUP] Removed signal file: {signal_file}")
                    except Exception as e:
                        print(f"[CLEANUP] Error removing signal file {signal_file}: {e}")
        except Exception as e:
            print(f"[CLEANUP] Error cleaning signal files: {e}")
        
        # 5. Clean up any orphaned .lock files
        try:
            import glob
            lock_files = glob.glob(os.path.join(os.getcwd(), '*.lock'))
            if lock_files:
                print(f"[CLEANUP] Cleaning {len(lock_files)} lock files...")
                for lock_file in lock_files:
                    try:
                        os.remove(lock_file)
                        files_cleaned += 1
                        print(f"[CLEANUP] Removed lock file: {lock_file}")
                    except Exception as e:
                        print(f"[CLEANUP] Error removing lock file {lock_file}: {e}")
        except Exception as e:
            print(f"[CLEANUP] Error cleaning lock files: {e}")
        
        # 6. Clean up temporary script files in system temp directory
        try:
            import tempfile
            import glob
            temp_dir = tempfile.gettempdir()
            script_temp_files = glob.glob(os.path.join(temp_dir, '*.pyw'))
            # Only remove files that are likely from our loader (recent and small)
            for temp_file in script_temp_files:
                try:
                    # Check if file is recent (within last hour) and reasonable size
                    if os.path.exists(temp_file):
                        file_age = time.time() - os.path.getmtime(temp_file)
                        file_size = os.path.getsize(temp_file)
                        if file_age < 3600 and 1000 < file_size < 1000000:  # 1KB to 1MB, less than 1 hour old
                            os.remove(temp_file)
                            files_cleaned += 1
                            print(f"[CLEANUP] Removed temp script: {temp_file}")
                except Exception as e:
                    print(f"[CLEANUP] Error removing temp script {temp_file}: {e}")
        except Exception as e:
            print(f"[CLEANUP] Error cleaning temp scripts: {e}")
        
        # 7. Clean up logging
        cleanup_logging()
        
        print(f"[CLEANUP] Cleanup completed. Removed {files_cleaned} files.")
        
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")

def register_cleanup_handlers():
    """Register cleanup handlers for various exit scenarios"""
    global CLEANUP_REGISTERED
    
    if CLEANUP_REGISTERED:
        return
    
    try:
        # Register atexit handler for normal exits
        atexit.register(cleanup_all_temporary_files)
        
        # Register signal handlers for forced termination
        def signal_handler(signum, frame):
            print(f"[CLEANUP] Signal {signum} received, cleaning up...")
            cleanup_all_temporary_files()
            os._exit(1)
        
        # Register handlers for common termination signals
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGBREAK'):  # Windows specific
            signal.signal(signal.SIGBREAK, signal_handler)
        
        CLEANUP_REGISTERED = True
        print("[CLEANUP] Cleanup handlers registered successfully")
        
    except Exception as e:
        print(f"[CLEANUP] Error registering cleanup handlers: {e}")

def add_temporary_file(file_path):
    """Add a file to the temporary files tracking list"""
    global TEMPORARY_FILES
    if file_path:
        TEMPORARY_FILES.add(file_path)
        print(f"[CLEANUP] Tracking temporary file: {file_path}")

def track_process(process):
    """Add a process to the cleanup tracking list"""
    global PROCESSES_LIST
    PROCESSES_LIST.append(process)
    print(f"[CLEANUP] Tracking process for cleanup")

def load_commands():
    """Load commands from commands.txt file if it exists"""
    commands = []
    try:
        print(f"[DEBUG] Checking for commands file at: {COMMANDS_FILE}")
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                if content.startswith('\ufeff'):
                    content = content[1:]
                print(f"[DEBUG] Commands file content: '{content}'")
                if content:

                    commands = [cmd.strip().lower() for cmd in content.split(',') if cmd.strip()]
                    print(f"[DEBUG] Parsed commands: {commands}")
                    pass
        else:
            print(f"[DEBUG] No commands file found at {COMMANDS_FILE}")
            pass
    except Exception as e:
        print(f"[DEBUG] Error reading commands file: {e}")
        pass
    return commands

def apply_commands():
    """Apply commands from commands.txt file"""
    global CONSOLE_CREATED
    print("[DEBUG] apply_commands() called")
    commands = load_commands()
    print(f"[DEBUG] Commands loaded: {commands}")
    

    if "debuglog" in commands:
        print("[DEBUG] Debuglog command found in commands list")

        setup_logging()
        print("[DEBUG] Debug logging enabled and writing to debug_log.txt")
        print("Commands processed:", commands)
    else:
        print("[DEBUG] Debuglog command NOT found in commands list")

def get_app_title():
    """Fetch application title from GitHub"""
    try:
        response = requests.get('https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/title.txt', timeout=5)
        if response.status_code == 200:
            title = response.text.strip()
            pass
            return title
    except Exception as e:
        pass
    
                    
    return "Popsicle - CS2"

def check_version():
    """Check if current version matches GitHub version"""
    try:
        response = requests.get('https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/version.txt', timeout=5)
        if response.status_code == 200:
            remote_version = response.text.strip()
            pass
            return VERSION == remote_version
    except Exception as e:
        pass
    
                                             
    return True

def version_check_worker():
    """Background worker to check version periodically"""
    while True:
        try:
            if not check_version():
                pass
                                                                      
                app_title = get_app_title()
                ctypes.windll.user32.MessageBoxW(
                    0, 
                    "New version available! Please relaunch loader", 
                    app_title,
                    0x00000000 | 0x00010000 | 0x00040000 | 0x00001000                                                          
                )
                
                pass
                                                
                remove_lock_file()
                                                                   
                try:
                    if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                        os.remove(KEYBIND_COOLDOWNS_FILE)
                except Exception:
                    pass
                                                                                  
                try:
                    with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                        f.write('version_mismatch')
                    add_temporary_file(TERMINATE_SIGNAL_FILE)  # Track for cleanup
                except Exception:
                    pass
                                                                              
                time.sleep(1)
                os._exit(0)
                
                                    
            time.sleep(30)
        except Exception as e:
            pass
            time.sleep(30)
                                     
offsets = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json').json()
client_dll = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json').json()
        
dwEntityList = offsets['client.dll']['dwEntityList']
dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
dwLocalPlayerController = offsets['client.dll']['dwLocalPlayerController']
dwViewMatrix = offsets['client.dll']['dwViewMatrix']
dwPlantedC4 = offsets['client.dll']['dwPlantedC4']
dwViewAngles = offsets['client.dll']['dwViewAngles']
dwSensitivity = offsets['client.dll']['dwSensitivity']
dwSensitivity_sensitivity = offsets['client.dll']['dwSensitivity_sensitivity']
                         
m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
m_lifeState = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_lifeState']
m_pGameSceneNode = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
m_fFlags = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_fFlags']
m_vecVelocity = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_vecVelocity']
                      
m_hPlayerPawn = client_dll['client.dll']['classes']['CCSPlayerController']['fields']['m_hPlayerPawn']
m_iszPlayerName = client_dll['client.dll']['classes']['CBasePlayerController']['fields']['m_iszPlayerName']
                
m_iIDEntIndex = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_iIDEntIndex']
m_ArmorValue = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_ArmorValue']
m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_entitySpottedState']
m_angEyeAngles = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_angEyeAngles']
m_aimPunchAngle = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_aimPunchAngle']
m_iShotsFired = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_iShotsFired']
                     
m_pCameraServices = client_dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_pCameraServices']
m_vOldOrigin = client_dll['client.dll']['classes']['C_BasePlayerPawn']['fields']['m_vOldOrigin']
                 
m_vecAbsOrigin = client_dll['client.dll']['classes']['CGameSceneNode']['fields']['m_vecAbsOrigin']
m_vecOrigin = client_dll['client.dll']['classes']['CGameSceneNode']['fields']['m_vecOrigin']
m_modelState = client_dll['client.dll']['classes']['CSkeletonInstance']['fields']['m_modelState']
            
m_AttributeManager = client_dll['client.dll']['classes']['C_EconEntity']['fields']['m_AttributeManager']
m_Item = client_dll['client.dll']['classes']['C_AttributeContainer']['fields']['m_Item']
m_iItemDefinitionIndex = client_dll['client.dll']['classes']['C_EconItemView']['fields']['m_iItemDefinitionIndex']
          
m_flTimerLength = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_flTimerLength']
m_flDefuseLength = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_flDefuseLength']
m_bBeingDefused = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_bBeingDefused']
m_nBombSite = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_nBombSite']
                    
m_bSpotted = client_dll['client.dll']['classes']['EntitySpottedState_t']['fields']['m_bSpotted']
m_bSpottedByMask = client_dll['client.dll']['classes']['EntitySpottedState_t']['fields']['m_bSpottedByMask']


try:
    m_iDesiredFOV = client_dll['client.dll']['classes']['CBasePlayerController']['fields']['m_iDesiredFOV']
except KeyError:
    m_iDesiredFOV = 0x194
                               
bone_ids = {
    "head": 6,
    "neck": 5,
    "spine": 4,
    "pelvis": 0,
    "left_shoulder": 13,
    "left_elbow": 14,
    "left_wrist": 15,
    "right_shoulder": 9,
    "right_elbow": 10,
    "right_wrist": 11,
    "left_hip": 25,
    "left_knee": 26,
    "left_ankle": 27,
    "right_hip": 22,
    "right_knee": 23,
    "right_ankle": 24,
}
                                       
bone_connections = [
    ("head", "neck"),
    ("neck", "spine"),
    ("spine", "pelvis"),
    ("pelvis", "left_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("pelvis", "right_hip"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
    ("neck", "left_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("neck", "right_shoulder"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
]
                              
BONE_TARGET_MODES = {
    0: {"name": "Body (Spine)", "bone": "spine"},
    1: {"name": "Head", "bone": "head"},
    2: {"name": "Neck", "bone": "neck"},
    3: {"name": "Pelvis", "bone": "pelvis"},
    4: {"name": "Left Shoulder", "bone": "left_shoulder"},
    5: {"name": "Right Shoulder", "bone": "right_shoulder"},
    6: {"name": "Left Elbow", "bone": "left_elbow"},
    7: {"name": "Right Elbow", "bone": "right_elbow"},
    8: {"name": "Left Wrist", "bone": "left_wrist"},
    9: {"name": "Right Wrist", "bone": "right_wrist"},
    10: {"name": "Left Hip", "bone": "left_hip"},
    11: {"name": "Right Hip", "bone": "right_hip"},
    12: {"name": "Left Knee", "bone": "left_knee"},
    13: {"name": "Right Knee", "bone": "right_knee"},
    14: {"name": "Left Ankle", "bone": "left_ankle"},
    15: {"name": "Right Ankle", "bone": "right_ankle"},
}

def is_keybind_on_global_cooldown(settings_key):
    """Check if a keybind is on cooldown across all processes"""
    try:
        cooldown_file = KEYBIND_COOLDOWNS_FILE
        if not os.path.exists(cooldown_file):
            return False
            
        with open(cooldown_file, 'r') as f:
            cooldown_data = json.load(f)
            
        cooldown_until = cooldown_data.get(settings_key, 0)
        return time.time() < cooldown_until
    except Exception:
        return False

def trigger_graphics_restart():
    """Send Ctrl+Shift+Windows+B to restart graphics driver"""
    try:
                                                
        win32api.keybd_event(0x11, 0, 0, 0)             
        win32api.keybd_event(0x10, 0, 0, 0)                
        win32api.keybd_event(0x5B, 0, 0, 0)                         
        win32api.keybd_event(0x42, 0, 0, 0)          
        
                                       
        win32api.keybd_event(0x42, 0, win32con.KEYEVENTF_KEYUP, 0)        
        win32api.keybd_event(0x5B, 0, win32con.KEYEVENTF_KEYUP, 0)                       
        win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)            
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)           
    except Exception:
        pass
          
CONFIG_DIR = os.path.join(os.getcwd(), 'configs')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'autosave.json')
TERMINATE_SIGNAL_FILE = os.path.join(os.getcwd(), 'terminate_now.signal')
LOCK_FILE = os.path.join(os.getcwd(), 'script_running.lock')
KEYBIND_COOLDOWNS_FILE = os.path.join(os.getcwd(), 'keybind_cooldowns.json')
COMMANDS_FILE = os.path.join(os.getcwd(), 'commands.txt')
CONSOLE_LOCK_FILE = os.path.join(os.getcwd(), 'debug_console.lock')
MODE_FILE = os.path.join(os.getcwd(), 'selected_mode.txt')

def load_selected_mode():
    """Load the selected mode from the mode file created by loader"""
    try:
        if os.path.exists(MODE_FILE):
            with open(MODE_FILE, 'r') as f:
                mode = f.read().strip().lower()
                if mode in ['legit', 'full']:
                    return mode
    except Exception:
        pass
    return 'full'  # Default to full mode if no mode file or error

# Load the selected mode at startup
SELECTED_MODE = load_selected_mode()


apply_commands()
                       
RAINBOW_HUE_MENU = 0.0
RAINBOW_HUE_CENTER_DOT = 0.33
RAINBOW_HUE_FOV = 0.66
TARGET_POSITIONS = {}                                                                      
TARGET_POSITION_TIMESTAMPS = {}                                         
BombPlantedTime = 0
BombDefusedTime = 0
            
aim_lock_state = {
    'locked_entity': None,
    'aim_was_pressed': False,
}

def is_script_already_running():
    """Check if another instance of the script is already running."""
    return os.path.exists(LOCK_FILE)

def create_lock_file():
    """Create a lock file to indicate this instance is running."""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        add_temporary_file(LOCK_FILE)  # Track for cleanup
        return True
    except Exception:
        return False

def disable_console_close_button():
    """Disable the close button on the console window."""
    try:
        import ctypes
        from ctypes import wintypes
        
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            hmenu = ctypes.windll.user32.GetSystemMenu(console_hwnd, False)
            if hmenu:
                ctypes.windll.user32.RemoveMenu(hmenu, 0xF060, 0x0)
                ctypes.windll.user32.DrawMenuBar(console_hwnd)
    except Exception as e:
        pass

def disable_console_close_button():
    """Disable the close button on the console window."""
    try:
        import ctypes
        from ctypes import wintypes
        
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            hmenu = ctypes.windll.user32.GetSystemMenu(console_hwnd, False)
            if hmenu:
                ctypes.windll.user32.RemoveMenu(hmenu, 0xF060, 0x0)
                ctypes.windll.user32.DrawMenuBar(console_hwnd)
    except Exception as e:
        pass

def remove_lock_file():
    """Remove the lock file when shutting down."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

        if os.path.exists(CONSOLE_LOCK_FILE):
            os.remove(CONSOLE_LOCK_FILE)
    except Exception:
        pass

def terminate_existing_instance():
    """Signal existing instance to terminate and wait for it to close."""
    try:
                                 
        with open(TERMINATE_SIGNAL_FILE, 'w') as f:
            f.write('terminate')
        add_temporary_file(TERMINATE_SIGNAL_FILE)  # Track for cleanup
        
                                                               
        timeout = 10                      
        start_time = time.time()
        while os.path.exists(LOCK_FILE) and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
                                   
        if os.path.exists(TERMINATE_SIGNAL_FILE):
            os.remove(TERMINATE_SIGNAL_FILE)
            
        return not os.path.exists(LOCK_FILE)
    except Exception:
        return False

def handle_instance_check():
    """Check for existing instance and handle user choice."""
    if not is_script_already_running():
        return True                                 
    
                               
    MB_OKCANCEL = 0x00000001
    MB_SETFOREGROUND = 0x00010000
    MB_TOPMOST = 0x00040000
    MB_ICONQUESTION = 0x00000020
    IDOK = 1
    
    app_title = get_app_title()
    
                          
    result = ctypes.windll.user32.MessageBoxW(
        0, 
        "Script already running. Press OK to override and close the existing instance, or Cancel to exit.",
        f"{app_title} - Already Running", 
        MB_OKCANCEL | MB_SETFOREGROUND | MB_TOPMOST | MB_ICONQUESTION
    )
    
    if result == IDOK:
                                
        if terminate_existing_instance():
            return True                                             
        else:
                                                   
            ctypes.windll.user32.MessageBoxW(
                0,
                "Failed to terminate existing instance. Please close it manually and try again.",
                f"{app_title} - Error",
                0x00000010 | MB_SETFOREGROUND | MB_TOPMOST                
            )
            return False
    else:
                              
        return False
                             
DEFAULT_SETTINGS = {
                  
    "esp_rendering": 1,
    "esp_mode": 0,
    "line_rendering": 1,
    "lines_position": "Bottom",
    "hp_bar_rendering": 1,
    "head_hitbox_rendering": 1,
    "box_rendering": 1,
    "box_mode": "2D",
    "Bones": 1,
    "nickname": 1,
    "bomb_esp": 1,
    "show_visibility": 1,
    "ESPToggleKey": "NONE",
    "center_dot": 0,
    "center_dot_size": 3,
    
                    
    "radar_enabled": 0,
    "radar_size": 200,
    "radar_scale": 5.0,
    "radar_position": "Top Right",
    "radar_position_x": 50,
    "radar_position_y": 50,
    "radar_opacity": 180,
    
                  
    "aim_active": 0,
    "aim_circle_visible": 1,
    "aim_mode": 1,                             
    "aim_bone_target": 1,                        
    "aim_mode_distance": 0,
    "aim_smoothness": 0,
    "aim_lock_target": 0,
    "aim_visibility_check": 0,
    "aim_disable_when_crosshair_on_enemy": 0,
    "aim_movement_prediction": 0,
    "require_aimkey": 1,
    "camera_lock_enabled": 0,
    "camera_lock_smoothness": 5,
    "camera_lock_tolerance": 5,
    "camera_lock_target_bone": 1,
    "camera_lock_key": "V",
    "camera_lock_draw_range_lines": 0,
    "camera_lock_line_width": 2,
    "camera_lock_use_radius": 0,
    "camera_lock_draw_radius": 0,
    "camera_lock_radius": 100,
    "camera_lock_spotted_check": 0,
    "radius": 50,
    "AimKey": "C",
    "circle_opacity": 127,
    "circle_thickness": 2,
    
                          
    "trigger_bot_active": 0,
    "TriggerKey": "X", 
    "triggerbot_between_shots_delay": 30,
    "triggerbot_first_shot_delay": 0,
    "triggerbot_burst_mode": 0,
    "triggerbot_burst_shots": 3,
    "triggerbot_head_only": 0,
    
                   
    "bhop_enabled": 0,
    "BhopKey": "SPACE",
    
                          
    "auto_accept_enabled": 0,
    
                 
    "topmost": 1,
    "MenuToggleKey": "F8",
    "PanicKey": "NONE",
    "team_color": "#47A76A",
    "enemy_color": "#C41E3A",
    "skeleton_color": "#FFFFFF",
    "aim_circle_color": "#FF0000",
    "center_dot_color": "#FFFFFF",
    "camera_lock_radius_color": "#FF0000",
    "menu_theme_color": "#FF0000",
    "rainbow_fov": 0,
    "rainbow_center_dot": 0,
    "rainbow_menu_theme": 0,
    "low_cpu": 0,
    "fps_limit": 60,
    "game_fov": 90,
    "auto_apply_fov": 0,
}

def key_str_to_vk(key_str):
    """Convert key string to virtual key code."""
    if not key_str: 
        return 0
    ks = str(key_str).strip()
    
    if len(ks) == 1:
        try:
            vk = win32api.VkKeyScan(ks)
            return vk & 0xFF
        except Exception:
            return ord(ks.upper())
            
    if ks.startswith('F') and ks[1:].isdigit():
        try:
            n = int(ks[1:])
            if 1 <= n <= 24:
                return 0x70 + (n - 1)
        except Exception:
            pass
            
    key_map = {
                       
        'LMB': 0x01, 'LEFTMOUSE': 0x01, 'MOUSE1': 0x01, 'LEFTCLICK': 0x01,
        'RMB': 0x02, 'RIGHTMOUSE': 0x02, 'MOUSE2': 0x02, 'RIGHTCLICK': 0x02,
        'MMB': 0x04, 'MIDDLEMOUSE': 0x04, 'MOUSE3': 0x04, 'MIDDLECLICK': 0x04,
        'MOUSE4': 0x05, 'X1': 0x05, 'XBUTTON1': 0x05,
        'MOUSE5': 0x06, 'X2': 0x06, 'XBUTTON2': 0x06,
        
                     
        'SPACE': win32con.VK_SPACE, 'ENTER': win32con.VK_RETURN, 'RETURN': win32con.VK_RETURN,
        'SHIFT': win32con.VK_SHIFT, 'CTRL': win32con.VK_CONTROL, 'CONTROL': win32con.VK_CONTROL,
        'ALT': win32con.VK_MENU, 'TAB': win32con.VK_TAB,
        'ESC': win32con.VK_ESCAPE, 'ESCAPE': win32con.VK_ESCAPE,
        
                    
        'UP': win32con.VK_UP, 'DOWN': win32con.VK_DOWN, 
        'LEFT': win32con.VK_LEFT, 'RIGHT': win32con.VK_RIGHT,
        'UPARROW': win32con.VK_UP, 'DOWNARROW': win32con.VK_DOWN,
        'LEFTARROW': win32con.VK_LEFT, 'RIGHTARROW': win32con.VK_RIGHT,
        
                       
        'LSHIFT': getattr(win32con, 'VK_LSHIFT', 0xA0),
        'RSHIFT': getattr(win32con, 'VK_RSHIFT', 0xA1),
        'LCTRL': getattr(win32con, 'VK_LCONTROL', 0xA2),
        'RCTRL': getattr(win32con, 'VK_RCONTROL', 0xA3),
        'LALT': getattr(win32con, 'VK_LMENU', 0xA4),
        'RALT': getattr(win32con, 'VK_RMENU', 0xA5),
        'RIGHTALT': getattr(win32con, 'VK_RMENU', 0xA5),
        
                    
        'CAPS': getattr(win32con, 'VK_CAPITAL', 0x14), 
        'CAPSLOCK': getattr(win32con, 'VK_CAPITAL', 0x14),
        'BACK': getattr(win32con, 'VK_BACK', 0x08),
        'BACKSPACE': getattr(win32con, 'VK_BACK', 0x08),
        'DELETE': getattr(win32con, 'VK_DELETE', 0x2E),
        'INSERT': getattr(win32con, 'VK_INSERT', 0x2D),
        'HOME': getattr(win32con, 'VK_HOME', 0x24),
        'END': getattr(win32con, 'VK_END', 0x23),
        'PAGEUP': getattr(win32con, 'VK_PRIOR', 0x21),
        'PAGEDOWN': getattr(win32con, 'VK_NEXT', 0x22),
        'PGUP': getattr(win32con, 'VK_PRIOR', 0x21),
        'PGDN': getattr(win32con, 'VK_NEXT', 0x22),
        
                     
        'NUMPAD0': getattr(win32con, 'VK_NUMPAD0', 0x60),
        'NUMPAD1': getattr(win32con, 'VK_NUMPAD1', 0x61),
        'NUMPAD2': getattr(win32con, 'VK_NUMPAD2', 0x62),
        'NUMPAD3': getattr(win32con, 'VK_NUMPAD3', 0x63),
        'NUMPAD4': getattr(win32con, 'VK_NUMPAD4', 0x64),
        'NUMPAD5': getattr(win32con, 'VK_NUMPAD5', 0x65),
        'NUMPAD6': getattr(win32con, 'VK_NUMPAD6', 0x66),
        'NUMPAD7': getattr(win32con, 'VK_NUMPAD7', 0x67),
        'NUMPAD8': getattr(win32con, 'VK_NUMPAD8', 0x68),
        'NUMPAD9': getattr(win32con, 'VK_NUMPAD9', 0x69),
        'MULTIPLY': getattr(win32con, 'VK_MULTIPLY', 0x6A),
        'ADD': getattr(win32con, 'VK_ADD', 0x6B),
        'SUBTRACT': getattr(win32con, 'VK_SUBTRACT', 0x6D),
        'DECIMAL': getattr(win32con, 'VK_DECIMAL', 0x6E),
        'DIVIDE': getattr(win32con, 'VK_DIVIDE', 0x6F),
        
                      
        'PRINTSCREEN': getattr(win32con, 'VK_SNAPSHOT', 0x2C),
        'PRTSC': getattr(win32con, 'VK_SNAPSHOT', 0x2C),
        'SCROLLLOCK': getattr(win32con, 'VK_SCROLL', 0x91),
        'PAUSE': getattr(win32con, 'VK_PAUSE', 0x13),
        'NUMLOCK': getattr(win32con, 'VK_NUMLOCK', 0x90),
        
                      
        'LWIN': getattr(win32con, 'VK_LWIN', 0x5B),
        'RWIN': getattr(win32con, 'VK_RWIN', 0x5C),
        'APPS': getattr(win32con, 'VK_APPS', 0x5D),
        'MENU': getattr(win32con, 'VK_APPS', 0x5D),
        
                               
        'SEMICOLON': getattr(win32con, 'VK_OEM_1', 0xBA),           
        'EQUALS': getattr(win32con, 'VK_OEM_PLUS', 0xBB),           
        'COMMA': getattr(win32con, 'VK_OEM_COMMA', 0xBC),           
        'MINUS': getattr(win32con, 'VK_OEM_MINUS', 0xBD),           
        'PERIOD': getattr(win32con, 'VK_OEM_PERIOD', 0xBE),           
        'SLASH': getattr(win32con, 'VK_OEM_2', 0xBF),           
        'GRAVE': getattr(win32con, 'VK_OEM_3', 0xC0),           
        'TILDE': getattr(win32con, 'VK_OEM_3', 0xC0),           
        'LBRACKET': getattr(win32con, 'VK_OEM_4', 0xDB),           
        'BACKSLASH': getattr(win32con, 'VK_OEM_5', 0xDC),           
        'RBRACKET': getattr(win32con, 'VK_OEM_6', 0xDD),           
        'QUOTE': getattr(win32con, 'VK_OEM_7', 0xDE),           
        'APOSTROPHE': getattr(win32con, 'VK_OEM_7', 0xDE),           
        
        'NONE': 0
    }
    
    ks = ks.replace(' ', '')
    if ks.startswith('VK_'):
        try:
            return int(ks[3:], 0)
        except Exception:
            pass
    if ks in key_map:
        return key_map[ks]
    return ord(ks[0]) if ks else 0

def get_window_size(window_name: str):
    """Return (width, height) of the top-level window with exact title `window_name`.
    
    Returns (None, None) if the window cannot be found or on error.
    """
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            return None, None
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return right - left, bottom - top
    except Exception:
        return None, None

def get_window_rect(window_name: str):
    """Return (x, y, width, height) of the top-level window with exact title `window_name`.
    
    Returns (None, None, None, None) if the window cannot be found or on error.
    """
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            return None, None, None, None
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left, top, right - left, bottom - top
    except Exception:
        return None, None, None, None

def get_window_client_rect(window_name: str):
    """Return (x, y, width, height) of the client area (game content area) of the window.
    
    This excludes title bars, borders, and other window decorations.
    Returns (None, None, None, None) if the window cannot be found or on error.
    """
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            return None, None, None, None
        
                                                               
        window_left, window_top, window_right, window_bottom = win32gui.GetWindowRect(hwnd)
        
                                                                      
        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
        
                                                          
        client_point = win32gui.ClientToScreen(hwnd, (0, 0))
        client_screen_x, client_screen_y = client_point
        
                                          
        client_width = client_right - client_left
        client_height = client_bottom - client_top
        
        return client_screen_x, client_screen_y, client_width, client_height
    except Exception:
        return None, None, None, None

def is_cs2_running():
    """Check if CS2 process is currently running"""
    try:
        pymem.Pymem("cs2.exe")
        return True
    except Exception:
        return False

def get_offsets_and_client_dll():
    """Fetch offsets and client_dll JSON from the remote repo.
    
    Returns a tuple (offsets, client_dll). On failure returns ({}, {}).
    """
    try:
        offsets = requests.get(
            'https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json'
        ).json()
        client_dll = requests.get(
            'https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json'
        ).json()
        return offsets, client_dll
    except Exception:
        return {}, {}

def w2s(view_matrix, x, y, z, width, height):
    """Minimal world-to-screen projection that tolerates different view_matrix shapes.
    
    Returns (screen_x, screen_y) or (-999, -999) if projection fails.
    """
    try:
        if not view_matrix or width is None or height is None:
            return -999, -999
            
                                                                            
        if hasattr(view_matrix, '__len__') and len(view_matrix) >= 16:
            m = view_matrix
                                                
            clip_x = m[0]*x + m[1]*y + m[2]*z + m[3]
            clip_y = m[4]*x + m[5]*y + m[6]*z + m[7]
            clip_w = m[12]*x + m[13]*y + m[14]*z + m[15]
        else:
            return -999, -999
            
        if clip_w < 1e-6:
            return -999, -999
            
        ndc_x = clip_x / clip_w
        ndc_y = clip_y / clip_w
        screen_x = int((width / 2.0) * (1.0 + ndc_x))
        screen_y = int((height / 2.0) * (1.0 - ndc_y))
        return screen_x, screen_y
    except Exception:
        return -999, -999

def load_settings():
    """Load settings from config file with proper defaults merging."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    

    merged_settings = DEFAULT_SETTINGS.copy()
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return merged_settings
    
    try:
        with open(CONFIG_FILE, "r") as f:
            loaded_settings = json.load(f)

            merged_settings.update(loaded_settings)
            return merged_settings
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):

        return merged_settings

def save_settings(settings: dict):
    """Save settings to config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass

class ConfigWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.drag_start_position = None
        self.is_dragging = False
        self.menu_toggle_pressed = False
        self.esp_toggle_pressed = False
        self._manually_hidden = False                                         
        self._fov_changed_during_runtime = False
        self._fov_warning_accepted = False
        self._fov_dialog_showing = False
        self._pending_fov_value = None
        self._is_initializing = True
        
                                                              
        initial_theme_color = self.settings.get('menu_theme_color', '#FF0000')
        self.update_menu_theme_styling(initial_theme_color)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("Popsicle CS2 Config")                                       

                               
        app_title = get_app_title()
        

        self.tooltips_enabled = "tooltips" in load_commands()
        

        self.fov_enabled = "fov" in load_commands()
        
        # Only show mode text for legit mode
        if SELECTED_MODE == 'legit':
            header_text = f"{app_title} - LEGIT Mode"
        else:
            header_text = app_title
        
        self.header_label = QtWidgets.QLabel(header_text)
        self.header_label.setAlignment(QtCore.Qt.AlignCenter)
        self.header_label.setMinimumHeight(28)
        header_font = QtGui.QFont('MS PGothic', 14, QtGui.QFont.Bold)
        self.header_label.setFont(header_font)
                                     
        theme_color = self.settings.get('menu_theme_color', '#FF0000')
        self.header_label.setStyleSheet(f"color: {theme_color}; font-family: 'MS PGothic'; font-weight: bold; font-size: 16px;")

        
        esp_container = self.create_esp_container()
        trigger_container = self.create_trigger_container()
        colors_container = self.create_colors_container()
        misc_container = self.create_misc_container()
        config_container = self.create_config_container()

        
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(esp_container, "ESP")
        
        # Only add aim tab in full mode
        if SELECTED_MODE == 'full':
            aim_container = self.create_aim_container()
            tabs.addTab(aim_container, "Aim")
            
        tabs.addTab(trigger_container, "Trigger")
        tabs.addTab(colors_container, "Colors")
        tabs.addTab(misc_container, "Misc")
        tabs.addTab(config_container, "Config")
        tabs.setTabPosition(QtWidgets.QTabWidget.North)
        tabs.setMovable(False)
        
                            
        tabs.setStyleSheet("")                                                       

        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(self.header_label)
        main_layout.addWidget(tabs)

        self.setLayout(main_layout)

                                  
        self.update_radius_label()
        self.update_triggerbot_delay_label()
        self.update_triggerbot_burst_shots_label()
        self.update_center_dot_size_label()
        self.update_opacity_label()
        self.update_thickness_label()
        self.update_smooth_label()

        if self.fov_enabled:
            self.update_game_fov_label_only()

                                                           
        self.initialize_fps_slider_state()

        
        self._menu_toggle_timer = QtCore.QTimer(self)
        self._menu_toggle_timer.timeout.connect(self.check_menu_toggle)
        self._menu_toggle_timer.start(50)

        
        try:
            self._menu_toggle_ignore_until = time.time() + 0.5
        except Exception:
            self._menu_toggle_ignore_until = 0

        
        try:
            self._escape_hold_start = 0
            self._escape_hold_timer = QtCore.QTimer(self)
            self._escape_hold_timer.timeout.connect(self._check_escape_hold)
            
            self._escape_hold_timer.start(200)
        except Exception:
            
            try:
                self._escape_hold_start = 0
            except Exception:
                pass

                                                                               
        self.setMinimumWidth(480)
        self.setMaximumWidth(480)
        
                                             
        self.apply_rounded_corners()



                                              
        self.keybind_cooldowns = {}                                        

                                                          
        self._window_monitor_timer = QtCore.QTimer(self)
        self._window_monitor_timer.timeout.connect(self._check_cs2_window_active)
        self._window_monitor_timer.start(100)                     
        self._was_visible = True                          
        self._drag_end_time = 0                             
        
                                                    
        self._rainbow_menu_timer = QtCore.QTimer(self)
        self._rainbow_menu_timer.timeout.connect(self._update_rainbow_menu_theme)
        self._rainbow_menu_timer.start(50)                     
        
                                                          
        if not self.is_game_window_active():
            self._was_visible = False


        self.disable_ui_focus()
        
        self._is_initializing = False

    def pause_rainbow_timer(self):
        """Pause rainbow timer during dialogs to prevent interference"""
        if hasattr(self, '_rainbow_menu_timer') and self._rainbow_menu_timer.isActive():
            self._rainbow_menu_timer.stop()
            self._rainbow_timer_was_active = True
        else:
            self._rainbow_timer_was_active = False

    def resume_rainbow_timer(self):
        """Resume rainbow timer after dialogs"""
        if hasattr(self, '_rainbow_timer_was_active') and self._rainbow_timer_was_active:
            if hasattr(self, '_rainbow_menu_timer'):
                self._rainbow_menu_timer.start(50)

    def set_tooltip_if_enabled(self, widget, tooltip_text):
        """Set tooltip only if tooltips are enabled via commands.txt"""
        if hasattr(self, 'tooltips_enabled') and self.tooltips_enabled:
            widget.setToolTip(tooltip_text)

    def disable_ui_focus(self):
        """Disable focus for all interactive UI elements to prevent keyboard shortcuts"""
        try:

            checkboxes = [
                self.esp_rendering_cb, self.line_rendering_cb, self.hp_bar_rendering_cb,
                self.head_hitbox_rendering_cb, self.box_rendering_cb, self.Bones_cb,
                self.nickname_cb, self.show_visibility_cb, self.bomb_esp_cb,
                self.radar_cb, self.center_dot_cb, self.trigger_bot_active_cb,
                self.triggerbot_burst_mode_cb, self.triggerbot_head_only_cb,
            ]
            
            # Add aim-related checkboxes only if they exist (full mode)
            aim_checkboxes = [
                'aim_active_cb', 'aim_circle_visible_cb', 'aim_visibility_cb', 
                'lock_target_cb', 'disable_crosshair_cb', 'movement_prediction_cb'
            ]
            
            for attr_name in aim_checkboxes:
                if hasattr(self, attr_name):
                    checkboxes.append(getattr(self, attr_name))
            
            # Add other checkboxes that should always exist
            misc_checkboxes = [
                'rainbow_fov_cb', 'rainbow_center_dot_cb', 'rainbow_menu_theme_cb', 
                'auto_accept_cb', 'low_cpu_cb'
            ]
            
            for attr_name in misc_checkboxes:
                if hasattr(self, attr_name):
                    checkboxes.append(getattr(self, attr_name))
            
            for cb in checkboxes:
                if cb:
                    cb.setFocusPolicy(QtCore.Qt.NoFocus)
            

            sliders = [
                self.triggerbot_delay_slider, self.triggerbot_first_shot_delay_slider,
                self.triggerbot_burst_shots_slider, 
                self.center_dot_size_slider, self.radar_size_slider, self.radar_scale_slider, 
                self.fps_limit_slider
            ]
            
            # Add aim-related sliders only if they exist (full mode)
            aim_sliders = [
                'radius_slider', 'opacity_slider', 'thickness_slider', 'smooth_slider'
            ]
            
            for attr_name in aim_sliders:
                if hasattr(self, attr_name):
                    sliders.append(getattr(self, attr_name))

            if hasattr(self, 'game_fov_slider') and self.game_fov_slider:
                sliders.append(self.game_fov_slider)
            
            for slider in sliders:
                if slider:
                    slider.setFocusPolicy(QtCore.Qt.NoFocus)
            

            buttons = [
                self.esp_toggle_key_btn, self.trigger_key_btn,
                self.bhop_key_btn, self.menu_key_btn, self.team_color_btn,
                self.enemy_color_btn, self.skeleton_color_btn, self.center_dot_color_btn,
                self.camera_lock_radius_color_btn, self.menu_theme_color_btn, self.reset_btn
            ]
            
            # Add aim-related buttons only if they exist (full mode)
            aim_buttons = ['aim_key_btn', 'aim_circle_color_btn']
            for attr_name in aim_buttons:
                if hasattr(self, attr_name):
                    buttons.append(getattr(self, attr_name))
            
            for btn in buttons:
                if btn:
                    btn.setFocusPolicy(QtCore.Qt.NoFocus)
            

            comboboxes = [
                self.esp_mode_cb, self.lines_position_combo, self.aim_mode_cb, self.aim_mode_distance_cb,
                self.radar_position_combo
            ]
            
            for combo in comboboxes:
                if hasattr(self, combo.objectName()) or combo:
                    combo.setFocusPolicy(QtCore.Qt.NoFocus)
                    
        except Exception:
            pass

    def is_game_window_active(self):
        """Check if CS2 or ESP overlay is the currently active window"""
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            if not foreground_hwnd:
                return False
            
                                    
            cs2_hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
            if cs2_hwnd and cs2_hwnd == foreground_hwnd:
                return True
            
                                                                         
            try:
                window_title = win32gui.GetWindowText(foreground_hwnd)
                if "ESP Overlay" in window_title:
                    return True
                
                                                     
                if "Popsicle CS2 Config" in window_title:
                    return True
            except Exception:
                pass
            
            return False
        except Exception:
            return False

    def _check_cs2_window_active(self):
        """Monitor CS2 window activity and show/hide config window accordingly"""
        try:
                                                             
            if self.is_dragging:
                return
            
                                                                                        
            import time
            if hasattr(self, '_drag_end_time') and time.time() - self._drag_end_time < 0.5:
                return
                
            is_cs2_active = self.is_game_window_active()
            
            if is_cs2_active and not self._was_visible:
                                                                                  
                if not self._manually_hidden:
                    self.show()
                    self._was_visible = True
            elif not is_cs2_active and self._was_visible:
                                                                             
                self.hide()
                self._was_visible = False
                self._manually_hidden = False                                       
        except Exception:
            pass

    def constrain_to_cs2_window(self, pos):
        """Constrain the config window position to stay within CS2 window boundaries"""
        try:
                                       
            cs2_rect = get_window_rect("Counter-Strike 2")
            if cs2_rect == (None, None, None, None):
                                                                   
                return pos
            
            cs2_x, cs2_y, cs2_width, cs2_height = cs2_rect
            
                                    
            config_width = self.width()
            config_height = self.height()
            
                                   
            min_x = cs2_x
            max_x = cs2_x + cs2_width - config_width
            min_y = cs2_y
            max_y = cs2_y + cs2_height - config_height
            
                               
            constrained_x = max(min_x, min(pos.x(), max_x))
            constrained_y = max(min_y, min(pos.y(), max_y))
            
            return QtCore.QPoint(constrained_x, constrained_y)
        except Exception:
                                                              
            return pos

    def is_keybind_on_cooldown(self, settings_key):
        """Check if a keybind is on cooldown (within 1 second of being set)"""
        try:
            cooldown_until = self.keybind_cooldowns.get(settings_key, 0)
            return time.time() < cooldown_until
        except Exception:
            return False

    def set_keybind_cooldown(self, settings_key):
        """Set a 1-second cooldown for a keybind and save to file for other processes"""
        try:
            cooldown_time = time.time() + 1.0
            self.keybind_cooldowns[settings_key] = cooldown_time
            
                                                               
            cooldown_file = KEYBIND_COOLDOWNS_FILE
            cooldown_data = {}
            try:
                if os.path.exists(cooldown_file):
                    with open(cooldown_file, 'r') as f:
                        cooldown_data = json.load(f)
            except:
                pass
            
            cooldown_data[settings_key] = cooldown_time
            
            with open(cooldown_file, 'w') as f:
                json.dump(cooldown_data, f)
            
            # Track the cooldown file for cleanup
            add_temporary_file(cooldown_file)
        except Exception:
            pass

    

    def create_esp_container(self):
        esp_container = QtWidgets.QWidget()
        esp_layout = QtWidgets.QVBoxLayout()
        esp_layout.setSpacing(6)
        esp_layout.setContentsMargins(6, 6, 6, 6)
        esp_layout.setAlignment(QtCore.Qt.AlignTop)

        esp_label = QtWidgets.QLabel("ESP Settings")
        esp_label.setAlignment(QtCore.Qt.AlignCenter)
        esp_label.setMinimumHeight(20)
        esp_layout.addWidget(esp_label)

        self.esp_rendering_cb = QtWidgets.QCheckBox("Enable ESP")
        self.esp_rendering_cb.setChecked(self.settings.get("esp_rendering", 1) == 1)
        self.esp_rendering_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.esp_rendering_cb, "Toggle ESP rendering on/off. When disabled, no ESP elements will be drawn.")
        self.esp_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_rendering_cb)

        self.line_rendering_cb = QtWidgets.QCheckBox("Draw Lines")
        self.line_rendering_cb.setChecked(self.settings.get("line_rendering", 1) == 1)
        self.line_rendering_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.line_rendering_cb, "Draw lines from the bottom center of your screen to each player's position.")
        self.line_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.line_rendering_cb)


        self.lines_position_label = QtWidgets.QLabel("Lines Position:")
        esp_layout.addWidget(self.lines_position_label)
        self.lines_position_combo = QtWidgets.QComboBox()
        self.lines_position_combo.addItems(["Bottom", "Top"])
        current_lines_position = self.settings.get('lines_position', 'Bottom')
        index = self.lines_position_combo.findText(current_lines_position)
        if index >= 0:
            self.lines_position_combo.setCurrentIndex(index)
        self.lines_position_combo.currentTextChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.lines_position_combo, "Choose whether ESP lines connect to the bottom or top of your screen.")
        self.lines_position_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.lines_position_combo)

        self.hp_bar_rendering_cb = QtWidgets.QCheckBox("Draw HP Bars")
        self.hp_bar_rendering_cb.setChecked(self.settings.get("hp_bar_rendering", 1) == 1)
        self.hp_bar_rendering_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.hp_bar_rendering_cb, "Display horizontal health and armor bars below each player showing their current HP and armor values.")
        self.hp_bar_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.hp_bar_rendering_cb)

        self.head_hitbox_rendering_cb = QtWidgets.QCheckBox("Draw Head Hitbox")
        self.head_hitbox_rendering_cb.setChecked(self.settings.get("head_hitbox_rendering", 1) == 1)
        self.head_hitbox_rendering_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.head_hitbox_rendering_cb, "Draw a circle around each player's head to show the head hitbox area for easier targeting.")
        self.head_hitbox_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.head_hitbox_rendering_cb)

        
        self.box_rendering_cb = QtWidgets.QCheckBox("Draw Boxes")
        self.box_rendering_cb.setChecked(self.settings.get("box_rendering", 1) == 1)
        self.box_rendering_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.box_rendering_cb, "Draw rectangular boxes around each player to highlight their position and make them easier to spot.")
        self.box_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.box_rendering_cb)


        self.box_mode_label = QtWidgets.QLabel("Box Mode:")
        esp_layout.addWidget(self.box_mode_label)
        self.box_mode_combo = QtWidgets.QComboBox()
        self.box_mode_combo.addItems(["2D", "3D"])
        current_box_mode = self.settings.get('box_mode', '2D')
        index = self.box_mode_combo.findText(current_box_mode)
        if index >= 0:
            self.box_mode_combo.setCurrentIndex(index)
        self.box_mode_combo.currentTextChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.box_mode_combo, "Choose between 2D flat boxes or 3D boxes that show actual player dimensions in game world.")
        self.box_mode_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.box_mode_combo)
        

        self.update_box_mode_dropdown_state()

        self.Bones_cb = QtWidgets.QCheckBox("Draw Bones")
        self.Bones_cb.setChecked(self.settings.get("Bones", 1) == 1)
        self.Bones_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.Bones_cb, "Draw skeletal structure connecting all major bones of each player for detailed body positioning.")
        self.Bones_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.Bones_cb)

        self.nickname_cb = QtWidgets.QCheckBox("Show Nickname")
        self.nickname_cb.setChecked(self.settings.get("nickname", 1) == 1)
        self.nickname_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.nickname_cb, "Display each player's username/nickname above their character for identification.")
        self.nickname_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.nickname_cb)

        
        self.show_visibility_cb = QtWidgets.QCheckBox("Show Spotted Status")
        self.show_visibility_cb.setChecked(self.settings.get("show_visibility", 1) == 1)
        self.show_visibility_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.show_visibility_cb, "Show visual indicator when enemies are spotted by your team or visible to you.")
        self.show_visibility_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.show_visibility_cb)

        self.bomb_esp_cb = QtWidgets.QCheckBox("Bomb ESP")
        self.bomb_esp_cb.setChecked(self.settings.get("bomb_esp", 1) == 1)
        self.bomb_esp_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.bomb_esp_cb, "Show planted C4 bomb location, timer, and defuse status information.")
        self.bomb_esp_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.bomb_esp_cb)

                        
        self.radar_cb = QtWidgets.QCheckBox("Radar")
        self.radar_cb.setChecked(self.settings.get("radar_enabled", 0) == 1)
        self.radar_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.radar_cb, "Enable minimap radar showing player positions and map layout from top-down view.")
        self.radar_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.radar_cb)

                           
        self.lbl_radar_size = QtWidgets.QLabel(f"Radar Size: ({self.settings.get('radar_size', 200)})")
        esp_layout.addWidget(self.lbl_radar_size)
        self.radar_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radar_size_slider.setRange(100, 400)
        self.radar_size_slider.setValue(self.settings.get('radar_size', 200))
        self.radar_size_slider.valueChanged.connect(self.update_radar_size_label)
        self.set_tooltip_if_enabled(self.radar_size_slider, "Adjust the size of the radar window. Larger values make the radar bigger on screen.")
        esp_layout.addWidget(self.radar_size_slider)

                            
        self.lbl_radar_scale = QtWidgets.QLabel(f"Radar Scale: ({self.settings.get('radar_scale', 5.0):.1f})")
        esp_layout.addWidget(self.lbl_radar_scale)
        self.radar_scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radar_scale_slider.setRange(10, 500)                     
        self.radar_scale_slider.setValue(int(self.settings.get('radar_scale', 5.0) * 10))
        self.radar_scale_slider.valueChanged.connect(self.update_radar_scale_label)
        self.set_tooltip_if_enabled(self.radar_scale_slider, "Control radar zoom level. Higher values zoom out to show more of the map, lower values zoom in for detail.")
        esp_layout.addWidget(self.radar_scale_slider)

                                 
        self.lbl_radar_position = QtWidgets.QLabel("Radar Position:")
        esp_layout.addWidget(self.lbl_radar_position)
        self.radar_position_combo = QtWidgets.QComboBox()
        self.radar_position_combo.addItems([
            "Top Right",
            "Top Left", 
            "Bottom Right",
            "Bottom Left",
            "Bottom Middle",
            "Center Right",
            "Center Left"
        ])
        self.set_tooltip_if_enabled(self.radar_position_combo, "Choose where on your screen the radar should be positioned.")
                                                
        current_position = self.settings.get('radar_position', 'Top Right')
        index = self.radar_position_combo.findText(current_position)
        if index >= 0:
            self.radar_position_combo.setCurrentIndex(index)
        self.radar_position_combo.currentTextChanged.connect(self.on_radar_position_changed)
        self.radar_position_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.radar_position_combo)

                                          
        self.esp_toggle_key_btn = QtWidgets.QPushButton(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")
        self.esp_toggle_key_btn.setObjectName("keybind_button")
        self.esp_toggle_key_btn.clicked.connect(lambda: self.record_key('ESPToggleKey', self.esp_toggle_key_btn))
        self.set_tooltip_if_enabled(self.esp_toggle_key_btn, "Click to set a hotkey for quickly toggling ESP on/off during gameplay. Set to NONE to disable.")
        self.esp_toggle_key_btn.setMinimumHeight(22)
        self.esp_toggle_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_toggle_key_btn)
        self.esp_toggle_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'ESPToggleKey', self.esp_toggle_key_btn)

        esp_container.setLayout(esp_layout)
        esp_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return esp_container

    def create_trigger_container(self):
        trigger_container = QtWidgets.QWidget()
        trigger_layout = QtWidgets.QVBoxLayout()
        trigger_layout.setSpacing(6)
        trigger_layout.setContentsMargins(6, 6, 6, 6)
        trigger_layout.setAlignment(QtCore.Qt.AlignTop)

        trigger_label = QtWidgets.QLabel("TriggerBot")
        trigger_label.setAlignment(QtCore.Qt.AlignCenter)
        trigger_label.setMinimumHeight(18)
        trigger_layout.addWidget(trigger_label)

        self.trigger_bot_active_cb = QtWidgets.QCheckBox("Enable Trigger Bot")
        self.trigger_bot_active_cb.setChecked(self.settings["trigger_bot_active"] == 1)
        self.trigger_bot_active_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.trigger_bot_active_cb, "Automatically shoots when your crosshair is on an enemy while holding the trigger key.")
        self.trigger_bot_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_bot_active_cb)


        self.triggerbot_head_only_cb = QtWidgets.QCheckBox("Head-Only Mode")
        self.triggerbot_head_only_cb.setChecked(self.settings.get("triggerbot_head_only", 0) == 1)
        self.triggerbot_head_only_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.triggerbot_head_only_cb, "When enabled, triggerbot will only shoot when crosshair is precisely on enemy heads.")
        self.triggerbot_head_only_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_head_only_cb)


        self.triggerbot_burst_mode_cb = QtWidgets.QCheckBox("Burst Mode")
        self.triggerbot_burst_mode_cb.setChecked(self.settings.get("triggerbot_burst_mode", 0) == 1)
        self.triggerbot_burst_mode_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.triggerbot_burst_mode_cb, "Fires a limited number of shots in bursts instead of continuous shooting for better recoil control.")
        self.triggerbot_burst_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_burst_mode_cb)


        self.triggerbot_burst_shots_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.triggerbot_burst_shots_slider.setMinimum(2)
        self.triggerbot_burst_shots_slider.setMaximum(5)
        self.triggerbot_burst_shots_slider.setValue(self.settings.get("triggerbot_burst_shots", 3))
        self.triggerbot_burst_shots_slider.valueChanged.connect(self.update_triggerbot_burst_shots_label)
        self.set_tooltip_if_enabled(self.triggerbot_burst_shots_slider, "Number of shots fired per burst when burst mode is enabled. Range: 2-5 shots.")
        self.lbl_burst_shots = QtWidgets.QLabel(f"Burst Shots: ({self.settings.get('triggerbot_burst_shots', 3)})")
        self.lbl_burst_shots.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_burst_shots)
        self.triggerbot_burst_shots_slider.setMinimumHeight(18)
        self.triggerbot_burst_shots_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_burst_shots_slider)
        

        self.triggerbot_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.triggerbot_delay_slider.setMinimum(0)
        self.triggerbot_delay_slider.setMaximum(1000)
        self.triggerbot_delay_slider.setValue(self.settings.get("triggerbot_between_shots_delay", 30))
        self.triggerbot_delay_slider.valueChanged.connect(self.update_triggerbot_delay_label)
        self.set_tooltip_if_enabled(self.triggerbot_delay_slider, "Delay in milliseconds between each shot to control fire rate. Higher values = slower shooting.")
        self.lbl_delay = QtWidgets.QLabel(f"Between Shots Delay (ms): ({self.settings.get('triggerbot_between_shots_delay', 30)})")
        self.lbl_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_delay)
        self.triggerbot_delay_slider.setMinimumHeight(18)
        self.triggerbot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_delay_slider)


        self.triggerbot_first_shot_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        
        # Apply legit mode restrictions for first shot delay
        if SELECTED_MODE == 'legit':
            self.triggerbot_first_shot_delay_slider.setMinimum(150)
            # Ensure saved value meets minimum requirement
            current_value = max(150, self.settings.get("triggerbot_first_shot_delay", 150))
        else:
            self.triggerbot_first_shot_delay_slider.setMinimum(0)
            current_value = self.settings.get("triggerbot_first_shot_delay", 0)
            
        self.triggerbot_first_shot_delay_slider.setMaximum(1000)
        self.triggerbot_first_shot_delay_slider.setValue(current_value)
        self.triggerbot_first_shot_delay_slider.valueChanged.connect(self.update_triggerbot_first_shot_delay_label)
        self.set_tooltip_if_enabled(self.triggerbot_first_shot_delay_slider, "Delay before the first shot when trigger key is pressed. Set to 0 for instant shooting, higher values add reaction time delay.")
        self.lbl_first_shot_delay = QtWidgets.QLabel(f"First Shot Delay (ms): ({current_value})")
        self.lbl_first_shot_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_first_shot_delay)
        self.triggerbot_first_shot_delay_slider.setMinimumHeight(18)
        self.triggerbot_first_shot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_first_shot_delay_slider)


        self.camera_lock_cb = QtWidgets.QCheckBox("Camera Lock")
        self.camera_lock_cb.setChecked(self.settings.get("camera_lock_enabled", 0) == 1)
        self.camera_lock_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.camera_lock_cb, "Automatically keeps your camera aligned with the selected body part when the triggerbot key is held. Uses the same key as triggerbot.")
        self.camera_lock_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_cb)


        self.camera_lock_target_label = QtWidgets.QLabel("Camera Lock Target:")
        trigger_layout.addWidget(self.camera_lock_target_label)
        self.camera_lock_target_combo = QtWidgets.QComboBox()
        for mode_id, mode_info in BONE_TARGET_MODES.items():
            self.camera_lock_target_combo.addItem(mode_info["name"])
        current_target = self.settings.get('camera_lock_target_bone', 1)
        self.camera_lock_target_combo.setCurrentIndex(current_target)
        self.camera_lock_target_combo.currentIndexChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.camera_lock_target_combo, "Choose which body part the camera lock should target when active.")
        self.camera_lock_target_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_target_combo)


        self.camera_lock_smoothness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        
        # Apply legit mode restrictions for camera lock smoothness
        if SELECTED_MODE == 'legit':
            self.camera_lock_smoothness_slider.setMinimum(20)
            self.camera_lock_smoothness_slider.setMaximum(20)
            # Force smoothness to 20 in legit mode
            smoothness_value = 20
        else:
            self.camera_lock_smoothness_slider.setMinimum(1)
            self.camera_lock_smoothness_slider.setMaximum(20)
            smoothness_value = self.settings.get("camera_lock_smoothness", 5)
            
        self.camera_lock_smoothness_slider.setValue(smoothness_value)
        self.camera_lock_smoothness_slider.valueChanged.connect(self.update_camera_lock_smoothness_label)
        self.set_tooltip_if_enabled(self.camera_lock_smoothness_slider, "Controls how aggressively camera lock adjusts to head level. Lower = less smoothness/slower, higher = more smoothness/faster.")
        self.lbl_camera_lock_smoothness = QtWidgets.QLabel(f"Camera Lock Smoothness: ({smoothness_value})")
        self.lbl_camera_lock_smoothness.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_camera_lock_smoothness)
        self.camera_lock_smoothness_slider.setMinimumHeight(18)
        self.camera_lock_smoothness_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_smoothness_slider)


        self.camera_lock_tolerance_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.camera_lock_tolerance_slider.setMinimum(1)
        self.camera_lock_tolerance_slider.setMaximum(50)
        self.camera_lock_tolerance_slider.setValue(self.settings.get("camera_lock_tolerance", 5))
        self.camera_lock_tolerance_slider.valueChanged.connect(self.update_camera_lock_tolerance_label)
        self.set_tooltip_if_enabled(self.camera_lock_tolerance_slider, "Controls the dead zone in pixels. Camera lock only activates when you're more than this many pixels off target. Lower = more sensitive, higher = less sensitive.")
        self.lbl_camera_lock_tolerance = QtWidgets.QLabel(f"Camera Lock Deadzone: ({self.settings.get('camera_lock_tolerance', 5)}px)")
        self.lbl_camera_lock_tolerance.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_camera_lock_tolerance)
        self.camera_lock_tolerance_slider.setMinimumHeight(18)
        self.camera_lock_tolerance_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_tolerance_slider)

        # Draw Range Lines toggle
        self.camera_lock_draw_range_lines_cb = QtWidgets.QCheckBox("Draw Range Lines")
        self.camera_lock_draw_range_lines_cb.setChecked(self.settings.get("camera_lock_draw_range_lines", 0) == 1)
        self.camera_lock_draw_range_lines_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.camera_lock_draw_range_lines_cb, "Show horizontal lines indicating the camera lock target's vertical position and deadzone area on screen.")
        self.camera_lock_draw_range_lines_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_draw_range_lines_cb)

        # Camera Lock Line Width Slider
        self.lbl_camera_lock_line_width = QtWidgets.QLabel(f"Camera Lock Line Width: ({self.settings.get('camera_lock_line_width', 2)})")
        trigger_layout.addWidget(self.lbl_camera_lock_line_width)
        self.camera_lock_line_width_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.camera_lock_line_width_slider.setMinimum(1)
        self.camera_lock_line_width_slider.setMaximum(10)
        self.camera_lock_line_width_slider.setValue(self.settings.get('camera_lock_line_width', 2))
        self.camera_lock_line_width_slider.valueChanged.connect(self.update_camera_lock_line_width_label)
        self.set_tooltip_if_enabled(self.camera_lock_line_width_slider, "Adjust the length of camera lock range lines. Higher values make lines wider/longer across the screen.")
        trigger_layout.addWidget(self.camera_lock_line_width_slider)

        # Camera Lock Use Radius Toggle
        self.camera_lock_use_radius_cb = QtWidgets.QCheckBox("Use Radius for Targeting")
        
        # Force use radius to be on in legit mode
        if SELECTED_MODE == 'legit':
            self.camera_lock_use_radius_cb.setChecked(True)
            self.camera_lock_use_radius_cb.setEnabled(False)  # Disable the checkbox in legit mode
        else:
            self.camera_lock_use_radius_cb.setChecked(self.settings.get("camera_lock_use_radius", 0) == 1)
            
        self.camera_lock_use_radius_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.camera_lock_use_radius_cb, "When enabled, camera lock will only target enemies within the radius circle instead of the entire screen.")
        self.camera_lock_use_radius_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_use_radius_cb)

        # Camera Lock Draw Radius Toggle
        self.camera_lock_draw_radius_cb = QtWidgets.QCheckBox("Draw Radius")
        self.camera_lock_draw_radius_cb.setChecked(self.settings.get("camera_lock_draw_radius", 0) == 1)
        self.camera_lock_draw_radius_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.camera_lock_draw_radius_cb, "Show a circle on screen indicating the camera lock targeting radius area.")
        self.camera_lock_draw_radius_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_draw_radius_cb)

        # Camera Lock Radius Size Slider
        self.camera_lock_radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.camera_lock_radius_slider.setMinimum(25)
        
        # Apply legit mode restrictions for radius
        if SELECTED_MODE == 'legit':
            self.camera_lock_radius_slider.setMaximum(200)
            # Ensure saved value doesn't exceed maximum
            radius_value = min(200, self.settings.get('camera_lock_radius', 100))
        else:
            self.camera_lock_radius_slider.setMaximum(300)
            radius_value = self.settings.get('camera_lock_radius', 100)
            
        self.camera_lock_radius_slider.setValue(radius_value)
        self.camera_lock_radius_slider.valueChanged.connect(self.update_camera_lock_radius_label)
        self.set_tooltip_if_enabled(self.camera_lock_radius_slider, "Adjust the size of the camera lock targeting radius. Larger values allow targeting enemies further from the center.")
        self.lbl_camera_lock_radius = QtWidgets.QLabel(f"Camera Lock Radius: ({radius_value})")
        trigger_layout.addWidget(self.lbl_camera_lock_radius)
        trigger_layout.addWidget(self.camera_lock_radius_slider)

        # Camera Lock Spotted Check Toggle
        self.camera_lock_spotted_check_cb = QtWidgets.QCheckBox("Camera Lock Spotted Check")
        self.camera_lock_spotted_check_cb.setChecked(self.settings.get("camera_lock_spotted_check", 0) == 1)
        self.camera_lock_spotted_check_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.camera_lock_spotted_check_cb, "Only lock camera to enemies that are visible/spotted by your team to avoid suspicious targeting through walls.")
        self.camera_lock_spotted_check_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.camera_lock_spotted_check_cb)

        self.trigger_key_btn = QtWidgets.QPushButton(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
        self.trigger_key_btn.setObjectName("keybind_button")
        self.trigger_key_btn.clicked.connect(lambda: self.record_key('TriggerKey', self.trigger_key_btn))
        self.set_tooltip_if_enabled(self.trigger_key_btn, "Click to set the key that activates trigger bot and camera lock. Hold this key while aiming at enemies to auto-shoot and maintain head level.")
        self.trigger_key_btn.setMinimumHeight(22)
        self.trigger_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_key_btn)
        self.trigger_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'TriggerKey', self.trigger_key_btn)

        trigger_container.setLayout(trigger_layout)
        trigger_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return trigger_container

    def create_aim_container(self):
        aim_container = QtWidgets.QWidget()
        aim_layout = QtWidgets.QVBoxLayout()
        aim_layout.setSpacing(6)
        aim_layout.setContentsMargins(6, 6, 6, 6)
        aim_layout.setAlignment(QtCore.Qt.AlignTop)

        aim_label = QtWidgets.QLabel("Aim Settings")
        aim_label.setAlignment(QtCore.Qt.AlignCenter)
        aim_label.setMinimumHeight(18)
        aim_layout.addWidget(aim_label)

        self.aim_active_cb = QtWidgets.QCheckBox("Enable Aimbot")
        self.aim_active_cb.setChecked(self.settings.get("aim_active", 0) == 1)
        self.aim_active_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.aim_active_cb, "Automatically aims at enemies when the aim key is held down.")
        self.aim_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_active_cb)

        self.require_aimkey_cb = QtWidgets.QCheckBox("Require Aimkey")
        self.require_aimkey_cb.setChecked(self.settings.get("require_aimkey", 1) == 1)
        self.require_aimkey_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.require_aimkey_cb, "When enabled, you must hold the aimkey for aimbot to work. When disabled, aimbot works automatically on valid targets.")
        self.require_aimkey_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.require_aimkey_cb)

        
        self.radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radius_slider.setMinimum(0)
        self.radius_slider.setMaximum(100)
        self.radius_slider.setValue(self.settings.get("radius", 50))
        self.radius_slider.valueChanged.connect(self.update_radius_label)
        self.set_tooltip_if_enabled(self.radius_slider, "Size of the Aim Radius area in pixels. Aimbot only targets enemies within this radius.")
        self.lbl_radius = QtWidgets.QLabel(f"Aim Radius: ({self.settings.get('radius', 50)})")
        self.lbl_radius.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_radius)
        self.radius_slider.setMinimumHeight(18)
        self.radius_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.radius_slider)

                                          
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(255)
        self.opacity_slider.setValue(self.settings.get("circle_opacity", 16))
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.set_tooltip_if_enabled(self.opacity_slider, "Transparency of the Aim Radius. 0 = invisible, 255 = fully opaque.")
        self.lbl_opacity = QtWidgets.QLabel(f"Circle Opacity: ({self.settings.get('circle_opacity', 16)})")
        self.lbl_opacity.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_opacity)
        self.opacity_slider.setMinimumHeight(18)
        self.opacity_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.opacity_slider)

                                 
        self.thickness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(10)
        self.thickness_slider.setValue(self.settings.get("circle_thickness", 2))
        self.thickness_slider.valueChanged.connect(self.update_thickness_label)
        self.set_tooltip_if_enabled(self.thickness_slider, "Thickness of the Aim Radius outline in pixels. Higher values make the circle border thicker.")
        self.lbl_thickness = QtWidgets.QLabel(f"Circle Thickness: ({self.settings.get('circle_thickness', 2)})")
        self.lbl_thickness.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_thickness)
        self.thickness_slider.setMinimumHeight(18)
        self.thickness_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.thickness_slider)

                                          
        self.smooth_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(3000000)
        self.smooth_slider.setValue(self.settings.get("aim_smoothness", 50))
        self.smooth_slider.valueChanged.connect(self.update_smooth_label)
        self.set_tooltip_if_enabled(self.smooth_slider, "Controls how smooth the aimbot movement is. Lower = instant snap, higher = gradual smooth aiming.")
        self.lbl_smooth = QtWidgets.QLabel(f"Aim Smoothness: ({self.settings.get('aim_smoothness', 50)})")
        self.lbl_smooth.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_smooth)
        self.smooth_slider.setMinimumHeight(18)
        self.smooth_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.smooth_slider)

                                      
        self.aim_circle_visible_cb = QtWidgets.QCheckBox("Show Aim Radius")
        self.aim_circle_visible_cb.setChecked(self.settings.get("aim_circle_visible", 1) == 1)
        self.aim_circle_visible_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.aim_circle_visible_cb, "Display the circular radius area showing aimbot's targeting zone around your crosshair.")
        self.aim_circle_visible_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_circle_visible_cb)

        self.aim_key_btn = QtWidgets.QPushButton(f"AimKey: {self.settings.get('AimKey', 'C')}")
        self.aim_key_btn.setObjectName("keybind_button")
        self.aim_key_btn.clicked.connect(lambda: self.record_key('AimKey', self.aim_key_btn))
        self.set_tooltip_if_enabled(self.aim_key_btn, "Click to set the key that activates aimbot. Hold this key to enable automatic aiming.")
        self.aim_key_btn.setMinimumHeight(22)
        self.aim_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_key_btn)
        self.aim_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'AimKey', self.aim_key_btn)

        self.aim_mode_cb = QtWidgets.QComboBox()
                                              
        bone_options = [BONE_TARGET_MODES[i]["name"] for i in sorted(BONE_TARGET_MODES.keys())]
        self.aim_mode_cb.addItems(bone_options)
        self.aim_mode_cb.setCurrentIndex(self.settings.get("aim_bone_target", 1))                   
        self.aim_mode_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.aim_mode_cb.currentIndexChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.aim_mode_cb, "Select which body part the aimbot should target (head, body, limbs, etc.).")
        lbl_aimmode = QtWidgets.QLabel("Target Bone:")
        lbl_aimmode.setMinimumHeight(16)
        aim_layout.addWidget(lbl_aimmode)
        self.aim_mode_cb.setMinimumHeight(22)
        self.aim_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_mode_cb)

        self.aim_mode_distance_cb = QtWidgets.QComboBox()
        self.aim_mode_distance_cb.addItems(["Closest to Crosshair", "Closest in 3D"])
        self.aim_mode_distance_cb.setCurrentIndex(self.settings.get("aim_mode_distance", 1))
        self.aim_mode_distance_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.aim_mode_distance_cb.currentIndexChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.aim_mode_distance_cb, "Choose targeting priority: closest to crosshair (2D screen distance) or closest in world space (3D distance).")
        lbl_aimdist = QtWidgets.QLabel("Aim Distance Mode:")
        lbl_aimdist.setMinimumHeight(16)
        aim_layout.addWidget(lbl_aimdist)
        self.aim_mode_distance_cb.setMinimumHeight(22)
        self.aim_mode_distance_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_mode_distance_cb)

        try:
            globals()['smooth_slider_max'] = self.smooth_slider.maximum()
        except Exception:
            pass

        
        self.aim_visibility_cb = QtWidgets.QCheckBox("Spotted Check")
        self.aim_visibility_cb.setChecked(self.settings.get("aim_visibility_check", 0) == 1)
        self.aim_visibility_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.aim_visibility_cb, "Only aim at enemies that are visible/spotted by your team to avoid suspicious targeting through walls.")
        self.aim_visibility_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_visibility_cb)

        
        self.lock_target_cb = QtWidgets.QCheckBox("Lock Target")
        self.lock_target_cb.setChecked(self.settings.get("aim_lock_target", 0) == 1)
        self.lock_target_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.lock_target_cb, "Once aimbot locks onto a target, it will continue tracking that enemy until they die or leave the aim radius.")
        self.lock_target_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.lock_target_cb)

                                                
        self.disable_crosshair_cb = QtWidgets.QCheckBox("Disable Aim When Crosshair on Enemy")
        self.disable_crosshair_cb.setChecked(self.settings.get("aim_disable_when_crosshair_on_enemy", 0) == 1)
        self.disable_crosshair_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.disable_crosshair_cb, "Disables aimbot when your crosshair is already on an enemy to maintain natural aiming behavior.")
        self.disable_crosshair_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.disable_crosshair_cb)


        self.movement_prediction_cb = QtWidgets.QCheckBox("Movement Prediction")
        self.movement_prediction_cb.setChecked(self.settings.get("aim_movement_prediction", 0) == 1)
        self.movement_prediction_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.movement_prediction_cb, "Predicts enemy movement and aims ahead of moving targets for more accurate shots.")
        self.movement_prediction_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.movement_prediction_cb)

        aim_container.setLayout(aim_layout)
        aim_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return aim_container

    def create_colors_container(self):
        colors_container = QtWidgets.QWidget()
        colors_layout = QtWidgets.QVBoxLayout()
        colors_layout.setSpacing(6)
        colors_layout.setContentsMargins(6, 6, 6, 6)
        colors_layout.setAlignment(QtCore.Qt.AlignTop)

        colors_label = QtWidgets.QLabel("Color Settings")
        colors_label.setAlignment(QtCore.Qt.AlignCenter)
        colors_label.setMinimumHeight(18)
        colors_layout.addWidget(colors_label)


        esp_colors_label = QtWidgets.QLabel("ESP Colors")
        esp_colors_label.setAlignment(QtCore.Qt.AlignLeft)
        colors_layout.addWidget(esp_colors_label)


        esp_colors_layout = QtWidgets.QHBoxLayout()
        esp_colors_layout.setSpacing(8)

        self.team_color_btn = QtWidgets.QPushButton('Team')
        team_hex = self.settings.get('team_color', '#47A76A')
        team_text_color = self.get_contrasting_text_color(team_hex)
        self.team_color_btn.setStyleSheet(f'background-color: {team_hex}; color: {team_text_color}; border-radius: 6px; font-weight: bold;')
        self.team_color_btn.clicked.connect(lambda: self.pick_color('team_color', self.team_color_btn))
        self.set_tooltip_if_enabled(self.team_color_btn, "Color used for drawing ESP elements of your teammates.")
        self.team_color_btn.setMinimumHeight(32)
        self.team_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_colors_layout.addWidget(self.team_color_btn)

        self.enemy_color_btn = QtWidgets.QPushButton('Enemy')
        enemy_hex = self.settings.get('enemy_color', '#C41E3A')
        enemy_text_color = self.get_contrasting_text_color(enemy_hex)
        self.enemy_color_btn.setStyleSheet(f'background-color: {enemy_hex}; color: {enemy_text_color}; border-radius: 6px; font-weight: bold;')
        self.enemy_color_btn.clicked.connect(lambda: self.pick_color('enemy_color', self.enemy_color_btn))
        self.set_tooltip_if_enabled(self.enemy_color_btn, "Color used for drawing ESP elements of enemy players.")
        self.enemy_color_btn.setMinimumHeight(32)
        self.enemy_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_colors_layout.addWidget(self.enemy_color_btn)

        self.skeleton_color_btn = QtWidgets.QPushButton('Skeleton')
        skeleton_hex = self.settings.get('skeleton_color', '#FFFFFF')
        skeleton_text_color = self.get_contrasting_text_color(skeleton_hex)
        self.skeleton_color_btn.setStyleSheet(f'background-color: {skeleton_hex}; color: {skeleton_text_color}; border-radius: 6px; font-weight: bold;')
        self.skeleton_color_btn.clicked.connect(lambda: self.pick_color('skeleton_color', self.skeleton_color_btn))
        self.set_tooltip_if_enabled(self.skeleton_color_btn, "Color used for drawing bone skeleton structures of players.")
        self.skeleton_color_btn.setMinimumHeight(32)
        self.skeleton_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_colors_layout.addWidget(self.skeleton_color_btn)

        colors_layout.addLayout(esp_colors_layout)


        crosshair_colors_label = QtWidgets.QLabel("Crosshair Colors")
        crosshair_colors_label.setAlignment(QtCore.Qt.AlignLeft)
        colors_layout.addWidget(crosshair_colors_label)


        crosshair_colors_layout = QtWidgets.QHBoxLayout()
        crosshair_colors_layout.setSpacing(8)

        self.aim_circle_color_btn = QtWidgets.QPushButton('Aim Radius')
        aim_hex = self.settings.get('aim_circle_color', '#FF0000')
        aim_text_color = self.get_contrasting_text_color(aim_hex)
        self.aim_circle_color_btn.setStyleSheet(f'background-color: {aim_hex}; color: {aim_text_color}; border-radius: 6px; font-weight: bold;')
        self.aim_circle_color_btn.clicked.connect(lambda: self.pick_color('aim_circle_color', self.aim_circle_color_btn))
        self.set_tooltip_if_enabled(self.aim_circle_color_btn, "Color of the Aim Radius that shows aimbot's targeting area.")
        self.aim_circle_color_btn.setMinimumHeight(32)
        self.aim_circle_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        crosshair_colors_layout.addWidget(self.aim_circle_color_btn)

        self.center_dot_color_btn = QtWidgets.QPushButton('Center Dot')
        center_dot_hex = self.settings.get('center_dot_color', '#FFFFFF')
        center_dot_text_color = self.get_contrasting_text_color(center_dot_hex)
        self.center_dot_color_btn.setStyleSheet(f'background-color: {center_dot_hex}; color: {center_dot_text_color}; border-radius: 6px; font-weight: bold;')
        self.center_dot_color_btn.clicked.connect(lambda: self.pick_color('center_dot_color', self.center_dot_color_btn))
        self.set_tooltip_if_enabled(self.center_dot_color_btn, "Color of the center crosshair dot displayed in the middle of your screen.")
        self.center_dot_color_btn.setMinimumHeight(32)
        self.center_dot_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        crosshair_colors_layout.addWidget(self.center_dot_color_btn)

        self.camera_lock_radius_color_btn = QtWidgets.QPushButton('Camera Lock Radius')
        camera_lock_radius_hex = self.settings.get('camera_lock_radius_color', '#FF0000')
        camera_lock_radius_text_color = self.get_contrasting_text_color(camera_lock_radius_hex)
        self.camera_lock_radius_color_btn.setStyleSheet(f'background-color: {camera_lock_radius_hex}; color: {camera_lock_radius_text_color}; border-radius: 6px; font-weight: bold;')
        self.camera_lock_radius_color_btn.clicked.connect(lambda: self.pick_color('camera_lock_radius_color', self.camera_lock_radius_color_btn))
        self.set_tooltip_if_enabled(self.camera_lock_radius_color_btn, "Color of the camera lock radius circle that shows the targeting area.")
        self.camera_lock_radius_color_btn.setMinimumHeight(32)
        self.camera_lock_radius_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        crosshair_colors_layout.addWidget(self.camera_lock_radius_color_btn)

        colors_layout.addLayout(crosshair_colors_layout)


        interface_colors_label = QtWidgets.QLabel("Interface Colors")
        interface_colors_label.setAlignment(QtCore.Qt.AlignLeft)
        colors_layout.addWidget(interface_colors_label)

        self.menu_theme_color_btn = QtWidgets.QPushButton('Menu Theme Color')
        menu_theme_hex = self.settings.get('menu_theme_color', '#FF0000')
        menu_theme_text_color = self.get_contrasting_text_color(menu_theme_hex)
        self.menu_theme_color_btn.setStyleSheet(f'background-color: {menu_theme_hex}; color: {menu_theme_text_color}; border-radius: 6px; font-weight: bold;')
        self.menu_theme_color_btn.clicked.connect(lambda: self.pick_color('menu_theme_color', self.menu_theme_color_btn))
        self.set_tooltip_if_enabled(self.menu_theme_color_btn, "Primary color theme for the configuration menu interface.")
        self.menu_theme_color_btn.setMinimumHeight(32)
        self.menu_theme_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.menu_theme_color_btn)


        rainbow_effects_label = QtWidgets.QLabel("Rainbow Effects")
        rainbow_effects_label.setAlignment(QtCore.Qt.AlignLeft)
        colors_layout.addWidget(rainbow_effects_label)

        self.rainbow_fov_cb = QtWidgets.QCheckBox("Rainbow Aim Radius")
        self.rainbow_fov_cb.setChecked(self.settings.get('rainbow_fov', 0) == 1)
        self.rainbow_fov_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.rainbow_fov_cb, "Makes the Aim Radius continuously cycle through rainbow colors instead of using a fixed color.")
        self.rainbow_fov_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.rainbow_fov_cb.setStyleSheet("margin-left: 8px;")
        colors_layout.addWidget(self.rainbow_fov_cb)

        self.rainbow_center_dot_cb = QtWidgets.QCheckBox("Rainbow Center Dot")
        self.rainbow_center_dot_cb.setChecked(self.settings.get('rainbow_center_dot', 0) == 1)
        self.rainbow_center_dot_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.rainbow_center_dot_cb, "Makes the center crosshair dot continuously cycle through rainbow colors instead of using a fixed color.")
        self.rainbow_center_dot_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.rainbow_center_dot_cb.setStyleSheet("margin-left: 8px;")
        colors_layout.addWidget(self.rainbow_center_dot_cb)

        self.rainbow_menu_theme_cb = QtWidgets.QCheckBox("Rainbow Menu Theme")
        self.rainbow_menu_theme_cb.setChecked(self.settings.get('rainbow_menu_theme', 0) == 1)
        self.rainbow_menu_theme_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.rainbow_menu_theme_cb, "Makes the menu theme color continuously cycle through rainbow colors instead of using a fixed color.")
        self.rainbow_menu_theme_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.rainbow_menu_theme_cb.setStyleSheet("margin-left: 8px;")
        colors_layout.addWidget(self.rainbow_menu_theme_cb)

        colors_container.setLayout(colors_layout)
        colors_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return colors_container

    def create_misc_container(self):
        misc_container = QtWidgets.QWidget()
        misc_layout = QtWidgets.QVBoxLayout()
        misc_layout.setSpacing(6)
        misc_layout.setContentsMargins(6, 6, 6, 6)
        misc_layout.setAlignment(QtCore.Qt.AlignTop)

        misc_label = QtWidgets.QLabel("Miscellaneous")
        misc_label.setAlignment(QtCore.Qt.AlignCenter)
        misc_label.setMinimumHeight(18)
        misc_layout.addWidget(misc_label)


        targeting_label = QtWidgets.QLabel("Targeting Type:")
        targeting_label.setAlignment(QtCore.Qt.AlignLeft)
        misc_layout.addWidget(targeting_label)
        
        self.esp_mode_cb = QtWidgets.QComboBox()
        self.esp_mode_cb.addItems(["Enemies Only", "All Players"])
        self.esp_mode_cb.setCurrentIndex(self.settings.get("esp_mode", 1))
        self.esp_mode_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.esp_mode_cb.currentIndexChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.esp_mode_cb, "Choose whether to show ESP for enemies only or all players including teammates.")
        self.esp_mode_cb.setMinimumHeight(22)
        self.esp_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.esp_mode_cb)

                                    
        self.auto_accept_cb = QtWidgets.QCheckBox("Auto Accept Match")
        self.auto_accept_cb.setChecked(self.settings.get('auto_accept_enabled', 0) == 1)
        self.auto_accept_cb.stateChanged.connect(self.on_auto_accept_changed)
        self.set_tooltip_if_enabled(self.auto_accept_cb, "Automatically clicks the accept button when a match is found in competitive queue.")
        self.auto_accept_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.auto_accept_cb)



        self.low_cpu_cb = QtWidgets.QCheckBox("Low CPU Mode (Performance Mode)")
        self.low_cpu_cb.setChecked(self.settings.get('low_cpu', 0) == 1)
        self.low_cpu_cb.stateChanged.connect(self.on_low_cpu_changed)
        self.set_tooltip_if_enabled(self.low_cpu_cb, "Reduces CPU usage by limiting frame rate and reducing update frequency for better performance on lower-end systems.")
        self.low_cpu_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.low_cpu_cb)

                          
        self.lbl_fps_limit = QtWidgets.QLabel(f"FPS Limit: ({self.settings.get('fps_limit', 60)})")
        self.lbl_fps_limit.setMinimumHeight(16)
        misc_layout.addWidget(self.lbl_fps_limit)
        
        self.fps_limit_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fps_limit_slider.setMinimum(20)                                                       
        self.fps_limit_slider.setMaximum(100)
        self.fps_limit_slider.setValue(self.settings.get('fps_limit', 60))
        self.fps_limit_slider.valueChanged.connect(self.update_fps_limit_label)
        self.set_tooltip_if_enabled(self.fps_limit_slider, "Maximum frames per second for ESP rendering. Lower values reduce CPU usage but may make animations less smooth.")
        self.fps_limit_slider.setMinimumHeight(18)
        self.fps_limit_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.fps_limit_slider)

                              

        if self.fov_enabled:
            self.lbl_game_fov = QtWidgets.QLabel(f"Camera FOV: ({self.settings.get('game_fov', 90)})")
            self.lbl_game_fov.setMinimumHeight(16)
            misc_layout.addWidget(self.lbl_game_fov)
            
            self.game_fov_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.game_fov_slider.setMinimum(60)
            self.game_fov_slider.setMaximum(160)

            self.game_fov_slider.setValue(self.settings.get('game_fov', 90))

            self.game_fov_slider.valueChanged.connect(self.on_fov_slider_value_changed)
            self.game_fov_slider.sliderReleased.connect(self.on_fov_slider_released)
            self.set_tooltip_if_enabled(self.game_fov_slider, "Adjust your in-game field of view from 60 (narrow) to 160 (wide) degrees. Higher FOV allows you to see more but may distort the view.")
            self.game_fov_slider.setMinimumHeight(18)
            self.game_fov_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            misc_layout.addWidget(self.game_fov_slider)
        else:

            self.lbl_game_fov = None
            self.game_fov_slider = None

                             
        self.center_dot_cb = QtWidgets.QCheckBox("Draw Center Dot")
        self.center_dot_cb.setChecked(self.settings.get("center_dot", 0) == 1)
        self.center_dot_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.center_dot_cb, "Draw a small dot in the center of your screen as a crosshair reference point.")
        self.center_dot_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.center_dot_cb)

                                
        self.center_dot_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.center_dot_size_slider.setMinimum(1)
        self.center_dot_size_slider.setMaximum(20)
        self.center_dot_size_slider.setValue(self.settings.get('center_dot_size', 3))
        self.center_dot_size_slider.valueChanged.connect(self.update_center_dot_size_label)
        self.set_tooltip_if_enabled(self.center_dot_size_slider, "Adjust the size of the center dot crosshair from 1 (smallest) to 20 (largest) pixels.")
        self.lbl_center_dot_size = QtWidgets.QLabel(f"Center Dot Size: ({self.settings.get('center_dot_size', 3)})")
        self.lbl_center_dot_size.setMinimumHeight(16)
        misc_layout.addWidget(self.lbl_center_dot_size)
        self.center_dot_size_slider.setMinimumHeight(18)
        self.center_dot_size_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.center_dot_size_slider)

                              
        self.bhop_cb = QtWidgets.QCheckBox("Bhop")
        self.bhop_cb.setChecked(self.settings.get("bhop_enabled", 0) == 1)
        self.bhop_cb.stateChanged.connect(self.on_bhop_changed)
        self.set_tooltip_if_enabled(self.bhop_cb, "Automatically times jump inputs for bunny hopping when holding the bhop key.")
        self.bhop_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.bhop_cb)

                         
        self.bhop_key_btn = QtWidgets.QPushButton(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")
        self.bhop_key_btn.setObjectName("keybind_button")
        self.bhop_key_btn.clicked.connect(lambda: self.record_key('BhopKey', self.bhop_key_btn))
        self.set_tooltip_if_enabled(self.bhop_key_btn, "Click to set the key that activates bunny hopping. Hold this key to automatically time your jumps.")
        self.bhop_key_btn.setMinimumHeight(22)
        self.bhop_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.bhop_key_btn)
        self.bhop_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'BhopKey', self.bhop_key_btn)

                                
        self.menu_key_btn = QtWidgets.QPushButton(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'M')}")
        self.menu_key_btn.setObjectName("keybind_button")
        self.menu_key_btn.clicked.connect(lambda: self.record_key('MenuToggleKey', self.menu_key_btn))
        self.set_tooltip_if_enabled(self.menu_key_btn, "Click to set the key for opening/closing this configuration menu during gameplay.")
        self.menu_key_btn.setMinimumHeight(22)
        self.menu_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.menu_key_btn)
        self.menu_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'MenuToggleKey', self.menu_key_btn)

        # Panic button
        self.panic_key_btn = QtWidgets.QPushButton(f"Panic Key: {self.settings.get('PanicKey', 'NONE')}")
        self.panic_key_btn.setObjectName("keybind_button")
        self.panic_key_btn.clicked.connect(lambda: self.record_key('PanicKey', self.panic_key_btn))
        self.set_tooltip_if_enabled(self.panic_key_btn, "Emergency key to instantly terminate all script processes. Use for quick shutdown if needed.")
        self.panic_key_btn.setMinimumHeight(22)
        self.panic_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.panic_key_btn)
        self.panic_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'PanicKey', self.panic_key_btn)



        misc_container.setLayout(misc_layout)
        misc_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return misc_container

    def create_config_container(self):
        config_container = QtWidgets.QWidget()
        config_layout = QtWidgets.QVBoxLayout()
        config_layout.setSpacing(6)
        config_layout.setContentsMargins(6, 6, 6, 6)
        config_layout.setAlignment(QtCore.Qt.AlignTop)

        config_label = QtWidgets.QLabel("Configuration")
        config_label.setAlignment(QtCore.Qt.AlignCenter)
        config_label.setMinimumHeight(20)
        config_layout.addWidget(config_label)


        config_files_label = QtWidgets.QLabel("Config Files (select to import):")
        config_layout.addWidget(config_files_label)
        self.config_files_combo = QtWidgets.QComboBox()
        self.config_files_combo.setMinimumHeight(22)
        self.config_files_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.set_tooltip_if_enabled(self.config_files_combo, "Select a config file to automatically import its settings. Files are loaded from the configs folder.")
        self.config_files_combo.currentTextChanged.connect(self.on_config_file_selected)
        config_layout.addWidget(self.config_files_combo)
        

        self._dropdown_updating = False
        self._dropdown_update_timer = QtCore.QTimer(self)
        self._dropdown_update_timer.setSingleShot(True)
        self._dropdown_update_timer.timeout.connect(self._perform_dropdown_update)
        

        self.update_config_files_dropdown()
        self.setup_config_folder_watcher()


        export_btn = QtWidgets.QPushButton("Export Config")
        export_btn.clicked.connect(self.on_export_config_clicked)
        export_btn.setMinimumHeight(22)
        export_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.set_tooltip_if_enabled(export_btn, "Export current configuration to a chosen location.")
        config_layout.addWidget(export_btn)


        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        config_layout.addWidget(separator)


        self.reset_btn = QtWidgets.QPushButton("Reset Config to Default")
        self.set_tooltip_if_enabled(self.reset_btn, "Reset all settings to their default values. This will restore the original configuration and cannot be undone.")
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.reset_btn.setMinimumHeight(22)
        self.reset_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        config_layout.addWidget(self.reset_btn)


        self.exit_script_label = QtWidgets.QLabel("Hold ESC to Exit Script")
        self.exit_script_label.setObjectName("exit_script_label")
        self.exit_script_label.setAlignment(QtCore.Qt.AlignCenter)
        self.exit_script_label.setMinimumHeight(22)
        self.exit_script_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.set_tooltip_if_enabled(self.exit_script_label, "Hold ESC for 3 seconds to safely exit the script and close all processes.")
        config_layout.addWidget(self.exit_script_label)

        config_container.setLayout(config_layout)
        config_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return config_container

    def on_export_config_clicked(self):
        """Export current configuration to chosen location"""
        try:
            self.pause_rainbow_timer()
            from PySide6.QtWidgets import QFileDialog
            default_path = os.path.join(CONFIG_DIR, "exportconfig.json")
            file_path, _ = QFileDialog.getSaveFileName(self, "Export Config", default_path, "JSON files (*.json)")
            if file_path:
                import shutil
                shutil.copy2(CONFIG_FILE, file_path)
                QtWidgets.QMessageBox.information(self, "Export Complete", f"Configuration exported to:\n{file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Failed to export configuration:\n{str(e)}")
        finally:
            self.resume_rainbow_timer()

    def on_import_config_clicked(self):
        """Import configuration from external file"""
        try:
            self.pause_rainbow_timer()
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(self, "Import Config File", "", "JSON files (*.json)")
            if file_path:
                import shutil
                shutil.copy2(file_path, CONFIG_FILE)
                self.settings = load_settings()
                self.reload_all_ui_from_settings()
                QtWidgets.QMessageBox.information(self, "Import Complete", "Configuration imported successfully!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Import Error", f"Failed to import configuration:\n{str(e)}")
        finally:
            self.resume_rainbow_timer()

    def on_config_file_selected(self, filename):
        """Handle config file selection from dropdown"""
        if not filename or not filename.endswith('.json') or filename == "-- Select config to import --":
            return
            
        try:
            self.pause_rainbow_timer()
            config_path = os.path.join(CONFIG_DIR, filename)
            
            if os.path.exists(config_path):
                import shutil

                backup_path = CONFIG_FILE + '.backup'
                if os.path.exists(CONFIG_FILE):
                    shutil.copy2(CONFIG_FILE, backup_path)
                

                shutil.copy2(config_path, CONFIG_FILE)
                self.settings = load_settings()

                self.reload_all_ui_from_settings()
                

                QtWidgets.QMessageBox.information(self, "Config Loaded", f"Successfully loaded config: {filename}")
                

                if hasattr(self, 'config_files_combo'):
                    self.config_files_combo.setCurrentIndex(0)
        except Exception as e:

            try:
                backup_path = CONFIG_FILE + '.backup'
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, CONFIG_FILE)
                    self.settings = load_settings()
                    self.reload_all_ui_from_settings()
            except Exception:
                pass
        finally:
            self.resume_rainbow_timer()

    def enforce_legit_mode_restrictions(self):
        """Enforce legit mode restrictions after config loading"""
        if SELECTED_MODE != 'legit':
            return
            
        try:
            # Disable all aim-related settings
            self.settings["aim_active"] = 0
            if hasattr(self, 'aim_active_cb') and self.aim_active_cb:
                self.aim_active_cb.setChecked(False)
            
            # Enforce triggerbot restrictions (minimum 150ms delay)
            current_delay = self.settings.get("triggerbot_between_shots_delay", 0)
            if current_delay < 150:
                self.settings["triggerbot_between_shots_delay"] = 150
                if hasattr(self, 'triggerbot_between_shots_delay_slider') and self.triggerbot_between_shots_delay_slider:
                    self.triggerbot_between_shots_delay_slider.setValue(150)
            
            # Enforce smoothness restriction (force to 20)
            self.settings["aim_smoothness"] = 20
            if hasattr(self, 'aim_smoothness_slider') and self.aim_smoothness_slider:
                self.aim_smoothness_slider.setValue(20)
            
            # Enforce radius limits (max 200 for legit mode)
            current_radius = self.settings.get("radius", 0)
            if current_radius > 200:
                self.settings["radius"] = 200
                if hasattr(self, 'radius_slider') and self.radius_slider:
                    self.radius_slider.setValue(200)
            
            # Force use radius setting
            self.settings["use_radius"] = 1
            if hasattr(self, 'use_radius_cb') and self.use_radius_cb:
                self.use_radius_cb.setChecked(True)
            
            # Enforce camera lock radius limits
            current_cam_radius = self.settings.get("camera_lock_radius", 0)
            if current_cam_radius > 200:
                self.settings["camera_lock_radius"] = 200
                if hasattr(self, 'camera_lock_radius_slider') and self.camera_lock_radius_slider:
                    self.camera_lock_radius_slider.setValue(200)
                    
            # Update labels if they exist
            if hasattr(self, 'triggerbot_between_shots_delay_label') and self.triggerbot_between_shots_delay_label:
                self.triggerbot_between_shots_delay_label.setText(f"Between shots delay: {self.settings['triggerbot_between_shots_delay']}ms")
            if hasattr(self, 'aim_smoothness_label') and self.aim_smoothness_label:
                self.aim_smoothness_label.setText(f"Smoothness: {self.settings['aim_smoothness']}")
            if hasattr(self, 'radius_label') and self.radius_label:
                self.radius_label.setText(f"Radius: {self.settings['radius']}")
            if hasattr(self, 'camera_lock_radius_label') and self.camera_lock_radius_label:
                self.camera_lock_radius_label.setText(f"Camera Lock Radius: {self.settings['camera_lock_radius']}")
                
        except Exception as e:
            print(f"Error enforcing legit mode restrictions: {e}")

    def reload_all_ui_from_settings(self):
        """Reload all UI elements from current settings"""
        try:

            self._loading_config = True
            

            self.blockSignals(True)
            

            widgets_to_block = [

                self.esp_rendering_cb, self.line_rendering_cb, self.hp_bar_rendering_cb,
                self.head_hitbox_rendering_cb, self.box_rendering_cb, self.Bones_cb,
                self.nickname_cb, self.show_visibility_cb, self.bomb_esp_cb, self.radar_cb,
                self.lines_position_combo, self.box_mode_combo, self.radar_position_combo,
                self.radar_size_slider, self.radar_scale_slider,
                

                self.trigger_bot_active_cb, self.triggerbot_head_only_cb, self.triggerbot_burst_mode_cb,
                self.triggerbot_delay_slider, self.triggerbot_first_shot_delay_slider,
                self.triggerbot_burst_shots_slider,
                

                self.aim_active_cb, self.aim_circle_visible_cb, self.aim_visibility_cb,
                self.lock_target_cb, self.disable_crosshair_cb, self.radius_slider,
                self.opacity_slider, self.thickness_slider, self.smooth_slider,
                self.aim_mode_cb, self.aim_mode_distance_cb,
                

                self.rainbow_fov_cb, self.rainbow_center_dot_cb, self.rainbow_menu_theme_cb,
                

                self.auto_accept_cb, self.low_cpu_cb, self.center_dot_cb, self.bhop_cb,
                self.fps_limit_slider, self.center_dot_size_slider
            ]
            

            if hasattr(self, 'require_aimkey_cb') and self.require_aimkey_cb:
                widgets_to_block.append(self.require_aimkey_cb)
            

            if hasattr(self, 'camera_lock_cb') and self.camera_lock_cb:
                widgets_to_block.append(self.camera_lock_cb)
            

            if hasattr(self, 'camera_lock_smoothness_slider') and self.camera_lock_smoothness_slider:
                widgets_to_block.append(self.camera_lock_smoothness_slider)
            
            if hasattr(self, 'camera_lock_spotted_check_cb') and self.camera_lock_spotted_check_cb:
                widgets_to_block.append(self.camera_lock_spotted_check_cb)
            

            if hasattr(self, 'game_fov_slider') and self.game_fov_slider:
                widgets_to_block.append(self.game_fov_slider)
            
            for widget in widgets_to_block:
                if widget is not None:
                    widget.blockSignals(True)
            

            self.esp_rendering_cb.setChecked(self.settings.get("esp_rendering", 1) == 1)
            self.line_rendering_cb.setChecked(self.settings.get("line_rendering", 1) == 1)
            self.hp_bar_rendering_cb.setChecked(self.settings.get("hp_bar_rendering", 1) == 1)
            self.head_hitbox_rendering_cb.setChecked(self.settings.get("head_hitbox_rendering", 1) == 1)
            self.box_rendering_cb.setChecked(self.settings.get("box_rendering", 1) == 1)
            self.Bones_cb.setChecked(self.settings.get("Bones", 1) == 1)
            self.nickname_cb.setChecked(self.settings.get("nickname", 1) == 1)
            self.show_visibility_cb.setChecked(self.settings.get("show_visibility", 1) == 1)
            self.bomb_esp_cb.setChecked(self.settings.get("bomb_esp", 1) == 1)
            self.radar_cb.setChecked(self.settings.get("radar_enabled", 0) == 1)
            

            current_lines_position = self.settings.get('lines_position', 'Bottom')
            index = self.lines_position_combo.findText(current_lines_position)
            if index >= 0:
                self.lines_position_combo.setCurrentIndex(index)
            
            current_box_mode = self.settings.get('box_mode', '2D')
            index = self.box_mode_combo.findText(current_box_mode)
            if index >= 0:
                self.box_mode_combo.setCurrentIndex(index)
            
            current_radar_position = self.settings.get('radar_position', 'Top Right')
            index = self.radar_position_combo.findText(current_radar_position)
            if index >= 0:
                self.radar_position_combo.setCurrentIndex(index)
            

            self.radar_size_slider.setValue(self.settings.get('radar_size', 200))
            self.radar_scale_slider.setValue(int(self.settings.get('radar_scale', 5.0) * 10))
            

            self.trigger_bot_active_cb.setChecked(self.settings.get("trigger_bot_active", 0) == 1)
            self.triggerbot_head_only_cb.setChecked(self.settings.get("triggerbot_head_only", 0) == 1)
            self.triggerbot_burst_mode_cb.setChecked(self.settings.get("triggerbot_burst_mode", 0) == 1)
            self.triggerbot_delay_slider.setValue(self.settings.get("triggerbot_between_shots_delay", 30))
            self.triggerbot_first_shot_delay_slider.setValue(self.settings.get("triggerbot_first_shot_delay", 0))
            self.triggerbot_burst_shots_slider.setValue(self.settings.get("triggerbot_burst_shots", 3))
            

            self.aim_active_cb.setChecked(self.settings.get("aim_active", 0) == 1) if hasattr(self, 'aim_active_cb') else None
            if hasattr(self, 'require_aimkey_cb') and self.require_aimkey_cb:
                self.require_aimkey_cb.setChecked(self.settings.get("require_aimkey", 1) == 1)
            if hasattr(self, 'camera_lock_cb') and self.camera_lock_cb:
                self.camera_lock_cb.setChecked(self.settings.get("camera_lock_enabled", 0) == 1)
            if hasattr(self, 'camera_lock_smoothness_slider') and self.camera_lock_smoothness_slider:
                self.camera_lock_smoothness_slider.setValue(self.settings.get("camera_lock_smoothness", 5))
            if hasattr(self, 'camera_lock_tolerance_slider') and self.camera_lock_tolerance_slider:
                self.camera_lock_tolerance_slider.setValue(self.settings.get("camera_lock_tolerance", 5))
            if hasattr(self, 'camera_lock_target_combo') and self.camera_lock_target_combo:
                self.camera_lock_target_combo.setCurrentIndex(self.settings.get("camera_lock_target_bone", 1))
            if hasattr(self, 'camera_lock_draw_range_lines_cb') and self.camera_lock_draw_range_lines_cb:
                self.camera_lock_draw_range_lines_cb.setChecked(self.settings.get("camera_lock_draw_range_lines", 0) == 1)
            if hasattr(self, 'camera_lock_line_width_slider') and self.camera_lock_line_width_slider:
                self.camera_lock_line_width_slider.setValue(self.settings.get("camera_lock_line_width", 2))
            if hasattr(self, 'camera_lock_use_radius_cb') and self.camera_lock_use_radius_cb:
                self.camera_lock_use_radius_cb.setChecked(self.settings.get("camera_lock_use_radius", 0) == 1)
            if hasattr(self, 'camera_lock_draw_radius_cb') and self.camera_lock_draw_radius_cb:
                self.camera_lock_draw_radius_cb.setChecked(self.settings.get("camera_lock_draw_radius", 0) == 1)
            if hasattr(self, 'camera_lock_spotted_check_cb') and self.camera_lock_spotted_check_cb:
                self.camera_lock_spotted_check_cb.setChecked(self.settings.get("camera_lock_spotted_check", 0) == 1)
            if hasattr(self, 'camera_lock_radius_slider') and self.camera_lock_radius_slider:
                self.camera_lock_radius_slider.setValue(self.settings.get("camera_lock_radius", 100))
            if hasattr(self, 'aim_circle_visible_cb') and self.aim_circle_visible_cb:
                self.aim_circle_visible_cb.setChecked(self.settings.get("aim_circle_visible", 1) == 1)
            if hasattr(self, 'aim_visibility_cb') and self.aim_visibility_cb:
                self.aim_visibility_cb.setChecked(self.settings.get("aim_visibility_check", 0) == 1)
            if hasattr(self, 'lock_target_cb') and self.lock_target_cb:
                self.lock_target_cb.setChecked(self.settings.get("aim_lock_target", 0) == 1)
            if hasattr(self, 'disable_crosshair_cb') and self.disable_crosshair_cb:
                self.disable_crosshair_cb.setChecked(self.settings.get("aim_disable_when_crosshair_on_enemy", 0) == 1)
            if hasattr(self, 'movement_prediction_cb') and self.movement_prediction_cb:
                self.movement_prediction_cb.setChecked(self.settings.get("aim_movement_prediction", 0) == 1)
            if hasattr(self, 'radius_slider') and self.radius_slider:
                self.radius_slider.setValue(self.settings.get("radius", 50))
            if hasattr(self, 'opacity_slider') and self.opacity_slider:
                self.opacity_slider.setValue(self.settings.get("circle_opacity", 127))
            if hasattr(self, 'thickness_slider') and self.thickness_slider:
                self.thickness_slider.setValue(self.settings.get("circle_thickness", 2))
            if hasattr(self, 'smooth_slider') and self.smooth_slider:
                self.smooth_slider.setValue(self.settings.get("aim_smoothness", 0))
            
            if hasattr(self, 'aim_mode_cb') and self.aim_mode_cb:
                aim_bone_target = self.settings.get('aim_bone_target', 1)
                self.aim_mode_cb.setCurrentIndex(aim_bone_target)
            
            if hasattr(self, 'aim_mode_distance_cb') and self.aim_mode_distance_cb:
                aim_mode_distance = self.settings.get('aim_mode_distance', 0)
                self.aim_mode_distance_cb.setCurrentIndex(aim_mode_distance)
            

            self.update_color_button_style(self.team_color_btn, self.settings.get('team_color', '#47A76A'))
            self.update_color_button_style(self.enemy_color_btn, self.settings.get('enemy_color', '#C41E3A'))
            self.update_color_button_style(self.skeleton_color_btn, self.settings.get('skeleton_color', '#FFFFFF'))
            if hasattr(self, 'aim_circle_color_btn') and self.aim_circle_color_btn:
                self.update_color_button_style(self.aim_circle_color_btn, self.settings.get('aim_circle_color', '#FF0000'))
            self.update_color_button_style(self.center_dot_color_btn, self.settings.get('center_dot_color', '#FFFFFF'))
            self.update_color_button_style(self.camera_lock_radius_color_btn, self.settings.get('camera_lock_radius_color', '#FF0000'))
            self.update_color_button_style(self.menu_theme_color_btn, self.settings.get('menu_theme_color', '#FF0000'))
            

            if hasattr(self, 'rainbow_fov_cb') and self.rainbow_fov_cb:
                self.rainbow_fov_cb.setChecked(self.settings.get("rainbow_fov", 0) == 1)
            self.rainbow_center_dot_cb.setChecked(self.settings.get("rainbow_center_dot", 0) == 1)
            self.rainbow_menu_theme_cb.setChecked(self.settings.get("rainbow_menu_theme", 0) == 1)
            

            self.auto_accept_cb.setChecked(self.settings.get("auto_accept_enabled", 0) == 1)

            self.low_cpu_cb.setChecked(self.settings.get("low_cpu", 0) == 1)
            self.center_dot_cb.setChecked(self.settings.get("center_dot", 0) == 1)
            self.bhop_cb.setChecked(self.settings.get("bhop_enabled", 0) == 1)
            self.fps_limit_slider.setValue(self.settings.get("fps_limit", 60))

            if hasattr(self, 'game_fov_slider') and self.game_fov_slider:
                self.game_fov_slider.setValue(self.settings.get("game_fov", 90))
            self.center_dot_size_slider.setValue(self.settings.get("center_dot_size", 3))
            

            self.esp_toggle_key_btn.setText(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")
            self.trigger_key_btn.setText(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
            self.aim_key_btn.setText(f"AimKey: {self.settings.get('AimKey', 'C')}")
            self.bhop_key_btn.setText(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")
            self.menu_key_btn.setText(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'F8')}")
            
            if hasattr(self, 'panic_key_btn') and self.panic_key_btn:
                self.panic_key_btn.setText(f"Panic Key: {self.settings.get('PanicKey', 'NONE')}")
            

            for widget in widgets_to_block:
                if widget is not None:
                    widget.blockSignals(False)
            self.blockSignals(False)
            
            # Clear loading flag to allow normal FOV operations
            self._loading_config = False
            


            self.settings['auto_apply_fov'] = 0
            

            self.update_radius_label()
            self.update_triggerbot_delay_label()
            self.update_triggerbot_first_shot_delay_label()
            self.update_triggerbot_burst_shots_label()
            self.update_center_dot_size_label()
            self.update_opacity_label()
            self.update_thickness_label()
            self.update_smooth_label()
            self.update_radar_size_label()
            self.update_radar_scale_label()
            self.update_fps_limit_label()
            self.update_game_fov_label_only()
            if hasattr(self, 'camera_lock_smoothness_slider') and self.camera_lock_smoothness_slider:
                self.update_camera_lock_smoothness_label()
            if hasattr(self, 'camera_lock_tolerance_slider') and self.camera_lock_tolerance_slider:
                self.update_camera_lock_tolerance_label()
            

            theme_color = self.settings.get('menu_theme_color', '#FF0000')
            self.update_menu_theme_styling(theme_color)
            self.header_label.setStyleSheet(f"color: {theme_color}; font-family: 'MS PGothic'; font-weight: bold; font-size: 16px;")
            

            self.update_box_mode_dropdown_state()
            

            self.initialize_fps_slider_state()
            

            topmost_enabled = self.settings.get('topmost', 1) == 1
            if topmost_enabled:
                self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            self.show()
            

            self.save_settings()
            
            # Enforce Legit mode restrictions after successful config reload
            if hasattr(self, 'enforce_legit_mode_restrictions'):
                self.enforce_legit_mode_restrictions()
            
        except Exception as e:
            # Make sure to clear loading flag and reset auto_apply_fov even if there's an error
            try:
                for widget in widgets_to_block:
                    if widget is not None:
                        widget.blockSignals(False)
                self.blockSignals(False)
                self._loading_config = False
                self.settings['auto_apply_fov'] = 0  # Ensure FOV won't auto-apply after error
            except:
                pass
            QtWidgets.QMessageBox.critical(self, "Reload Error", f"Failed to reload UI from settings:\n{str(e)}")
        
        # Enforce Legit mode restrictions after config reload
        if hasattr(self, 'enforce_legit_mode_restrictions'):
            self.enforce_legit_mode_restrictions()

    def update_color_button_style(self, button, color):
        """Update color button style to show the color"""
        try:
            contrasting_color = self.get_contrasting_text_color(color)
            button.setStyleSheet(f"background-color: {color}; color: {contrasting_color}; border-radius: 6px; font-weight: bold;")
        except Exception:
            pass

    def on_auto_accept_changed(self):
        try:
            self.settings["auto_accept_enabled"] = 1 if self.auto_accept_cb.isChecked() else 0
            save_settings(self.settings)
        except Exception:
            pass

    def on_bhop_changed(self):
        """Handle bhop toggle change"""
        try:
            self.settings["bhop_enabled"] = 1 if self.bhop_cb.isChecked() else 0
            save_settings(self.settings)
        except Exception:
            pass



    def handle_keybind_mouse_event(self, event, key_name, btn):
        if event.button() == QtCore.Qt.RightButton:
                                      
            self.settings[key_name] = 'NONE'
            btn.setText(f"{btn.text().split(':')[0]}: NONE")
            self.save_settings()
        else:
                                                                       
            QtWidgets.QPushButton.mousePressEvent(btn, event)

    def on_low_cpu_changed(self):
        """Handle low CPU mode toggle and lock/unlock FPS slider accordingly"""
        try:
            low_cpu_enabled = self.low_cpu_cb.isChecked()
            self.settings["low_cpu"] = 1 if low_cpu_enabled else 0
            
            if low_cpu_enabled:
                                                                        
                self.fps_limit_slider.setMinimum(10)                                        
                self.fps_limit_slider.setValue(10)
                self.fps_limit_slider.setEnabled(False)
                self.settings["fps_limit"] = 10
                self.lbl_fps_limit.setText("FPS Limit: (10) - Locked by Low CPU Mode")
            else:
                                                                 
                self.fps_limit_slider.setMinimum(20)                           
                                                        
                current_fps = max(20, self.settings.get('fps_limit', 60))
                self.fps_limit_slider.setValue(current_fps)
                self.fps_limit_slider.setEnabled(True)
                self.settings["fps_limit"] = current_fps
                self.lbl_fps_limit.setText(f"FPS Limit: ({current_fps})")
            
            self.update_box_mode_dropdown_state()
            
            save_settings(self.settings)
        except Exception:
            pass

    def initialize_fps_slider_state(self):
        """Initialize FPS slider state based on current low CPU mode setting"""
        try:
            low_cpu_enabled = self.settings.get('low_cpu', 0) == 1
            
            if low_cpu_enabled:
                                                                              
                self.fps_limit_slider.setMinimum(10)                                        
                self.fps_limit_slider.setValue(10)
                self.fps_limit_slider.setEnabled(False)
                self.settings["fps_limit"] = 10
                self.lbl_fps_limit.setText("FPS Limit: (10) - Locked by Low CPU Mode")
                save_settings(self.settings)
            else:
                                                                          
                self.fps_limit_slider.setMinimum(20)                                      
                current_fps = max(20, self.settings.get('fps_limit', 60))                        
                self.fps_limit_slider.setValue(current_fps)
                self.fps_limit_slider.setEnabled(True)
                self.settings["fps_limit"] = current_fps
                self.lbl_fps_limit.setText(f"FPS Limit: ({current_fps})")
        except Exception:
            pass

    def apply_rounded_corners(self):
        """Apply smooth rounded corners to the window using antialiased masking"""
        try:
                                         
            rect = self.rect()
            
                                                                
            scale_factor = 2                                 
            scaled_size = rect.size() * scale_factor
            pixmap = QtGui.QPixmap(scaled_size)
            pixmap.fill(QtCore.Qt.transparent)
            
                                                      
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
            
                                                      
            painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
            painter.setPen(QtCore.Qt.NoPen)
            scaled_rect = QtCore.QRectF(0, 0, scaled_size.width(), scaled_size.height())
            painter.drawRoundedRect(scaled_rect, 15 * scale_factor, 15 * scale_factor)
            painter.end()
            
                                                    
            smooth_pixmap = pixmap.scaled(rect.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            
                                                
            mask = smooth_pixmap.createMaskFromColor(QtCore.Qt.transparent)
            self.setMask(QtGui.QBitmap(mask))
            
        except Exception:
                                                                       
            try:
                path = QtGui.QPainterPath()
                path.addRoundedRect(QtCore.QRectF(self.rect()), 15, 15)
                region = QtGui.QRegion(path.toFillPolygon().toPolygon())
                self.setMask(region)
            except Exception:
                                                                         
                pass

    def apply_topmost(self):
        """Always apply topmost flag to keep window on top"""
        flags = self.windowFlags()
        flags |= QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()



    def on_terminate_clicked(self):
        """Terminate the application without confirmation"""
        try:
            self.pause_rainbow_timer()
            

            self.reset_fov_to_default()
            

            import time
            time.sleep(0.2)
            
            try:

                with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                    f.write('terminate')
                add_temporary_file(TERMINATE_SIGNAL_FILE)  # Track for cleanup
            except Exception:
                pass
            try:

                if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                    os.remove(KEYBIND_COOLDOWNS_FILE)
            except Exception:
                pass
            
            try:

                print("[DEBUG] Application terminating - check debug_log.txt for full output")
                

                import os
                os._exit(0)
            except Exception:
                pass
        except Exception:

            import os
            os._exit(0)
        finally:
            self.resume_rainbow_timer()

    def update_box_mode_dropdown_state(self):
        """Update box mode dropdown state based on low CPU mode setting"""
        try:
            low_cpu_enabled = self.settings.get('low_cpu', 0) == 1
            
            if hasattr(self, 'box_mode_combo'):
                if low_cpu_enabled:

                    self.box_mode_combo.setCurrentText('2D')
                    self.box_mode_combo.setEnabled(False)
                    if hasattr(self, 'box_mode_label'):
                        self.box_mode_label.setToolTip('Box mode is locked to 2D when Low CPU Mode is enabled for better performance')
                else:

                    self.box_mode_combo.setEnabled(True)
                    if hasattr(self, 'box_mode_label'):
                        self.box_mode_label.setToolTip('Choose between 2D flat boxes or 3D boxes that show actual player dimensions in game world')
        except Exception:
            pass

    def on_reset_clicked(self):
        """Reset all settings to defaults with confirmation"""
        try:
            self.pause_rainbow_timer()
            

            reply = QtWidgets.QMessageBox.question(
                self, 
                'Reset Configuration', 
                'Are you sure you want to reset all settings to default values?\n\nThis action cannot be undone.',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply != QtWidgets.QMessageBox.Yes:
                return
            

            self._loading_config = True
            
            self.settings = DEFAULT_SETTINGS.copy()
            save_settings(self.settings)
            


            

            try:

                widget_names = [
                    'esp_rendering_cb', 'line_rendering_cb', 'hp_bar_rendering_cb',
                    'head_hitbox_rendering_cb', 'box_rendering_cb', 'Bones_cb', 'nickname_cb', 
                    'show_visibility_cb', 'bomb_esp_cb', 'radar_cb', 'center_dot_cb',
                    'trigger_bot_active_cb', 'aim_active_cb', 'aim_circle_visible_cb',
                    'auto_accept_cb', 'bhop_cb', 'topmost_cb', 'low_cpu_cb',
                    'rainbow_fov_cb', 'rainbow_center_dot_cb', 'rainbow_menu_theme_cb'
                ]
                
                widgets = [getattr(self, name, None) for name in widget_names if hasattr(self, name)]
                

                for w in widgets:
                    if w is not None:
                        w.blockSignals(True)
                

                if hasattr(self, 'esp_rendering_cb'):
                    self.esp_rendering_cb.setChecked(self.settings.get('esp_rendering', 1) == 1)
                if hasattr(self, 'line_rendering_cb'):
                    self.line_rendering_cb.setChecked(self.settings.get('line_rendering', 1) == 1)
                if hasattr(self, 'hp_bar_rendering_cb'):
                    self.hp_bar_rendering_cb.setChecked(self.settings.get('hp_bar_rendering', 1) == 1)
                if hasattr(self, 'head_hitbox_rendering_cb'):
                    self.head_hitbox_rendering_cb.setChecked(self.settings.get('head_hitbox_rendering', 1) == 1)
                if hasattr(self, 'box_rendering_cb'):
                    self.box_rendering_cb.setChecked(self.settings.get('box_rendering', 1) == 1)
                if hasattr(self, 'Bones_cb'):
                    self.Bones_cb.setChecked(self.settings.get('Bones', 1) == 1)
                if hasattr(self, 'nickname_cb'):
                    self.nickname_cb.setChecked(self.settings.get('nickname', 1) == 1)
                if hasattr(self, 'show_visibility_cb'):
                    self.show_visibility_cb.setChecked(self.settings.get('show_visibility', 1) == 1)
                if hasattr(self, 'bomb_esp_cb'):
                    self.bomb_esp_cb.setChecked(self.settings.get('bomb_esp', 1) == 1)
                if hasattr(self, 'radar_cb'):
                    self.radar_cb.setChecked(self.settings.get('radar_enabled', 0) == 1)
                if hasattr(self, 'center_dot_cb'):
                    self.center_dot_cb.setChecked(self.settings.get('center_dot', 0) == 1)
                if hasattr(self, 'trigger_bot_active_cb'):
                    self.trigger_bot_active_cb.setChecked(self.settings.get('trigger_bot_active', 0) == 1)
                if hasattr(self, 'aim_active_cb'):
                    self.aim_active_cb.setChecked(self.settings.get('aim_active', 0) == 1)
                if hasattr(self, 'aim_circle_visible_cb'):
                    self.aim_circle_visible_cb.setChecked(self.settings.get('aim_circle_visible', 1) == 1)
                if hasattr(self, 'auto_accept_cb'):
                    self.auto_accept_cb.setChecked(self.settings.get('auto_accept_enabled', 0) == 1)
                if hasattr(self, 'bhop_cb'):
                    self.bhop_cb.setChecked(self.settings.get('bhop_enabled', 0) == 1)
                if hasattr(self, 'topmost_cb'):
                    self.topmost_cb.setChecked(self.settings.get('topmost', 1) == 1)
                if hasattr(self, 'low_cpu_cb'):
                    self.low_cpu_cb.setChecked(self.settings.get('low_cpu', 0) == 1)
                if hasattr(self, 'rainbow_fov_cb'):
                    self.rainbow_fov_cb.setChecked(self.settings.get('rainbow_fov', 0) == 1)
                if hasattr(self, 'rainbow_center_dot_cb'):
                    self.rainbow_center_dot_cb.setChecked(self.settings.get('rainbow_center_dot', 0) == 1)
                if hasattr(self, 'rainbow_menu_theme_cb'):
                    self.rainbow_menu_theme_cb.setChecked(self.settings.get('rainbow_menu_theme', 0) == 1)
                

                if hasattr(self, 'radius_slider'):
                    self.radius_slider.setValue(self.settings.get('radius', 50))
                if hasattr(self, 'opacity_slider'):
                    self.opacity_slider.setValue(self.settings.get('circle_opacity', 127))
                if hasattr(self, 'thickness_slider'):
                    self.thickness_slider.setValue(self.settings.get('circle_thickness', 2))
                if hasattr(self, 'smooth_slider'):
                    self.smooth_slider.setValue(self.settings.get('aim_smoothness', 0))
                if hasattr(self, 'center_dot_size_slider'):
                    self.center_dot_size_slider.setValue(self.settings.get('center_dot_size', 3))
                if hasattr(self, 'fps_limit_slider'):
                    self.fps_limit_slider.setValue(self.settings.get('fps_limit', 60))
                if hasattr(self, 'radar_size_slider'):
                    self.radar_size_slider.setValue(self.settings.get('radar_size', 200))
                if hasattr(self, 'radar_scale_slider'):
                    self.radar_scale_slider.setValue(int(self.settings.get('radar_scale', 5.0) * 10))
                
                # Handle FOV slider reset - block signals to prevent auto-application
                if hasattr(self, 'game_fov_slider') and self.game_fov_slider:
                    self.game_fov_slider.setValue(self.settings.get('game_fov', 90))
                
                # Update dropdowns
                if hasattr(self, 'lines_position_combo'):
                    position = self.settings.get('lines_position', 'Bottom')
                    index = self.lines_position_combo.findText(position)
                    if index >= 0:
                        self.lines_position_combo.setCurrentIndex(index)
                
                if hasattr(self, 'radar_position_combo'):
                    position = self.settings.get('radar_position', 'Top Right')
                    index = self.radar_position_combo.findText(position)
                    if index >= 0:
                        self.radar_position_combo.setCurrentIndex(index)
                
                if hasattr(self, 'box_mode_combo'):
                    box_mode = self.settings.get('box_mode', '2D')
                    index = self.box_mode_combo.findText(box_mode)
                    if index >= 0:
                        self.box_mode_combo.setCurrentIndex(index)
                
                if hasattr(self, 'esp_toggle_key_btn'):
                    self.esp_toggle_key_btn.setText(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")
                if hasattr(self, 'aim_key_btn'):
                    self.aim_key_btn.setText(f"AimKey: {self.settings.get('AimKey', 'C')}")
                if hasattr(self, 'trigger_key_btn'):
                    self.trigger_key_btn.setText(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
                if hasattr(self, 'bhop_key_btn'):
                    self.bhop_key_btn.setText(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")
                if hasattr(self, 'menu_key_btn'):
                    self.menu_key_btn.setText(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'F8')}")
                
                if hasattr(self, 'team_color_btn'):
                    color = self.settings.get('team_color', '#47A76A')
                    self.team_color_btn.setStyleSheet(f'background-color: {color}; color: white;')
                if hasattr(self, 'enemy_color_btn'):
                    color = self.settings.get('enemy_color', '#C41E3A')
                    self.enemy_color_btn.setStyleSheet(f'background-color: {color}; color: white;')
                if hasattr(self, 'skeleton_color_btn'):
                    color = self.settings.get('skeleton_color', '#FFFFFF')
                    self.skeleton_color_btn.setStyleSheet(f'background-color: {color}; color: black;')
                if hasattr(self, 'aim_circle_color_btn'):
                    color = self.settings.get('aim_circle_color', '#FF0000')
                    self.aim_circle_color_btn.setStyleSheet(f'background-color: {color}; color: white;')
                if hasattr(self, 'center_dot_color_btn'):
                    color = self.settings.get('center_dot_color', '#FFFFFF')
                    self.center_dot_color_btn.setStyleSheet(f'background-color: {color}; color: black;')
                if hasattr(self, 'menu_theme_color_btn'):
                    color = self.settings.get('menu_theme_color', '#FF0000')
                    self.menu_theme_color_btn.setStyleSheet(f'background-color: {color}; color: white;')
                    self.update_menu_theme_styling(color)
                
                # Update labels
                if hasattr(self, 'update_radius_label'):
                    self.update_radius_label()
                if hasattr(self, 'update_opacity_label'):
                    self.update_opacity_label()
                if hasattr(self, 'update_thickness_label'):
                    self.update_thickness_label()
                if hasattr(self, 'update_smooth_label'):
                    self.update_smooth_label()
                if hasattr(self, 'update_center_dot_size_label'):
                    self.update_center_dot_size_label()
                if hasattr(self, 'update_fps_limit_label'):
                    self.update_fps_limit_label()
                if hasattr(self, 'update_radar_size_label'):
                    self.update_radar_size_label()
                if hasattr(self, 'update_radar_scale_label'):
                    self.update_radar_scale_label()
                if hasattr(self, 'update_game_fov_label_only') and hasattr(self, 'game_fov_slider') and self.game_fov_slider:
                    self.update_game_fov_label_only()
                
                # Apply settings
                if hasattr(self, 'apply_topmost'):
                    self.apply_topmost()
                if hasattr(self, 'initialize_fps_slider_state'):
                    self.initialize_fps_slider_state()
                if hasattr(self, 'update_box_mode_dropdown_state'):
                    self.update_box_mode_dropdown_state()
                
                # Unblock signals
                for w in widgets:
                    if w is not None:
                        w.blockSignals(False)
                
                # Clear loading flag to allow normal FOV operations
                self._loading_config = False
                
                # CRITICAL: Reset auto_apply_fov to 0 after reset to prevent automatic FOV application
                self.settings['auto_apply_fov'] = 0
                
                # SECURITY: Enforce legit mode restrictions after reset to prevent bypass
                self.enforce_legit_mode_restrictions()
                
                # Save settings after enforcing restrictions
                save_settings(self.settings)
                
                QtWidgets.QMessageBox.information(self, "Reset Complete", "All settings have been reset to default values.")
                
            except Exception as e:
                # Make sure to clear loading flag and reset auto_apply_fov even if there's an error
                self._loading_config = False
                self.settings['auto_apply_fov'] = 0  # Ensure FOV won't auto-apply after error
                
                # SECURITY: Enforce legit mode restrictions even after error
                try:
                    self.enforce_legit_mode_restrictions()
                    save_settings(self.settings)
                except:
                    pass
                    
                QtWidgets.QMessageBox.critical(self, "Reset Error", f"Settings were reset but UI update failed:\n{str(e)}")
                
        except Exception as e:
            # Make sure to clear loading flag and reset auto_apply_fov even if there's an error
            self._loading_config = False
            self.settings['auto_apply_fov'] = 0  # Ensure FOV won't auto-apply after error
            
            # SECURITY: Enforce legit mode restrictions even after error
            try:
                self.enforce_legit_mode_restrictions()
                save_settings(self.settings)
            except:
                pass
                
            QtWidgets.QMessageBox.critical(self, "Reset Error", f"Failed to reset settings:\n{str(e)}")
        finally:
            self.resume_rainbow_timer()

    def save_settings(self):
        
        self.settings["esp_rendering"] = 1 if self.esp_rendering_cb.isChecked() else 0
        self.settings["esp_mode"] = self.esp_mode_cb.currentIndex() if hasattr(self, 'esp_mode_cb') else self.settings.get("esp_mode", 0)
        self.settings["line_rendering"] = 1 if self.line_rendering_cb.isChecked() else 0
        self.settings["lines_position"] = self.lines_position_combo.currentText() if hasattr(self, 'lines_position_combo') else "Bottom"
        low_cpu_enabled = self.settings.get('low_cpu', 0) == 1
        if low_cpu_enabled:
            self.settings["box_mode"] = "2D"
        else:
            self.settings["box_mode"] = self.box_mode_combo.currentText() if hasattr(self, 'box_mode_combo') else "2D"
        self.settings["hp_bar_rendering"] = 1 if self.hp_bar_rendering_cb.isChecked() else 0
        self.settings["head_hitbox_rendering"] = 1 if self.head_hitbox_rendering_cb.isChecked() else 0
        self.settings["Bones"] = 1 if self.Bones_cb.isChecked() else 0
        
        try:
            self.settings["box_rendering"] = 1 if getattr(self, 'box_rendering_cb', None) and self.box_rendering_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["rainbow_fov"] = 1 if getattr(self, 'rainbow_fov_cb', None) and self.rainbow_fov_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["center_dot"] = 1 if getattr(self, 'center_dot_cb', None) and self.center_dot_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["rainbow_center_dot"] = 1 if getattr(self, 'rainbow_center_dot_cb', None) and self.rainbow_center_dot_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["rainbow_menu_theme"] = 1 if getattr(self, 'rainbow_menu_theme_cb', None) and self.rainbow_menu_theme_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["low_cpu"] = 1 if getattr(self, 'low_cpu_cb', None) and self.low_cpu_cb.isChecked() else 0
        except Exception:
            pass
        self.settings["nickname"] = 1 if self.nickname_cb.isChecked() else 0
        
        try:
            self.settings["show_visibility"] = 1 if getattr(self, 'show_visibility_cb', None) and self.show_visibility_cb.isChecked() else 0
        except Exception:
            self.settings["show_visibility"] = self.settings.get("show_visibility", 1)
        self.settings["bomb_esp"] = 1 if self.bomb_esp_cb.isChecked() else 0
        self.settings["radar_enabled"] = 1 if self.radar_cb.isChecked() else 0
        self.settings["aim_active"] = 1 if hasattr(self, 'aim_active_cb') and self.aim_active_cb.isChecked() else 0
        
        try:
            self.settings["require_aimkey"] = 1 if getattr(self, 'require_aimkey_cb', None) and self.require_aimkey_cb.isChecked() else 0
        except Exception:
            self.settings["require_aimkey"] = 1  # Default to requiring aimkey
        
        try:
            self.settings["camera_lock_enabled"] = 1 if getattr(self, 'camera_lock_cb', None) and self.camera_lock_cb.isChecked() else 0
        except Exception:
            self.settings["camera_lock_enabled"] = 0  # Default to disabled
        
                                       
        try:
            self.settings["aim_circle_visible"] = 1 if getattr(self, 'aim_circle_visible_cb', None) and self.aim_circle_visible_cb.isChecked() else 0
        except Exception:
            pass

        
        self.settings["radius"] = self.radius_slider.value() if hasattr(self, 'radius_slider') else self.settings.get("radius", 50)
        
                        
        if hasattr(self, 'radar_size_slider'):
            self.settings["radar_size"] = self.radar_size_slider.value()
        if hasattr(self, 'radar_scale_slider'):
            self.settings["radar_scale"] = self.radar_scale_slider.value() / 10.0
        if hasattr(self, 'radar_position_combo'):
            self.settings["radar_position"] = self.radar_position_combo.currentText()
        
                           
        if hasattr(self, 'fps_limit_slider'):
            self.settings["fps_limit"] = self.fps_limit_slider.value()

    

        
        if getattr(self, "triggerbot_delay_slider", None):
            self.settings["triggerbot_between_shots_delay"] = self.triggerbot_delay_slider.value()
        if getattr(self, "triggerbot_burst_mode_cb", None):
            self.settings["triggerbot_burst_mode"] = 1 if self.triggerbot_burst_mode_cb.isChecked() else 0
        if getattr(self, "triggerbot_burst_shots_slider", None):
            self.settings["triggerbot_burst_shots"] = self.triggerbot_burst_shots_slider.value()

        if getattr(self, "triggerbot_first_shot_delay_slider", None):
            self.settings["triggerbot_first_shot_delay"] = self.triggerbot_first_shot_delay_slider.value()

        if getattr(self, "triggerbot_head_only_cb", None):
            self.settings["triggerbot_head_only"] = 1 if self.triggerbot_head_only_cb.isChecked() else 0

        if getattr(self, "center_dot_size_slider", None):
            self.settings["center_dot_size"] = self.center_dot_size_slider.value()

        if getattr(self, "camera_lock_smoothness_slider", None):
            self.settings["camera_lock_smoothness"] = self.camera_lock_smoothness_slider.value()
        
        if getattr(self, "camera_lock_tolerance_slider", None):
            self.settings["camera_lock_tolerance"] = self.camera_lock_tolerance_slider.value()
        
        if getattr(self, "camera_lock_target_combo", None):
            self.settings["camera_lock_target_bone"] = self.camera_lock_target_combo.currentIndex()
        
        if getattr(self, "camera_lock_draw_range_lines_cb", None):
            self.settings["camera_lock_draw_range_lines"] = 1 if self.camera_lock_draw_range_lines_cb.isChecked() else 0
        
        if getattr(self, "camera_lock_line_width_slider", None):
            self.settings["camera_lock_line_width"] = self.camera_lock_line_width_slider.value()
        
        if getattr(self, "camera_lock_use_radius_cb", None):
            self.settings["camera_lock_use_radius"] = 1 if self.camera_lock_use_radius_cb.isChecked() else 0
        
        if getattr(self, "camera_lock_draw_radius_cb", None):
            self.settings["camera_lock_draw_radius"] = 1 if self.camera_lock_draw_radius_cb.isChecked() else 0
        
        if getattr(self, "camera_lock_radius_slider", None):
            self.settings["camera_lock_radius"] = self.camera_lock_radius_slider.value()
        
        if getattr(self, "camera_lock_spotted_check_cb", None):
            self.settings["camera_lock_spotted_check"] = 1 if self.camera_lock_spotted_check_cb.isChecked() else 0

        
        try:
            if getattr(self, "aim_key_btn", None) is not None:
                
                text = self.aim_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                else:
                    val = text.strip()
                if val:
                    self.settings["AimKey"] = val
        except Exception:
            pass

        self.settings["aim_bone_target"] = self.aim_mode_cb.currentIndex() if hasattr(self, 'aim_mode_cb') else self.settings.get("aim_bone_target", 1)
        self.settings["aim_mode_distance"] = self.aim_mode_distance_cb.currentIndex() if hasattr(self, 'aim_mode_distance_cb') else self.settings.get("aim_mode_distance", 0)

        
        self.settings["trigger_bot_active"] = 1 if self.trigger_bot_active_cb.isChecked() else 0

        
        
        try:
            if getattr(self, 'trigger_key_btn', None) is not None:
                text = self.trigger_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["TriggerKey"] = val
        except Exception:
            pass

        
        self.settings["circle_opacity"] = self.opacity_slider.value() if hasattr(self, 'opacity_slider') else self.settings.get("circle_opacity", 127)

        
        self.settings["circle_thickness"] = self.thickness_slider.value() if hasattr(self, 'thickness_slider') else self.settings.get("circle_thickness", 2)

                                                                 
        try:
            self.settings["topmost"] = 1
        except Exception:
            pass

        
        try:
            val = getattr(self, "menu_key_combo", None)
            if val is not None:
                self.settings["MenuToggleKey"] = val.itemData(val.currentIndex())
        except Exception:
            pass

                                
        try:
            self.settings["aim_smoothness"] = self.smooth_slider.value()
        except Exception:
            pass
        
        try:
            self.settings["aim_visibility_check"] = 1 if getattr(self, 'aim_visibility_cb', None) and self.aim_visibility_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["aim_lock_target"] = 1 if getattr(self, 'lock_target_cb', None) and self.lock_target_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["aim_disable_when_crosshair_on_enemy"] = 1 if getattr(self, 'disable_crosshair_cb', None) and self.disable_crosshair_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["aim_movement_prediction"] = 1 if getattr(self, 'movement_prediction_cb', None) and self.movement_prediction_cb.isChecked() else 0
        except Exception:
            pass
        
                               
        try:
            if getattr(self, 'bhop_key_btn', None) is not None:
                text = self.bhop_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["BhopKey"] = val
        except Exception:
            pass
        
        try:
            if getattr(self, 'menu_key_btn', None) is not None:
                text = self.menu_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["MenuToggleKey"] = val
        except Exception:
            pass
        
        try:
            if getattr(self, 'panic_key_btn', None) is not None:
                text = self.panic_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["PanicKey"] = val
        except Exception:
            pass
        
        # Apply legit mode restrictions before saving
        if SELECTED_MODE == 'legit':
            # Force minimum first shot delay of 150ms
            if self.settings.get("triggerbot_first_shot_delay", 0) < 150:
                self.settings["triggerbot_first_shot_delay"] = 150
            
            # Force camera lock smoothness to 20
            self.settings["camera_lock_smoothness"] = 20
            
            # Force use radius for targeting to be on
            self.settings["camera_lock_use_radius"] = 1
            
            # Limit camera lock radius to maximum 200
            if self.settings.get("camera_lock_radius", 100) > 200:
                self.settings["camera_lock_radius"] = 200
        
        save_settings(self.settings)

    def record_key(self, settings_key: str, btn: QtWidgets.QPushButton):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Press a key or mouse button')
        dialog.setModal(False)                                                
        dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Dialog)               
        lbl = QtWidgets.QLabel('Press desired key or mouse button now...')
        v = QtWidgets.QVBoxLayout(dialog)
        v.addWidget(lbl)

        timer = QtCore.QTimer(dialog)
        dialog_cancelled = False

        def on_dialog_close():
            nonlocal dialog_cancelled
            dialog_cancelled = True
            timer.stop()

                                                                 
        def closeEvent(event):
            on_dialog_close()
            QtWidgets.QDialog.closeEvent(dialog, event)

        dialog.closeEvent = closeEvent

        def check():
            if dialog_cancelled:
                return
                
                                       
            mouse_buttons = [
                (0x01, 'LMB'),                       
                (0x02, 'RMB'),                          
                (0x04, 'MMB'),                         
                (0x05, 'MOUSE4'),                  
                (0x06, 'MOUSE5'),                  
            ]
            
            for code, name in mouse_buttons:
                try:
                    if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                                                                                  
                        if code == 0x01:
                                                                                       
                            QtCore.QTimer.singleShot(50, lambda: check_delayed_mouse(code, name))
                            return
                        else:
                            self.settings[settings_key] = name
                            save_settings(self.settings)
                            
                                                                      
                            self.set_keybind_cooldown(settings_key)
                            
                            short = settings_key
                            if '_' in settings_key:
                                short = settings_key.split('_')[0]
                            btn.setText(f"{short.capitalize()}: {name}")
                            timer.stop()
                            dialog.accept()
                            return
                except Exception:
                    continue
            
                                 
            for code in range(0x08, 0xFF):
                try:
                    if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                                                                          
                        if code in [0x01, 0x02, 0x04, 0x05, 0x06]:
                            continue
                            
                        try:
                            mods = []
                            
                            if (win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_LCONTROL', 0xA2)) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_RCONTROL', 0xA3)) & 0x8000) != 0:
                                mods.append('CTRL')
                            
                            if (win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_LMENU', 0xA4)) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_RMENU', 0xA5)) & 0x8000) != 0:
                                mods.append('ALT')
                            
                            if (win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000) != 0:
                                mods.append('SHIFT')

                                                  
                            vk_name_map = {
                                getattr(win32con, 'VK_ESCAPE', 0x1B): 'ESC',
                                getattr(win32con, 'VK_RETURN', 0x0D): 'ENTER',
                                getattr(win32con, 'VK_SPACE', 0x20): 'SPACE',
                                getattr(win32con, 'VK_TAB', 0x09): 'TAB',
                                getattr(win32con, 'VK_LEFT', 0x25): 'LEFT',
                                getattr(win32con, 'VK_UP', 0x26): 'UP',
                                getattr(win32con, 'VK_RIGHT', 0x27): 'RIGHT',
                                getattr(win32con, 'VK_DOWN', 0x28): 'DOWN',
                                getattr(win32con, 'VK_BACK', 0x08): 'BACKSPACE',
                                getattr(win32con, 'VK_DELETE', 0x2E): 'DELETE',
                                getattr(win32con, 'VK_INSERT', 0x2D): 'INSERT',
                                getattr(win32con, 'VK_HOME', 0x24): 'HOME',
                                getattr(win32con, 'VK_END', 0x23): 'END',
                                getattr(win32con, 'VK_PRIOR', 0x21): 'PAGEUP',
                                getattr(win32con, 'VK_NEXT', 0x22): 'PAGEDOWN',
                                getattr(win32con, 'VK_LSHIFT', 0xA0): 'LSHIFT',
                                getattr(win32con, 'VK_RSHIFT', 0xA1): 'RSHIFT',
                                getattr(win32con, 'VK_LCONTROL', 0xA2): 'LCTRL',
                                getattr(win32con, 'VK_RCONTROL', 0xA3): 'RCTRL',
                                getattr(win32con, 'VK_LMENU', 0xA4): 'LALT',
                                getattr(win32con, 'VK_RMENU', 0xA5): 'RALT',
                                getattr(win32con, 'VK_CAPITAL', 0x14): 'CAPS',
                                getattr(win32con, 'VK_NUMPAD0', 0x60): 'NUMPAD0',
                                getattr(win32con, 'VK_NUMPAD1', 0x61): 'NUMPAD1',
                                getattr(win32con, 'VK_NUMPAD2', 0x62): 'NUMPAD2',
                                getattr(win32con, 'VK_NUMPAD3', 0x63): 'NUMPAD3',
                                getattr(win32con, 'VK_NUMPAD4', 0x64): 'NUMPAD4',
                                getattr(win32con, 'VK_NUMPAD5', 0x65): 'NUMPAD5',
                                getattr(win32con, 'VK_NUMPAD6', 0x66): 'NUMPAD6',
                                getattr(win32con, 'VK_NUMPAD7', 0x67): 'NUMPAD7',
                                getattr(win32con, 'VK_NUMPAD8', 0x68): 'NUMPAD8',
                                getattr(win32con, 'VK_NUMPAD9', 0x69): 'NUMPAD9',
                                getattr(win32con, 'VK_MULTIPLY', 0x6A): 'MULTIPLY',
                                getattr(win32con, 'VK_ADD', 0x6B): 'ADD',
                                getattr(win32con, 'VK_SUBTRACT', 0x6D): 'SUBTRACT',
                                getattr(win32con, 'VK_DECIMAL', 0x6E): 'DECIMAL',
                                getattr(win32con, 'VK_DIVIDE', 0x6F): 'DIVIDE',
                                getattr(win32con, 'VK_SNAPSHOT', 0x2C): 'PRINTSCREEN',
                                getattr(win32con, 'VK_SCROLL', 0x91): 'SCROLLLOCK',
                                getattr(win32con, 'VK_PAUSE', 0x13): 'PAUSE',
                                getattr(win32con, 'VK_NUMLOCK', 0x90): 'NUMLOCK',
                                getattr(win32con, 'VK_LWIN', 0x5B): 'LWIN',
                                getattr(win32con, 'VK_RWIN', 0x5C): 'RWIN',
                                getattr(win32con, 'VK_APPS', 0x5D): 'APPS',
                                                    
                                getattr(win32con, 'VK_OEM_1', 0xBA): 'SEMICOLON',
                                getattr(win32con, 'VK_OEM_PLUS', 0xBB): 'EQUALS',
                                getattr(win32con, 'VK_OEM_COMMA', 0xBC): 'COMMA',
                                getattr(win32con, 'VK_OEM_MINUS', 0xBD): 'MINUS',
                                getattr(win32con, 'VK_OEM_PERIOD', 0xBE): 'PERIOD',
                                getattr(win32con, 'VK_OEM_2', 0xBF): 'SLASH',
                                getattr(win32con, 'VK_OEM_3', 0xC0): 'GRAVE',
                                getattr(win32con, 'VK_OEM_4', 0xDB): 'LBRACKET',
                                getattr(win32con, 'VK_OEM_5', 0xDC): 'BACKSLASH',
                                getattr(win32con, 'VK_OEM_6', 0xDD): 'RBRACKET',
                                getattr(win32con, 'VK_OEM_7', 0xDE): 'QUOTE',
                            }
                            
                            base = ''
                            if 0x30 <= code <= 0x5A:
                                base = chr(code)
                            elif 0x70 <= code <= 0x87:
                                base = f'F{code - 0x6F}'
                            else:
                                base = vk_name_map.get(code, '')
                                if not base:
                                                          
                                    if code == win32con.VK_MENU:
                                        base = 'ALT'
                                    elif code == win32con.VK_CONTROL:
                                        base = 'CTRL'
                                    elif code == win32con.VK_SHIFT:
                                        base = 'SHIFT'
                                    elif code == getattr(win32con, 'VK_CAPITAL', 0x14):
                                        base = 'CAPS'
                                    else:
                                        base = str(code)

                                                    
                            parts = []
                            for m in mods:
                                if m not in parts:
                                    parts.append(m)
                            if base and base.upper() not in parts:
                                parts.append(str(base).upper())
                            if parts:
                                val = '+'.join(parts)
                            else:
                                val = str(base).upper()
                        except Exception:
                                                 
                            if 0x30 <= code <= 0x5A:
                                val = chr(code)
                            elif 0x70 <= code <= 0x87:
                                val = f'F{code - 0x6F}'
                            else:
                                val = str(code)

                                                         
                        self.settings[settings_key] = val
                        save_settings(self.settings)
                        
                                                                  
                        self.set_keybind_cooldown(settings_key)
                        
                        button_text_map = {
                            'AimKey': 'AimKey',
                            'TriggerKey': 'TriggerKey', 
                            'HeadTriggerKey': 'Head TriggerKey',
                            'MenuToggleKey': 'MenuToggleKey',
                            'BhopKey': 'BhopKey',
                            'ESPToggleKey': 'ESP Toggle'
                        }
                        display_text = button_text_map.get(settings_key, settings_key)
                        btn.setText(f"{display_text}: {val}")
                        timer.stop()
                        dialog.accept()
                        return
                except Exception:
                    continue

        def check_delayed_mouse(code, name):
                                                                    
            if dialog_cancelled:
                return
            
                                                                           
            if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                self.settings[settings_key] = name
                save_settings(self.settings)
                
                                                          
                self.set_keybind_cooldown(settings_key)
                
                short = settings_key
                if '_' in settings_key:
                    short = settings_key.split('_')[0]
                btn.setText(f"{short.capitalize()}: {name}")
                timer.stop()
                dialog.accept()

        timer.timeout.connect(check)
        timer.start(20)
        dialog.show()                                                             

    def get_contrasting_text_color(self, background_color):
        """Calculate optimal text color (black or white) based on background color luminance"""
        try:
            # Remove # if present and convert to RGB
            hex_color = background_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            def get_luminance_component(c):
                c = c / 255.0
                if c <= 0.03928:
                    return c / 12.92
                else:
                    return ((c + 0.055) / 1.055) ** 2.4
            
            r_lum = get_luminance_component(r)
            g_lum = get_luminance_component(g)
            b_lum = get_luminance_component(b)
            
            luminance = 0.2126 * r_lum + 0.7152 * g_lum + 0.0722 * b_lum
            
            return 'black' if luminance > 0.5 else 'white'
        except:
            return 'white'

    def pick_color(self, settings_key: str, btn: QtWidgets.QPushButton):
        rainbow_timer_was_active = False
        if hasattr(self, '_rainbow_menu_timer') and self._rainbow_menu_timer.isActive():
            rainbow_timer_was_active = True
            self._rainbow_menu_timer.stop()
        
        try:
            init = QtGui.QColor(self.settings.get(settings_key, '#FFFFFF'))
            col = QtWidgets.QColorDialog.getColor(init, self, f'Choose {settings_key}')
            if col.isValid():
                hexc = col.name()
                self.settings[settings_key] = hexc
                save_settings(self.settings)
                
                # Calculate optimal text color for contrast
                text_color = self.get_contrasting_text_color(hexc)
                btn.setStyleSheet(f'background-color: {hexc}; color: {text_color};')
                
                                                                               
                if settings_key == 'menu_theme_color':
                    self.update_menu_theme_styling(hexc)
        finally:
            if rainbow_timer_was_active and hasattr(self, '_rainbow_menu_timer'):
                self._rainbow_menu_timer.start(50)

    def update_menu_theme_styling(self, theme_color):
        """Update the UI styling with the new menu theme color"""
                                                  
        color = QtGui.QColor(theme_color)
        darker_color = color.darker(110).name()
        
                                                                    
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #020203;
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
                border-radius: 15px;
            }}
            
            QLabel {{
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
                font-size: 12px;
            }}
            
            /* Special styling for exit script label */
            QLabel[objectName="exit_script_label"] {{
                color: {theme_color};
                font-family: "MS PGothic";
                font-weight: bold;
                font-size: 13px;
                border: 1px solid {theme_color};
                border-radius: 4px;
                padding: 6px 12px;
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 0.1);
            }}
            
            QCheckBox {{
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
                font-size: 12px;
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }}
            
            QCheckBox::indicator:hover {{
                border: 2px solid #777;
                background-color: #3a3a3a;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {theme_color};
                border: 2px solid {darker_color};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjM1IDQuNjVMMTQuNjUgNS45NUw2IDEzLjM1TDEuMzUgOC43TDIuNjUgNy40TDYgMTAuNjVMMTMuMzUgNC42NVoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=);
            }}
            
            QCheckBox::indicator:checked:hover {{
                background-color: {darker_color};
                border: 2px solid {color.darker(120).name()};
            }}
            
            QCheckBox::indicator:unchecked {{
                background-color: #2a2a2a;
                border: 2px solid #555;
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                background-color: #3a3a3a;
                border: 2px solid #777;
            }}
            
            QSlider::groove:horizontal {{
                background-color: #3a3a3a;
                height: 6px;
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background-color: {theme_color};
                border: 2px solid {darker_color};
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {darker_color};
            }}
            
            QSlider::sub-page:horizontal {{
                background-color: {theme_color};
                border-radius: 3px;
            }}
            
            QComboBox {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
                font-size: 12px;
                min-height: 20px;
            }}
            
            QComboBox:hover {{
                background-color: #4a4a4a;
                border: 1px solid #777;
            }}
            
            QComboBox:on {{
                background-color: #4a4a4a;
                border: 1px solid {theme_color};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik02IDhMMCAwSDEyTDYgOFoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=);
                width: 12px;
                height: 8px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                selection-background-color: {theme_color};
                selection-color: white;
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
            }}
            
            QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
                font-size: 12px;
                min-height: 20px;
            }}
            
            QPushButton:hover {{
                background-color: #4a4a4a;
                border: 1px solid #777;
            }}
            
            QPushButton:pressed {{
                background-color: #2a2a2a;
                border: 1px solid {theme_color};
            }}
            
            QPushButton:focus {{
                border: 1px solid {theme_color};
            }}
            
            /* Keybind buttons with theme-colored borders */
            QPushButton[objectName="keybind_button"] {{
                background-color: #3a3a3a;
                border: 2px solid {theme_color};
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-family: "MS PGothic";
                font-weight: normal;
                font-size: 12px;
                min-height: 20px;
            }}
            
            QPushButton[objectName="keybind_button"]:hover {{
                background-color: #4a4a4a;
                border: 2px solid {darker_color};
            }}
            
            QPushButton[objectName="keybind_button"]:pressed {{
                background-color: #2a2a2a;
                border: 2px solid {color.lighter(120).name()};
            }}
            
            QPushButton[objectName="keybind_button"]:focus {{
                border: 2px solid {color.lighter(130).name()};
            }}
            
            QTabWidget::pane {{
                border: none;
                background-color: #020203;
            }}
            
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            
            QTabBar::tab {{
                background-color: #3c3c3c;
                color: {theme_color};
                padding: 8px 20px;
                margin: 2px;
                border-radius: 4px;
                font-family: "MS PGothic";
                font-weight: bold;
            }}
            
            QTabBar::tab:selected {{
                background-color: #555;
                color: {theme_color};
            }}
            
            QTabBar::tab:hover {{
                background-color: #4a4a4a;
                color: {theme_color};
            }}
            
            /* Ensure message boxes and dialogs have proper styling */
            QMessageBox {{
                background-color: #020203;
                color: white;
                font-family: "MS PGothic";
            }}
            
            QMessageBox QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-family: "MS PGothic";
                min-width: 60px;
                min-height: 20px;
            }}
            
            QMessageBox QPushButton:hover {{
                background-color: #4a4a4a;
                border: 1px solid #777;
            }}
            
            QMessageBox QPushButton:pressed {{
                background-color: #2a2a2a;
                border: 1px solid {theme_color};
            }}
            
            QFileDialog {{
                background-color: #020203;
                color: white;
                font-family: "MS PGothic";
            }}
            
            QFileDialog QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-family: "MS PGothic";
                min-width: 60px;
                min-height: 20px;
            }}
            
            QFileDialog QPushButton:hover {{
                background-color: #4a4a4a;
                border: 1px solid #777;
            }}
            
            QFileDialog QPushButton:pressed {{
                background-color: #2a2a2a;
                border: 1px solid {theme_color};
            }}
            
            /* Ensure message boxes and dialogs have proper styling */
            QMessageBox {{
                background-color: #020203;
                color: white;
                font-family: "MS PGothic";
            }}
            
            QMessageBox QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-family: "MS PGothic";
                min-width: 60px;
                min-height: 20px;
            }}
            
            QMessageBox QPushButton:hover {{
                background-color: #4a4a4a;
                border: 1px solid #777;
            }}
            
            QMessageBox QPushButton:pressed {{
                background-color: #2a2a2a;
                border: 1px solid {theme_color};
            }}
            
            QFileDialog {{
                background-color: #020203;
                color: white;
                font-family: "MS PGothic";
            }}
            
            QFileDialog QPushButton {{
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-family: "MS PGothic";
                min-width: 60px;
                min-height: 20px;
            }}
            
            QFileDialog QPushButton:hover {{
                background-color: #4a4a4a;
                border: 1px solid #777;
            }}
            
            QFileDialog QPushButton:pressed {{
                background-color: #2a2a2a;
                border: 1px solid {theme_color};
            }}
        """)
        
                                                                      
        try:
            if hasattr(self, 'header_label') and self.header_label:
                self.header_label.setStyleSheet(f"color: {theme_color}; font-family: 'MS PGothic'; font-weight: bold; font-size: 14px;")
        except Exception:
            pass

    def _update_rainbow_menu_theme(self):
        """Update menu theme with rainbow colors when rainbow_menu_theme is enabled"""
        try:
            rainbow_enabled = self.settings.get('rainbow_menu_theme', 0) == 1
            
                                                                               
            if not hasattr(self, '_rainbow_was_enabled'):
                self._rainbow_was_enabled = False
                
            if rainbow_enabled:
                global RAINBOW_HUE_MENU
                                                                                               
                RAINBOW_HUE_MENU = (RAINBOW_HUE_MENU + 0.005) % 1.0
                
                r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE_MENU, 1.0, 1.0)]
                rainbow_color = f"#{r:02x}{g:02x}{b:02x}"
                
                                                                                          
                self.settings['current_rainbow_color'] = rainbow_color
                save_settings(self.settings)
                
                                                                             
                self.update_menu_theme_styling(rainbow_color)
                
                                                                        
                if hasattr(self, 'menu_theme_color_btn') and self.menu_theme_color_btn:
                    self.menu_theme_color_btn.setStyleSheet(f'background-color: {rainbow_color}; color: white;')
                    
                self._rainbow_was_enabled = True
                
            elif self._rainbow_was_enabled:
                                                                                    
                                                                               
                if 'current_rainbow_color' in self.settings:
                    del self.settings['current_rainbow_color']
                save_settings(self.settings)
                
                                                                                  
                original_color = self.settings.get('menu_theme_color', '#FF0000')
                self.update_menu_theme_styling(original_color)
                
                                                                              
                if hasattr(self, 'menu_theme_color_btn') and self.menu_theme_color_btn:
                    self.menu_theme_color_btn.setStyleSheet(f'background-color: {original_color}; color: white;')
                    
                self._rainbow_was_enabled = False
                
        except Exception:
            pass
    
    def check_panic_key(self):
        """Check for panic key press and terminate all processes if pressed"""
        try:
            key = self.settings.get("PanicKey", "NONE")
            
            if not key or str(key).upper() == "NONE":
                return
                
            # Check if panic key is on cooldown to prevent accidental double-press
            if self.is_keybind_on_cooldown("PanicKey"):
                return
                
            vk = key_str_to_vk(key)
            pressed = (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
            
            if pressed:
                # Set cooldown to prevent multiple activations
                self.set_keybind_cooldown("PanicKey")
                
                # Force terminate all processes immediately using proper cleanup
                self.panic_shutdown()
                
        except Exception:
            pass
    
    def panic_shutdown(self):
        """Emergency shutdown of all script processes using proper cleanup mechanism"""
        try:
            # Hide the config window immediately
            self.hide()
            
            # Reset FOV to default before shutdown
            try:
                self.reset_fov_to_default()
            except Exception:
                pass
            
            # Create the terminate signal file that the main process monitors
            try:
                with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                    f.write('panic_shutdown')
                add_temporary_file(TERMINATE_SIGNAL_FILE)  # Track for cleanup
            except Exception:
                pass
            
            # Clean up panic signal file if it exists
            try:
                panic_file = os.path.join(os.getcwd(), 'panic_shutdown.signal')
                if os.path.exists(panic_file):
                    os.remove(panic_file)
            except Exception:
                pass
                
            # Exit this process cleanly and let main process handle cleanup
            try:
                import sys
                sys.exit(0)
            except Exception:
                # Last resort - force exit
                import os
                os._exit(0)
                
        except Exception:
            # Last resort - force exit
            import os
            os._exit(0)

    def check_menu_toggle(self):
        
        try:
            # Check panic key first
            self.check_panic_key()
            
            if getattr(self, "_menu_toggle_ignore_until", 0) > time.time():
                return
            key = self.settings.get("MenuToggleKey", "M")
            
            if not key or str(key).upper() == "NONE":
                return
                
                                                   
            if self.is_keybind_on_cooldown("MenuToggleKey"):
                return
                
            vk = key_str_to_vk(key)
            pressed = (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
            if pressed and not self.menu_toggle_pressed:
                
                if self.isVisible():
                    self.hide()
                    self._manually_hidden = True                                
                    self._was_visible = False                              
                else:
                    
                    try:
                        self.apply_topmost()
                    except Exception:
                        pass
                    self.show()
                    self._manually_hidden = False                                   
                    self._was_visible = True                              
                self.menu_toggle_pressed = True
            elif not pressed:
                self.menu_toggle_pressed = False
                                                                        
            try:
                esp_key = self.settings.get('ESPToggleKey', 'NONE')
                if esp_key and str(esp_key).upper() != 'NONE':
                                                          
                    if not self.is_keybind_on_cooldown("ESPToggleKey"):
                        esp_vk = key_str_to_vk(esp_key)
                        esp_pressed = (win32api.GetAsyncKeyState(esp_vk) & 0x8000) != 0 if esp_vk != 0 else False
                        if esp_pressed and not getattr(self, 'esp_toggle_pressed', False):
                                          
                            cur = 1 if self.settings.get('esp_rendering', 1) == 1 else 0
                            self.settings['esp_rendering'] = 0 if cur == 1 else 1
                            save_settings(self.settings)
                                                           
                            try:
                                if getattr(self, 'esp_rendering_cb', None) is not None:
                                    self.esp_rendering_cb.setChecked(self.settings['esp_rendering'] == 1)
                            except Exception:
                                pass
                            self.esp_toggle_pressed = True
                        elif not esp_pressed:
                            self.esp_toggle_pressed = False
            except Exception:
                pass
        except Exception:
            pass

    def _check_escape_hold(self):
        """Poll ESC state; if held continuously for 4 seconds, trigger termination.

        This uses GetAsyncKeyState high-bit detection so it responds while the key is held.
        """
        try:
            
            app = QtWidgets.QApplication.instance()
            if app is not None:
                widget = app.focusWidget()
                
                if widget is not None and widget.metaObject().className() in ('QLineEdit', 'QTextEdit', 'QPlainTextEdit'):
                    self._escape_hold_start = 0
                    return

            
            if (win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0:
                if self._escape_hold_start == 0:
                    self._escape_hold_start = time.time()
                else:
                    if time.time() - self._escape_hold_start >= 2.0:
                        
                        try:
                            self.on_terminate_clicked()
                        except Exception:
                            pass
                        
                        try:
                            self._escape_hold_timer.stop()
                        except Exception:
                            pass
            else:
                
                self._escape_hold_start = 0
        except Exception:
            
            try:
                self._escape_hold_start = 0
            except Exception:
                pass

    
    def hideEvent(self, event: QtGui.QHideEvent):
        try:
            
            for le in (getattr(self, 'trigger_key_input', None), getattr(self, 'keyboard_input', None), getattr(self, 'menu_key_combo', None)):
                if le is not None:
                    le.setEnabled(False)
                    le.clearFocus()
        except Exception:
            pass
        super().hideEvent(event)
    
    def showEvent(self, event: QtGui.QShowEvent):
        try:
            
            for le in (getattr(self, 'trigger_key_input', None), getattr(self, 'keyboard_input', None), getattr(self, 'menu_key_combo', None)):
                if le is not None:
                    le.setEnabled(True)
        except Exception:
            pass
        super().showEvent(event)
        
                                                                  
        try:
            current_pos = self.pos()
            constrained_pos = self.constrain_to_cs2_window(current_pos)
            if constrained_pos != current_pos:
                self.move(constrained_pos)
        except Exception:
            pass

    def resizeEvent(self, event):
        """Ensure window stays within CS2 bounds when resized and reapply rounded corners"""
        super().resizeEvent(event)
        try:
            current_pos = self.pos()
            constrained_pos = self.constrain_to_cs2_window(current_pos)
            if constrained_pos != current_pos:
                self.move(constrained_pos)
            
                                                  
            self.apply_rounded_corners()
        except Exception:
            pass

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            new_pos = self.pos() + delta
            
                                                           
            constrained_pos = self.constrain_to_cs2_window(new_pos)
            
            self.move(constrained_pos)
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = False
                                                                            
            import time
            self._drag_end_time = time.time()

    def update_radius_label(self):
        if hasattr(self, 'radius_slider') and hasattr(self, 'lbl_radius'):
            val = self.radius_slider.value()
            self.lbl_radius.setText(f"Aim Radius: ({val})")
            self.save_settings()

    def update_opacity_label(self):
        if hasattr(self, 'opacity_slider') and hasattr(self, 'lbl_opacity'):
            val = self.opacity_slider.value()
            self.lbl_opacity.setText(f"Circle Transparency: ({val})")
            self.save_settings()

    def update_thickness_label(self):
        if hasattr(self, 'thickness_slider') and hasattr(self, 'lbl_thickness'):
            val = self.thickness_slider.value()
            self.lbl_thickness.setText(f"Circle Thickness: ({val})")
            self.save_settings()

    def update_smooth_label(self):
        if hasattr(self, 'smooth_slider') and hasattr(self, 'lbl_smooth'):
            val = self.smooth_slider.value()
            self.lbl_smooth.setText(f"Aim Smoothness: ({val})")
            self.save_settings()

    def update_camera_lock_smoothness_label(self):
        val = self.camera_lock_smoothness_slider.value()
        self.lbl_camera_lock_smoothness.setText(f"Camera Lock Smoothness: ({val})")
        self.save_settings()

    def update_camera_lock_tolerance_label(self):
        val = self.camera_lock_tolerance_slider.value()
        self.lbl_camera_lock_tolerance.setText(f"Camera Lock Tolerance: ({val}px)")
        self.save_settings()

    def update_camera_lock_line_width_label(self):
        val = self.camera_lock_line_width_slider.value()
        self.lbl_camera_lock_line_width.setText(f"Camera Lock Line Length: ({val})")
        self.save_settings()

    def update_camera_lock_radius_label(self):
        val = self.camera_lock_radius_slider.value()
        self.lbl_camera_lock_radius.setText(f"Camera Lock Radius: ({val})")
        self.save_settings()

    def update_triggerbot_delay_label(self):
        val = self.triggerbot_delay_slider.value()
        self.lbl_delay.setText(f"Triggerbot Delay (ms): ({val})")
        self.save_settings()

    def update_triggerbot_first_shot_delay_label(self):
        val = self.triggerbot_first_shot_delay_slider.value()
        self.lbl_first_shot_delay.setText(f"First Shot Delay (ms): ({val})")
        self.save_settings()

    def update_triggerbot_burst_shots_label(self):
        self.lbl_burst_shots.setText(f"Burst Shots: ({self.triggerbot_burst_shots_slider.value()})")
        self.save_settings()

    def update_center_dot_size_label(self):
        val = self.center_dot_size_slider.value()
        self.lbl_center_dot_size.setText(f"Center Dot Size: ({val})")
        self.save_settings()

    def update_radar_size_label(self):
        try:
            val = self.radar_size_slider.value()
            self.lbl_radar_size.setText(f"Radar Size: ({val})")
            self.save_settings()
        except Exception:
            pass

    def update_radar_scale_label(self):
        try:
            val = self.radar_scale_slider.value() / 10.0
            self.lbl_radar_scale.setText(f"Radar Scale: ({val:.1f})")
            self.save_settings()
        except Exception:
            pass

    def on_radar_position_changed(self):
        try:
            position = self.radar_position_combo.currentText()
            self.settings["radar_position"] = position
            self.save_settings()
        except Exception:
            pass

    def update_fps_limit_label(self):
        try:
                                                                 
            if self.settings.get('low_cpu', 0) == 1:
                self.fps_limit_slider.setValue(10)                    
                self.lbl_fps_limit.setText("FPS Limit: (10) - Locked by Low CPU Mode")
                return
                
            val = self.fps_limit_slider.value()
            self.lbl_fps_limit.setText(f"FPS Limit: ({val})")
            self.save_settings()
        except Exception:
            pass

    def update_game_fov_label(self):
        try:
            if hasattr(self, 'game_fov_slider') and self.game_fov_slider and hasattr(self, 'lbl_game_fov') and self.lbl_game_fov:
                val = self.game_fov_slider.value()
                self.lbl_game_fov.setText(f"Camera FOV: ({val})")
                self.settings['game_fov'] = val
                self.save_settings()
                # Only apply FOV when manually changed by user
                if getattr(self, '_fov_manual_change', False):
                    self.apply_fov_change(val)
                    self._fov_manual_change = False
        except Exception:
            pass

    def update_game_fov_label_only(self):
        """Update FOV label without applying FOV change or updating settings - used during config reload and initialization"""
        try:
            if hasattr(self, 'game_fov_slider') and self.game_fov_slider and hasattr(self, 'lbl_game_fov') and self.lbl_game_fov:
                val = self.game_fov_slider.value()
                self.lbl_game_fov.setText(f"Camera FOV: ({val})")
        except Exception:
            pass

    def on_fov_slider_value_changed(self):
        """Handle FOV slider value changes for immediate label updates"""
        print(f"[DEBUG] FOV slider value changed: {self.game_fov_slider.value()}")  # Debug
        try:
            # Check if FOV controls are available
            if not (hasattr(self, 'game_fov_slider') and self.game_fov_slider):
                print("[DEBUG] FOV controls not available")  # Debug
                return
                
            # Don't apply FOV during initialization or config loading
            if getattr(self, '_is_initializing', False) or getattr(self, '_loading_config', False):
                print("[DEBUG] Initializing or loading config, updating label only")  # Debug
                # Just update the label during initialization or config loading
                self.update_game_fov_label_only()
                return
            
            if not hasattr(self, '_fov_original_value'):
                self._fov_original_value = self.game_fov_slider.value()
                print(f"[DEBUG] Storing original FOV value: {self._fov_original_value}")  # Debug
                
            if self._fov_warning_accepted:
                print("[DEBUG] Warning accepted, applying change immediately")  # Debug
                new_value = self.game_fov_slider.value()
                self.settings['game_fov'] = new_value
                self.settings['auto_apply_fov'] = 1
                self.save_settings()
                self._fov_manual_change = True
                self.update_game_fov_label()
                return
            
            print("[DEBUG] Updating label only (warning not accepted)")  # Debug
            # Just update the label to show current value while dragging
            # Also update settings so they're saved when user accepts
            new_value = self.game_fov_slider.value()
            self.settings['game_fov'] = new_value
            self.save_settings()
            self.update_game_fov_label_only()
            
        except Exception as e:
            print(f"[DEBUG] Exception in on_fov_slider_value_changed: {e}")  # Debug
            pass

    def on_fov_slider_released(self):
        """Handle FOV slider release - this is when we show the popup"""
        print("[DEBUG] FOV slider released")  # Debug
        try:
            # Check if FOV controls are available
            if not (hasattr(self, 'game_fov_slider') and self.game_fov_slider):
                print("[DEBUG] FOV controls not available on release")  # Debug
                return
                
            if getattr(self, '_is_initializing', False):
                print("[DEBUG] Still initializing, ignoring release")  # Debug
                return
                
            # If dialog is currently showing, ignore
            if getattr(self, '_fov_dialog_showing', False):
                print("[DEBUG] Dialog already showing, ignoring release")  # Debug
                return
                
            # If warning already accepted, no need for popup
            if self._fov_warning_accepted:
                print("[DEBUG] Warning already accepted, no popup needed")  # Debug
                # Clear the original value tracker
                if hasattr(self, '_fov_original_value'):
                    delattr(self, '_fov_original_value')
                return
            
            current_value = self.game_fov_slider.value()
            original_value = getattr(self, '_fov_original_value', 90)
            print(f"[DEBUG] Current: {current_value}, Original: {original_value}")  # Debug
            
            # Only show popup if value actually changed from original
            if current_value != original_value:
                print("[DEBUG] Value changed, showing popup")  # Debug
                self._pending_fov_value = current_value
                # Small delay to ensure slider is fully released
                QtCore.QTimer.singleShot(50, self._show_delayed_fov_popup)
            else:
                print("[DEBUG] Value unchanged, no popup needed")  # Debug
                # Clear the original value tracker
                if hasattr(self, '_fov_original_value'):
                    delattr(self, '_fov_original_value')
                # Clear the original value tracker
                if hasattr(self, '_fov_original_value'):
                    delattr(self, '_fov_original_value')
            
        except Exception as e:
            print(f"[DEBUG] Exception in on_fov_slider_released: {e}")  # Debug
            pass

    def _show_delayed_fov_popup(self):
        """Show FOV warning popup after slider is released"""
        try:
            # Check if we have a pending FOV value and warning hasn't been accepted
            if self._pending_fov_value is None or self._fov_warning_accepted:
                return
                
            # Check if dialog is already showing
            if getattr(self, '_fov_dialog_showing', False):
                return
                
            # Set flag to prevent multiple dialogs
            self._fov_dialog_showing = True
            
            # Store the values
            new_fov_value = self._pending_fov_value
            original_fov_value = self.settings.get('game_fov', 90)
            
            # Pause rainbow timer during dialog
            self.pause_rainbow_timer()
            
            try:
                # Show confirmation dialog
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setWindowTitle("FOV Change Warning")
                msg_box.setText("Changing FOV can cause VAC ban. Change FOV?")
                msg_box.setIcon(QtWidgets.QMessageBox.Warning)
                
                # Create custom buttons
                yes_button = msg_box.addButton("Yes, Apply FOV", QtWidgets.QMessageBox.YesRole)
                cancel_button = msg_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                msg_box.setDefaultButton(cancel_button)
                
                # Set dialog flags to stay on top
                msg_box.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
                
                # Show dialog and get result
                msg_box.exec()
                clicked_button = msg_box.clickedButton()
                
                if clicked_button == yes_button:
                    # User accepted - apply the FOV change
                    self._fov_warning_accepted = True
                    self.settings['auto_apply_fov'] = 1
                    self.settings['game_fov'] = new_fov_value
                    self.save_settings()
                    self._fov_manual_change = True
                    self.update_game_fov_label()
                else:
                    # User cancelled - reset slider to original value
                    original_value = getattr(self, '_fov_original_value', 90)
                    self.game_fov_slider.blockSignals(True)
                    self.game_fov_slider.setValue(original_value)
                    self.game_fov_slider.blockSignals(False)
                    self.update_game_fov_label_only()
                    # Reset settings to original value
                    self.settings['game_fov'] = original_value
                    self.save_settings()
                    
            finally:
                # Clear pending value and flags
                self._pending_fov_value = None
                self._fov_dialog_showing = False
                # Clear the original value tracker
                if hasattr(self, '_fov_original_value'):
                    delattr(self, '_fov_original_value')
                self.resume_rainbow_timer()
                
        except Exception:
            # Make sure flags are cleared even if an exception occurs
            self._pending_fov_value = None
            self._fov_dialog_showing = False
            pass

    def apply_fov_change(self, fov_value):
        """Apply FOV change to the game"""
        try:
            # Try to connect to CS2 process and apply FOV change
            import pymem
            pm = None
            client = None
            
            try:
                pm = pymem.Pymem("cs2.exe")
                client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                
                if pm and client:
                    # Read local player controller
                    local_player_controller = pm.read_longlong(client + dwLocalPlayerController)
                    if local_player_controller:
                        # Write FOV value to the player controller
                        pm.write_int(local_player_controller + m_iDesiredFOV, int(fov_value))
                        # Mark that FOV was changed during runtime
                        self._fov_changed_during_runtime = True
                        print(f"[DEBUG] FOV changed to {fov_value}, flag set to True")
            except Exception:
                pass
        except Exception:
            pass

    def reset_fov_to_default(self, force=False):
        """Reset FOV to default value (90) when terminating, but only if FOV was changed during runtime"""
        print(f"[DEBUG] reset_fov_to_default called: force={force}, _fov_changed_during_runtime={self._fov_changed_during_runtime}")
        
        if not force and not self._fov_changed_during_runtime:
            print("[DEBUG] FOV reset skipped - not changed during runtime")
            return  # Don't reset if FOV wasn't changed during script execution
            
        print("[DEBUG] Attempting FOV reset to 90...")
        try:
            # Reset FOV to 90 (default FOV) directly without setting the tracking flag
            import pymem
            
            # Use global offsets that were loaded at startup
            global dwLocalPlayerController, m_iDesiredFOV
            
            try:
                pm = pymem.Pymem("cs2.exe")
                client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                
                if pm and client:
                    print(f"[DEBUG] Using dwLocalPlayerController offset: {dwLocalPlayerController}")
                    print(f"[DEBUG] Using m_iDesiredFOV offset: {m_iDesiredFOV}")
                    
                    # Read local player controller
                    local_player_controller = pm.read_longlong(client + dwLocalPlayerController)
                    if local_player_controller:
                        print(f"[DEBUG] Local player controller found at: 0x{local_player_controller:X}")
                        
                        # Read current FOV to verify
                        current_fov = pm.read_int(local_player_controller + m_iDesiredFOV)
                        print(f"[DEBUG] Current FOV before reset: {current_fov}")
                        
                        # Try multiple reset attempts with different approaches
                        reset_success = False
                        
                        # Method 1: Direct write with multiple attempts
                        for attempt in range(3):
                            pm.write_int(local_player_controller + m_iDesiredFOV, 90)
                            time.sleep(0.02)  # Small delay between attempts
                            verify_fov = pm.read_int(local_player_controller + m_iDesiredFOV)
                            print(f"[DEBUG] Reset attempt {attempt + 1}: FOV now shows {verify_fov}")
                            if verify_fov == 90:
                                reset_success = True
                                break
                        
                        # Method 2: Try writing 0 first, then 90 (sometimes helps bypass game protection)
                        if not reset_success:
                            print("[DEBUG] Trying alternative reset method...")
                            pm.write_int(local_player_controller + m_iDesiredFOV, 0)
                            time.sleep(0.05)
                            pm.write_int(local_player_controller + m_iDesiredFOV, 90)
                            time.sleep(0.05)
                            verify_fov = pm.read_int(local_player_controller + m_iDesiredFOV)
                            print(f"[DEBUG] Alternative method result: FOV now shows {verify_fov}")
                            if verify_fov == 90:
                                reset_success = True
                        
                        # Method 3: Try updating the UI slider value as well
                        if not reset_success:
                            print("[DEBUG] Trying UI slider sync method...")
                            # Update our internal tracking
                            self.settings['game_fov'] = 90
                            if hasattr(self, 'game_fov_slider') and self.game_fov_slider:
                                self.game_fov_slider.setValue(90)
                            if hasattr(self, 'update_game_fov_label_only'):
                                self.update_game_fov_label_only()
                            
                            # Try the memory write again
                            pm.write_int(local_player_controller + m_iDesiredFOV, 90)
                            time.sleep(0.1)
                            verify_fov = pm.read_int(local_player_controller + m_iDesiredFOV)
                            print(f"[DEBUG] UI sync method result: FOV now shows {verify_fov}")
                            if verify_fov == 90:
                                reset_success = True
                        
                        # Final verification
                        final_fov = pm.read_int(local_player_controller + m_iDesiredFOV)
                        print(f"[DEBUG] Final FOV check: {final_fov}")
                        
                        if reset_success or final_fov == 90:
                            print("[DEBUG] FOV successfully reset to 90")
                            # Disable auto-apply FOV when resetting to default
                            self.settings['auto_apply_fov'] = 0
                            self.save_settings()
                            print("[DEBUG] Auto-apply FOV disabled")
                        else:
                            print(f"[DEBUG] FOV reset failed - CS2 may be preventing FOV changes. Final value: {final_fov}")
                            print("[DEBUG] Note: You may need to manually reset FOV in-game or restart CS2")
                    else:
                        print("[DEBUG] Failed to get local player controller")
                else:
                    print("[DEBUG] Failed to connect to CS2 process")
            except Exception as e:
                print(f"[DEBUG] Exception in FOV reset: {e}")
                import traceback
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        except Exception as e:
            print(f"[DEBUG] Outer exception in FOV reset: {e}")
            import traceback
            print(f"[DEBUG] Outer traceback: {traceback.format_exc()}")
    
    def setup_config_folder_watcher(self):
        """Setup file system watcher for the configs folder and commands.txt"""
        try:
            self.config_folder_watcher = QFileSystemWatcher()
            if os.path.exists(CONFIG_DIR):
                self.config_folder_watcher.addPath(CONFIG_DIR)
                self.config_folder_watcher.directoryChanged.connect(self.on_config_folder_changed)
            
            # Also watch commands.txt for FOV availability changes
            commands_file = os.path.join(os.getcwd(), 'commands.txt')
            if os.path.exists(commands_file):
                self.config_folder_watcher.fileChanged.connect(self.on_commands_file_changed)
                self.config_folder_watcher.addPath(commands_file)
        except Exception:
            pass
    
    def on_commands_file_changed(self):
        """Handle changes to commands.txt file"""
        try:
            # Check if FOV command availability changed
            new_fov_enabled = "fov" in load_commands()
            if hasattr(self, 'fov_enabled') and new_fov_enabled != self.fov_enabled:
                print(f"[DEBUG] FOV command availability changed: {self.fov_enabled} -> {new_fov_enabled}")
                # Note: Dynamic FOV control creation/removal would require rebuilding UI
                # For now, just update the flag - user needs to restart for full effect
                self.fov_enabled = new_fov_enabled
        except Exception:
            pass
    
    def on_config_folder_changed(self):
        """Handle changes in the config folder with debounce"""
        # Don't update if we're already updating or if user is interacting with dropdown
        if self._dropdown_updating or (hasattr(self, 'config_files_combo') and self.config_files_combo.view().isVisible()):
            return
        
        # Use debounce timer to prevent rapid updates
        self._dropdown_update_timer.stop()
        self._dropdown_update_timer.start(500)  # 500ms debounce
    
    def _perform_dropdown_update(self):
        """Perform the actual dropdown update after debounce"""
        self.update_config_files_dropdown()
    
    def update_config_files_dropdown(self):
        """Update the config files dropdown with current JSON files"""
        try:
            if not hasattr(self, 'config_files_combo'):
                return
            
            # Initialize dropdown updating flag if it doesn't exist
            if not hasattr(self, '_dropdown_updating'):
                self._dropdown_updating = False
                
            if self._dropdown_updating:
                return
            
            # Don't update if dropdown is currently open/visible
            if self.config_files_combo.view().isVisible():
                return
                
            self._dropdown_updating = True
                
            # Temporarily disconnect signal to prevent triggering import during population
            try:
                self.config_files_combo.currentTextChanged.disconnect()
            except:
                pass
            
            # Store current selection
            current_text = self.config_files_combo.currentText()
            
            # Get current file list
            new_files = []
            if os.path.exists(CONFIG_DIR):
                new_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json') and f != 'autosave.json']
                new_files.sort()  # Sort alphabetically
            
            # Check if files have actually changed
            current_items = []
            for i in range(1, self.config_files_combo.count()):  # Skip placeholder item
                current_items.append(self.config_files_combo.itemText(i))
            
            # Only update if the file list has changed
            if current_items != new_files:
                # Clear and repopulate
                self.config_files_combo.clear()
                
                # Add placeholder item
                self.config_files_combo.addItem("-- Select config to import --")
                
                for json_file in new_files:
                    self.config_files_combo.addItem(json_file)
                
                # Only restore selection if it's not the placeholder and still exists
                if current_text and current_text != "-- Select config to import --":
                    index = self.config_files_combo.findText(current_text)
                    if index >= 0:
                        self.config_files_combo.setCurrentIndex(index)
            
            # Reconnect the signal
            self.config_files_combo.currentTextChanged.connect(self.on_config_file_selected)
            
        except Exception:
            pass
        finally:
            self._dropdown_updating = False

def configurator():
    try:
                                                                            
        import os
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
        
                              
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.window.debug=false"
        
        app = QtWidgets.QApplication(sys.argv)
        
                                                
        try:
            app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
            app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        except Exception:
            pass
        
        pass  # Using default Qt styling
        
        window = ConfigWindow()
        
                                                                
        if window.is_game_window_active():
            window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        app_title = get_app_title()
        ctypes.windll.user32.MessageBoxW(0, f"An error occured: {str(e)}", app_title, 0x00000000 | 0x00010000 | 0x00040000)
        try:
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('error')
        except:
            pass
        sys.exit(0)

class ESPWindow(QtWidgets.QWidget):
    def __init__(self, settings, window_width=None, window_height=None):
        super().__init__()
        # Ensure settings are properly merged with defaults BEFORE any rendering
        merged_settings = DEFAULT_SETTINGS.copy()
        if settings and isinstance(settings, dict):
            merged_settings.update(settings)
        self.settings = merged_settings
        
        # Mark initialization as complete to prevent settings reloading during render
        self._initialization_complete = True
        
        self.setWindowTitle('ESP Overlay')
        
        if window_width is not None and window_height is not None:
            self.window_width, self.window_height = window_width, window_height
                                                                                         
            self.window_x, self.window_y, _, _ = get_window_client_rect("Counter-Strike 2")
            if self.window_x is None or self.window_y is None:
                self.window_x, self.window_y = 0, 0
        else:
            self.window_x, self.window_y, self.window_width, self.window_height = get_window_client_rect("Counter-Strike 2")
            if self.window_width is None or self.window_height is None:
                self.window_width, self.window_height = 800, 600
                self.window_x, self.window_y = 0, 0
        
        
        if self.window_width is None or self.window_height is None:
            self.window_width, self.window_height = 800, 600
            self.window_x, self.window_y = 0, 0
        
                                                            
        self.last_window_width = self.window_width
        self.last_window_height = self.window_height
        self.last_window_x = self.window_x
        self.last_window_y = self.window_y
        self.window_check_counter = 0
        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        hwnd = self.winId()
        try:
            
            curr_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            new_exstyle = curr_exstyle | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            
            new_exstyle |= getattr(win32con, 'WS_EX_TOOLWINDOW', 0)
            
            new_exstyle &= ~getattr(win32con, 'WS_EX_APPWINDOW', 0)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_exstyle)
            
            try:
                win32gui.SetWindowPos(int(hwnd), win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)
            except Exception:
                try:
                    
                    SWP_FLAGS = 0x0010 | 0x0001 | 0x0002 | 0x0040
                    win32gui.SetWindowPos(int(hwnd), -1, 0, 0, 0, 0, SWP_FLAGS)
                except Exception:
                    pass
        except Exception:
            
            try:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
            except Exception:
                pass

        self.file_watcher = QFileSystemWatcher([CONFIG_FILE])
        self.file_watcher.fileChanged.connect(self.reload_settings)

                                           
        self.offsets = offsets
        self.client_dll = client_dll
        
        import pymem
        import time
        self.pm = None
        self.client = None
        while self.pm is None or self.client is None:
            try:
                self.pm = pymem.Pymem("cs2.exe")
                self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            except Exception:
                self.pm = None
                self.client = None
                time.sleep(1)  
        

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, self.window_width, self.window_height)
        
                                                                     
        low_cpu_mode = self.settings.get('low_cpu', 0) == 1
        if not low_cpu_mode:
                                                                                                   
            self.view.setRenderHint(QtGui.QPainter.Antialiasing, True)
            self.view.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
            self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
            self.view.setRenderHint(QtGui.QPainter.LosslessImageRendering, True)
        else:
                                                  
            self.view.setRenderHint(QtGui.QPainter.Antialiasing, False)
            self.view.setRenderHint(QtGui.QPainter.TextAntialiasing, False)
            self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)
            self.view.setRenderHint(QtGui.QPainter.LosslessImageRendering, False)
        
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent;")
        self.view.setSceneRect(0, 0, self.window_width, self.window_height)
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)

                                                
        try:
                                                            
            self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.MinimalViewportUpdate)
        except Exception:
            try:
                self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
            except Exception:
                pass
        try:
                                                                          
            self.view.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        except Exception:
            pass

                                   
        try:
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
                                               
            self.setAttribute(QtCore.Qt.WA_NoBackground)
            self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
        except Exception:
            pass

        
        self._entity_items = {}

        self.timer = QtCore.QTimer(self)
        
        try:
            self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        except Exception:
            pass
        self.timer.timeout.connect(self.update_scene)
        
        self.timer.start(33)

        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
                                                   
        self.last_frame_time = time.time()
        self.target_fps = 60
        self.target_frame_time = 1.0 / 60.0

        
        try:
            self.apply_low_cpu_mode()
        except Exception:
            pass



    

    

    

    def reload_settings(self):
        # Load new settings with validation - prevent partial updates during load
        try:
            new_settings = load_settings()
        except Exception:
            # If loading fails, keep current settings
            return
        
        # Only update if settings actually changed and are valid
        if new_settings and isinstance(new_settings, dict) and len(new_settings) > 0:
            # Atomic settings update - merge with defaults to ensure completeness
            merged_settings = DEFAULT_SETTINGS.copy()
            merged_settings.update(new_settings)
            
            if merged_settings != self.settings:
                # Temporarily pause updates during settings change
                old_settings = self.settings
                self.settings = merged_settings
                
                # If settings update fails, rollback
                try:
                    self._perform_settings_dependent_updates()
                except Exception:
                    self.settings = old_settings
                    return
            else:
                return  # No change, skip the rest of reload
        else:
            # Invalid settings loaded, skip update
            return

    def _perform_settings_dependent_updates(self):
        """Perform all updates that depend on settings in a safe manner"""
        # Update window geometry based on current CS2 window
        current_x, current_y, current_width, current_height = get_window_client_rect("Counter-Strike 2")
        if current_width is not None and current_height is not None:
            self.window_x = current_x
            self.window_y = current_y
            self.window_width = current_width
            self.window_height = current_height
            self.last_window_x = current_x
            self.last_window_y = current_y
            self.last_window_width = current_width
            self.last_window_height = current_height
            self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
            try:
                self.view.setGeometry(0, 0, self.window_width, self.window_height)
                self.view.setSceneRect(0, 0, self.window_width, self.window_height)
            except Exception as view_error:
                pass
        
        # Update scene and apply low CPU mode settings
        self.update_scene()
        try:
            self.apply_low_cpu_mode()
        except Exception:
            pass
        


    def apply_low_cpu_mode(self):
        """Adjust internal timers/intervals for low CPU mode and FPS limit.

        This uses either low CPU mode (10 FPS) or the custom FPS limit setting.
        Low CPU mode overrides the FPS limit when enabled and disables high-quality rendering.
        """
        try:
            low = int(self.settings.get('low_cpu', 0)) if isinstance(self.settings, dict) else 0
            fps_limit = int(self.settings.get('fps_limit', 60)) if isinstance(self.settings, dict) else 60
            
                                                               
            if low:
                                                                       
                self.view.setRenderHint(QtGui.QPainter.Antialiasing, False)
                self.view.setRenderHint(QtGui.QPainter.TextAntialiasing, False)
                self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)
                self.view.setRenderHint(QtGui.QPainter.LosslessImageRendering, False)
                
                                                       
                self.target_fps = 10
                self.target_frame_time = 1.0 / 10.0                   
                                                                
                self.timer.start(100)
                                                                  
                self.setUpdatesEnabled(False)
                self.view.setOptimizationFlags(QtWidgets.QGraphicsView.DontAdjustForAntialiasing | 
                                              QtWidgets.QGraphicsView.DontSavePainterState)
                self.setUpdatesEnabled(True)
            else:
                                                                     
                self.view.setRenderHint(QtGui.QPainter.Antialiasing, True)
                self.view.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
                self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
                self.view.setRenderHint(QtGui.QPainter.LosslessImageRendering, True)
                
                self.target_fps = fps_limit
                self.target_frame_time = 1.0 / max(fps_limit, 1)
                                                                             
                                                                            
                if fps_limit < 80:
                    interval_ms = int(1000 / max(fps_limit, 1))                                          
                else:
                    interval_ms = max(int(1000 / max(fps_limit, 1)) - 3, 1)                                                 
                self.timer.start(interval_ms)
                                                          
                try:
                    self.view.setOptimizationFlags(QtWidgets.QGraphicsView.DontSavePainterState)
                except Exception:
                    pass
            
                                                                        
            if not hasattr(self, 'last_frame_time'):
                self.last_frame_time = time.time()
                
        except Exception:
            pass



    def check_and_update_window_size(self):
        """Check for CS2 window size and position changes and update overlay accordingly."""
        try:
                                                                           
            low_cpu_mode = int(self.settings.get('low_cpu', 0)) if isinstance(self.settings, dict) else 0
            fps_limit = int(self.settings.get('fps_limit', 60)) if isinstance(self.settings, dict) else 60
            
                                                                
                                                                       
            if low_cpu_mode:
                check_interval = 50                                    
            elif fps_limit >= 100:
                check_interval = 500                                     
            elif fps_limit >= 60:
                check_interval = 300                                   
            else:
                check_interval = 150                                   
            
            self.window_check_counter += 1
            if self.window_check_counter < check_interval:
                return False                       
            
                           
            self.window_check_counter = 0
            
                                                                            
                                                                                               
            try:
                                                                      
                current_x, current_y, current_width, current_height = get_window_client_rect("Counter-Strike 2")
                
                                                                                 
                if current_width is None or current_height is None:
                    return False
                
                                                                                                      
                size_threshold = 15                                                     
                if (abs(current_width - self.last_window_width) > size_threshold or 
                    abs(current_height - self.last_window_height) > size_threshold or
                    abs(current_x - self.last_window_x) > size_threshold or
                    abs(current_y - self.last_window_y) > size_threshold):
                    
                                                           
                    self.window_x = current_x
                    self.window_y = current_y
                    self.window_width = current_width
                    self.window_height = current_height
                    self.last_window_x = current_x
                    self.last_window_y = current_y
                    self.last_window_width = current_width
                    self.last_window_height = current_height
                    
                                                          
                    self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
                    
                                           
                    try:
                        self.view.setGeometry(0, 0, self.window_width, self.window_height)
                        self.view.setSceneRect(0, 0, self.window_width, self.window_height)
                                                                               
                        self.scene.clear()
                    except Exception:
                        pass
                    
                    return True                             
            except Exception:
                                                              
                pass
                
        except Exception:
            pass
            
        return False

    def update_scene(self):
        # Early validation: ensure settings are properly loaded
        if not hasattr(self, 'settings') or not self.settings:
            # Only load settings on first initialization, not during normal operation
            if not hasattr(self, '_initialization_complete'):
                self._initialization_complete = True
            return  # Skip this frame to prevent settings issues
                                                                 
        if not self.is_game_window_active():
            if hasattr(self, 'scene') and self.scene.items():
                self.scene.clear()
            return
            
                                                      
        if not hasattr(self, 'pm') or not hasattr(self, 'client') or self.pm is None or self.client is None:
            if hasattr(self, 'scene') and self.scene.items():
                self.scene.clear()
            return

                                                                   
                                                          
        current_time = time.time()
        if hasattr(self, 'target_fps') and hasattr(self, 'target_frame_time') and hasattr(self, 'last_frame_time'):
            if self.target_fps >= 80:                                       
                elapsed_time = current_time - self.last_frame_time
                if elapsed_time < self.target_frame_time * 0.85:                              
                    return
            self.last_frame_time = current_time

                                                                                      
        size_or_position_changed = self.check_and_update_window_size()

        # Final safety check: ensure settings are complete before rendering
        if not self.settings or not isinstance(self.settings, dict) or len(self.settings) == 0:
            return

                                       
        if hasattr(self, 'scene'):
            self.scene.clear()
        
        try:
                                                                                
            esp_enabled = self.settings.get('esp_rendering', 1) == 1
            radar_enabled = self.settings.get('radar_enabled', 0) == 1
            center_dot_enabled = self.settings.get('center_dot', 0) == 1
            aim_active = self.settings.get('aim_active', 0) == 1
            aim_circle_visible = self.settings.get('aim_circle_visible', 1) == 1
            
                                                                    
            if center_dot_enabled:
                render_center_dot(self.scene, self.window_width, self.window_height, self.settings)
            
            if aim_circle_visible:
                # Render Aim Radius
                render_aim_circle(self.scene, self.window_width, self.window_height, self.settings)
            
            # Render camera lock range lines if enabled
            camera_lock_range_lines_enabled = self.settings.get('camera_lock_draw_range_lines', 0) == 1
            if camera_lock_range_lines_enabled:
                render_camera_lock_range_lines(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
            # Render camera lock radius circle
            camera_lock_radius_enabled = self.settings.get('camera_lock_draw_radius', 0) == 1
            if camera_lock_radius_enabled:
                render_camera_lock_radius(self.scene, self.window_width, self.window_height, self.settings)
            
            if radar_enabled:
                render_radar(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
            if esp_enabled:
                esp(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
                                                              
            render_bomb_esp(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
                                                                                         
            self.frame_count += 1
            if current_time - self.last_time >= 1.0:
                                                          
                actual_elapsed = current_time - self.last_time
                self.fps = round(self.frame_count / actual_elapsed)
                self.frame_count = 0
                self.last_time = current_time
            
                                                                                 
            try:
                fps_font = QtGui.QFont('MS PGothic', 15, QtGui.QFont.Bold)
                fps_font.setHintingPreference(QtGui.QFont.PreferFullHinting)                         
                fps_item = self.scene.addText(f"OVERLAY | FPS: {self.fps}", fps_font)
                
                                                               
                if self.settings.get('rainbow_menu_theme', 0) == 1:
                    try:
                        rainbow_color_hex = self.settings.get('current_rainbow_color', '#FF0000')
                        theme_color = QtGui.QColor(rainbow_color_hex)
                    except Exception:
                        theme_color_hex = self.settings.get('menu_theme_color', '#FF0000')
                        theme_color = QtGui.QColor(theme_color_hex)
                else:
                    theme_color_hex = self.settings.get('menu_theme_color', '#FF0000')
                    theme_color = QtGui.QColor(theme_color_hex)
                fps_item.setDefaultTextColor(theme_color)
                fps_item.setPos(5, 5)
            except Exception:
                pass
            
        except Exception as e:
                                                          
            if not hasattr(self, '_last_error_time') or current_time - self._last_error_time > 5.0:
                pass
                self._last_error_time = current_time

    

    def is_game_window_active(self):
        """Check if CS2 or config UI is the currently active window"""
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            if not foreground_hwnd:
                return False
            
                                    
            cs2_hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
            if cs2_hwnd and cs2_hwnd == foreground_hwnd:
                return True
            
                                                          
            try:
                window_title = win32gui.GetWindowText(foreground_hwnd)
                if "Popsicle CS2 Config" in window_title:
                    return True
            except Exception:
                pass
            
            return False
        except Exception:
            return False

def render_center_dot(scene, window_width, window_height, settings):
    """Render center dot independently of ESP settings"""
    try:
        # Safety check: ensure settings are valid and complete
        if not settings or not isinstance(settings, dict):
            return
            
        center_dot_enabled = settings.get('center_dot', 0) == 1
        if center_dot_enabled:
            center_x = window_width / 2
            center_y = window_height / 2
            dot_size = settings.get('center_dot_size', 3)
            
                                       
            if settings.get('rainbow_center_dot', 0) == 1:
                try:
                    global RAINBOW_HUE_CENTER_DOT
                                                                    
                    RAINBOW_HUE_CENTER_DOT = (RAINBOW_HUE_CENTER_DOT + 0.005) % 1.0
                    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE_CENTER_DOT, 1.0, 1.0)]
                    dot_qcolor = QtGui.QColor(r, g, b)
                except Exception:
                    dot_hex = settings.get('center_dot_color', '#FFFFFF')
                    dot_qcolor = QtGui.QColor(dot_hex)
            else:
                dot_hex = settings.get('center_dot_color', '#FFFFFF')
                dot_qcolor = QtGui.QColor(dot_hex)
            
                                                            
            dot_rect = QtCore.QRectF(center_x - dot_size/2, center_y - dot_size/2, dot_size, dot_size)
            
                                                    
            dot_pen = QtGui.QPen(dot_qcolor, 1)
            dot_pen.setCapStyle(QtCore.Qt.RoundCap)
            
                                                      
            outline_color = QtGui.QColor(0, 0, 0, 128)                                  
            outline_pen = QtGui.QPen(outline_color, 1)
            outline_rect = QtCore.QRectF(center_x - (dot_size+2)/2, center_y - (dot_size+2)/2, dot_size+2, dot_size+2)
            scene.addEllipse(outline_rect, outline_pen, QtGui.QBrush(outline_color))
            
                                 
            scene.addEllipse(dot_rect, dot_pen, QtGui.QBrush(dot_qcolor))
    except Exception:
        pass

def render_aim_circle(scene, window_width, window_height, settings):
    """Render Aim Radius independently of ESP settings"""
    try:
        # Safety check: ensure settings are valid and complete
        if not settings or not isinstance(settings, dict):
            return
            
        aim_circle_visible = settings.get('aim_circle_visible', 1) == 1
        if aim_circle_visible and 'radius' in settings and settings.get('radius', 0) != 0:
            center_x = window_width / 2
            center_y = window_height / 2
            screen_radius = settings['radius'] / 100.0 * min(center_x, center_y)
            opacity = settings.get("circle_opacity", 16)
            
            global RAINBOW_HUE_FOV
            if settings.get('rainbow_fov', 0) == 1:
                try:
                                                                                           
                                                                                       
                    # FOV always updates its own hue when enabled
                    RAINBOW_HUE_FOV = (RAINBOW_HUE_FOV + 0.005) % 1.0
                    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE_FOV, 1.0, 1.0)]
                    aim_qcolor = QtGui.QColor(r, g, b)
                    aim_qcolor.setAlpha(opacity)
                except Exception:
                    aim_hex = settings.get('aim_circle_color', '#FF0000')
                    aim_qcolor = QtGui.QColor(aim_hex)
                    aim_qcolor.setAlpha(opacity)
            else:
                aim_hex = settings.get('aim_circle_color', '#FF0000')
                aim_qcolor = QtGui.QColor(aim_hex)
                aim_qcolor.setAlpha(opacity)
            
                                                
            circle_thickness = settings.get('circle_thickness', 2)
            
                                                            
            circle_pen = QtGui.QPen(aim_qcolor, circle_thickness)
            circle_pen.setCapStyle(QtCore.Qt.RoundCap)                                
            circle_pen.setJoinStyle(QtCore.Qt.RoundJoin)                
            
                                                     
            scene.addEllipse(
                QtCore.QRectF(center_x - screen_radius, center_y - screen_radius, screen_radius * 2, screen_radius * 2),
                circle_pen,
                QtCore.Qt.NoBrush
            )
    except Exception:
        pass

def render_camera_lock_range_lines(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    """Render horizontal lines showing camera lock target position and deadzone"""
    try:
        # Check if draw range lines is enabled
        if not settings.get('camera_lock_draw_range_lines', 0) == 1:
            return
        
        # Check if camera lock is enabled
        if not settings.get('camera_lock_enabled', 0) == 1:
            return
            
        # Check if trigger key is being held down
        trigger_key = settings.get('TriggerKey', 'X')
        trigger_vk = key_str_to_vk(trigger_key)
        
        # Only show lines if trigger key is being pressed
        if trigger_vk != 0:
            try:
                import win32api
                if not (win32api.GetAsyncKeyState(trigger_vk) & 0x8000):
                    return  # Trigger key is not being held
            except Exception:
                return  # Can't check key state, don't show lines
        else:
            return  # Invalid trigger key
            
        # Get camera lock tolerance (deadzone)
        tolerance = settings.get('camera_lock_tolerance', 5)
        
        # Find the actual camera lock target position using the same logic as camera_lock function
        target_y = None
        valid_target_found = False
        
        try:
            # Get view matrix and local player info
            view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]
            local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
            
            try:
                local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
            except:
                # If we can't get player info, don't show lines
                return
            
            # Scan for valid targets using same logic as camera_lock
            entity_list = pm.read_longlong(client + dwEntityList)
            entity_ptr = pm.read_longlong(entity_list + 0x10)
            
            closest_target = None
            min_distance = float('inf')
            center_x = window_width // 2
            center_y = window_height // 2
            
            for i in range(1, 64):
                try:
                    if entity_ptr == 0:
                        break

                    entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
                    if entity_controller == 0:
                        continue

                    entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
                    if entity_controller_pawn == 0:
                        continue

                    entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
                    if entity_list_pawn == 0:
                        continue

                    entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
                    if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                        continue

                    entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
                    
                    # Use esp_mode setting: 0 = enemies only, 1 = all players
                    esp_mode = settings.get('esp_mode', 0)
                    if esp_mode == 0 and entity_team == local_player_team:
                        continue  # Skip teammates when in enemies-only mode

                    entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
                    if entity_alive != 256:
                        continue

                    # Check spotted status if enabled
                    spotted_check_enabled = settings.get('camera_lock_spotted_check', 0) == 1
                    if spotted_check_enabled:
                        try:
                            spotted_flag = pm.read_int(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            is_spotted = spotted_flag != 0
                        except:
                            is_spotted = False
                        
                        # Skip non-spotted enemies when spotted check is enabled
                        if not is_spotted:
                            continue

                    # Get target bone position
                    game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                    bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)
                    
                    # Get selected bone ID from settings
                    target_bone_mode = settings.get('camera_lock_target_bone', 1)
                    target_bone_name = BONE_TARGET_MODES.get(target_bone_mode, {"bone": "head"}).get("bone", "head")
                    target_bone_id = bone_ids.get(target_bone_name, 6)  # Default to head (6) if not found
                    
                    # Get target bone position
                    target_x = pm.read_float(bone_matrix + target_bone_id * 0x20)
                    target_y_world = pm.read_float(bone_matrix + target_bone_id * 0x20 + 0x4)
                    target_z = pm.read_float(bone_matrix + target_bone_id * 0x20 + 0x8)
                    
                    # Project to screen
                    target_pos = w2s(view_matrix, target_x, target_y_world, target_z, window_width, window_height)
                    
                    # Only consider targets within screen bounds
                    if (target_pos[0] != -999 and target_pos[1] != -999 and
                        0 <= target_pos[0] <= window_width and 
                        0 <= target_pos[1] <= window_height):
                        
                        # Calculate distance from center of screen
                        dx = target_pos[0] - center_x
                        dy = target_pos[1] - center_y
                        distance = (dx * dx + dy * dy) ** 0.5
                        
                        # Check if radius targeting is enabled
                        use_radius = settings.get('camera_lock_use_radius', 0) == 1
                        if use_radius:
                            # Only consider targets within the radius
                            radius = settings.get('camera_lock_radius', 100)
                            if distance > radius:
                                continue  # Skip targets outside the radius
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_target = target_pos
                            valid_target_found = True
                            
                except Exception:
                    continue
            
            # Only proceed if we found a valid target
            if not valid_target_found or not closest_target:
                return  # No valid target found, don't show lines
                
            target_y = closest_target[1]  # Y coordinate of the target
                    
        except Exception:
            # If anything fails, don't show lines
            return
        
        # Calculate line positions based on target position and deadzone
        upper_line_y = target_y - tolerance
        lower_line_y = target_y + tolerance
        
        # Get theme color for the lines
        try:
            if settings.get('rainbow_menu_theme', 0) == 1:
                line_color_hex = settings.get('current_rainbow_color', '#FF0000')
            else:
                line_color_hex = settings.get('menu_theme_color', '#FF0000')
            line_color = QtGui.QColor(line_color_hex)
            line_color.setAlpha(180)  # Semi-transparent
        except Exception:
            line_color = QtGui.QColor('#FF0000')
            line_color.setAlpha(180)
            
        # Create pen for drawing lines - keep thickness constant and thin
        pen = QtGui.QPen(line_color)
        pen.setWidth(0.1)  # Thinnest possible thickness for deadzone lines
        pen.setStyle(QtCore.Qt.DashLine)
        
        # Calculate line width using user setting - control line length
        line_width_setting = settings.get('camera_lock_line_width', 2)
        line_width_multiplier = line_width_setting / 10.0  # Convert 1-10 to 0.1-1.0
        # Modified formula: smaller minimum (5%) and reduced scaling for shorter lines at low values
        line_width = window_width * (0.05 + line_width_multiplier * 0.3)  # 5% to 35% of screen width
        line_start_x = (window_width - line_width) / 2  # Center the lines
        line_end_x = line_start_x + line_width
        
        # Draw upper line
        if 0 <= upper_line_y <= window_height:
            upper_line = scene.addLine(line_start_x, upper_line_y, line_end_x, upper_line_y, pen)
            
        # Draw lower line  
        if 0 <= lower_line_y <= window_height:
            lower_line = scene.addLine(line_start_x, lower_line_y, line_end_x, lower_line_y, pen)
            
        # Draw center target line (solid) - same thickness as deadzone lines
        center_pen = QtGui.QPen(line_color)
        center_pen.setWidth(0)  # Thinnest possible thickness for center line
        center_pen.setStyle(QtCore.Qt.SolidLine)
        center_line = scene.addLine(line_start_x, target_y, line_end_x, target_y, center_pen)
        
    except Exception:
        pass

def render_camera_lock_radius(scene, window_width, window_height, settings):
    """Render camera lock radius circle"""
    try:
        # Check if draw radius is enabled
        if not settings.get('camera_lock_draw_radius', 0) == 1:
            return
        
        # Check if camera lock is enabled
        if not settings.get('camera_lock_enabled', 0) == 1:
            return
            
        # Get radius size
        radius = settings.get('camera_lock_radius', 100)
        
        # Calculate circle position (center of screen)
        center_x = window_width / 2
        center_y = window_height / 2
        
        # Get color for the circle
        try:
            if settings.get('rainbow_menu_theme', 0) == 1:
                circle_color_hex = settings.get('current_rainbow_color', '#FF0000')
            else:
                circle_color_hex = settings.get('camera_lock_radius_color', '#FF0000')
            circle_color = QtGui.QColor(circle_color_hex)
            circle_color.setAlpha(100)  # Semi-transparent
        except Exception:
            circle_color = QtGui.QColor('#FF0000')
            circle_color.setAlpha(100)
            
        # Create pen for drawing circle
        pen = QtGui.QPen(circle_color)
        pen.setWidth(0.1)  # Thinnest possible thickness for radius circle
        pen.setStyle(QtCore.Qt.DashLine)
        
        # Draw the radius circle
        scene.addEllipse(
            QtCore.QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2),
            pen,
            QtCore.Qt.NoBrush
        )
        
    except Exception:
        pass

def render_radar(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    """Render radar showing enemy positions"""
    try:
        # Safety check: ensure settings are valid and complete
        if not settings or not isinstance(settings, dict):
            return
            
        if not settings.get('radar_enabled', 0):
            return
            
                        
        radar_size = settings.get('radar_size', 200)
        radar_scale = settings.get('radar_scale', 5.0)
        radar_position = settings.get('radar_position', 'Top Right')
        radar_opacity = settings.get('radar_opacity', 180)
        
                                                   
        margin = 50                            
        if radar_position == 'Top Right':
            radar_x = window_width - radar_size - margin
            radar_y = margin
        elif radar_position == 'Top Left':
            radar_x = margin
            radar_y = margin
        elif radar_position == 'Bottom Right':
            radar_x = window_width - radar_size - margin
            radar_y = window_height - radar_size - margin
        elif radar_position == 'Bottom Left':
            radar_x = margin
            radar_y = window_height - radar_size - margin
        elif radar_position == 'Bottom Middle':
            radar_x = (window_width - radar_size) / 2
            radar_y = window_height - radar_size - margin
        elif radar_position == 'Center Right':
            radar_x = window_width - radar_size - margin
            radar_y = (window_height - radar_size) / 2
        elif radar_position == 'Center Left':
            radar_x = margin
            radar_y = (window_height - radar_size) / 2
        else:
                                                      
            radar_x = window_width - radar_size - margin
            radar_y = margin
        
                                                            
        radar_bg = QtGui.QColor(0, 0, 0, radar_opacity)
        
                                          
        if settings.get('rainbow_menu_theme', 0) == 1:
            try:
                rainbow_color_hex = settings.get('current_rainbow_color', '#FF0000')
                theme_color = QtGui.QColor(rainbow_color_hex)
            except Exception:
                theme_color_hex = settings.get('menu_theme_color', '#FF0000')
                theme_color = QtGui.QColor(theme_color_hex)
        else:
            theme_color_hex = settings.get('menu_theme_color', '#FF0000')
            theme_color = QtGui.QColor(theme_color_hex)
        theme_color.setAlpha(200)                                   
        radar_border = theme_color
        
                                                             
        radar_pen = QtGui.QPen(radar_border, 3)                  
        radar_pen.setCapStyle(QtCore.Qt.RoundCap)
        
                                 
        scene.addEllipse(
            QtCore.QRectF(radar_x, radar_y, radar_size, radar_size),
            radar_pen,
            QtGui.QBrush(radar_bg)
        )
        
                                     
        center_x = radar_x + radar_size / 2
        center_y = radar_y + radar_size / 2
        
                                                 
        player_color = QtGui.QColor(255, 255, 255, 255)                          
        player_outline = QtGui.QColor(0, 0, 0, 180)                 
        
                                                       
        scene.addEllipse(
            QtCore.QRectF(center_x - 4, center_y - 4, 8, 8),
            QtGui.QPen(player_outline, 1),
            QtGui.QBrush(player_outline)
        )
        scene.addEllipse(
            QtCore.QRectF(center_x - 3, center_y - 3, 6, 6),
            QtGui.QPen(player_color, 1),
            QtGui.QBrush(player_color)
        )
        
                                            
        
        local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
        if not local_player_pawn_addr:
            return
            
        try:
            local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
            local_game_scene = pm.read_longlong(local_player_pawn_addr + m_pGameSceneNode)
            local_x = pm.read_float(local_game_scene + m_vecAbsOrigin)
            local_y = pm.read_float(local_game_scene + m_vecAbsOrigin + 0x4)
            local_z = pm.read_float(local_game_scene + m_vecAbsOrigin + 0x8)                                           
            
                                                                              
            view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]
            
                                                                               
                                                                                  
                                                                                            
            forward_x = view_matrix[8]                        
            forward_y = view_matrix[9]                        
            
                                                                                   
            local_yaw = math.degrees(math.atan2(forward_x, -forward_y))
            
        except Exception:
                                                               
            local_yaw = 0.0
        
                         
        entity_list = pm.read_longlong(client + dwEntityList)
        entity_ptr = pm.read_longlong(entity_list + 0x10)
        
                                                                           
        max_radar_entities = 16 if settings.get('low_cpu', 0) == 1 else 32
        entities_processed = 0
        
                               
        for i in range(1, 64):
            if entities_processed >= max_radar_entities:
                break
                
            try:
                if entity_ptr == 0:
                    break

                entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
                if entity_controller == 0:
                    continue

                entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
                if entity_controller_pawn == 0:
                    continue

                entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
                if entity_list_pawn == 0:
                    continue

                entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
                if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                    continue

                                                   
                try:
                                                                  
                    entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
                    entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
                    entity_health = pm.read_int(entity_pawn_addr + m_iHealth)
                    
                                                                
                                                         
                                                     
                                                              
                                                                                    
                    if entity_alive != 256:
                        continue
                    if entity_health <= 0:
                        continue
                    if entity_team < 2 or entity_team > 3:                                        
                        continue
                    if entity_team == local_player_team:
                                                                      
                        esp_mode = settings.get('esp_mode', 0)
                        if esp_mode == 0:                     
                            continue
                    
                                                                                    
                    entity_game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                    if entity_game_scene == 0:
                        continue
                        
                    entity_x = pm.read_float(entity_game_scene + m_vecAbsOrigin)
                    entity_y = pm.read_float(entity_game_scene + m_vecAbsOrigin + 0x4)
                    entity_z = pm.read_float(entity_game_scene + m_vecAbsOrigin + 0x8)
                    
                                                                                    
                    if abs(entity_x) > 50000 or abs(entity_y) > 50000 or abs(entity_z) > 50000:
                        continue
                    if entity_x == 0.0 and entity_y == 0.0 and entity_z == 0.0:
                        continue
                        
                except Exception:
                                                                          
                    continue
                
                entities_processed += 1
                
                                             
                rel_x = (entity_x - local_x) / radar_scale
                rel_y = (entity_y - local_y) / radar_scale
                
                                                                                       
                try:
                                                                                                  
                    rotation_angle = math.radians(-local_yaw + 180)
                    cos_rot = math.cos(rotation_angle)
                    sin_rot = math.sin(rotation_angle)
                    
                                                                                     
                    rotated_x = rel_x * cos_rot - rel_y * sin_rot
                    rotated_y = rel_x * sin_rot + rel_y * cos_rot
                    
                                                  
                    radar_entity_x = center_x + rotated_x
                    radar_entity_y = center_y - rotated_y                                          
                except Exception:
                                                                           
                    radar_entity_x = center_x + rel_x
                    radar_entity_y = center_y - rel_y               
                
                                                        
                radar_radius = radar_size / 2
                distance_from_center = ((radar_entity_x - center_x) ** 2 + (radar_entity_y - center_y) ** 2) ** 0.5
                
                if distance_from_center <= radar_radius - 5:
                                                                                     
                    if entity_team == local_player_team:
                        entity_color = QtGui.QColor(0, 255, 0, 255)                       
                    else:
                        entity_color = QtGui.QColor(255, 0, 0, 255)                   
                    
                                                                                    
                    is_spotted = False
                    if entity_team != local_player_team:
                        try:
                            spotted_flag = pm.read_int(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            is_spotted = spotted_flag != 0
                        except Exception:
                            is_spotted = False
                    
                                                                    
                    try:
                        height_threshold = 50.0                                                                
                        height_diff = entity_z - local_z
                        is_height_different = abs(height_diff) > height_threshold
                        is_above = height_diff > 0
                    except Exception:
                        is_height_different = False
                        is_above = False
                    
                                                                      
                    if is_spotted and entity_team != local_player_team:
                        if is_height_different:
                                                                         
                            if is_above:
                                                      
                                outline_points = [
                                    QtCore.QPointF(radar_entity_x, radar_entity_y - 4),                 
                                    QtCore.QPointF(radar_entity_x - 4, radar_entity_y + 2),               
                                    QtCore.QPointF(radar_entity_x + 4, radar_entity_y + 2)                 
                                ]
                            else:
                                                        
                                outline_points = [
                                    QtCore.QPointF(radar_entity_x, radar_entity_y + 4),                    
                                    QtCore.QPointF(radar_entity_x - 4, radar_entity_y - 2),            
                                    QtCore.QPointF(radar_entity_x + 4, radar_entity_y - 2)              
                                ]
                            outline_polygon = QtGui.QPolygonF(outline_points)
                            outline_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 255), 2)
                            outline_pen.setCapStyle(QtCore.Qt.RoundCap)
                            outline_pen.setJoinStyle(QtCore.Qt.RoundJoin)
                            scene.addPolygon(
                                outline_polygon,
                                outline_pen,
                                QtCore.Qt.NoBrush
                            )
                        else:
                                                                                         
                            outline_rect = QtCore.QRectF(radar_entity_x - 4, radar_entity_y - 4, 8, 8)
                            outline_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 255), 2)
                            outline_pen.setCapStyle(QtCore.Qt.RoundCap)
                            scene.addEllipse(
                                outline_rect,
                                outline_pen,
                                QtCore.Qt.NoBrush
                            )
                    
                                                                                      
                    if is_height_different:
                                                                     
                        if is_above:
                                                            
                            arrow_points = [
                                QtCore.QPointF(radar_entity_x, radar_entity_y - 3),                 
                                QtCore.QPointF(radar_entity_x - 3, radar_entity_y + 1),               
                                QtCore.QPointF(radar_entity_x + 3, radar_entity_y + 1)                 
                            ]
                        else:
                                                              
                            arrow_points = [
                                QtCore.QPointF(radar_entity_x, radar_entity_y + 3),                    
                                QtCore.QPointF(radar_entity_x - 3, radar_entity_y - 1),            
                                QtCore.QPointF(radar_entity_x + 3, radar_entity_y - 1)              
                            ]
                        arrow_polygon = QtGui.QPolygonF(arrow_points)
                        arrow_pen = QtGui.QPen(entity_color, 1)
                        arrow_pen.setCapStyle(QtCore.Qt.RoundCap)
                        arrow_pen.setJoinStyle(QtCore.Qt.RoundJoin)
                        scene.addPolygon(
                            arrow_polygon,
                            arrow_pen,
                            QtGui.QBrush(entity_color)
                        )
                    else:
                                                                    
                        dot_rect = QtCore.QRectF(radar_entity_x - 3, radar_entity_y - 3, 6, 6)
                        dot_pen = QtGui.QPen(entity_color, 1)
                        dot_pen.setCapStyle(QtCore.Qt.RoundCap)
                        scene.addEllipse(
                            dot_rect,
                            dot_pen,
                            QtGui.QBrush(entity_color)
                        )
                    
            except Exception:
                continue
                
    except Exception:
        pass

def render_bomb_esp(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    """Render bomb ESP independently of main ESP"""
    try:
        # Safety check: ensure settings are valid and complete
        if not settings or not isinstance(settings, dict):
            return
            
        bomb_esp_enabled = settings.get('bomb_esp', 0) == 1
        if not bomb_esp_enabled:
            return
            
                                    
                                                        
        view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]

        def bombisplant():
            global BombPlantedTime
            bombisplant = pm.read_bool(client + dwPlantedC4 - 0x8)
            if bombisplant:
                if (BombPlantedTime == 0):
                    BombPlantedTime = time.time()
            else:
                BombPlantedTime = 0
            return bombisplant
        
        def getC4BaseClass():
            plantedc4 = pm.read_longlong(client + dwPlantedC4)
            plantedc4class = pm.read_longlong(plantedc4)
            return plantedc4class
        
        def getPositionWTS():
            c4node = pm.read_longlong(getC4BaseClass() + m_pGameSceneNode)
            c4posX = pm.read_float(c4node + m_vecAbsOrigin)
            c4posY = pm.read_float(c4node + m_vecAbsOrigin + 0x4)
            c4posZ = pm.read_float(c4node + m_vecAbsOrigin + 0x8)
            bomb_pos = w2s(view_matrix, c4posX, c4posY, c4posZ, window_width, window_height)
            return bomb_pos
        
        def getBombTime():
            BombTime = pm.read_float(getC4BaseClass() + m_flTimerLength) - (time.time() - BombPlantedTime)
            return BombTime if (BombTime >= 0) else 0
        
        def isBeingDefused():
            global BombDefusedTime
            BombIsDefused = pm.read_bool(getC4BaseClass() + m_bBeingDefused)
            if (BombIsDefused):
                if (BombDefusedTime == 0):
                    BombDefusedTime = time.time() 
            else:
                BombDefusedTime = 0
            return BombIsDefused
        
        def getDefuseTime():
            DefuseTime = pm.read_float(getC4BaseClass() + m_flDefuseLength) - (time.time() - BombDefusedTime)
            return DefuseTime if (isBeingDefused() and DefuseTime >= 0) else 0

        bfont = QtGui.QFont('MS PGothic', 10, QtGui.QFont.Bold)
        bfont.setHintingPreference(QtGui.QFont.PreferFullHinting)                         

                            
        if bombisplant():
            BombPosition = getPositionWTS()
            BombTime = getBombTime()
            DefuseTime = getDefuseTime()
        
            if (BombPosition[0] > 0 and BombPosition[1] > 0):
                                                            
                if DefuseTime > 0:
                    bomb_text = f'BOMB: {round(BombTime, 2)} | DEFUSE: {round(DefuseTime, 2)}'
                    # Determine text color based on bomb time vs defuse time
                    if BombTime < DefuseTime:
                        text_color = QtGui.QColor(255, 0, 0)  # Red - bomb will explode before defuse finishes
                    elif BombTime > DefuseTime:
                        text_color = QtGui.QColor(0, 255, 0)  # Green - defuse will finish before bomb explodes
                    else:
                        text_color = QtGui.QColor(255, 255, 0)  # Yellow - exact timing (very rare)
                else:
                    bomb_text = f'BOMB: {round(BombTime, 2)}'
                    text_color = QtGui.QColor(255, 255, 255)  # White - no defuse
                
                c4_name_x = BombPosition[0]
                c4_name_y = BombPosition[1]
                
                                                                               
                stroke_offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
                for offset_x, offset_y in stroke_offsets:
                    stroke_text = scene.addText(bomb_text, bfont)
                    stroke_text.setPos(c4_name_x + offset_x, c4_name_y + offset_y)
                    stroke_text.setDefaultTextColor(QtGui.QColor(0, 0, 0))                
                
                                            
                c4_name_text = scene.addText(bomb_text, bfont)
                c4_name_text.setPos(c4_name_x, c4_name_y)
                c4_name_text.setDefaultTextColor(text_color)
                
    except Exception:
        pass

def esp(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    # Safety check: ensure settings are valid and complete
    if not settings or not isinstance(settings, dict):
        return
                                   
    if settings.get('esp_rendering', 1) == 0:
        return
    
                                                        
    esp_mode = settings.get('esp_mode', 1)
    
                                                     
    box_rendering = settings.get('box_rendering', 1) == 1
    line_rendering = settings.get('line_rendering', 1) == 1
    hp_bar_rendering = settings.get('hp_bar_rendering', 1) == 1
    head_hitbox_rendering = settings.get('head_hitbox_rendering', 1) == 1
    bones_rendering = settings.get('Bones', 0) == 1
    nickname_rendering = settings.get('nickname', 0) == 1
    
                                                                
    if not (box_rendering or line_rendering or hp_bar_rendering or head_hitbox_rendering or 
            bones_rendering or nickname_rendering):
        return
    
                                                    
    try:
        team_hex = settings.get('team_color', '#47A76A')
        enemy_hex = settings.get('enemy_color', '#C41E3A')
        team_color = QtGui.QColor(team_hex)
        enemy_color = QtGui.QColor(enemy_hex)
    except Exception:
        team_color = QtGui.QColor(71, 167, 106)
        enemy_color = QtGui.QColor(196, 30, 58)

                                          
    view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]

    local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
    try:
        local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
    except:
        return

    no_center_x = window_width / 2
    lines_position = settings.get('lines_position', 'Bottom')
    if lines_position == 'Top':
        no_center_y = 0  # Top of screen
    else:
        no_center_y = window_height  # Very bottom of screen (default)
    entity_list = pm.read_longlong(client + dwEntityList)
    entity_ptr = pm.read_longlong(entity_list + 0x10)

    for i in range(1, 64):
        try:
            if entity_ptr == 0:
                break

            entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
            if entity_controller == 0:
                continue

            entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
            if entity_controller_pawn == 0:
                continue

            entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
            if entity_list_pawn == 0:
                continue

            entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
            if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                continue

            entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
            if entity_team == local_player_team and esp_mode == 0:
                continue

            entity_hp = pm.read_int(entity_pawn_addr + m_iHealth)
            if entity_hp <= 0:
                continue

            entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
            if entity_alive != 256:
                continue
            
                                                            
            armor_hp = 0
            if hp_bar_rendering:
                armor_hp = pm.read_int(entity_pawn_addr + m_ArmorValue)
            
                                      
            color = team_color if entity_team == local_player_team else enemy_color
            
                                                           
            game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
            bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)

            try:
                                          
                headX = pm.read_float(bone_matrix + 6 * 0x20)
                headY = pm.read_float(bone_matrix + 6 * 0x20 + 0x4)
                headZ = pm.read_float(bone_matrix + 6 * 0x20 + 0x8) + 8
                legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                
                                                 
                head_pos = w2s(view_matrix, headX, headY, headZ, window_width, window_height)
                if head_pos[1] < 0:
                    continue
                    
                leg_pos = w2s(view_matrix, headX, headY, legZ, window_width, window_height)
                deltaZ = abs(head_pos[1] - leg_pos[1])
                leftX = head_pos[0] - deltaZ // 4
                rightX = head_pos[0] + deltaZ // 4
                
                                        
                if line_rendering:
                    # Choose connection point based on lines position setting
                    if lines_position == 'Top':
                        # Connect to top of ESP box
                        connection_x = head_pos[0]
                        connection_y = head_pos[1]  # This is already the top of the ESP box
                    else:
                        # Connect to bottom of player (feet) - default behavior
                        connection_x = head_pos[0] - (head_pos[0] - leg_pos[0]) // 2
                        connection_y = leg_pos[1]
                    
                                                              
                    line_pen = QtGui.QPen(color, 1.5)                       
                    line_pen.setCapStyle(QtCore.Qt.RoundCap)                                  
                    line = scene.addLine(connection_x, connection_y, no_center_x, no_center_y, line_pen)
                
                                       
                if box_rendering:
                                                                     
                    box_pen = QtGui.QPen(color, 0.5)                                             
                    box_pen.setCapStyle(QtCore.Qt.SquareCap)                                  
                    box_pen.setJoinStyle(QtCore.Qt.MiterJoin)
                    
                    # Check box mode setting - force 2D if low CPU mode is enabled
                    low_cpu_enabled = settings.get('low_cpu', 0) == 1
                    box_mode = '2D' if low_cpu_enabled else settings.get('box_mode', '2D')
                    
                    if box_mode == '3D':
                        # True 3D bounding box - define player dimensions in game units
                        player_width = 32.0    # CS2 player width in game units
                        player_length = 32.0   # CS2 player depth in game units  
                        player_height = 72.0   # CS2 player height in game units
                        
                        # Get player's 3D position
                        try:
                            player_origin_addr = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                            origin_x = pm.read_float(player_origin_addr + m_vecAbsOrigin)
                            origin_y = pm.read_float(player_origin_addr + m_vecAbsOrigin + 4)
                            origin_z = pm.read_float(player_origin_addr + m_vecAbsOrigin + 8)
                            
                            # Define 8 corners of 3D bounding box around player
                            half_width = player_width / 2
                            half_length = player_length / 2
                            
                            # Bottom face corners (at player's feet)
                            bottom_corners = [
                                (origin_x - half_width, origin_y - half_length, origin_z),  # Bottom front-left
                                (origin_x + half_width, origin_y - half_length, origin_z),  # Bottom front-right
                                (origin_x + half_width, origin_y + half_length, origin_z),  # Bottom back-right
                                (origin_x - half_width, origin_y + half_length, origin_z),  # Bottom back-left
                            ]
                            
                            # Top face corners (at player's head)
                            top_corners = [
                                (origin_x - half_width, origin_y - half_length, origin_z + player_height),  # Top front-left
                                (origin_x + half_width, origin_y - half_length, origin_z + player_height),  # Top front-right
                                (origin_x + half_width, origin_y + half_length, origin_z + player_height),  # Top back-right
                                (origin_x - half_width, origin_y + half_length, origin_z + player_height),  # Top back-left
                            ]
                            
                            # Project all 8 corners to screen coordinates
                            bottom_screen = []
                            top_screen = []
                            
                            all_corners_valid = True
                            for corner in bottom_corners:
                                screen_x, screen_y = w2s(view_matrix, corner[0], corner[1], corner[2], window_width, window_height)
                                if screen_x == -999:
                                    all_corners_valid = False
                                    break
                                bottom_screen.append((screen_x, screen_y))
                                
                            if all_corners_valid:
                                for corner in top_corners:
                                    screen_x, screen_y = w2s(view_matrix, corner[0], corner[1], corner[2], window_width, window_height)
                                    if screen_x == -999:
                                        all_corners_valid = False
                                        break
                                    top_screen.append((screen_x, screen_y))
                            
                            # Draw the 3D bounding box if all corners are valid
                            if all_corners_valid:
                                # Draw bottom face edges
                                for i in range(4):
                                    next_i = (i + 1) % 4
                                    scene.addLine(bottom_screen[i][0], bottom_screen[i][1], 
                                                bottom_screen[next_i][0], bottom_screen[next_i][1], box_pen)
                                
                                # Draw top face edges  
                                for i in range(4):
                                    next_i = (i + 1) % 4
                                    scene.addLine(top_screen[i][0], top_screen[i][1],
                                                top_screen[next_i][0], top_screen[next_i][1], box_pen)
                                
                                # Draw vertical edges connecting bottom to top
                                for i in range(4):
                                    scene.addLine(bottom_screen[i][0], bottom_screen[i][1],
                                                top_screen[i][0], top_screen[i][1], box_pen)
                            else:
                                # Fallback to 2D box if 3D projection fails
                                scene.addRect(QtCore.QRectF(leftX, head_pos[1], rightX - leftX, leg_pos[1] - head_pos[1]), box_pen, QtCore.Qt.NoBrush)
                                
                        except Exception:
                            # Fallback to 2D box if 3D calculation fails
                            scene.addRect(QtCore.QRectF(leftX, head_pos[1], rightX - leftX, leg_pos[1] - head_pos[1]), box_pen, QtCore.Qt.NoBrush)
                    else:
                        # 2D box mode (default)
                        scene.addRect(QtCore.QRectF(leftX, head_pos[1], rightX - leftX, leg_pos[1] - head_pos[1]), box_pen, QtCore.Qt.NoBrush)                                          
                if hp_bar_rendering:
                    max_hp = 100
                    hp_percentage = min(1.0, max(0.0, entity_hp / max_hp))
                    
                    # Horizontal HP bar under player
                    hp_bar_width = (rightX - leftX) + 10  # Extended width (5px on each side)
                    hp_bar_height = 3  # Fixed height for horizontal bar
                    hp_bar_x_left = leftX - 5  # Start 5px to the left
                    hp_bar_y_top = leg_pos[1] + 5  # Position under player feet
                    
                    # HP bar background (smaller outline)
                    bg_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180), 1)
                    hp_bar_bg = scene.addRect(QtCore.QRectF(hp_bar_x_left-0.5, hp_bar_y_top-0.5, hp_bar_width+1, hp_bar_height+1), bg_pen, QtGui.QColor(0, 0, 0, 120))
                    
                    # HP color based on percentage
                    hp_color = QtGui.QColor()
                    if hp_percentage > 0.6:
                        hp_color.setRgb(int(255*(1-hp_percentage)), 255, 0)                   
                    elif hp_percentage > 0.3:
                        hp_color.setRgb(255, int(255*hp_percentage/0.6), 0)                 
                    else:
                        hp_color.setRgb(255, 0, 0)       
                    
                    # Current HP bar (fills from left to right)
                    current_hp_width = hp_bar_width * hp_percentage
                    hp_bar_current = scene.addRect(QtCore.QRectF(hp_bar_x_left, hp_bar_y_top, current_hp_width, hp_bar_height), QtGui.QPen(QtCore.Qt.NoPen), hp_color)
                    
                    # Armor bar (if armor exists, place it below HP bar)
                    if armor_hp > 0:
                        max_armor_hp = 100
                        armor_hp_percentage = min(1.0, max(0.0, armor_hp / max_armor_hp))
                        
                        # Horizontal armor bar below HP bar
                        armor_bar_width = (rightX - leftX) + 10  # Extended width (5px on each side)
                        armor_bar_height = 3  # Fixed height for horizontal bar
                        armor_bar_x_left = leftX - 5  # Start 5px to the left
                        armor_bar_y_top = hp_bar_y_top + hp_bar_height + 2  # Below HP bar with 2px gap
                        
                        # Armor bar background (smaller outline)
                        armor_bg_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180), 1)
                        armor_bar_bg = scene.addRect(QtCore.QRectF(armor_bar_x_left-0.5, armor_bar_y_top-0.5, armor_bar_width+1, armor_bar_height+1), armor_bg_pen, QtGui.QColor(0, 0, 0, 120))
                        
                        # Current armor bar (fills from left to right)
                        current_armor_width = armor_bar_width * armor_hp_percentage
                        armor_color = QtGui.QColor(100, 149, 237)                   
                        armor_bar_current = scene.addRect(QtCore.QRectF(armor_bar_x_left, armor_bar_y_top, current_armor_width, armor_bar_height), QtGui.QPen(QtCore.Qt.NoPen), armor_color)

                                               
                if head_hitbox_rendering:
                    head_hitbox_size = (rightX - leftX) / 5
                    head_hitbox_radius = head_hitbox_size * 2 ** 0.5 / 2
                    head_hitbox_x = leftX + 2.5 * head_hitbox_size
                    head_hitbox_y = head_pos[1] + deltaZ / 9
                    
                                                    
                    hitbox_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 2)
                    hitbox_pen.setCapStyle(QtCore.Qt.RoundCap)
                    hitbox_color = QtGui.QColor(255, 0, 0, 100)                        
                    ellipse = scene.addEllipse(QtCore.QRectF(head_hitbox_x - head_hitbox_radius, head_hitbox_y - head_hitbox_radius, head_hitbox_radius * 2, head_hitbox_radius * 2), hitbox_pen, hitbox_color)

                                         
                if bones_rendering:
                    draw_Bones(scene, pm, bone_matrix, view_matrix, window_width, window_height, settings)

                                                     
                if nickname_rendering:
                    player_name = pm.read_string(entity_controller + m_iszPlayerName, 32)
                    font_size = max(6, min(18, deltaZ / 25))
                    font = QtGui.QFont('MS PGothic', font_size, QtGui.QFont.Bold)
                    font.setHintingPreference(QtGui.QFont.PreferFullHinting)                         
                    name_text = scene.addText(player_name, font)
                    text_rect = name_text.boundingRect()
                    name_x = head_pos[0] - text_rect.width() / 2
                    name_y = head_pos[1] - text_rect.height()
                    name_text.setPos(name_x, name_y)
                    
                                                            
                    name_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                    
                                               
                    shadow_text = scene.addText(player_name, font)
                    shadow_text.setPos(name_x + 1, name_y + 1)
                    shadow_text.setDefaultTextColor(QtGui.QColor(0, 0, 0, 150))
                    shadow_text.setZValue(-1)                               
                
                                                                            
                if settings.get('show_visibility', 0) == 1:
                    try:
                        try:
                            spotted_flag = pm.read_int(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            is_spotted = spotted_flag != 0
                        except Exception:
                                                   
                            try:
                                is_spotted = pm.read_bool(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            except Exception:
                                is_spotted = False
                        vis_text = "(Spotted)" if is_spotted else "(Not Spotted)"
                        
                        font_size = max(6, min(18, deltaZ / 25))
                        vis_font = QtGui.QFont('MS PGothic', max(5, min(14, font_size)))
                        vis_font.setBold(True)
                        vis_font.setHintingPreference(QtGui.QFont.PreferFullHinting)                         
                        vis_item = scene.addText(vis_text, vis_font)
                        vrect = vis_item.boundingRect()
                        vis_x = head_pos[0] - vrect.width() / 2
                        
                                                                                    
                        if nickname_rendering:
                                                                                 
                            name_y = head_pos[1] - 20                                 
                            vis_y = name_y - 15
                        else:
                                                                             
                            vis_y = head_pos[1] - 20
                        
                        vis_item.setPos(vis_x, vis_y)
                        
                        if is_spotted:
                            vis_item.setDefaultTextColor(QtGui.QColor(0, 200, 0))
                        else:
                            vis_item.setDefaultTextColor(QtGui.QColor(200, 0, 0))
                    except Exception:
                        pass
                    
                                                   
                    
                    
                    
                    


            except:
                return
        except:
            return

def draw_Bones(scene, pm, bone_matrix, view_matrix, width, height, settings):
    bone_ids = {
        "head": 6,
        "neck": 5,
        "spine": 4,
        "pelvis": 0,
        "left_shoulder": 13,
        "left_elbow": 14,
        "left_wrist": 15,
        "right_shoulder": 9,
        "right_elbow": 10,
        "right_wrist": 11,
        "left_hip": 25,
        "left_knee": 26,
        "left_ankle": 27,
        "right_hip": 22,
        "right_knee": 23,
        "right_ankle": 24,
    }
    bone_connections = [
        ("head", "neck"),
        ("neck", "spine"),
        ("spine", "pelvis"),
        ("pelvis", "left_hip"),
        ("left_hip", "left_knee"),
        ("left_knee", "left_ankle"),
        ("pelvis", "right_hip"),
        ("right_hip", "right_knee"),
        ("right_knee", "right_ankle"),
        ("neck", "left_shoulder"),
        ("left_shoulder", "left_elbow"),
        ("left_elbow", "left_wrist"),
        ("neck", "right_shoulder"),
        ("right_shoulder", "right_elbow"),
        ("right_elbow", "right_wrist"),
    ]
    bone_positions = {}
    try:
        for bone_name, bone_id in bone_ids.items():
            boneX = pm.read_float(bone_matrix + bone_id * 0x20)
            boneY = pm.read_float(bone_matrix + bone_id * 0x20 + 0x4)
            boneZ = pm.read_float(bone_matrix + bone_id * 0x20 + 0x8)
            bone_pos = w2s(view_matrix, boneX, boneY, boneZ, width, height)
            if bone_pos[0] != -999 and bone_pos[1] != -999:
                bone_positions[bone_name] = bone_pos
        for connection in bone_connections:
            if connection[0] in bone_positions and connection[1] in bone_positions:
                skeleton_hex = settings.get('skeleton_color', '#FFFFFF')
                skeleton_color = QtGui.QColor(skeleton_hex)
                scene.addLine(
                    bone_positions[connection[0]][0], bone_positions[connection[0]][1],
                    bone_positions[connection[1]][0], bone_positions[connection[1]][1],
                    QtGui.QPen(skeleton_color, 1)
                )
    except Exception as e:
        pass

def esp_main():
    try:
        # Load settings with retry logic to ensure config is ready
        settings = None
        for attempt in range(5):  # Try up to 5 times instead of 3
            try:
                settings = load_settings()
                # Validate that settings are complete and valid
                if settings and isinstance(settings, dict) and len(settings) >= len(DEFAULT_SETTINGS) // 2:
                    # Ensure all critical settings exist by merging with defaults
                    complete_settings = DEFAULT_SETTINGS.copy()
                    complete_settings.update(settings)
                    settings = complete_settings
                    break
            except Exception:
                settings = None
            time.sleep(0.2)  # Longer delay between attempts
        
        if not settings:
            settings = DEFAULT_SETTINGS.copy()
            # Try to save default settings to ensure config file exists
            try:
                save_settings(settings)
            except Exception:
                pass
        
        app = QtWidgets.QApplication(sys.argv)
        
        
        window_width = None
        window_height = None
        pm = None
        client = None
        while True:
            
            w, h = get_window_size("Counter-Strike 2")
            if w is not None and h is not None:
                window_width, window_height = w, h
            
                                                     
            if is_cs2_running():
                try:
                    pm = pymem.Pymem("cs2.exe")
                    try:
                        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                    except Exception:
                        client = None
                except Exception:
                    pm = None
            else:
                pm = None
                client = None
        
            
            if window_width and window_height and pm is not None and client is not None:
                break
            time.sleep(1)

        
        window = ESPWindow(settings, window_width=window_width, window_height=window_height)
        
        try:
                                               
            window.offsets = offsets
            window.client_dll = client_dll
            window.pm = pm
            window.client = client
        except Exception:
                   pass

        window.show()
        sys.exit(app.exec())
    except Exception as e:
        app_title = get_app_title()
        ctypes.windll.user32.MessageBoxW(0, f"An error occured: {str(e)}", app_title, 0x00000000 | 0x00010000 | 0x00040000)
        try:
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('error')
        except:
            pass
        sys.exit(0)

def triggerbot():
    from pynput.mouse import Controller, Button
    mouse = Controller()
    default_settings = {
        "TriggerKey": "X",
        "trigger_bot_active":  1,
        "esp_mode": 1,
        "triggerbot_head_only": 0,
        "triggerbot_between_shots_delay": 30,
        "triggerbot_burst_mode": 0,
        "triggerbot_burst_shots": 3,
        "triggerbot_first_shot_delay": 0
    }

    def load_settings():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return default_settings

    def _check_target_valid(pm, client, head_only):
        """Helper function to check if current target is still valid for shooting"""
        try:
            player = pm.read_longlong(client + dwLocalPlayerPawn)
            entityId = pm.read_int(player + m_iIDEntIndex)
            if entityId <= 0:
                return False
                
            entList = pm.read_longlong(client + dwEntityList)
            entEntry = pm.read_longlong(entList + 0x8 * (entityId >> 9) + 0x10)
            entity = pm.read_longlong(entEntry + 0x78 * (entityId & 0x1FF))
            entityTeam = pm.read_int(entity + m_iTeamNum)
            playerTeam = pm.read_int(player + m_iTeamNum)
            
            if entityTeam == playerTeam:
                return False
                
            entityHp = pm.read_int(entity + m_iHealth)
            if entityHp <= 0:
                return False
                
            # Head-only check
            if head_only:
                view_matrix = []
                for i in range(16):
                    view_matrix.append(pm.read_float(client + dwViewMatrix + i * 4))
                
                w, h = get_window_size("Counter-Strike 2")
                if w is not None and h is not None:
                    bone_ptr = pm.read_longlong(entity + m_pGameSceneNode)
                    if bone_ptr:
                        bone_matrix = pm.read_longlong(bone_ptr + m_modelState + 0x80)
                        if bone_matrix:
                            head_id = 6
                            head_x = pm.read_float(bone_matrix + head_id * 0x20)
                            head_y = pm.read_float(bone_matrix + head_id * 0x20 + 0x4)
                            head_z = pm.read_float(bone_matrix + head_id * 0x20 + 0x8)
                            sx, sy = w2s(view_matrix, head_x, head_y, head_z, w, h)
                            
                            if sx != -999 and sy != -999:
                                cx, cy = w // 2, h // 2
                                distance_to_head = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
                                return distance_to_head <= 8
                return False
            
            return True
        except Exception:
            return False

    def main(settings):
        pm = None
        client = None
        
        # Triggerbot state tracking
        trigger_key_pressed = False
        first_shot_time = None
        burst_shot_count = 0  # Track shots fired in current burst
        last_burst_time = 0   # Track time of last burst
        
        while pm is None or client is None:
            if is_cs2_running():
                try:
                    pm = pymem.Pymem("cs2.exe")
                    client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                except Exception:
                    pm = None
                    client = None
                    time.sleep(1)
            else:
                pm = None
                client = None
                time.sleep(1)
        while True:
            try:
                # Triggerbot settings
                trigger_bot_active = settings.get("trigger_bot_active", 0)
                keyboards = settings.get("TriggerKey", "X")
                between_shots_delay_ms = settings.get("triggerbot_between_shots_delay", 30)
                first_shot_delay_ms = settings.get("triggerbot_first_shot_delay", 0)
                burst_mode = settings.get("triggerbot_burst_mode", 0)
                burst_shots = settings.get("triggerbot_burst_shots", 3)
                head_only_mode = settings.get("triggerbot_head_only", 0)
                vk = key_str_to_vk(keyboards)
                
                # Check triggerbot key state
                if is_keybind_on_global_cooldown("TriggerKey"):
                    key_currently_pressed = False
                else:
                    key_currently_pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                
                # Handle triggerbot key transitions
                if key_currently_pressed and not trigger_key_pressed:
                    trigger_key_pressed = True
                    first_shot_time = time.time()
                elif not key_currently_pressed and trigger_key_pressed:
                    trigger_key_pressed = False
                    first_shot_time = None
                
                # Process regular triggerbot
                if key_currently_pressed and trigger_bot_active == 1:
                    try:
                        player = pm.read_longlong(client + dwLocalPlayerPawn)
                        entityId = pm.read_int(player + m_iIDEntIndex)
                        
                        if entityId > 0:
                            entList = pm.read_longlong(client + dwEntityList)
                            entEntry = pm.read_longlong(entList + 0x8 * (entityId >> 9) + 0x10)
                            entity = pm.read_longlong(entEntry + 0x78 * (entityId & 0x1FF))
                            entityTeam = pm.read_int(entity + m_iTeamNum)
                            playerTeam = pm.read_int(player + m_iTeamNum)
                            entityHp = pm.read_int(entity + m_iHealth)
                            
                            if entityTeam != playerTeam and entityHp > 0:
                                should_shoot = False
                                
                                if head_only_mode:
                                    # Head-only mode - check if crosshair is on head
                                    try:
                                        view_matrix = []
                                        for i in range(16):
                                            view_matrix.append(pm.read_float(client + dwViewMatrix + i * 4))
                                        
                                        w, h = get_window_size("Counter-Strike 2")
                                        if w is not None and h is not None:
                                            bone_ptr = pm.read_longlong(entity + m_pGameSceneNode)
                                            if bone_ptr:
                                                bone_matrix = pm.read_longlong(bone_ptr + m_modelState + 0x80)
                                                if bone_matrix:
                                                    head_id = 6
                                                    head_x = pm.read_float(bone_matrix + head_id * 0x20)
                                                    head_y = pm.read_float(bone_matrix + head_id * 0x20 + 0x4)
                                                    head_z = pm.read_float(bone_matrix + head_id * 0x20 + 0x8)
                                                    sx, sy = w2s(view_matrix, head_x, head_y, head_z, w, h)
                                                    
                                                    if sx != -999 and sy != -999:
                                                        cx, cy = w // 2, h // 2
                                                        distance_to_head = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
                                                        if distance_to_head <= 8:
                                                            should_shoot = True
                                    except Exception:
                                        pass
                                else:
                                    # Normal mode - shoot at any enemy body part
                                    should_shoot = True
                                
                                if should_shoot:
                                    current_time = time.time()
                                    
                                    # Handle first shot delay
                                    if first_shot_time is None or current_time - first_shot_time >= (first_shot_delay_ms / 1000.0):
                                        if not burst_mode:
                                            # Normal mode - continuous shooting with delay
                                            try:
                                                mouse.press(Button.left)
                                                mouse.release(Button.left)
                                                if first_shot_time is not None:
                                                    first_shot_time = None                          
                                                last_shot_time = current_time
                                                
                                                # Continue shooting while key is held
                                                while key_currently_pressed and trigger_bot_active == 1:
                                                    time.sleep(0.001)                     
                                                    current_time = time.time()
                                                    if current_time - last_shot_time >= (between_shots_delay_ms / 1000.0):
                                                        key_currently_pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                                                        if not key_currently_pressed:
                                                            break
                                                        trigger_bot_active = settings.get("trigger_bot_active", 0)
                                                        if trigger_bot_active != 1:
                                                            break
                                                        
                                                        # Re-check target validity for continuous shooting
                                                        if not _check_target_valid(pm, client, head_only_mode):
                                                            break
                                                            
                                                        mouse.press(Button.left)
                                                        mouse.release(Button.left)
                                                        last_shot_time = current_time
                                            except Exception:
                                                pass
                                        else:
                                            # Burst mode - fire exact number of shots specified
                                            try:
                                                # Check if enough time has passed since last burst
                                                if burst_shot_count == 0 or current_time - last_burst_time >= (between_shots_delay_ms / 1000.0):
                                                    # Click mouse exactly burst_shots times
                                                    actual_clicks = 0
                                                    i = 0
                                                    while i < burst_shots:
                                                        mouse.click(Button.left)
                                                        actual_clicks += 1
                                                        i += 1
                                                        # Delay between clicks to ensure CS2 registers them
                                                        if i < burst_shots:
                                                            time.sleep(0.1)
                                                    
                                                    # Mark burst as completed
                                                    burst_shot_count = actual_clicks
                                                    last_burst_time = current_time
                                                    if first_shot_time is not None:
                                                        first_shot_time = None
                                            except Exception:
                                                pass
                    except Exception:
                        pass
                
                # Reload settings every 10 loops to pick up config changes
                settings = load_settings()
                        
            except Exception:
                pass
            
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                break
            time.sleep(0.001)

    def start_main_thread(settings):
        while True:
            main(settings)

    def setup_watcher(app, settings):
        watcher = QFileSystemWatcher()
        watcher.addPath(CONFIG_FILE)
        def reload_settings():
            new_settings = load_settings()
            settings.update(new_settings)
        watcher.fileChanged.connect(reload_settings)
        app.exec()

    def main_program():
        app = QCoreApplication(sys.argv)
        settings = load_settings()
        threading.Thread(target=start_main_thread, args=(settings,), daemon=True).start()
        setup_watcher(app, settings)

    try:
        main_program()
    except Exception as e:
        app_title = get_app_title()
        ctypes.windll.user32.MessageBoxW(0, f"An error occured: {str(e)}", app_title, 0x00000000 | 0x00010000 | 0x00040000)
        try:
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('error')
        except:
            pass
        sys.exit(0)

def bhop():
    """Bunny hop function with configurable keybind"""
    import time
    import keyboard
    
                      
    TICK_64_MS = 0.0156
    exit_key = "end"
    toggle_key = "+"
    
    toggle = True
    
    def convert_key_to_keyboard_format(key_str):
        """Convert key string to keyboard library format"""
        if not key_str:
            return "space"
        
        key = str(key_str).strip().upper()
        
                                                   
        key_mapping = {
            'SPACE': 'space',
            'ENTER': 'enter',
            'RETURN': 'enter',
            'SHIFT': 'shift',
            'CTRL': 'ctrl',
            'CONTROL': 'ctrl',
            'ALT': 'alt',
            'TAB': 'tab',
            'ESC': 'esc',
            'ESCAPE': 'esc',
            'UP': 'up',
            'DOWN': 'down',
            'LEFT': 'left',
            'RIGHT': 'right',
            'BACKSPACE': 'backspace',
            'DELETE': 'delete',
            'INSERT': 'insert',
            'HOME': 'home',
            'END': 'end',
            'PAGEUP': 'page up',
            'PAGEDOWN': 'page down',
                                             
            'LMB': 'space',
            'RMB': 'space',
            'MMB': 'space',
            'MOUSE4': 'space',
            'MOUSE5': 'space',
        }
        
        if key in key_mapping:
            return key_mapping[key]
        
                       
        if key.startswith('F') and key[1:].isdigit():
            try:
                num = int(key[1:])
                if 1 <= num <= 24:
                    return f"f{num}"
            except:
                pass
        
                                                                  
        if len(key) == 1:
            if key.isalpha():
                return key.lower()
            elif key.isdigit():
                return key
        
                                                                          
        try:
                                                          
            keyboard.is_pressed(key.lower())
            return key.lower()
        except:
            pass
        
        try:
                            
            keyboard.is_pressed(key)
            return key
        except:
            pass
        
                                            
        return "space"

    def send_space(duration):
        try:
            keyboard.send("space")
            time.sleep(duration)
        except Exception:
            time.sleep(duration)
    
    def press_space():
        """Press and hold space key"""
        try:
            keyboard.press("space")
        except Exception:
            pass
    
    def release_space():
        """Release space key"""
        try:
            keyboard.release("space")
        except Exception:
            pass
    
    try:
        keyboard.add_hotkey(exit_key, lambda: exit())
    except Exception:
        pass
    
    default_settings = {
        "bhop_enabled": 1,
        "BhopKey": "SPACE"
    }

    def load_settings():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    settings = default_settings.copy()
                    settings.update(loaded)
                    return settings
            except:
                pass
        return default_settings

    def is_cs2_window_active():
        """Check if CS2 is the currently active window"""
        try:
            hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
            if hwnd:
                foreground_hwnd = win32gui.GetForegroundWindow()
                return hwnd == foreground_hwnd
            return False
        except Exception:
            return False

    def main(settings):
        nonlocal toggle
        
        bhop_key_pressed = False
        space_pressed = False
        last_jump_time = 0
        
        while True:
            try:
                bhop_enabled = settings.get("bhop_enabled", 0)
                
                if bhop_enabled == 1 and is_cs2_window_active():
                    bhop_key_setting = settings.get("BhopKey", "SPACE")
                    activation_key = convert_key_to_keyboard_format(bhop_key_setting)
                    
                    # Fallback key validation
                    try:
                        keyboard.is_pressed(activation_key)
                    except:
                        activation_key = "space"
                    
                    key_currently_pressed = keyboard.is_pressed(activation_key)
                    current_time = time.time()
                    
                    if key_currently_pressed and toggle:
                        if not bhop_key_pressed:
                            # Key just pressed - start bhop
                            bhop_key_pressed = True
                            send_space(TICK_64_MS * 1.5)
                            last_jump_time = current_time
                        else:
                            # Key held down - continue bhop timing
                            if current_time - last_jump_time >= TICK_64_MS * 3:
                                send_space(TICK_64_MS * 3)
                                last_jump_time = current_time
                    else:
                        if bhop_key_pressed:
                            # Key just released - ensure space is released
                            bhop_key_pressed = False
                            release_space()
                            time.sleep(0.001)  # Small delay to ensure release is processed
                    
                    # Handle toggle key
                    if keyboard.is_pressed(toggle_key):
                        toggle = not toggle
                        time.sleep(0.2)
                    
                    time.sleep(0.001)  # Small sleep to prevent excessive CPU usage
                else:
                    # Bhop disabled or not in CS2 - ensure space is released
                    if bhop_key_pressed:
                        bhop_key_pressed = False
                        release_space()
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                # Ensure space is released on exit
                if bhop_key_pressed:
                    release_space()
                break
            except Exception:
                # Ensure space is released on error
                if bhop_key_pressed:
                    bhop_key_pressed = False
                    release_space()
                time.sleep(1)

    def start_main_thread(settings):
        while True:
            try:
                main(settings)
            except Exception:
                time.sleep(5)

    def setup_watcher(app, settings):
        watcher = QFileSystemWatcher()
        watcher.addPath(CONFIG_FILE)
        def reload_settings():
            new_settings = load_settings()
            settings.update(new_settings)
        watcher.fileChanged.connect(reload_settings)
        app.exec()

    def main_program():
        app = QCoreApplication(sys.argv)
        settings = load_settings()
        threading.Thread(target=start_main_thread, args=(settings,), daemon=True).start()
        setup_watcher(app, settings)

    try:
        main_program()
    except Exception as e:
        app_title = get_app_title()
        ctypes.windll.user32.MessageBoxW(0, f"An error occured: {str(e)}", app_title, 0x00000000 | 0x00010000 | 0x00040000)
        try:
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('error')
        except:
            pass
        sys.exit(0)

def aim():
    default_settings = {
         'esp_rendering': 1,
         'esp_mode': 1,
         'AimKey': "C",
         'aim_active': 1,
         'aim_mode': 1,
         'radius': 20,
         'aim_mode_distance': 1,
         'aim_smoothness': 50,
         'aim_disable_when_crosshair_on_enemy': 0,
         'aim_movement_prediction': 0,
         'auto_apply_fov': 0
     }
    
    def get_window_size(window_name="Counter-Strike 2"):
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd:
            rect = win32gui.GetClientRect(hwnd)
            return rect[2] - rect[0], rect[3] - rect[1]
        return 1920, 1080

    def load_settings():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return default_settings

    def esp(pm, client, settings, target_list, window_size):
        width, height = window_size
        if settings['aim_active'] == 0:
            return
        view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]

        local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
        try:
            local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
        except:
            return
        entity_list = pm.read_longlong(client + dwEntityList)
        entity_ptr = pm.read_longlong(entity_list + 0x10)
    
        for i in range(1, 64):
            try:
                if entity_ptr == 0:
                    break

                entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
                if entity_controller == 0:
                    continue

                entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
                if entity_controller_pawn == 0:
                    continue

                entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
                if entity_list_pawn == 0:
                    continue

                entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
                if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                    continue

                entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
                if entity_team == local_player_team and settings['esp_mode'] == 0:
                    continue

                entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
                if entity_alive != 256:
                    continue
                
                if settings.get('aim_active', 0) == 1 and settings.get('aim_visibility_check', 0) == 1:
                    is_visible = pm.read_bool(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                    if not is_visible:
                        continue
                game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)
                try:
                                                             
                    aim_bone_target_idx = int(settings.get('aim_bone_target', 1))                   
                    
                                                                                   
                    global BONE_TARGET_MODES, bone_ids
                    
                                                                                 
                    if aim_bone_target_idx in BONE_TARGET_MODES:
                        target_bone_name = BONE_TARGET_MODES[aim_bone_target_idx]["bone"]
                    else:
                        target_bone_name = "head"                    
                    
                                                                         
                    if target_bone_name in bone_ids:
                        bone_id = bone_ids[target_bone_name]
                    else:
                        bone_id = bone_ids["head"]                           

                                                                                            
                    bone_positions = {}
                    bone_ids_to_calc = list(bone_ids.values())                                  
                    for bone_name, bid in bone_ids.items():
                        try:
                            bx = pm.read_float(bone_matrix + bid * 0x20)
                            by = pm.read_float(bone_matrix + bid * 0x20 + 0x4)
                            bz = pm.read_float(bone_matrix + bid * 0x20 + 0x8)
                            bpos = w2s(view_matrix, bx, by, bz, width, height)
                            bone_positions[bid] = bpos
                        except Exception:
                            bone_positions[bid] = (-999, -999)

                    
                    head_pos = bone_positions.get(6, (-999, -999))
                    legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                    leg_pos = w2s(view_matrix, head_pos[0], head_pos[1], legZ, width, height) if head_pos[0] != -999 else (-999, -999)
                    deltaZ = abs(head_pos[1] - leg_pos[1]) if head_pos[1] != -999 and leg_pos[1] != -999 else None

                    
                    # Get velocity for movement prediction
                    try:
                        velocity_x = pm.read_float(entity_pawn_addr + m_vecVelocity)
                        velocity_y = pm.read_float(entity_pawn_addr + m_vecVelocity + 4)
                        velocity_z = pm.read_float(entity_pawn_addr + m_vecVelocity + 8)
                        velocity = (velocity_x, velocity_y, velocity_z)
                    except Exception:
                        velocity = (0, 0, 0)
                    
                    any_valid = any(p[0] != -999 and p[1] != -999 for p in bone_positions.values())
                    if any_valid:
                        target_list.append({
                            'bone_positions': bone_positions,
                            'deltaZ': deltaZ,
                            'entity_pawn_addr': entity_pawn_addr,
                            'velocity': velocity
                        })
                except Exception as e:
                    pass
            except:
                return
        return target_list

    def apply_fov_change(self, fov_value):
        """Apply FOV change to the game"""
        try:
            if hasattr(self, 'cheat_loop') and self.cheat_loop and hasattr(self.cheat_loop, 'pm') and self.cheat_loop.pm:
                pm = self.cheat_loop.pm
                client = self.cheat_loop.client
                
                if pm and client:
                    # Read local player controller
                    local_player_controller = pm.read_longlong(client + dwLocalPlayerController)
                    if local_player_controller:
                        # Write FOV value to the player controller
                        pm.write_int(local_player_controller + m_iDesiredFOV, int(fov_value))
        except Exception:
            pass

    def aimbot(target_list, radius, aim_mode_distance, smoothness, pm=None, client=None, offsets=None, client_dll=None):
        """Select a target and move the mouse toward it applying smoothing.

        When 'Lock Target' is enabled, the function will prefer a previously
        locked entity and will only set a new lock when the AimKey edge was
        detected in `main()` (that clears previous lock on fresh press).
        """
                                          
        try:
            settings = load_settings()
        except Exception:
            settings = {}
        
        if not target_list:
            return

        center_x = win32api.GetSystemMetrics(0) // 2
        center_y = win32api.GetSystemMetrics(1) // 2

        # Get current FOV for compensation calculations
        current_fov = 90  # Default FOV
        try:
            if pm and client:
                local_player_controller = pm.read_longlong(client + dwLocalPlayerController)
                if local_player_controller:
                    current_fov = pm.read_int(local_player_controller + m_iDesiredFOV)
                    # Clamp FOV to actual game values (60-160)
                    if current_fov < 60 or current_fov > 160:
                        current_fov = 90
        except Exception:
            pass

        aim_bone_target_idx = int(settings.get('aim_bone_target', 1)) if settings.get('aim_bone_target') is not None else 1                   
        
                                                                       
        global BONE_TARGET_MODES, bone_ids

        def _select_bone_for_entity(ent_addr):
                                                                         
            if aim_bone_target_idx in BONE_TARGET_MODES:
                target_bone_name = BONE_TARGET_MODES[aim_bone_target_idx]["bone"]
            else:
                target_bone_name = "head"                    

                                                                 
            if target_bone_name in bone_ids:
                return bone_ids[target_bone_name]
            else:
                return bone_ids["head"]                           

        
        closest = None  
        closest_dist = float('inf')

        if radius == 0:
            for target in target_list:
                ent_addr = target.get('entity_pawn_addr')
                bone_positions = target.get('bone_positions', {})
                bone_id = _select_bone_for_entity(ent_addr)
                pos = bone_positions.get(bone_id, (-999, -999))
                if pos[0] == -999:
                    continue
                dist = ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5
                if dist < closest_dist:
                    closest = (pos, ent_addr)
                    closest_dist = dist
        else:
            # Apply FOV compensation to radius calculation
            # Use the same angular compensation as mouse movement for consistency
            import math
            fov_rad_current = math.radians(current_fov / 2.0)
            fov_rad_default = math.radians(90.0 / 2.0)
            fov_scale = math.tan(fov_rad_current) / math.tan(fov_rad_default)
            adjusted_radius = radius * fov_scale
            
            screen_radius = adjusted_radius / 100.0 * min(center_x, center_y)
            if aim_mode_distance == 1:
                
                target_with_max_deltaZ = None
                max_deltaZ = -float('inf')
                for target in target_list:
                    ent_addr = target.get('entity_pawn_addr')
                    bone_positions = target.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(ent_addr)
                    pos = bone_positions.get(bone_id, (-999, -999))
                    if pos[0] == -999:
                        continue
                    dist = ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5
                    if dist < screen_radius and (target.get('deltaZ') or 0) > max_deltaZ:
                        max_deltaZ = target.get('deltaZ') or 0
                        target_with_max_deltaZ = target
                if target_with_max_deltaZ:
                    ent_addr = target_with_max_deltaZ.get('entity_pawn_addr')
                    bone_positions = target_with_max_deltaZ.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(ent_addr)
                    pos = bone_positions.get(bone_id, (-999, -999))
                    if pos[0] != -999:
                        closest = (pos, ent_addr)
            else:
                for target in target_list:
                    ent_addr = target.get('entity_pawn_addr')
                    bone_positions = target.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(ent_addr)
                    pos = bone_positions.get(bone_id, (-999, -999))
                    if pos[0] == -999:
                        continue
                    dist = ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5
                    if dist < screen_radius and dist < closest_dist:
                        closest = (pos, ent_addr)
                        closest_dist = dist

        if not closest:
            return

        
        try:
            lock_enabled = int(settings.get('aim_lock_target', 0)) == 1
        except Exception:
            lock_enabled = False

        pos, ent_addr = closest
        
        if lock_enabled and aim_lock_state.get('locked_entity') is not None:
            locked_ent = aim_lock_state.get('locked_entity')
            found = None
            for t in target_list:
                if t.get('entity_pawn_addr') == locked_ent:
                    bone_positions = t.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(locked_ent)
                    p = bone_positions.get(bone_id, (-999, -999))
                    if p[0] != -999:
                        found = (p, locked_ent)
                        break
            if found is not None:
                pos, ent_addr = found
            else:
                
                aim_lock_state['locked_entity'] = None

        
        if lock_enabled and aim_lock_state.get('locked_entity') is None:
            aim_lock_state['locked_entity'] = ent_addr

        

        # Movement prediction logic
        movement_prediction_enabled = settings.get('aim_movement_prediction', 0) == 1
        target_x, target_y = pos
        
        if movement_prediction_enabled and pm and client:
            try:
                # Get velocity data for the target entity
                target_velocity = None
                target_bone_id = _select_bone_for_entity(ent_addr)
                
                for target in target_list:
                    if target.get('entity_pawn_addr') == ent_addr:
                        target_velocity = target.get('velocity', (0, 0, 0))
                        break
                
                # Only predict for targets with significant movement (reduced threshold for better accuracy)
                if target_velocity and (abs(target_velocity[0]) > 30 or abs(target_velocity[1]) > 30):
                    # Much more conservative prediction time - CS2 is hitscan so we need minimal lead
                    # Base on 2D screen distance, but keep it very small
                    distance_to_target = ((pos[0] - center_x)**2 + (pos[1] - center_y)**2)**0.5
                    
                    # Very short prediction time: 0.01 to 0.08 seconds max
                    # This accounts for network latency and minor movement prediction
                    max_screen_distance = 500  # Reasonable screen distance reference
                    prediction_time = 0.01 + min(distance_to_target / max_screen_distance, 1.0) * 0.07
                    
                    # Get the specific bone position we're targeting, not just world center
                    try:
                        # Read the bone matrix for the target
                        game_scene_node = pm.read_longlong(ent_addr + m_pGameSceneNode)
                        bone_matrix = pm.read_longlong(game_scene_node + m_modelState + 0x80)
                        
                        # Get current bone world position
                        current_bone_x = pm.read_float(bone_matrix + target_bone_id * 0x20)
                        current_bone_y = pm.read_float(bone_matrix + target_bone_id * 0x20 + 0x4)
                        current_bone_z = pm.read_float(bone_matrix + target_bone_id * 0x20 + 0x8)
                        
                        # Apply conservative movement prediction to the bone position
                        predicted_bone_x = current_bone_x + (target_velocity[0] * prediction_time)
                        predicted_bone_y = current_bone_y + (target_velocity[1] * prediction_time)
                        predicted_bone_z = current_bone_z + (target_velocity[2] * prediction_time)
                        
                        # Get view matrix and convert predicted bone position to screen coordinates
                        view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]
                        
                        # Project predicted bone position to screen
                        screen_width = win32api.GetSystemMetrics(0)
                        screen_height = win32api.GetSystemMetrics(1)
                        predicted_screen = w2s(view_matrix, predicted_bone_x, predicted_bone_y, predicted_bone_z, screen_width, screen_height)
                        
                        if predicted_screen and predicted_screen[0] != -999 and predicted_screen[1] != -999:
                            # Use predicted screen position as new target
                            target_x, target_y = predicted_screen
                    except Exception:
                        # If prediction fails, fall back to original position
                        pass
            except Exception:
                # If any part of movement prediction fails, continue with original position
                pass

        # Calculate final aim adjustments with FOV compensation                                                           
        dx = target_x - center_x
        dy = target_y - center_y

        # Apply FOV compensation to mouse movement
        # In CS2, mouse sensitivity is inversely related to FOV for maintaining consistent angular movement
        # Higher FOV = wider view = need MORE mouse movement to achieve same angular rotation
        # Lower FOV = narrower view = need LESS mouse movement to achieve same angular rotation
        # Formula: compensation = tan(current_fov/2) / tan(90/2) for proper angular scaling
        import math
        fov_rad_current = math.radians(current_fov / 2.0)
        fov_rad_default = math.radians(90.0 / 2.0)
        fov_compensation = math.tan(fov_rad_current) / math.tan(fov_rad_default)
        
        # Apply FOV compensation to the deltas
        dx *= fov_compensation
        dy *= fov_compensation

                                      
        if smoothness is None:
            smoothness = 0

                                                                                      
                         

        if smoothness <= 0:
            move_x = int(dx)
            move_y = int(dy)
        else:
                                                                                     
                                                  
                                                              
            max_smoothness = 3000000.0  # Updated to 3 million maximum
            min_alpha = 0.0005                                       
            max_alpha = 1.0                                         
            
                                                                
            normalized_smoothness = min(1.0, smoothness / max_smoothness)
            alpha = min_alpha + (max_alpha - min_alpha) * (1.0 - normalized_smoothness) ** 2
            
            move_x = int(dx * alpha)
            move_y = int(dy * alpha)
            if move_x == 0 and dx != 0:
                move_x = 1 if dx > 0 else -1
            if move_y == 0 and dy != 0:
                move_y = 1 if dy > 0 else -1

                                                                   
        disable_when_crosshair_on_enemy = settings.get('aim_disable_when_crosshair_on_enemy', 0) == 1
        
        if disable_when_crosshair_on_enemy and pm and client:
            try:
                                                                
                local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
                if local_player_pawn_addr:
                                                       
                    entity_id = pm.read_int(local_player_pawn_addr + m_iIDEntIndex)
                    
                    if entity_id > 0:
                                                     
                        entity_list = pm.read_longlong(client + dwEntityList)
                        entity_entry = pm.read_longlong(entity_list + 0x8 * (entity_id >> 9) + 0x10)
                        entity = pm.read_longlong(entity_entry + 0x78 * (entity_id & 0x1FF))
                        
                        if entity:
                            entity_team = pm.read_int(entity + m_iTeamNum)
                            entity_health = pm.read_int(entity + m_iHealth)
                            local_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
                            
                                                                                 
                            if entity_health > 0 and entity_team != local_team:
                                return                             
                            
            except Exception:
                pass                                                      

                                           
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)

    def camera_lock(pm, client, settings):
        """Independent camera lock system that scans for enemies and locks to closest head when triggerbot key is held"""
        try:
            if not settings.get('camera_lock_enabled', 0):
                return
            
            # Check if triggerbot key is being held (same key as triggerbot)
            trigger_key = settings.get('TriggerKey', 'X')
            trigger_key_vk = key_str_to_vk(trigger_key)
            if not trigger_key_vk or not (win32api.GetAsyncKeyState(trigger_key_vk) & 0x8000):
                return
            
            # Get window dimensions
            window_width = win32api.GetSystemMetrics(0)
            window_height = win32api.GetSystemMetrics(1)
            center_x = window_width // 2
            center_y = window_height // 2
            
            # Get view matrix and local player info
            view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]
            local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
            
            try:
                local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
            except:
                return
            
            # Scan for valid targets
            entity_list = pm.read_longlong(client + dwEntityList)
            entity_ptr = pm.read_longlong(entity_list + 0x10)
            
            closest_target = None
            min_distance = float('inf')
            
            for i in range(1, 64):
                try:
                    if entity_ptr == 0:
                        break

                    entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
                    if entity_controller == 0:
                        continue

                    entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
                    if entity_controller_pawn == 0:
                        continue

                    entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
                    if entity_list_pawn == 0:
                        continue

                    entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
                    if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                        continue

                    entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
                    
                    # Use esp_mode setting: 0 = enemies only, 1 = all players
                    esp_mode = settings.get('esp_mode', 0)
                    if esp_mode == 0 and entity_team == local_player_team:
                        continue  # Skip teammates when in enemies-only mode

                    entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
                    if entity_alive != 256:
                        continue

                    # Check spotted status if enabled
                    spotted_check_enabled = settings.get('camera_lock_spotted_check', 0) == 1
                    if spotted_check_enabled:
                        try:
                            spotted_flag = pm.read_int(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            is_spotted = spotted_flag != 0
                        except:
                            is_spotted = False
                        
                        # Skip non-spotted enemies when spotted check is enabled
                        if not is_spotted:
                            continue

                    # Get target bone position
                    game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                    bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)
                    
                    # Get selected bone ID from settings
                    target_bone_mode = settings.get('camera_lock_target_bone', 1)
                    target_bone_name = BONE_TARGET_MODES.get(target_bone_mode, {"bone": "head"}).get("bone", "head")
                    target_bone_id = bone_ids.get(target_bone_name, 6)  # Default to head (6) if not found
                    
                    # Get target bone position
                    target_x = pm.read_float(bone_matrix + target_bone_id * 0x20)
                    target_y = pm.read_float(bone_matrix + target_bone_id * 0x20 + 0x4)
                    target_z = pm.read_float(bone_matrix + target_bone_id * 0x20 + 0x8)
                    
                    # Project to screen
                    target_pos = w2s(view_matrix, target_x, target_y, target_z, window_width, window_height)
                    
                    # Only consider targets within screen bounds
                    if (target_pos[0] != -999 and target_pos[1] != -999 and
                        0 <= target_pos[0] <= window_width and 
                        0 <= target_pos[1] <= window_height):
                        
                        # Calculate distance from center of screen
                        dx = target_pos[0] - center_x
                        dy = target_pos[1] - center_y
                        distance = (dx * dx + dy * dy) ** 0.5
                        
                        # Check if radius targeting is enabled
                        use_radius = settings.get('camera_lock_use_radius', 0) == 1
                        if use_radius:
                            # Only consider targets within the radius
                            radius = settings.get('camera_lock_radius', 100)
                            if distance > radius:
                                continue  # Skip targets outside the radius
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_target = target_pos
                            
                except Exception:
                    continue
            
            # Apply camera adjustment if target found
            if closest_target:
                target_x, target_y = closest_target
                
                # Calculate vertical adjustment needed to align with target
                dy = target_y - center_y
                
                # Get user-configurable tolerance (dead zone)
                tolerance = settings.get('camera_lock_tolerance', 5)
                
                # Only adjust if the difference is significant (more than tolerance pixels)
                if abs(dy) > tolerance:
                    # Apply smooth camera movement with user-configurable smoothness
                    smoothness_value = settings.get('camera_lock_smoothness', 5)
                    if smoothness_value <= 0:
                        smoothness_value = 1
                    # Calculate smoothness factor: 1=0.95 (almost instant), 20=1.0 (full movement)
                    # Use exponential curve for better feel: base + (value-1) * increment
                    smoothness_factor = 0.95 + (smoothness_value - 1) * 0.00263  # 0.95 to 1.0 range
                    move_y = int(dy * smoothness_factor)  # Apply smoothness factor
                    
                    # Limit maximum movement to prevent jerky camera
                    if move_y > 8:
                        move_y = 8
                    elif move_y < -8:
                        move_y = -8
                        
                    # Apply the camera adjustment
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, move_y, 0, 0)
                    
        except Exception:
            pass

    def main(settings):
        import time
        pm = None
        client = None
        
        while pm is None or client is None:
            if is_cs2_running():
                try:
                    pm = pymem.Pymem("cs2.exe")
                    client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                except Exception:
                    pm = None
                    client = None
                    time.sleep(1)
            else:
                pm = None
                client = None
                time.sleep(1)
        window_size = get_window_size()
        
        # Counter for periodic settings reload
        loop_counter = 0
        
        while True:
            # Reload settings every 10 loops to pick up changes
            if loop_counter % 10 == 0:
                try:
                    new_settings = load_settings()
                    settings.update(new_settings)
                except Exception:
                    pass
            loop_counter += 1
            
            # Only run ESP and aimbot if aim is active
            if settings.get('aim_active', 0) == 1:
                target_list = []
                target_list = esp(pm, client, settings, target_list, window_size)
                
                # Apply FOV setting only if auto-apply is enabled
                try:
                    if settings.get('auto_apply_fov', 0) == 1:
                        game_fov = settings.get('game_fov', 90)
                        local_player_controller = pm.read_longlong(client + dwLocalPlayerController)
                        if local_player_controller:
                            pm.write_int(local_player_controller + m_iDesiredFOV, int(game_fov))
                except Exception:
                    pass
                
                           
                try:
                    vk = key_str_to_vk(settings.get('AimKey', ''))
                except Exception:
                    vk = 0
                try:
                                                     
                    if is_keybind_on_global_cooldown("AimKey"):
                        pressed = False
                    else:
                        pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                except Exception:
                    pressed = False

                
                
                                        
                try:
                    if pressed and not aim_lock_state.get('aim_was_pressed', False):
                        aim_lock_state['locked_entity'] = None
                        aim_lock_state['aim_was_pressed'] = True
                    if not pressed:
                        
                        aim_lock_state['aim_was_pressed'] = False
                except Exception:
                    pass

                # Check if aimkey is required or if it's pressed
                require_aimkey = settings.get('require_aimkey', 1) == 1
                should_aim = pressed if require_aimkey else True
                
                if should_aim:
                                                    
                    smoothness = settings.get('aim_smoothness', 0)
                    aimbot(target_list, settings['radius'], settings['aim_mode_distance'], smoothness, pm, client, offsets, client_dll)
            
            # Apply camera lock (completely independent)
            camera_lock(pm, client, settings)
            
            time.sleep(0.001)

    def start_main_thread(settings):
        while True:
            main(settings)

    def setup_watcher(app, settings):
        watcher = QFileSystemWatcher()
        watcher.addPath(CONFIG_FILE)
        def reload_settings():
            new_settings = load_settings()
            settings.update(new_settings)
        watcher.fileChanged.connect(reload_settings)
        app.exec()

    def main_program():
        app = QCoreApplication(sys.argv)
        settings = load_settings()
        threading.Thread(target=start_main_thread, args=(settings,), daemon=True).start()
        setup_watcher(app, settings)

    try:
        main_program()
    except Exception as e:
        app_title = get_app_title()
        ctypes.windll.user32.MessageBoxW(0, f"An error occured: {str(e)}", app_title, 0x00000000 | 0x00010000 | 0x00040000)
        try:
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('error')
        except:
            pass
        sys.exit(0)

def wait_for_cs2_startup():
    """Wait for CS2 to start and then wait additional 6 seconds"""
    pass
    
                                    
    while not is_cs2_running():
        time.sleep(0.5)
    
                                         
    if STARTUP_ENABLED:
        pass
        time.sleep(25)
        
                                 
        trigger_graphics_restart()
        
        pass

def find_accept_button():
    """Find the green accept button on screen"""
    try:
        screenshot = ImageGrab.grab()
        img = np.array(screenshot)
                                                             
        color = (54, 183, 82)
        color_match = np.all(img == color, axis=-1).astype(int)
        kernel = np.ones((10, 10))
        from scipy.signal import convolve2d
        convolution = convolve2d(color_match, kernel, mode='valid')
        y_coords, x_coords = np.where(convolution == 100)
        if len(y_coords) > 0:
            x = x_coords[0] + 5
            y = y_coords[0] + 5
            return (x, y)
    except Exception:
        pass
    return None

def auto_accept_main():
    """Main auto accept loop"""
    while True:
        try:
                                                        
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            if not settings.get("auto_accept_enabled", 0):
                time.sleep(1)
                continue
                
            pos = find_accept_button()
            if pos:
                x, y = pos
                pyautogui.moveTo(x, y)
                pyautogui.click()
                                           
                screen_width, screen_height = pyautogui.size()
                pyautogui.moveTo(screen_width // 2, screen_height // 2)
                time.sleep(3)
            else:
                time.sleep(0.5)
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    
    # Register cleanup handlers as early as possible
    register_cleanup_handlers()
    
    print("Starting Popsicle CS2 application...")
    
    try:
        multiprocessing.freeze_support()
    except Exception:
        pass

    # Version check worker started
    version_thread = threading.Thread(target=version_check_worker, daemon=True)
    version_thread.start()
    pass  # Version check worker started

                                                        
    if not handle_instance_check():
        sys.exit(0)
    
                                                           
    if not create_lock_file():
        app_title = get_app_title()
        ctypes.windll.user32.MessageBoxW(
            0,
            "Failed to create lock file. Another instance may be starting.",
            f"{app_title} - Error",
            0x00000010 | 0x00010000 | 0x00040000                                                
        )
        sys.exit(0)
    
    MB_OK = 0x00000000
    MB_OKCANCEL = 0x00000001
    MB_SETFOREGROUND = 0x00010000
    MB_TOPMOST = 0x00040000
    MB_SYSTEMMODAL = 0x00001000
    IDOK = 1
    IDCANCEL = 2
    
                                     
    if is_cs2_running():
        pass  # CS2 is already running
                                             
        if STARTUP_ENABLED:
            pass  # Startup delays enabled
            time.sleep(4)
            
                                     
            pass  # Triggering graphics restart
            trigger_graphics_restart()
            
                                                              
        pm = None
        try:
            pm = pymem.Pymem("cs2.exe")
            pass  # Successfully connected to CS2 process
        except Exception:
            pass  # Failed to connect to CS2 process initially
    else:
        pass  # CS2 is not running - showing wait dialog
                                                   
        app_title = get_app_title()
        result = ctypes.windll.user32.MessageBoxW(0, "Waiting for CS2.exe", app_title, MB_OKCANCEL | MB_SETFOREGROUND | MB_TOPMOST | MB_SYSTEMMODAL)
        if result != IDOK:
                                                                       
            remove_lock_file()
            try:
                if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                    os.remove(KEYBIND_COOLDOWNS_FILE)
            except Exception:
                pass
            sys.exit(0)
        
                                                       
        wait_for_cs2_startup()
        
                                      
        pm = None
        while pm is None:
            try:
                pm = pymem.Pymem("cs2.exe")
                break
            except Exception:
                time.sleep(1)


    procs = [
        multiprocessing.Process(target=configurator),
        multiprocessing.Process(target=esp_main),
        multiprocessing.Process(target=triggerbot),
        multiprocessing.Process(target=bhop),
        multiprocessing.Process(target=auto_accept_main),
    ]
    
    process_names = ["configurator", "esp_main", "triggerbot", "bhop", "auto_accept_main"]
    
    # Only add aim process in full mode
    if SELECTED_MODE == 'full':
        procs.append(multiprocessing.Process(target=aim))
        process_names.append("aim")
    
    # Track all processes for cleanup
    for proc in procs:
        track_process(proc)
    
    def cleanup_and_exit(reason=""):
        """Clean shutdown of all processes and resources"""
        print(f"[DEBUG] Cleanup initiated: {reason}")
        
        # Use the comprehensive cleanup function
        cleanup_all_temporary_files()
        
        # Legacy cleanup for any missed processes
        if 'procs' in locals() or 'procs' in globals():
            for i, p in enumerate(procs):
                try:
                    if p.is_alive():
                        print(f"[DEBUG] Legacy terminating process: {process_names[i]}")
                        p.terminate()
                        p.join(2)  # Wait up to 2 seconds for clean shutdown
                        if p.is_alive():
                            print(f"[DEBUG] Legacy force killing process: {process_names[i]}")
                            p.kill()
                            p.join(1)
                except Exception as e:
                    print(f"[DEBUG] Error terminating {process_names[i]}: {e}")
        
        # Final fallback cleanup
        remove_lock_file()
        
    # Start all processes
    print("[DEBUG] Starting all processes...")
    for i, p in enumerate(procs):
        print(f"[DEBUG] Starting process: {process_names[i]}")
        p.start()
        time.sleep(0.5)  # Small delay between process starts

    try:
        print("[DEBUG] Entering main monitoring loop...")
        process_check_interval = 0
        
        while True:
            time.sleep(1)
            process_check_interval += 1
            
            # Check for terminate signal (including panic shutdowns)
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                print("[DEBUG] Terminate signal detected")
                break
            
            # Also check for panic signal file (backup check)
            panic_file = os.path.join(os.getcwd(), 'panic_shutdown.signal')
            if os.path.exists(panic_file):
                print("[DEBUG] Panic shutdown signal detected")
                try:
                    os.remove(panic_file)
                except Exception:
                    pass
                break
                                                                                         
            # Check if CS2 is still running
            if not is_cs2_running():
                print("[DEBUG] CS2 no longer running")
                break
            
            # Check process health every 5 seconds
            if process_check_interval >= 5:
                process_check_interval = 0
                
                dead_processes = []
                for i, p in enumerate(procs):
                    if not p.is_alive():
                        dead_processes.append(process_names[i])
                
                if dead_processes:
                    print(f"[DEBUG] Dead processes detected: {', '.join(dead_processes)}")
                    
                    # Show error message to user
                    app_title = get_app_title()
                    error_msg = f"The following process(es) have stopped unexpectedly:\\n{', '.join(dead_processes)}\\n\\nAll processes will be terminated for safety."
                    try:
                        ctypes.windll.user32.MessageBoxW(
                            0, 
                            error_msg, 
                            f"{app_title} - Process Failure", 
                            0x00000000 | 0x00010000 | 0x00040000 | 0x00000030  # OK + SetForeground + TopMost + Warning Icon
                        )
                    except Exception:
                        pass
                    
                    cleanup_and_exit(f"Process failure: {', '.join(dead_processes)}")
                    sys.exit(1)
                    
    except KeyboardInterrupt:
        print("[DEBUG] Keyboard interrupt received")
        cleanup_and_exit("Keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        print(f"[DEBUG] Unexpected error in main loop: {e}")
        app_title = get_app_title()
        try:
            ctypes.windll.user32.MessageBoxW(
                0, 
                f"An unexpected error occurred in the main process:\\n{str(e)}\\n\\nAll processes will be terminated.", 
                f"{app_title} - Critical Error", 
                0x00000000 | 0x00010000 | 0x00040000 | 0x00000010  # OK + SetForeground + TopMost + Error Icon
            )
        except Exception:
            pass
        cleanup_and_exit(f"Main loop error: {str(e)}")
        sys.exit(1)
    finally:
        print("[DEBUG] Main loop exited, cleaning up...")
        cleanup_and_exit("Normal shutdown")
        sys.exit(0)
