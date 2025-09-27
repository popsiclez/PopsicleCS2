VERSION = "2"
DEBUG_MODE = False
CONSOLE_CREATED = False  # Global flag to track console creation
                 
import threading
import keyboard
import os
import sys
import json
import time
                                                                                  
STARTUP_ENABLED = True

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

def setup_debug_console():
    """Create a console window for debug output if DEBUG_MODE is True - only in main process"""
    if DEBUG_MODE and __name__ == "__main__":  # Only create console in main process
        try:
                                                         
            ctypes.windll.kernel32.AllocConsole()
            
            # Disable close button
            disable_console_close_button()
            
            import sys
            sys.stdout = open('CONOUT$', 'w')
            sys.stderr = open('CONOUT$', 'w')
            sys.stdin = open('CONIN$', 'r')
            
                               
            ctypes.windll.kernel32.SetConsoleTitleW("Debug Console - Popsicle CS2")
            
            print("Debug mode enabled - Console output active")
        except Exception as e:
            pass

def debug_print(*args, **kwargs):
    """Print debug information only if DEBUG_MODE is True"""
    if DEBUG_MODE:
        print(*args, **kwargs)

def load_commands():
    """Load commands from commands.txt file if it exists"""
    commands = []
    try:
        print(f"[DEBUG] Checking for commands file at: {COMMANDS_FILE}")  # Always print this
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, 'r') as f:
                content = f.read().strip()
                print(f"[DEBUG] Commands file content: '{content}'")  # Always print this
                if content:
                    # Parse commands separated by commas
                    commands = [cmd.strip().lower() for cmd in content.split(',') if cmd.strip()]
                    print(f"[DEBUG] Parsed commands: {commands}")  # Always print this
                    debug_print(f"Loaded commands from {COMMANDS_FILE}: {commands}")
        else:
            print(f"[DEBUG] No commands file found at {COMMANDS_FILE}")  # Always print this
            debug_print(f"No commands file found at {COMMANDS_FILE}")
    except Exception as e:
        print(f"[DEBUG] Error reading commands file: {e}")  # Always print this
        debug_print(f"Error reading commands file: {e}")
    return commands

def apply_commands():
    """Apply commands from commands.txt file"""
    global DEBUG_MODE, CONSOLE_CREATED
    print("[DEBUG] apply_commands() called")  # Always print this
    commands = load_commands()
    print(f"[DEBUG] Commands loaded: {commands}")  # Always print this
    
    # Process debug command
    if "debug" in commands:
        print("[DEBUG] Debug command found in commands list")  # Always print this
        original_debug_mode = DEBUG_MODE
        DEBUG_MODE = True
        
        # Check if console already created by any process - only allow main process to create console
        if not original_debug_mode and not CONSOLE_CREATED and not os.path.exists(CONSOLE_LOCK_FILE) and __name__ == "__main__":
            print("[DEBUG] Creating debug console in main process...")  # Always print this
            # Force console creation for debug command - but only once globally
            try:
                # Create lock file first to prevent other processes
                with open(CONSOLE_LOCK_FILE, 'w') as f:
                    f.write(str(os.getpid()))
                
                # Try to allocate console
                result = ctypes.windll.kernel32.AllocConsole()
                if result != 0:  # Success
                    # Disable close button
                    disable_console_close_button()
                    
                    import sys
                    sys.stdout = open('CONOUT$', 'w')
                    sys.stderr = open('CONOUT$', 'w')
                    sys.stdin = open('CONIN$', 'r')
                    ctypes.windll.kernel32.SetConsoleTitleW("Debug Console - Popsicle CS2")
                    CONSOLE_CREATED = True
                    print("Debug mode enabled via commands.txt override - Console output active (close disabled)")
                else:
                    print("Console allocation failed - may already exist")
                    # Remove lock file if console creation failed
                    try:
                        os.remove(CONSOLE_LOCK_FILE)
                    except:
                        pass
            except Exception as e:
                print(f"Console creation error: {e}")
                # Remove lock file if console creation failed
                try:
                    os.remove(CONSOLE_LOCK_FILE)
                except:
                    pass
        elif os.path.exists(CONSOLE_LOCK_FILE):
            print("[DEBUG] Console lock file exists, skipping console creation")
        elif CONSOLE_CREATED:
            print("[DEBUG] Console already created in this process, skipping")
        debug_print("Commands processed:", commands)
    else:
        print("[DEBUG] Debug command NOT found in commands list")  # Always print this

def get_app_title():
    """Fetch application title from GitHub"""
    try:
        response = requests.get('https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/title.txt', timeout=5)
        if response.status_code == 200:
            title = response.text.strip()
            debug_print(f"Fetched title from GitHub: {title}")
            return title
    except Exception as e:
        debug_print(f"Failed to fetch title from GitHub: {e}")
    
                    
    return "Popsicle - CS2"

def check_version():
    """Check if current version matches GitHub version"""
    try:
        response = requests.get('https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/version.txt', timeout=5)
        if response.status_code == 200:
            remote_version = response.text.strip()
            debug_print(f"Local version: {VERSION}, Remote version: {remote_version}")
            return VERSION == remote_version
    except Exception as e:
        debug_print(f"Failed to check version: {e}")
    
                                             
    return True

def version_check_worker():
    """Background worker to check version periodically"""
    while True:
        try:
            if not check_version():
                debug_print("Version mismatch detected - showing update notification")
                                                                      
                app_title = get_app_title()
                ctypes.windll.user32.MessageBoxW(
                    0, 
                    "New version available! Please relaunch loader", 
                    app_title,
                    0x00000000 | 0x00010000 | 0x00040000 | 0x00001000                                                          
                )
                
                debug_print("User dismissed update notification - creating terminate signal to exit all processes")
                                                
                remove_lock_file()
                                                                   
                try:
                    if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                        os.remove(KEYBIND_COOLDOWNS_FILE)
                except Exception:
                    pass
                                                                                  
                try:
                    with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                        f.write('version_mismatch')
                except Exception:
                    pass
                                                                              
                time.sleep(1)
                os._exit(0)
                
                                    
            time.sleep(30)
        except Exception as e:
            debug_print(f"Version check error: {e}")
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
m_pClippingWeapon = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_pClippingWeapon']
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
          
CONFIG_DIR = os.getcwd()
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
TERMINATE_SIGNAL_FILE = os.path.join(CONFIG_DIR, 'terminate_now.signal')
LOCK_FILE = os.path.join(CONFIG_DIR, 'script_running.lock')
KEYBIND_COOLDOWNS_FILE = os.path.join(CONFIG_DIR, 'keybind_cooldowns.json')
COMMANDS_FILE = os.path.join(CONFIG_DIR, 'commands.txt')
CONSOLE_LOCK_FILE = os.path.join(CONFIG_DIR, 'debug_console.lock')

# Apply commands from commands.txt if it exists (now that COMMANDS_FILE is defined)
apply_commands()
                       
RAINBOW_HUE = 0.0
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
        return True
    except Exception:
        return False

def disable_console_close_button():
    """Disable the close button on the console window."""
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get console window handle
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            # Get system menu handle
            hmenu = ctypes.windll.user32.GetSystemMenu(console_hwnd, False)
            if hmenu:
                # Remove close button (SC_CLOSE = 0xF060)
                ctypes.windll.user32.RemoveMenu(hmenu, 0xF060, 0x0)
                # Redraw the menu bar
                ctypes.windll.user32.DrawMenuBar(console_hwnd)
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Failed to disable console close button: {e}")

def disable_console_close_button():
    """Disable the close button on the console window."""
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get console window handle
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            # Get system menu handle
            hmenu = ctypes.windll.user32.GetSystemMenu(console_hwnd, False)
            if hmenu:
                # Remove close button (SC_CLOSE = 0xF060)
                ctypes.windll.user32.RemoveMenu(hmenu, 0xF060, 0x0)
                # Redraw the menu bar
                ctypes.windll.user32.DrawMenuBar(console_hwnd)
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG] Failed to disable console close button: {e}")

def remove_lock_file():
    """Remove the lock file when shutting down."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        # Also remove console lock file
        if os.path.exists(CONSOLE_LOCK_FILE):
            os.remove(CONSOLE_LOCK_FILE)
    except Exception:
        pass

def terminate_existing_instance():
    """Signal existing instance to terminate and wait for it to close."""
    try:
                                 
        with open(TERMINATE_SIGNAL_FILE, 'w') as f:
            f.write('terminate')
        
                                                               
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
    "hp_bar_rendering": 1,
    "head_hitbox_rendering": 1,
    "box_rendering": 1,
    "Bones": 1,
    "nickname": 1,
    "weapon": 1,
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
    "radius": 50,
    "AimKey": "C",
    "circle_opacity": 127,
    "circle_thickness": 2,
    
                          
    "trigger_bot_active": 0,
    "TriggerKey": "X", 
    "triggerbot_between_shots_delay": 30,  # Renamed from triggerbot_delay
    "triggerbot_first_shot_delay": 0,
    "triggerbot_burst_mode": 0,  # Burst mode toggle
    "triggerbot_burst_shots": 3,  # Number of shots per burst (2-5)
    
    # Head-only triggerbot settings
    "head_triggerbot_active": 0,
    "HeadTriggerKey": "Z",
    "head_triggerbot_between_shots_delay": 30,
    "head_triggerbot_first_shot_delay": 0,
    "head_triggerbot_burst_mode": 0,
    "head_triggerbot_burst_shots": 3,
    
                   
    "bhop_enabled": 0,
    "BhopKey": "SPACE",
    
                          
    "auto_accept_enabled": 0,
    
                 
    "topmost": 1,
    "MenuToggleKey": "F8",
    "team_color": "#47A76A",
    "enemy_color": "#C41E3A",
    "aim_circle_color": "#FF0000",
    "center_dot_color": "#FFFFFF",
    "menu_theme_color": "#FF0000",
    "rainbow_fov": 0,
    "rainbow_center_dot": 0,
    "rainbow_menu_theme": 0,
    "low_cpu": 0,
    "fps_limit": 60,
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

def get_weapon_name_by_index(index):
    """Get weapon name by index."""
    weapon_names = {
        32: "P2000", 61: "USP-S", 4: "Glock", 2: "Dual Berettas", 36: "P250",
        30: "Tec-9", 63: "CZ75-Auto", 1: "Desert Eagle", 3: "Five-SeveN", 64: "R8",
        35: "Nova", 25: "XM1014", 27: "MAG-7", 29: "Sawed-Off", 14: "M249", 28: "Negev",
        17: "MAC-10", 23: "MP5-SD", 24: "UMP-45", 19: "P90", 26: "Bizon", 34: "MP9",
        33: "MP7", 10: "FAMAS", 16: "M4A4", 60: "M4A1-S", 8: "AUG", 43: "Galil",
        7: "AK-47", 39: "SG 553", 40: "SSG 08", 9: "AWP", 38: "SCAR-20", 11: "G3SG1",
        43: "Flashbang", 44: "Hegrenade", 45: "Smoke", 46: "Molotov", 47: "Decoy",
        48: "Incgrenage", 49: "C4", 31: "Taser", 42: "Knife", 41: "Knife Gold",
        59: "Knife", 80: "Knife Ghost", 500: "Knife Bayonet", 505: "Knife Flip",
        506: "Knife Gut", 507: "Knife Karambit", 508: "Knife M9", 509: "Knife Tactica",
        512: "Knife Falchion", 514: "Knife Survival Bowie", 515: "Knife Butterfly",
        516: "Knife Rush", 519: "Knife Ursus", 520: "Knife Gypsy Jackknife",
        522: "Knife Stiletto", 523: "Knife Widowmaker"
    }
    return weapon_names.get(index, 'Unknown')

def load_settings():
    """Load settings from config file."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return DEFAULT_SETTINGS.copy()

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
        
                                                              
        initial_theme_color = self.settings.get('menu_theme_color', '#FF0000')
        self.update_menu_theme_styling(initial_theme_color)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("Popsicle CS2 Config")                                       

                               
        app_title = get_app_title()
        
        # Check if tooltips command is enabled
        self.tooltips_enabled = "tooltips" in load_commands()
        
        self.header_label = QtWidgets.QLabel(app_title)
        self.header_label.setAlignment(QtCore.Qt.AlignCenter)
        self.header_label.setMinimumHeight(28)
        header_font = QtGui.QFont('MS PGothic', 14, QtGui.QFont.Bold)
        self.header_label.setFont(header_font)
                                     
        theme_color = self.settings.get('menu_theme_color', '#FF0000')
        self.header_label.setStyleSheet(f"color: {theme_color}; font-family: 'MS PGothic'; font-weight: bold; font-size: 16px;")

        
        esp_container = self.create_esp_container()
        aim_container = self.create_aim_container()
        trigger_container = self.create_trigger_container()
        colors_container = self.create_colors_container()
        misc_container = self.create_misc_container()

        
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(esp_container, "ESP")
        tabs.addTab(aim_container, "Aim")
        tabs.addTab(trigger_container, "Trigger")
        tabs.addTab(colors_container, "Colors")
        tabs.addTab(misc_container, "Misc")
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
        self.update_head_triggerbot_delay_label()
        self.update_head_triggerbot_first_shot_delay_label()
        self.update_head_triggerbot_burst_shots_label()
        self.update_center_dot_size_label()
        self.update_opacity_label()
        self.update_thickness_label()
        self.update_smooth_label()

                                                           
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

                                                                               
        self.setFixedWidth(450)
        
                                             
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

        # Disable focus for all UI elements to prevent keyboard interaction
        self.disable_ui_focus()

    def set_tooltip_if_enabled(self, widget, tooltip_text):
        """Set tooltip only if tooltips are enabled via commands.txt"""
        if hasattr(self, 'tooltips_enabled') and self.tooltips_enabled:
            widget.setToolTip(tooltip_text)

    def disable_ui_focus(self):
        """Disable focus for all interactive UI elements to prevent keyboard shortcuts"""
        try:
            # Disable focus for all checkboxes
            checkboxes = [
                self.esp_rendering_cb, self.line_rendering_cb, self.hp_bar_rendering_cb,
                self.head_hitbox_rendering_cb, self.box_rendering_cb, self.Bones_cb,
                self.nickname_cb, self.show_visibility_cb, self.weapon_cb, self.bomb_esp_cb,
                self.radar_cb, self.center_dot_cb, self.trigger_bot_active_cb,
                self.triggerbot_burst_mode_cb, 
                self.head_trigger_bot_active_cb, self.head_triggerbot_burst_mode_cb,
                self.aim_active_cb, self.aim_circle_visible_cb, self.aim_visibility_cb, 
                self.lock_target_cb, self.disable_crosshair_cb, self.rainbow_fov_cb, 
                self.rainbow_center_dot_cb, self.rainbow_menu_theme_cb, self.auto_accept_cb, 
                self.low_cpu_cb
            ]
            
            for cb in checkboxes:
                if hasattr(self, cb.objectName()) or cb:
                    cb.setFocusPolicy(QtCore.Qt.NoFocus)
            
            # Disable focus for all sliders
            sliders = [
                self.radius_slider, self.opacity_slider, self.thickness_slider,
                self.smooth_slider, self.triggerbot_delay_slider, self.triggerbot_first_shot_delay_slider,
                self.triggerbot_burst_shots_slider, self.head_triggerbot_delay_slider, 
                self.head_triggerbot_first_shot_delay_slider, self.head_triggerbot_burst_shots_slider,
                self.center_dot_size_slider, self.radar_size_slider, self.radar_scale_slider, 
                self.fps_limit_slider
            ]
            
            for slider in sliders:
                if hasattr(self, slider.objectName()) or slider:
                    slider.setFocusPolicy(QtCore.Qt.NoFocus)
            
            # Disable focus for all buttons
            buttons = [
                self.esp_toggle_key_btn, self.trigger_key_btn, self.head_trigger_key_btn,
                self.aim_key_btn, self.bhop_key_btn, self.menu_key_btn, self.team_color_btn,
                self.enemy_color_btn, self.aim_circle_color_btn, self.center_dot_color_btn,
                self.menu_theme_color_btn, self.terminate_btn, self.reset_btn
            ]
            
            for btn in buttons:
                if hasattr(self, btn.objectName()) or btn:
                    btn.setFocusPolicy(QtCore.Qt.NoFocus)
            
            # Disable focus for combo boxes
            comboboxes = [
                self.esp_mode_cb, self.aim_mode_cb, self.aim_mode_distance_cb,
                self.radar_position_combo
            ]
            
            for combo in comboboxes:
                if hasattr(self, combo.objectName()) or combo:
                    combo.setFocusPolicy(QtCore.Qt.NoFocus)
                    
        except Exception:
            pass  # Silently ignore any missing widgets

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

        self.esp_mode_cb = QtWidgets.QComboBox()
        self.esp_mode_cb.addItems(["Enemies Only", "All Players"])
        self.esp_mode_cb.setCurrentIndex(self.settings.get("esp_mode", 1))
        self.esp_mode_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.esp_mode_cb.currentIndexChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.esp_mode_cb, "Choose whether to show ESP for enemies only or all players including teammates.")
        self.esp_mode_cb.setMinimumHeight(22)
        self.esp_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_mode_cb)

        self.line_rendering_cb = QtWidgets.QCheckBox("Draw Lines")
        self.line_rendering_cb.setChecked(self.settings.get("line_rendering", 1) == 1)
        self.line_rendering_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.line_rendering_cb, "Draw lines from the bottom center of your screen to each player's position.")
        self.line_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.line_rendering_cb)

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

        self.weapon_cb = QtWidgets.QCheckBox("Show Weapon")
        self.weapon_cb.setChecked(self.settings.get("weapon", 1) == 1)
        self.weapon_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.weapon_cb, "Display the name of the weapon each player is currently holding.")
        self.weapon_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.weapon_cb)

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

                             
        self.center_dot_cb = QtWidgets.QCheckBox("Draw Center Dot")
        self.center_dot_cb.setChecked(self.settings.get("center_dot", 0) == 1)
        self.center_dot_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.center_dot_cb, "Draw a small dot in the center of your screen as a crosshair reference point.")
        self.center_dot_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.center_dot_cb)

                                
        self.center_dot_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.center_dot_size_slider.setMinimum(1)
        self.center_dot_size_slider.setMaximum(20)
        self.center_dot_size_slider.setValue(self.settings.get('center_dot_size', 3))
        self.center_dot_size_slider.valueChanged.connect(self.update_center_dot_size_label)
        self.set_tooltip_if_enabled(self.center_dot_size_slider, "Adjust the size of the center dot crosshair from 1 (smallest) to 20 (largest) pixels.")
        self.lbl_center_dot_size = QtWidgets.QLabel(f"Center Dot Size: ({self.settings.get('center_dot_size', 3)})")
        self.lbl_center_dot_size.setMinimumHeight(16)
        esp_layout.addWidget(self.lbl_center_dot_size)
        self.center_dot_size_slider.setMinimumHeight(18)
        self.center_dot_size_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.center_dot_size_slider)

                                          
        self.esp_toggle_key_btn = QtWidgets.QPushButton(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")
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

        trigger_label = QtWidgets.QLabel("Trigger Bot Settings")
        trigger_label.setAlignment(QtCore.Qt.AlignCenter)
        trigger_label.setMinimumHeight(18)
        trigger_layout.addWidget(trigger_label)

        self.trigger_bot_active_cb = QtWidgets.QCheckBox("Enable Trigger Bot")
        self.trigger_bot_active_cb.setChecked(self.settings["trigger_bot_active"] == 1)
        self.trigger_bot_active_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.trigger_bot_active_cb, "Automatically shoots when your crosshair is on an enemy while holding the trigger key.")
        self.trigger_bot_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_bot_active_cb)

        # Burst Mode Toggle
        self.triggerbot_burst_mode_cb = QtWidgets.QCheckBox("Burst Mode")
        self.triggerbot_burst_mode_cb.setChecked(self.settings.get("triggerbot_burst_mode", 0) == 1)
        self.triggerbot_burst_mode_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.triggerbot_burst_mode_cb, "Fires a limited number of shots in bursts instead of continuous shooting for better recoil control.")
        self.triggerbot_burst_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_burst_mode_cb)

        # Burst Shots Slider
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
        
        # Between Shots Delay (renamed from Triggerbot Delay)
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
        self.triggerbot_first_shot_delay_slider.setMinimum(0)
        self.triggerbot_first_shot_delay_slider.setMaximum(1000)
        self.triggerbot_first_shot_delay_slider.setValue(self.settings.get("triggerbot_first_shot_delay", 0))
        self.triggerbot_first_shot_delay_slider.valueChanged.connect(self.update_triggerbot_first_shot_delay_label)
        self.set_tooltip_if_enabled(self.triggerbot_first_shot_delay_slider, "Delay before the first shot when trigger key is pressed. Set to 0 for instant shooting, higher values add reaction time delay.")
        self.lbl_first_shot_delay = QtWidgets.QLabel(f"First Shot Delay (ms): ({self.settings.get('triggerbot_first_shot_delay', 0)})")
        self.lbl_first_shot_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_first_shot_delay)
        self.triggerbot_first_shot_delay_slider.setMinimumHeight(18)
        self.triggerbot_first_shot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_first_shot_delay_slider)

        
        self.trigger_key_btn = QtWidgets.QPushButton(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
        self.trigger_key_btn.clicked.connect(lambda: self.record_key('TriggerKey', self.trigger_key_btn))
        self.set_tooltip_if_enabled(self.trigger_key_btn, "Click to set the key that activates trigger bot. Hold this key while aiming at enemies to auto-shoot.")
        self.trigger_key_btn.setMinimumHeight(22)
        self.trigger_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_key_btn)
        self.trigger_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'TriggerKey', self.trigger_key_btn)

        # Separator for head-only triggerbot
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        trigger_layout.addWidget(separator)
        
        head_trigger_label = QtWidgets.QLabel("Head-Only Trigger Bot")
        head_trigger_label.setAlignment(QtCore.Qt.AlignCenter)
        head_trigger_label.setMinimumHeight(18)
        trigger_layout.addWidget(head_trigger_label)

        self.head_trigger_bot_active_cb = QtWidgets.QCheckBox("Enable Head-Only Trigger Bot")
        self.head_trigger_bot_active_cb.setChecked(self.settings.get("head_triggerbot_active", 0) == 1)
        self.head_trigger_bot_active_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.head_trigger_bot_active_cb, "Automatically shoots when crosshair is on enemy head while holding the head trigger key.")
        self.head_trigger_bot_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.head_trigger_bot_active_cb)

        # Head Trigger Bot Burst Mode Toggle
        self.head_triggerbot_burst_mode_cb = QtWidgets.QCheckBox("Head Burst Mode")
        self.head_triggerbot_burst_mode_cb.setChecked(self.settings.get("head_triggerbot_burst_mode", 0) == 1)
        self.head_triggerbot_burst_mode_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.head_triggerbot_burst_mode_cb, "Fires limited shots in bursts for head-only triggerbot instead of continuous shooting.")
        self.head_triggerbot_burst_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.head_triggerbot_burst_mode_cb)

        # Head Trigger Bot Burst Shots Slider
        self.head_triggerbot_burst_shots_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.head_triggerbot_burst_shots_slider.setMinimum(2)
        self.head_triggerbot_burst_shots_slider.setMaximum(5)
        self.head_triggerbot_burst_shots_slider.setValue(self.settings.get("head_triggerbot_burst_shots", 3))
        self.head_triggerbot_burst_shots_slider.valueChanged.connect(self.update_head_triggerbot_burst_shots_label)
        self.set_tooltip_if_enabled(self.head_triggerbot_burst_shots_slider, "Number of shots per burst for head-only triggerbot when burst mode is enabled.")
        self.lbl_head_burst_shots = QtWidgets.QLabel(f"Head Burst Shots: ({self.settings.get('head_triggerbot_burst_shots', 3)})")
        self.lbl_head_burst_shots.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_head_burst_shots)
        self.head_triggerbot_burst_shots_slider.setMinimumHeight(18)
        self.head_triggerbot_burst_shots_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.head_triggerbot_burst_shots_slider)
        
        # Head Trigger Bot Between Shots Delay
        self.head_triggerbot_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.head_triggerbot_delay_slider.setMinimum(0)
        self.head_triggerbot_delay_slider.setMaximum(1000)
        self.head_triggerbot_delay_slider.setValue(self.settings.get("head_triggerbot_between_shots_delay", 30))
        self.head_triggerbot_delay_slider.valueChanged.connect(self.update_head_triggerbot_delay_label)
        self.set_tooltip_if_enabled(self.head_triggerbot_delay_slider, "Delay in milliseconds between each shot for head-only triggerbot.")
        self.lbl_head_delay = QtWidgets.QLabel(f"Head Between Shots Delay (ms): ({self.settings.get('head_triggerbot_between_shots_delay', 30)})")
        self.lbl_head_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_head_delay)
        self.head_triggerbot_delay_slider.setMinimumHeight(18)
        self.head_triggerbot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.head_triggerbot_delay_slider)

        # Head Trigger Bot First Shot Delay
        self.head_triggerbot_first_shot_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.head_triggerbot_first_shot_delay_slider.setMinimum(0)
        self.head_triggerbot_first_shot_delay_slider.setMaximum(1000)
        self.head_triggerbot_first_shot_delay_slider.setValue(self.settings.get("head_triggerbot_first_shot_delay", 0))
        self.head_triggerbot_first_shot_delay_slider.valueChanged.connect(self.update_head_triggerbot_first_shot_delay_label)
        self.set_tooltip_if_enabled(self.head_triggerbot_first_shot_delay_slider, "Delay before first shot for head-only triggerbot when trigger key is pressed.")
        self.lbl_head_first_shot_delay = QtWidgets.QLabel(f"Head First Shot Delay (ms): ({self.settings.get('head_triggerbot_first_shot_delay', 0)})")
        self.lbl_head_first_shot_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_head_first_shot_delay)
        self.head_triggerbot_first_shot_delay_slider.setMinimumHeight(18)
        self.head_triggerbot_first_shot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.head_triggerbot_first_shot_delay_slider)

        # Head Trigger Key Button
        self.head_trigger_key_btn = QtWidgets.QPushButton(f"Head TriggerKey: {self.settings.get('HeadTriggerKey', 'Z')}")
        self.head_trigger_key_btn.clicked.connect(lambda: self.record_key('HeadTriggerKey', self.head_trigger_key_btn))
        self.set_tooltip_if_enabled(self.head_trigger_key_btn, "Click to set the key for head-only triggerbot. Hold this key while aiming at enemy heads.")
        self.head_trigger_key_btn.setMinimumHeight(22)
        self.head_trigger_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.head_trigger_key_btn)
        self.head_trigger_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'HeadTriggerKey', self.head_trigger_key_btn)

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

        
        self.radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radius_slider.setMinimum(0)
        self.radius_slider.setMaximum(100)
        self.radius_slider.setValue(self.settings.get("radius", 50))
        self.radius_slider.valueChanged.connect(self.update_radius_label)
        self.set_tooltip_if_enabled(self.radius_slider, "Size of the aim circle area in pixels. Aimbot only targets enemies within this circle.")
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
        self.set_tooltip_if_enabled(self.opacity_slider, "Transparency of the aim circle. 0 = invisible, 255 = fully opaque.")
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
        self.set_tooltip_if_enabled(self.thickness_slider, "Thickness of the aim circle outline in pixels. Higher values make the circle border thicker.")
        self.lbl_thickness = QtWidgets.QLabel(f"Circle Thickness: ({self.settings.get('circle_thickness', 2)})")
        self.lbl_thickness.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_thickness)
        self.thickness_slider.setMinimumHeight(18)
        self.thickness_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.thickness_slider)

                                          
        self.smooth_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(2000000)
        self.smooth_slider.setValue(self.settings.get("aim_smoothness", 50))
        self.smooth_slider.valueChanged.connect(self.update_smooth_label)
        self.set_tooltip_if_enabled(self.smooth_slider, "Controls how smooth the aimbot movement is. Lower = instant snap, higher = gradual smooth aiming.")
        self.lbl_smooth = QtWidgets.QLabel(f"Aim Smoothness: ({self.settings.get('aim_smoothness', 50)})")
        self.lbl_smooth.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_smooth)
        self.smooth_slider.setMinimumHeight(18)
        self.smooth_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.smooth_slider)

                                      
        self.aim_circle_visible_cb = QtWidgets.QCheckBox("Show Aim Circle")
        self.aim_circle_visible_cb.setChecked(self.settings.get("aim_circle_visible", 1) == 1)
        self.aim_circle_visible_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.aim_circle_visible_cb, "Display the circular area showing aimbot's targeting zone around your crosshair.")
        self.aim_circle_visible_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_circle_visible_cb)

        self.aim_key_btn = QtWidgets.QPushButton(f"AimKey: {self.settings.get('AimKey', 'C')}")
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

                           
        self.team_color_btn = QtWidgets.QPushButton('Team Color')
        team_hex = self.settings.get('team_color', '#47A76A')
        team_text_color = self.get_contrasting_text_color(team_hex)
        self.team_color_btn.setStyleSheet(f'background-color: {team_hex}; color: {team_text_color};')
        self.team_color_btn.clicked.connect(lambda: self.pick_color('team_color', self.team_color_btn))
        self.set_tooltip_if_enabled(self.team_color_btn, "Color used for drawing ESP elements of your teammates.")
        self.team_color_btn.setMinimumHeight(28)
        self.team_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.team_color_btn)

                            
        self.enemy_color_btn = QtWidgets.QPushButton('Enemy Color')
        enemy_hex = self.settings.get('enemy_color', '#C41E3A')
        enemy_text_color = self.get_contrasting_text_color(enemy_hex)
        self.enemy_color_btn.setStyleSheet(f'background-color: {enemy_hex}; color: {enemy_text_color};')
        self.enemy_color_btn.clicked.connect(lambda: self.pick_color('enemy_color', self.enemy_color_btn))
        self.set_tooltip_if_enabled(self.enemy_color_btn, "Color used for drawing ESP elements of enemy players.")
        self.enemy_color_btn.setMinimumHeight(28)
        self.enemy_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.enemy_color_btn)

                                 
        self.aim_circle_color_btn = QtWidgets.QPushButton('Aim Circle Color')
        aim_hex = self.settings.get('aim_circle_color', '#FF0000')
        aim_text_color = self.get_contrasting_text_color(aim_hex)
        self.aim_circle_color_btn.setStyleSheet(f'background-color: {aim_hex}; color: {aim_text_color};')
        self.aim_circle_color_btn.clicked.connect(lambda: self.pick_color('aim_circle_color', self.aim_circle_color_btn))
        self.set_tooltip_if_enabled(self.aim_circle_color_btn, "Color of the aim circle that shows aimbot's targeting area.")
        self.aim_circle_color_btn.setMinimumHeight(28)
        self.aim_circle_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.aim_circle_color_btn)

                                 
        self.center_dot_color_btn = QtWidgets.QPushButton('Center Dot Color')
        center_dot_hex = self.settings.get('center_dot_color', '#FFFFFF')
        center_dot_text_color = self.get_contrasting_text_color(center_dot_hex)
        self.center_dot_color_btn.setStyleSheet(f'background-color: {center_dot_hex}; color: {center_dot_text_color};')
        self.center_dot_color_btn.clicked.connect(lambda: self.pick_color('center_dot_color', self.center_dot_color_btn))
        self.set_tooltip_if_enabled(self.center_dot_color_btn, "Color of the center crosshair dot displayed in the middle of your screen.")
        self.center_dot_color_btn.setMinimumHeight(28)
        self.center_dot_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.center_dot_color_btn)

                                 
        self.menu_theme_color_btn = QtWidgets.QPushButton('Menu Theme Color')
        menu_theme_hex = self.settings.get('menu_theme_color', '#FF0000')
        menu_theme_text_color = self.get_contrasting_text_color(menu_theme_hex)
        self.menu_theme_color_btn.setStyleSheet(f'background-color: {menu_theme_hex}; color: {menu_theme_text_color};')
        self.menu_theme_color_btn.clicked.connect(lambda: self.pick_color('menu_theme_color', self.menu_theme_color_btn))
        self.set_tooltip_if_enabled(self.menu_theme_color_btn, "Primary color theme for the configuration menu interface.")
        self.menu_theme_color_btn.setMinimumHeight(28)
        self.menu_theme_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.menu_theme_color_btn)

                                   
        self.rainbow_fov_cb = QtWidgets.QCheckBox("Rainbow FOV Circle")
        self.rainbow_fov_cb.setChecked(self.settings.get('rainbow_fov', 0) == 1)
        self.rainbow_fov_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.rainbow_fov_cb, "Makes the aim circle continuously cycle through rainbow colors instead of using a fixed color.")
        self.rainbow_fov_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.rainbow_fov_cb)

                                   
        self.rainbow_center_dot_cb = QtWidgets.QCheckBox("Rainbow Center Dot")
        self.rainbow_center_dot_cb.setChecked(self.settings.get('rainbow_center_dot', 0) == 1)
        self.rainbow_center_dot_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.rainbow_center_dot_cb, "Makes the center crosshair dot continuously cycle through rainbow colors instead of using a fixed color.")
        self.rainbow_center_dot_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.rainbow_center_dot_cb)

                                   
        self.rainbow_menu_theme_cb = QtWidgets.QCheckBox("Rainbow Menu Theme")
        self.rainbow_menu_theme_cb.setChecked(self.settings.get('rainbow_menu_theme', 0) == 1)
        self.rainbow_menu_theme_cb.stateChanged.connect(self.save_settings)
        self.set_tooltip_if_enabled(self.rainbow_menu_theme_cb, "Makes the menu theme color continuously cycle through rainbow colors instead of using a fixed color.")
        self.rainbow_menu_theme_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
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

                                
        self.menu_key_btn = QtWidgets.QPushButton(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'M')}")
        self.menu_key_btn.clicked.connect(lambda: self.record_key('MenuToggleKey', self.menu_key_btn))
        self.set_tooltip_if_enabled(self.menu_key_btn, "Click to set the key for opening/closing this configuration menu during gameplay.")
        self.menu_key_btn.setMinimumHeight(22)
        self.menu_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.menu_key_btn)
        self.menu_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'MenuToggleKey', self.menu_key_btn)

                                    
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

                              
        self.bhop_cb = QtWidgets.QCheckBox("Bhop")
        self.bhop_cb.setChecked(self.settings.get("bhop_enabled", 0) == 1)
        self.bhop_cb.stateChanged.connect(self.on_bhop_changed)
        self.set_tooltip_if_enabled(self.bhop_cb, "Automatically times jump inputs for bunny hopping when holding the bhop key.")
        self.bhop_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.bhop_cb)

                         
        self.bhop_key_btn = QtWidgets.QPushButton(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")
        self.bhop_key_btn.clicked.connect(lambda: self.record_key('BhopKey', self.bhop_key_btn))
        self.set_tooltip_if_enabled(self.bhop_key_btn, "Click to set the key that activates bunny hopping. Hold this key to automatically time your jumps.")
        self.bhop_key_btn.setMinimumHeight(22)
        self.bhop_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.bhop_key_btn)
        self.bhop_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'BhopKey', self.bhop_key_btn)

        self.terminate_btn = QtWidgets.QPushButton("Exit Script (Hold ESC or click here)")
        self.set_tooltip_if_enabled(self.terminate_btn, "Close the entire script and all its processes. You can also hold ESC for 3 seconds to exit.")
        self.terminate_btn.clicked.connect(self.on_terminate_clicked)
        self.terminate_btn.setMinimumHeight(22)
        self.terminate_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.reset_btn = QtWidgets.QPushButton("Reset Config")
        self.set_tooltip_if_enabled(self.reset_btn, "Reset all settings to their default values. This will restore the original configuration and cannot be undone.")
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.reset_btn.setMinimumHeight(22)
        self.reset_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.reset_btn)

        misc_layout.addWidget(self.terminate_btn)

        misc_container.setLayout(misc_layout)
        misc_container.setStyleSheet("background-color: #020203; border-radius: 10px;")
        return misc_container

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
        try:
            
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('terminate')
        except Exception:
            pass
        try:
                                             
            if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                os.remove(KEYBIND_COOLDOWNS_FILE)
        except Exception:
            pass
        try:
            
            app = QtWidgets.QApplication.instance()
            if app is not None:
                app.quit()
            else:
                self.close()
        except Exception:
            pass

    def on_reset_clicked(self):
        """Restore DEFAULT_SETTINGS and update every configurable UI element in one atomic operation.

        This blocks widget signals while values are applied to avoid incremental saves
        or partial state, persists the new config once, applies the topmost
        setting, then unblocks signals and persists again as a final confirmation.
        """
        
        widget_names = [
            'esp_rendering_cb', 'esp_mode_cb', 'line_rendering_cb', 'hp_bar_rendering_cb',
            'head_hitbox_rendering_cb', 'box_rendering_cb', 'Bones_cb', 'nickname_cb', 'show_visibility_cb', 'weapon_cb', 'bomb_esp_cb',
            'center_dot_cb', 'trigger_bot_active_cb', 'aim_active_cb', 'aim_circle_visible_cb', 'radius_slider', 'opacity_slider', 'thickness_slider',
            'smooth_slider', 'center_dot_size_slider',
            'aim_visibility_cb', 'lock_target_cb', 'aim_mode_cb', 'aim_key_btn', 'trigger_key_btn', 'menu_key_btn', 'bhop_key_btn',
            'team_color_btn', 'enemy_color_btn', 'aim_circle_color_btn', 'center_dot_color_btn', 'menu_theme_color_btn', 'rainbow_fov_cb', 'rainbow_center_dot_cb', 'rainbow_menu_theme_cb',
            'low_cpu_cb', 'fps_limit_slider', 'radar_position_combo'
        ]
        widgets = [getattr(self, name, None) for name in widget_names]

        try:
            
            self.settings = DEFAULT_SETTINGS.copy()
            save_settings(self.settings)

            
            for w in widgets:
                try:
                    if w is not None:
                        w.blockSignals(True)
                except Exception:
                    pass

            
            try:
                if getattr(self, 'esp_rendering_cb', None) is not None:
                    self.esp_rendering_cb.setChecked(self.settings.get('esp_rendering', 1) == 1)
                if getattr(self, 'esp_mode_cb', None) is not None:
                    self.esp_mode_cb.setCurrentIndex(self.settings.get('esp_mode', 1))

                
                mapping = {
                    'line_rendering_cb': 'line_rendering',
                    'hp_bar_rendering_cb': 'hp_bar_rendering',
                    'head_hitbox_rendering_cb': 'head_hitbox_rendering',
                    'box_rendering_cb': 'box_rendering',
                    'Bones_cb': 'Bones',
                    'nickname_cb': 'nickname',
                    'show_visibility_cb': 'show_visibility',
                    'aim_visibility_cb': 'aim_visibility_check',
                    'lock_target_cb': 'aim_lock_target',
                    'weapon_cb': 'weapon',
                    'bomb_esp_cb': 'bomb_esp',
                    'radar_cb': 'radar_enabled',
                    'trigger_bot_active_cb': 'trigger_bot_active',
                    'aim_active_cb': 'aim_active',
                    'aim_circle_visible_cb': 'aim_circle_visible',
                    'rainbow_fov_cb': 'rainbow_fov', 'rainbow_center_dot_cb': 'rainbow_center_dot', 'rainbow_menu_theme_cb': 'rainbow_menu_theme', 'low_cpu_cb': 'low_cpu'
                }
                for cb_name, key in mapping.items():
                    cb = getattr(self, cb_name, None)
                    if cb is not None:
                        cb.setChecked(self.settings.get(key, 0) == 1)

                
                if getattr(self, 'radius_slider', None) is not None:
                    self.radius_slider.setValue(self.settings.get('radius', 50))
                if getattr(self, 'opacity_slider', None) is not None:
                    self.opacity_slider.setValue(self.settings.get('circle_opacity', 16))
                if getattr(self, 'thickness_slider', None) is not None:
                    self.thickness_slider.setValue(self.settings.get('circle_thickness', 2))
                if getattr(self, 'smooth_slider', None) is not None:
                    self.smooth_slider.setValue(self.settings.get('aim_smoothness', 50))
                if getattr(self, 'triggerbot_delay_slider', None) is not None:
                    self.triggerbot_delay_slider.setValue(self.settings.get('triggerbot_delay', 30))
                
                               
                if getattr(self, 'radar_size_slider', None) is not None:
                    self.radar_size_slider.setValue(self.settings.get('radar_size', 200))
                if getattr(self, 'radar_scale_slider', None) is not None:
                    self.radar_scale_slider.setValue(int(self.settings.get('radar_scale', 5.0) * 10))
                if getattr(self, 'radar_position_combo', None) is not None:
                    position = self.settings.get('radar_position', 'Top Right')
                    index = self.radar_position_combo.findText(position)
                    if index >= 0:
                        self.radar_position_combo.setCurrentIndex(index)
                if getattr(self, 'triggerbot_first_shot_delay_slider', None) is not None:
                    self.triggerbot_first_shot_delay_slider.setValue(self.settings.get('triggerbot_first_shot_delay', 0))
                if getattr(self, 'center_dot_size_slider', None) is not None:
                    self.center_dot_size_slider.setValue(self.settings.get('center_dot_size', 3))

                                                               
                try:
                    if hasattr(self, 'update_radius_label'):
                        self.update_radius_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_opacity_label'):
                        self.update_opacity_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_thickness_label'):
                        self.update_thickness_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_smooth_label'):
                        self.update_smooth_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_triggerbot_delay_label'):
                        self.update_triggerbot_delay_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_triggerbot_first_shot_delay_label'):
                        self.update_triggerbot_first_shot_delay_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_center_dot_size_label'):
                        self.update_center_dot_size_label()
                except Exception:
                    pass

                
                if getattr(self, 'aim_key_btn', None) is not None:
                    self.aim_key_btn.setText(f"AimKey: {self.settings.get('AimKey', 'C')}")
                if getattr(self, 'trigger_key_btn', None) is not None:
                    self.trigger_key_btn.setText(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
                if getattr(self, 'menu_key_btn', None) is not None:
                    self.menu_key_btn.setText(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'F8')}")
                if getattr(self, 'bhop_key_btn', None) is not None:
                    self.bhop_key_btn.setText(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")

                if getattr(self, 'esp_toggle_key_btn', None) is not None:
                    self.esp_toggle_key_btn.setText(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")

                                                                
                if getattr(self, 'aim_mode_cb', None) is not None:
                    self.aim_mode_cb.setCurrentIndex(self.settings.get('aim_bone_target', DEFAULT_SETTINGS.get('aim_bone_target', 1)))

                
                try:
                    if getattr(self, 'team_color_btn', None) is not None:
                        team_hex = self.settings.get('team_color', DEFAULT_SETTINGS.get('team_color'))
                        self.team_color_btn.setStyleSheet(f'background-color: {team_hex}; color: white;')
                    if getattr(self, 'enemy_color_btn', None) is not None:
                        enemy_hex = self.settings.get('enemy_color', DEFAULT_SETTINGS.get('enemy_color'))
                        self.enemy_color_btn.setStyleSheet(f'background-color: {enemy_hex}; color: white;')
                    if getattr(self, 'aim_circle_color_btn', None) is not None:
                        aim_hex = self.settings.get('aim_circle_color', DEFAULT_SETTINGS.get('aim_circle_color'))
                        self.aim_circle_color_btn.setStyleSheet(f'background-color: {aim_hex}; color: white;')
                    if getattr(self, 'menu_theme_color_btn', None) is not None:
                        menu_theme_hex = self.settings.get('menu_theme_color', DEFAULT_SETTINGS.get('menu_theme_color'))
                        self.menu_theme_color_btn.setStyleSheet(f'background-color: {menu_theme_hex}; color: white;')
                        self.update_menu_theme_styling(menu_theme_hex)
                except Exception:
                    pass

                                                                    
                try:
                    self.apply_topmost()
                except Exception:
                    pass

            except Exception as e:
                pass
        finally:
            
            for w in widgets:
                try:
                    if w is not None:
                        w.blockSignals(False)
                except Exception:
                    pass
            try:
                                                         
                self.initialize_fps_slider_state()
                save_settings(self.settings)
            except Exception:
                pass

    def save_settings(self):
        
        self.settings["esp_rendering"] = 1 if self.esp_rendering_cb.isChecked() else 0
        self.settings["esp_mode"] = self.esp_mode_cb.currentIndex()
        self.settings["line_rendering"] = 1 if self.line_rendering_cb.isChecked() else 0
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
        self.settings["weapon"] = 1 if self.weapon_cb.isChecked() else 0
        self.settings["bomb_esp"] = 1 if self.bomb_esp_cb.isChecked() else 0
        self.settings["radar_enabled"] = 1 if self.radar_cb.isChecked() else 0
        self.settings["aim_active"] = 1 if self.aim_active_cb.isChecked() else 0
        
                                       
        try:
            self.settings["aim_circle_visible"] = 1 if getattr(self, 'aim_circle_visible_cb', None) and self.aim_circle_visible_cb.isChecked() else 0
        except Exception:
            pass

        
        self.settings["radius"] = self.radius_slider.value()
        
                        
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

        # Head-only triggerbot settings
        if getattr(self, "head_trigger_bot_active_cb", None):
            self.settings["head_triggerbot_active"] = 1 if self.head_trigger_bot_active_cb.isChecked() else 0
        if getattr(self, "head_triggerbot_burst_mode_cb", None):
            self.settings["head_triggerbot_burst_mode"] = 1 if self.head_triggerbot_burst_mode_cb.isChecked() else 0
        if getattr(self, "head_triggerbot_delay_slider", None):
            self.settings["head_triggerbot_between_shots_delay"] = self.head_triggerbot_delay_slider.value()
        if getattr(self, "head_triggerbot_first_shot_delay_slider", None):
            self.settings["head_triggerbot_first_shot_delay"] = self.head_triggerbot_first_shot_delay_slider.value()
        if getattr(self, "head_triggerbot_burst_shots_slider", None):
            self.settings["head_triggerbot_burst_shots"] = self.head_triggerbot_burst_shots_slider.value()

        if getattr(self, "center_dot_size_slider", None):
            self.settings["center_dot_size"] = self.center_dot_size_slider.value()

        
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

        self.settings["aim_bone_target"] = self.aim_mode_cb.currentIndex()
        self.settings["aim_mode_distance"] = self.aim_mode_distance_cb.currentIndex()

        
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

        try:
            if getattr(self, 'head_trigger_key_btn', None) is not None:
                text = self.head_trigger_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["HeadTriggerKey"] = val
        except Exception:
            pass

        
        self.settings["circle_opacity"] = self.opacity_slider.value()

        
        self.settings["circle_thickness"] = self.thickness_slider.value()

                                                                 
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
            self.settings["aim_visibility_check"] = 1 if self.aim_visibility_cb.isChecked() else 0
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
            if getattr(self, 'bhop_key_btn', None) is not None:
                text = self.bhop_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["BhopKey"] = val
        except Exception:
            pass
        
        try:
            pass
        except Exception:
            pass
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
                        
                        short = settings_key
                        if '_' in settings_key:
                            short = settings_key.split('_')[0]
                        btn.setText(f"{short.capitalize()}: {val}")
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
            
            # Calculate relative luminance using WCAG formula
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
            
            # Return black text for light backgrounds, white text for dark backgrounds
            return 'black' if luminance > 0.5 else 'white'
        except:
            # Fallback to white text if color parsing fails
            return 'white'

    def pick_color(self, settings_key: str, btn: QtWidgets.QPushButton):
        # Temporarily pause rainbow menu timer to prevent interference with color dialog
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
            # Restart rainbow menu timer if it was active before
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
                global RAINBOW_HUE
                                                                                               
                if (self.settings.get('rainbow_fov', 0) != 1 and 
                    self.settings.get('rainbow_center_dot', 0) != 1):
                    RAINBOW_HUE = (RAINBOW_HUE + 0.005) % 1.0
                
                r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE, 1.0, 1.0)]
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

    def check_menu_toggle(self):
        
        try:
            
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
                    if time.time() - self._escape_hold_start >= 1.20:
                        
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
        val = self.radius_slider.value()
        self.lbl_radius.setText(f"Aim Radius: ({val})")
        self.save_settings()

    def update_opacity_label(self):
        val = self.opacity_slider.value()
        self.lbl_opacity.setText(f"Circle Transparency: ({val})")
        self.save_settings()

    def update_thickness_label(self):
        val = self.thickness_slider.value()
        self.lbl_thickness.setText(f"Circle Thickness: ({val})")
        self.save_settings()

    def update_smooth_label(self):
        val = self.smooth_slider.value()
        self.lbl_smooth.setText(f"Aim Smoothness: ({val})")
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

    def update_head_triggerbot_delay_label(self):
        self.lbl_head_delay.setText(f"Head Between Shots Delay (ms): ({self.head_triggerbot_delay_slider.value()})")
        self.save_settings()

    def update_head_triggerbot_first_shot_delay_label(self):
        self.lbl_head_first_shot_delay.setText(f"Head First Shot Delay (ms): ({self.head_triggerbot_first_shot_delay_slider.value()})")
        self.save_settings()

    def update_head_triggerbot_burst_shots_label(self):
        self.lbl_head_burst_shots.setText(f"Head Burst Shots: ({self.head_triggerbot_burst_shots_slider.value()})")
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

def configurator():
                                                                            
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
    
    debug_print("Using default Qt styling - no themes applied")
    
    window = ConfigWindow()
    
                                                                
    if window.is_game_window_active():
        window.show()
    
    sys.exit(app.exec())

class ESPWindow(QtWidgets.QWidget):
    def __init__(self, settings, window_width=None, window_height=None):
        super().__init__()
        self.settings = settings
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
        self.settings = load_settings()
        
                                                                           
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
                render_aim_circle(self.scene, self.window_width, self.window_height, self.settings)
            
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
        center_dot_enabled = settings.get('center_dot', 0) == 1
        if center_dot_enabled:
            center_x = window_width / 2
            center_y = window_height / 2
            dot_size = settings.get('center_dot_size', 3)
            
                                       
            if settings.get('rainbow_center_dot', 0) == 1:
                try:
                    global RAINBOW_HUE
                                                                    
                    RAINBOW_HUE = (RAINBOW_HUE + 0.005) % 1.0
                    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE, 1.0, 1.0)]
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
    """Render aim circle independently of ESP settings"""
    try:
        aim_circle_visible = settings.get('aim_circle_visible', 1) == 1
        if aim_circle_visible and 'radius' in settings and settings.get('radius', 0) != 0:
            center_x = window_width / 2
            center_y = window_height / 2
            screen_radius = settings['radius'] / 100.0 * min(center_x, center_y)
            opacity = settings.get("circle_opacity", 16)
            
            global RAINBOW_HUE
            if settings.get('rainbow_fov', 0) == 1:
                try:
                                                                                           
                                                                                       
                    if settings.get('rainbow_center_dot', 0) != 1:
                        RAINBOW_HUE = (RAINBOW_HUE + 0.005) % 1.0
                    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE, 1.0, 1.0)]
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

def render_radar(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    """Render radar showing enemy positions"""
    try:
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
                    # Determine text color based on defuse time vs bomb time
                    if DefuseTime > BombTime:
                        text_color = QtGui.QColor(0, 255, 0)  # Green - defuse will succeed
                    else:
                        text_color = QtGui.QColor(255, 0, 0)  # Red - defuse will fail
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
                                   
    if settings.get('esp_rendering', 1) == 0:
        return
    
                                                        
    esp_mode = settings.get('esp_mode', 1)
    
                                                     
    box_rendering = settings.get('box_rendering', 1) == 1
    line_rendering = settings.get('line_rendering', 1) == 1
    hp_bar_rendering = settings.get('hp_bar_rendering', 1) == 1
    head_hitbox_rendering = settings.get('head_hitbox_rendering', 1) == 1
    bones_rendering = settings.get('Bones', 0) == 1
    nickname_rendering = settings.get('nickname', 0) == 1
    weapon_rendering = settings.get('weapon', 0) == 1
    
                                                                
    if not (box_rendering or line_rendering or hp_bar_rendering or head_hitbox_rendering or 
            bones_rendering or nickname_rendering or weapon_rendering):
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
    no_center_y = window_height * 0.9
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
            
                                                             
            weapon_name = ""
            if weapon_rendering:
                try:
                    weapon_pointer = pm.read_longlong(entity_pawn_addr + m_pClippingWeapon)
                    weapon_index = pm.read_int(weapon_pointer + m_AttributeManager + m_Item + m_iItemDefinitionIndex)
                    weapon_name = get_weapon_name_by_index(weapon_index)
                except Exception:
                    weapon_name = "Unknown"

                                      
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
                    bottom_left_x = head_pos[0] - (head_pos[0] - leg_pos[0]) // 2
                    bottom_y = leg_pos[1]
                                                              
                    line_pen = QtGui.QPen(color, 2)                       
                    line_pen.setCapStyle(QtCore.Qt.RoundCap)                                  
                    line = scene.addLine(bottom_left_x, bottom_y, no_center_x, no_center_y, line_pen)
                
                                       
                if box_rendering:
                                                                     
                    box_pen = QtGui.QPen(color, 2)                                             
                    box_pen.setCapStyle(QtCore.Qt.SquareCap)                                  
                    box_pen.setJoinStyle(QtCore.Qt.MiterJoin)                 
                    rect = scene.addRect(QtCore.QRectF(leftX, head_pos[1], rightX - leftX, leg_pos[1] - head_pos[1]), box_pen, QtCore.Qt.NoBrush)

                                          
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
                    draw_Bones(scene, pm, bone_matrix, view_matrix, window_width, window_height)

                                                     
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
                
                                                   
                if weapon_rendering and weapon_name:
                    font_size = max(6, min(18, deltaZ / 25))
                    font = QtGui.QFont('MS PGothic', font_size, QtGui.QFont.Bold)
                    font.setHintingPreference(QtGui.QFont.PreferFullHinting)                         
                    weapon_name_text = scene.addText(weapon_name, font)
                    text_rect = weapon_name_text.boundingRect()
                    weapon_name_x = head_pos[0] - text_rect.width() / 2
                    weapon_name_y = head_pos[1] + deltaZ
                    weapon_name_text.setPos(weapon_name_x, weapon_name_y)
                    weapon_name_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                    
                                                   
                    weapon_shadow_text = scene.addText(weapon_name, font)
                    weapon_shadow_text.setPos(weapon_name_x + 1, weapon_name_y + 1)
                    weapon_shadow_text.setDefaultTextColor(QtGui.QColor(0, 0, 0, 150))
                    weapon_shadow_text.setZValue(-1)                               


            except:
                return
        except:
            return

def draw_Bones(scene, pm, bone_matrix, view_matrix, width, height):
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
                scene.addLine(
                    bone_positions[connection[0]][0], bone_positions[connection[0]][1],
                    bone_positions[connection[1]][0], bone_positions[connection[1]][1],
                    QtGui.QPen(QtGui.QColor(255, 255, 255, 128), 1)
                )
    except Exception as e:
        pass

def esp_main():
    settings = load_settings()
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
        "triggerbot_first_shot_delay": 0,
        # Head-only triggerbot settings
        "HeadTriggerKey": "Z",
        "head_triggerbot_active": 0,
        "head_triggerbot_between_shots_delay": 30,
        "head_triggerbot_burst_mode": 0,
        "head_triggerbot_burst_shots": 3,
        "head_triggerbot_first_shot_delay": 0
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
        head_trigger_key_pressed = False
        first_shot_time = None
        head_first_shot_time = None
        burst_shot_count = 0  # Track shots fired in current burst
        head_burst_shot_count = 0
        last_burst_time = 0   # Track time of last burst
        head_last_burst_time = 0
        
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
                # Regular triggerbot settings
                trigger_bot_active = settings.get("trigger_bot_active", 0)
                keyboards = settings.get("TriggerKey", "X")
                between_shots_delay_ms = settings.get("triggerbot_between_shots_delay", 30)
                first_shot_delay_ms = settings.get("triggerbot_first_shot_delay", 0)
                burst_mode = settings.get("triggerbot_burst_mode", 0)
                burst_shots = settings.get("triggerbot_burst_shots", 3)
                vk = key_str_to_vk(keyboards)
                
                # Head-only triggerbot settings
                head_triggerbot_active = settings.get("head_triggerbot_active", 0)
                head_keyboards = settings.get("HeadTriggerKey", "Z")
                head_between_shots_delay_ms = settings.get("head_triggerbot_between_shots_delay", 30)
                head_first_shot_delay_ms = settings.get("head_triggerbot_first_shot_delay", 0)
                head_burst_mode = settings.get("head_triggerbot_burst_mode", 0)
                head_burst_shots = settings.get("head_triggerbot_burst_shots", 3)
                head_vk = key_str_to_vk(head_keyboards)
                
                # Check regular triggerbot key state
                if is_keybind_on_global_cooldown("TriggerKey"):
                    key_currently_pressed = False
                else:
                    key_currently_pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                
                # Check head-only triggerbot key state  
                if is_keybind_on_global_cooldown("HeadTriggerKey"):
                    head_key_currently_pressed = False
                else:
                    head_key_currently_pressed = head_vk != 0 and (win32api.GetAsyncKeyState(head_vk) & 0x8000) != 0
                
                # Handle regular triggerbot key transitions
                if key_currently_pressed and not trigger_key_pressed:
                    trigger_key_pressed = True
                    first_shot_time = time.time()
                elif not key_currently_pressed and trigger_key_pressed:
                    trigger_key_pressed = False
                    first_shot_time = None
                
                # Handle head-only triggerbot key transitions
                if head_key_currently_pressed and not head_trigger_key_pressed:
                    head_trigger_key_pressed = True
                    head_first_shot_time = time.time()
                elif not head_key_currently_pressed and head_trigger_key_pressed:
                    head_trigger_key_pressed = False
                    head_first_shot_time = None
                
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
                                                        if not _check_target_valid(pm, client, 0):
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
                
                # Process head-only triggerbot
                if head_key_currently_pressed and head_triggerbot_active == 1:
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
                                # Always head-only for head triggerbot
                                should_shoot = False
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
                                
                                if should_shoot:
                                    current_time = time.time()
                                    
                                    # Handle first shot delay
                                    if head_first_shot_time is None or current_time - head_first_shot_time >= (head_first_shot_delay_ms / 1000.0):
                                        if not head_burst_mode:
                                            # Normal mode - continuous shooting with delay
                                            try:
                                                mouse.press(Button.left)
                                                mouse.release(Button.left)
                                                if head_first_shot_time is not None:
                                                    head_first_shot_time = None                          
                                                head_last_shot_time = current_time
                                                
                                                # Continue shooting while key is held
                                                while head_key_currently_pressed and head_triggerbot_active == 1:
                                                    time.sleep(0.001)                     
                                                    current_time = time.time()
                                                    if current_time - head_last_shot_time >= (head_between_shots_delay_ms / 1000.0):
                                                        head_key_currently_pressed = head_vk != 0 and (win32api.GetAsyncKeyState(head_vk) & 0x8000) != 0
                                                        if not head_key_currently_pressed:
                                                            break
                                                        head_triggerbot_active = settings.get("head_triggerbot_active", 0)
                                                        if head_triggerbot_active != 1:
                                                            break
                                                        
                                                        # Re-check target validity for continuous shooting (always head-only)
                                                        if not _check_target_valid(pm, client, True):
                                                            break
                                                            
                                                        mouse.press(Button.left)
                                                        mouse.release(Button.left)
                                                        head_last_shot_time = current_time
                                            except Exception:
                                                pass
                                        else:
                                            # Burst mode - fire exact number of shots specified
                                            try:
                                                # Check if enough time has passed since last burst
                                                if head_burst_shot_count == 0 or current_time - head_last_burst_time >= (head_between_shots_delay_ms / 1000.0):
                                                    # Click mouse exactly burst_shots times
                                                    actual_clicks = 0
                                                    i = 0
                                                    while i < head_burst_shots:
                                                        mouse.click(Button.left)
                                                        actual_clicks += 1
                                                        i += 1
                                                        # Delay between clicks to ensure CS2 registers them
                                                        if i < head_burst_shots:
                                                            time.sleep(0.1)
                                                    
                                                    # Mark burst as completed
                                                    head_burst_shot_count = actual_clicks
                                                    head_last_burst_time = current_time
                                                    if head_first_shot_time is not None:
                                                        head_first_shot_time = None
                                            except Exception:
                                                pass
                    except Exception:
                        pass
                        
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

    main_program()

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
        
        while True:
            try:
                bhop_enabled = settings.get("bhop_enabled", 0)
                
                if bhop_enabled == 1 and is_cs2_window_active():
                                                                                                
                    bhop_key_setting = settings.get("BhopKey", "SPACE")
                    activation_key = convert_key_to_keyboard_format(bhop_key_setting)
                    
                                                                        
                    try:
                        keyboard.is_pressed(activation_key)
                    except:
                        activation_key = "space"
                    
                    if keyboard.is_pressed(activation_key):
                        if toggle:
                            send_space(TICK_64_MS * 1.5)
                            
                            while keyboard.is_pressed(activation_key) and is_cs2_window_active():
                                send_space(TICK_64_MS * 3)
                    elif keyboard.is_pressed(toggle_key):
                        toggle = not toggle
                        time.sleep(0.2)
                    else:
                        time.sleep(0.001)
                else:
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                break
            except Exception:
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

    main_program()

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
         'aim_disable_when_crosshair_on_enemy': 0
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

                    
                    any_valid = any(p[0] != -999 and p[1] != -999 for p in bone_positions.values())
                    if any_valid:
                        target_list.append({
                            'bone_positions': bone_positions,
                            'deltaZ': deltaZ,
                            'entity_pawn_addr': entity_pawn_addr
                        })
                except Exception as e:
                    pass
            except:
                return
        return target_list

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
            screen_radius = radius / 100.0 * min(center_x, center_y)
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

        

                                                                   
        target_x, target_y = pos
        dx = target_x - center_x
        dy = target_y - center_y

                                      
        if smoothness is None:
            smoothness = 0

                                                                                      
                         

        if smoothness <= 0:
            move_x = int(dx)
            move_y = int(dy)
        else:
                                                                                     
                                                  
                                                              
            max_smoothness = float(globals().get('smooth_slider_max', 1000000))
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
        while True:
            target_list = []
            target_list = esp(pm, client, settings, target_list, window_size)
            
                           
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

            if pressed:
                                                
                smoothness = settings.get('aim_smoothness', 0)
                aimbot(target_list, settings['radius'], settings['aim_mode_distance'], smoothness, pm, client, offsets, client_dll)
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

    main_program()

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
    
                                                  
    setup_debug_console()
    debug_print("Starting Popsicle CS2 application...")
    
    try:
        multiprocessing.freeze_support()
    except Exception:
        pass

                                              
    version_thread = threading.Thread(target=version_check_worker, daemon=True)
    version_thread.start()
    debug_print("Version check worker started")

                                                        
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
        debug_print("CS2 is already running - proceeding with startup")
                                             
        if STARTUP_ENABLED:
            debug_print("Startup delays enabled - waiting 4 seconds")
            time.sleep(4)
            
                                     
            debug_print("Triggering graphics restart")
            trigger_graphics_restart()
            
                                                              
        pm = None
        try:
            pm = pymem.Pymem("cs2.exe")
            debug_print("Successfully connected to CS2 process")
        except Exception:
            debug_print("Failed to connect to CS2 process initially")
    else:
        debug_print("CS2 is not running - showing wait dialog")
                                                   
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
        multiprocessing.Process(target=aim),
        multiprocessing.Process(target=bhop),
        multiprocessing.Process(target=auto_accept_main),
    ]
    
    debug_print("Starting all processes...")
    for i, p in enumerate(procs):
        process_names = ["configurator", "esp_main", "triggerbot", "aim", "bhop", "auto_accept_main"]
        debug_print(f"Starting process: {process_names[i]}")
        p.start()

    try:
        
        
        while True:
            time.sleep(1)
            
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                break
                                                                                         
            if not is_cs2_running():
                pass
                break
    finally:
        for p in procs:
            try:
                if p.is_alive():
                    p.terminate()
                    p.join(1)
            except Exception:
                pass
        
                        
        remove_lock_file()
        try:
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                os.remove(TERMINATE_SIGNAL_FILE)
        except Exception:
            pass
        try:
            if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                os.remove(KEYBIND_COOLDOWNS_FILE)
        except Exception:
            pass
        sys.exit(0)
